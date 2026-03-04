import os
import logging
from core.crypto import generate_key, encrypt_bytes
from core.ecc import ecc_encode
from core.bio_constraints import (
    constrained_binary_to_dna,
    encode_rotations,
    compute_constraint_stats,
    NAIVE_MAP,
)
from ai.generate_dna import generate_dna
from ai.dna_analysis import analyze_dna, realism_score
from ai.watermark import embed_integrity_hash, compute_camouflage_score

logger = logging.getLogger(__name__)


def file_to_bytes(file_path: str) -> bytes:
    """Read a file and return its raw bytes."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    with open(file_path, "rb") as f:
        return f.read()


def bytes_to_binary(data: bytes) -> str:
    """Convert bytes to a binary string (8 bits per byte)."""
    return ''.join(format(byte, '08b') for byte in data)


def binary_to_dna(binary: str) -> str:
    """
    Convert a binary string to a DNA nucleotide sequence (naive mapping).
    Mapping: 00->A, 01->T, 10->G, 11->C
    Kept for backward compatibility and comparison benchmarks.
    """
    if len(binary) % 2 != 0:
        binary += '0'
    return ''.join(NAIVE_MAP[binary[i:i+2]] for i in range(0, len(binary), 2))


def encode_file_to_dna(input_path: str, dna_path: str, key_path: str) -> dict:
    """
    Full encoding pipeline with novel features:
      File -> AES -> ECC -> Constrained DNA + AI Fingerprint + Integrity Hash.
    
    Returns metadata dict with encoding statistics.
    """
    # 1. Read file
    raw_bytes = file_to_bytes(input_path)
    original_size = len(raw_bytes)
    logger.info(f"Read {original_size} bytes from {input_path}")

    # 2. Generate AES key
    key = generate_key()

    # 3. Encrypt
    encrypted_bytes = encrypt_bytes(raw_bytes, key)

    # 4. Apply Reed-Solomon ECC
    ecc_bytes = ecc_encode(encrypted_bytes)

    # 5. Convert to binary
    binary = bytes_to_binary(ecc_bytes)

    # 6. Biologically-constrained DNA encoding (NOVEL)
    payload_dna, rotations = constrained_binary_to_dna(binary)
    rotation_hex = encode_rotations(rotations)
    rotation_count = sum(1 for r in rotations if r > 0)

    # 7. Generate AI DNA fingerprint
    fingerprint_dna = generate_dna(length=120, temperature=1.0)

    # 8. Embed integrity hash into fingerprint (NOVEL - tamper detection)
    fingerprint_with_hash, payload_hash = embed_integrity_hash(
        fingerprint_dna, payload_dna
    )

    # 9. Analyze DNA quality
    freq, gc_content, entropy = analyze_dna(payload_dna)
    fp_freq, fp_gc, fp_entropy = analyze_dna(fingerprint_with_hash)
    payload_realism = realism_score(payload_dna)
    constraint_stats = compute_constraint_stats(payload_dna)

    # 10. Compute camouflage score (NOVEL)
    camouflage = compute_camouflage_score(fingerprint_with_hash, payload_dna)

    # 11. Also compute naive encoding for comparison
    naive_dna = binary_to_dna(binary)
    naive_realism = realism_score(naive_dna)
    naive_constraints = compute_constraint_stats(naive_dna)

    # 12. Save DNA file with all metadata
    with open(dna_path, "w") as f:
        f.write(f"FINGERPRINT:{fingerprint_with_hash}\n")
        f.write(f"ROTATIONS:{rotation_hex}\n")
        f.write(f"ROTATION_COUNT:{len(rotations)}\n")
        f.write(f"HASH:{payload_hash}\n")
        f.write("PAYLOAD:\n")
        f.write(payload_dna)

    # 13. Save AES key
    with open(key_path, "wb") as f:
        f.write(key)

    logger.info(f"Encoding complete -> {dna_path}")

    return {
        "original_size": original_size,
        "encrypted_size": len(encrypted_bytes),
        "ecc_size": len(ecc_bytes),
        "dna_length": len(payload_dna),
        "fingerprint_length": len(fingerprint_with_hash),
        "gc_content": gc_content,
        "entropy": entropy,
        "base_freq": freq,
        "fp_gc_content": fp_gc,
        "fp_entropy": fp_entropy,
        # Novel: constraint compliance
        "constraint_compliant": constraint_stats["constraint_compliant"],
        "max_homopolymer": constraint_stats["max_homopolymer"],
        "gc_windows_in_range": constraint_stats["gc_windows_in_range"],
        "forbidden_motifs": constraint_stats["forbidden_motifs_found"],
        "rotations_applied": rotation_count,
        "rotation_rate": round(rotation_count / max(len(rotations), 1) * 100, 2),
        # Novel: realism comparison
        "realism_score": payload_realism["overall_realism"],
        "naive_realism_score": naive_realism["overall_realism"],
        "realism_improvement": round(
            payload_realism["overall_realism"] - naive_realism["overall_realism"], 1
        ),
        "naive_max_homopolymer": naive_constraints["max_homopolymer"],
        "naive_constraint_compliant": naive_constraints["constraint_compliant"],
        # Novel: camouflage
        "camouflage": camouflage,
        # Integrity
        "payload_hash": payload_hash,
    }


if __name__ == "__main__":
    stats = encode_file_to_dna(
        "../data/input/sample.txt",
        "../data/output/sample_encoded.dna.txt",
        "../data/output/aes.key"
    )
    print("Encoding completed with AI fingerprint")
    print(f"Stats: {stats}")
