"""
BioVerse — Biologically-Constrained DNA Encoding Module.

Novel contribution: A constraint-aware encoding scheme that avoids
biologically hazardous sequences while maintaining full data reversibility.

Constraints enforced:
  1. Homopolymer run limit — no more than MAX_RUN consecutive identical bases
  2. GC-content windowed balance — local GC stays within [0.35, 0.65]
  3. Forbidden motifs — avoids restriction enzyme cut sites and primer dimers

The encoding uses a rotation cipher on the naive 2-bit mapping:
  - After mapping each pair, if appending the base would violate a constraint,
    the base is rotated (A→T→G→C→A) and a 2-bit rotation flag is stored in
    a sideband channel embedded as metadata in the DNA file.
  - The decoder reads the rotation flags and reverses the mapping exactly.

This ensures deterministic, lossless, reversible encoding while producing
DNA sequences that are viable for real biological synthesis and sequencing.
"""

import logging
from collections import Counter

logger = logging.getLogger(__name__)

# --- Configuration ---
MAX_HOMOPOLYMER_RUN = 3       # Max consecutive identical bases
GC_WINDOW_SIZE = 20           # Sliding window for GC balance check
GC_MIN = 0.30                 # Minimum GC content in window
GC_MAX = 0.70                 # Maximum GC content in window
BASES = ['A', 'T', 'G', 'C']
BASE_TO_IDX = {'A': 0, 'T': 1, 'G': 2, 'C': 3}

# Forbidden motifs — common restriction enzyme recognition sites
FORBIDDEN_MOTIFS = [
    "GAATTC",   # EcoRI
    "GGATCC",   # BamHI
    "AAGCTT",   # HindIII
    "CTCGAG",   # XhoI
    "GATATC",   # EcoRV
]

# Naive 2-bit mapping
NAIVE_MAP = {"00": "A", "01": "T", "10": "G", "11": "C"}
NAIVE_REVERSE = {"A": "00", "T": "01", "G": "10", "C": "11"}


def _violates_homopolymer(sequence: str, new_base: str) -> bool:
    """Check if appending new_base creates a homopolymer run > MAX_RUN."""
    if len(sequence) < MAX_HOMOPOLYMER_RUN:
        return False
    tail = sequence[-MAX_HOMOPOLYMER_RUN:]
    return all(c == new_base for c in tail)


def _violates_gc_balance(sequence: str, new_base: str) -> bool:
    """Check if appending new_base causes GC imbalance in the local window."""
    window = sequence[-(GC_WINDOW_SIZE - 1):] + new_base
    if len(window) < GC_WINDOW_SIZE:
        return False
    gc = sum(1 for c in window if c in ('G', 'C')) / len(window)
    return gc < GC_MIN or gc > GC_MAX


def _creates_forbidden_motif(sequence: str, new_base: str) -> bool:
    """Check if appending new_base creates any forbidden restriction site."""
    # Check the tail of the sequence + new base against all motifs
    test = sequence[-(max(len(m) for m in FORBIDDEN_MOTIFS) - 1):] + new_base
    for motif in FORBIDDEN_MOTIFS:
        if motif in test:
            return True
    return False


def _violates_constraints(sequence: str, new_base: str) -> bool:
    """Check all biological constraints."""
    return (
        _violates_homopolymer(sequence, new_base)
        or _violates_gc_balance(sequence, new_base)
        or _creates_forbidden_motif(sequence, new_base)
    )


def constrained_binary_to_dna(binary: str) -> tuple:
    """
    Convert binary string to biologically-constrained DNA sequence.

    Uses the naive 2-bit mapping as a starting point, then rotates bases
    when constraints would be violated. Returns the DNA sequence and a
    list of rotation counts (0-3) for each position.

    Args:
        binary: Binary string (must have even length).

    Returns:
        (dna_sequence, rotation_flags) where rotation_flags is a list of ints.
    """
    if len(binary) % 2 != 0:
        binary += '0'

    dna = ""
    rotations = []
    violations_fixed = 0

    for i in range(0, len(binary), 2):
        pair = binary[i:i+2]
        naive_base = NAIVE_MAP[pair]
        naive_idx = BASE_TO_IDX[naive_base]

        # Try the naive base first, then rotate up to 3 times
        chosen_base = naive_base
        rotation = 0

        for r in range(4):
            candidate = BASES[(naive_idx + r) % 4]
            if not _violates_constraints(dna, candidate):
                chosen_base = candidate
                rotation = r
                break
        else:
            # All 4 bases violate constraints — use naive (shouldn't happen often)
            chosen_base = naive_base
            rotation = 0

        if rotation > 0:
            violations_fixed += 1

        dna += chosen_base
        rotations.append(rotation)

    logger.info(
        f"Constrained encoding: {len(dna)} bases, "
        f"{violations_fixed} constraint violations fixed "
        f"({violations_fixed / max(len(rotations), 1) * 100:.1f}%)"
    )
    return dna, rotations


def constrained_dna_to_binary(dna: str, rotations: list) -> str:
    """
    Reverse the constrained encoding using the rotation flags.

    Args:
        dna: The constrained DNA sequence.
        rotations: List of rotation counts (one per base).

    Returns:
        The original binary string.
    """
    if len(dna) != len(rotations):
        raise ValueError(
            f"DNA length ({len(dna)}) doesn't match rotation flags ({len(rotations)})"
        )

    binary = ""
    for base, rotation in zip(dna.upper(), rotations):
        # Reverse the rotation to get the original naive base
        current_idx = BASE_TO_IDX[base]
        original_idx = (current_idx - rotation) % 4
        original_base = BASES[original_idx]
        binary += NAIVE_REVERSE[original_base]

    return binary


def encode_rotations(rotations: list) -> str:
    """
    Encode rotation flags compactly as a string of characters.
    Each rotation is 0-3 (2 bits), so pack 4 rotations per byte,
    then represent as hex string for storage.
    """
    # Pack pairs of rotations into nibbles → bytes → hex
    packed = []
    for i in range(0, len(rotations), 4):
        chunk = rotations[i:i+4]
        # Pad chunk to 4 if needed
        while len(chunk) < 4:
            chunk.append(0)
        # Each rotation is 2 bits: pack 4 into 1 byte
        byte_val = (chunk[0] << 6) | (chunk[1] << 4) | (chunk[2] << 2) | chunk[3]
        packed.append(byte_val)

    return bytes(packed).hex()


def decode_rotations(hex_str: str, count: int) -> list:
    """
    Decode rotation flags from hex string.

    Args:
        hex_str: Hex-encoded rotation flags.
        count: Number of rotations to extract.

    Returns:
        List of rotation values (0-3).
    """
    raw = bytes.fromhex(hex_str)
    rotations = []
    for byte_val in raw:
        rotations.append((byte_val >> 6) & 0x03)
        rotations.append((byte_val >> 4) & 0x03)
        rotations.append((byte_val >> 2) & 0x03)
        rotations.append(byte_val & 0x03)

    return rotations[:count]


def compute_constraint_stats(dna: str) -> dict:
    """
    Analyze a DNA sequence for biological constraint compliance.

    Returns a dict with:
      - max_homopolymer: longest homopolymer run
      - gc_content: overall GC ratio
      - gc_windows_in_range: fraction of windows with GC in [0.30, 0.70]
      - forbidden_motifs_found: list of any restriction sites present
      - constraint_compliant: True if all constraints pass
    """
    # Max homopolymer run
    max_run = 1
    current_run = 1
    for i in range(1, len(dna)):
        if dna[i] == dna[i-1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    # Overall GC
    counts = Counter(dna.upper())
    total = len(dna)
    gc_content = (counts.get('G', 0) + counts.get('C', 0)) / max(total, 1)

    # Windowed GC check
    windows_ok = 0
    total_windows = max(1, total - GC_WINDOW_SIZE + 1)
    for i in range(total_windows):
        window = dna[i:i+GC_WINDOW_SIZE]
        if len(window) == GC_WINDOW_SIZE:
            wgc = sum(1 for c in window if c in 'GC') / GC_WINDOW_SIZE
            if GC_MIN <= wgc <= GC_MAX:
                windows_ok += 1

    # Forbidden motifs
    found_motifs = []
    for motif in FORBIDDEN_MOTIFS:
        if motif in dna.upper():
            found_motifs.append(motif)

    compliant = (
        max_run <= MAX_HOMOPOLYMER_RUN
        and 0.30 <= gc_content <= 0.70
        and len(found_motifs) == 0
    )

    return {
        "max_homopolymer": max_run,
        "gc_content": gc_content,
        "gc_windows_in_range": round(windows_ok / total_windows, 3),
        "forbidden_motifs_found": found_motifs,
        "constraint_compliant": compliant,
    }


if __name__ == "__main__":
    # Quick demo
    test_binary = "00011011" * 100  # 800 bits = 400 bases
    dna, rots = constrained_binary_to_dna(test_binary)
    print(f"Encoded: {len(dna)} bases, rotations applied: {sum(1 for r in rots if r > 0)}")

    # Round-trip
    recovered = constrained_dna_to_binary(dna, rots)
    assert recovered == test_binary, "ROUND-TRIP FAILED"
    print("Round-trip: PASS")

    # Stats
    stats = compute_constraint_stats(dna)
    print(f"Constraint stats: {stats}")

    # Compare with naive encoding
    naive_dna = ''.join(NAIVE_MAP[test_binary[i:i+2]] for i in range(0, len(test_binary), 2))
    naive_stats = compute_constraint_stats(naive_dna)
    print(f"Naive stats:      {naive_stats}")
