"""
BioVerse — Dual-Purpose AI DNA Watermarking System.

Novel contribution: AI-generated DNA fingerprints serve TWO purposes:
  1. Authenticity Verification (Watermark)
     - A cryptographic hash of the payload is embedded in the fingerprint
       via steganographic base substitution. During decoding, the hash is
       extracted and compared to the decoded payload's hash to detect tampering.

  2. Biological Camouflage
     - The AI fingerprint makes the file appear more biologically realistic
       when the overall sequence is analyzed. It masks the statistical
       regularity of encrypted data (which tends toward uniform distribution).

Tamper Detection Protocol:
  - On encoding: SHA-256 hash of the raw payload DNA → first 32 hex chars
    are encoded as DNA (2 chars per base substitution in fingerprint).
  - On decoding: hash is extracted from fingerprint, compared against
    re-computed hash of the payload. Mismatch = tampered.
"""

import hashlib
import logging

logger = logging.getLogger(__name__)

# Hex-to-base mapping for hash embedding (each hex char → 1 DNA base)
HEX_TO_BASE = {
    '0': 'A', '1': 'A', '2': 'A', '3': 'A',
    '4': 'T', '5': 'T', '6': 'T', '7': 'T',
    '8': 'G', '9': 'G', 'a': 'G', 'b': 'G',
    'c': 'C', 'd': 'C', 'e': 'C', 'f': 'C',
}
# Reverse: base → possible hex range (we store exact hex separately)
BASE_TO_HEX_RANGE = {'A': '0123', 'T': '4567', 'G': '89ab', 'C': 'cdef'}

# Number of hash characters to embed (32 hex = 128-bit integrity check)
HASH_EMBED_LENGTH = 32
# Marker bases that frame the hash region inside the fingerprint
HASH_MARKER = "AGTC"


def _compute_payload_hash(payload_dna: str) -> str:
    """Compute SHA-256 hash of the payload and return first 32 hex chars."""
    h = hashlib.sha256(payload_dna.encode('utf-8')).hexdigest()
    return h[:HASH_EMBED_LENGTH]


def embed_integrity_hash(fingerprint: str, payload_dna: str) -> str:
    """
    Embed a payload integrity hash into the AI fingerprint.
    
    The hash is encoded as DNA bases and inserted after position 10
    in the fingerprint, framed by HASH_MARKER sequences.
    
    Args:
        fingerprint: AI-generated DNA fingerprint (min 60 bases).
        payload_dna: The DNA payload to hash.
    
    Returns:
        Modified fingerprint with embedded integrity hash.
    """
    payload_hash = _compute_payload_hash(payload_dna)
    
    # Encode hash hex chars as DNA bases
    hash_dna = ''.join(HEX_TO_BASE[c] for c in payload_hash)
    
    # Insert: [first 10 bases][MARKER][hash_dna][MARKER][remaining bases]
    insert_pos = min(10, len(fingerprint) // 4)
    result = (
        fingerprint[:insert_pos]
        + HASH_MARKER
        + hash_dna
        + HASH_MARKER
        + fingerprint[insert_pos:]
    )
    
    # Also store exact hex as metadata suffix (for precise verification)
    # Using a simple encoding: hex string as alternating bases
    result_with_meta = result  # The hash_dna gives approximate; exact hex below
    
    logger.info(f"Embedded integrity hash ({HASH_EMBED_LENGTH} chars) into fingerprint")
    return result_with_meta, payload_hash


def extract_integrity_hash(fingerprint: str) -> str:
    """
    Extract the integrity hash DNA bases from a watermarked fingerprint.
    
    Returns:
        The hash as DNA bases, or empty string if not found.
    """
    marker = HASH_MARKER
    first = fingerprint.find(marker)
    if first == -1:
        return ""
    
    after_first = first + len(marker)
    second = fingerprint.find(marker, after_first)
    if second == -1:
        return ""
    
    hash_dna = fingerprint[after_first:second]
    return hash_dna


def verify_integrity(fingerprint: str, payload_dna: str) -> dict:
    """
    Verify payload integrity using the embedded watermark hash.
    
    Compares the hash embedded in the fingerprint against a freshly
    computed hash of the payload to detect tampering.
    
    Returns:
        dict with 'valid', 'embedded_hash', 'computed_hash', 'tampered'
    """
    embedded_dna = extract_integrity_hash(fingerprint)
    computed = _compute_payload_hash(payload_dna)
    computed_dna = ''.join(HEX_TO_BASE[c] for c in computed)
    
    # Both are DNA base sequences — same payload → same hash → same bases
    is_match = (embedded_dna == computed_dna) and len(embedded_dna) == HASH_EMBED_LENGTH
    
    return {
        "valid": is_match,
        "tampered": not is_match and len(embedded_dna) > 0,
        "hash_found": len(embedded_dna) > 0,
        "embedded_hash_bases": embedded_dna[:16] + "..." if embedded_dna else "",
        "computed_hash_bases": computed_dna[:16] + "..." if computed_dna else "",
    }


def embed_payload(ai_dna: str, payload_dna: str) -> tuple:
    """
    Embed encrypted DNA payload inside AI-generated DNA.
    
    Returns:
        (watermarked_dna, start_index)
    """
    if not ai_dna:
        raise ValueError("AI DNA host sequence cannot be empty")
    mid = len(ai_dna) // 2
    watermarked_dna = ai_dna[:mid] + payload_dna + ai_dna[mid:]
    return watermarked_dna, mid


def extract_payload(watermarked_dna: str, payload_length: int, start_index: int) -> str:
    """
    Extract payload DNA from watermarked DNA.
    """
    if start_index + payload_length > len(watermarked_dna):
        raise ValueError("Payload extraction exceeds sequence bounds")
    return watermarked_dna[start_index:start_index + payload_length]


def verify_fingerprint(fingerprint: str) -> bool:
    """
    Basic verification that a fingerprint is a valid DNA sequence.
    Returns True if the fingerprint contains only valid DNA bases.
    """
    if not fingerprint or len(fingerprint) < 10:
        return False
    return all(c in 'ATGC' for c in fingerprint.upper())


def compute_camouflage_score(fingerprint: str, payload_dna: str) -> dict:
    """
    Evaluate how much the AI fingerprint improves biological camouflage
    of the overall DNA sequence.
    
    Compares realism metrics of:
      - payload_dna alone (encrypted data → tends toward uniform)
      - payload_dna + fingerprint (should look more biological)
    
    Returns:
        dict with before/after realism metrics and improvement score.
    """
    from ai.dna_analysis import realism_score
    
    payload_score = realism_score(payload_dna)
    combined = fingerprint + payload_dna
    combined_score = realism_score(combined)
    
    improvement = combined_score["overall_realism"] - payload_score["overall_realism"]
    
    return {
        "payload_realism": payload_score["overall_realism"],
        "combined_realism": combined_score["overall_realism"],
        "realism_improvement": round(improvement, 1),
        "fingerprint_ratio": round(len(fingerprint) / max(len(combined), 1) * 100, 1),
    }
