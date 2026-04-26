import os
import logging
from core.crypto import decrypt_bytes
from core.ecc import ecc_decode
from core.bio_constraints import (
    constrained_dna_to_binary,
    decode_rotations,
    compute_constraint_stats,
)
from ai.watermark import verify_integrity, verify_fingerprint

logger = logging.getLogger(__name__)

# Reverse DNA mapping (for backward compatibility with naive-encoded files)
DNA_REVERSE_MAP = {"A": "00", "T": "01", "G": "10", "C": "11"}


def dna_to_binary(dna: str) -> str:
    """Convert a DNA nucleotide sequence back to binary (naive mapping)."""
    invalid = set(dna.upper()) - {'A', 'T', 'G', 'C'}
    if invalid:
        raise ValueError(f"Invalid DNA bases found: {invalid}")
    return ''.join(DNA_REVERSE_MAP[base] for base in dna.upper())


def binary_to_bytes(binary: str) -> bytes:
    """Convert a binary string to bytes (truncates to 8-bit boundary)."""
    usable = len(binary) - (len(binary) % 8)
    return bytes(
        int(binary[i:i+8], 2)
        for i in range(0, usable, 8)
    )


def parse_dna_file(dna_path: str) -> dict:
    """
    Parse a BioVerse DNA file and extract all metadata.
    
    Supports both new format (with ROTATIONS/HASH) and legacy format.
    
    Returns dict with: fingerprint, payload_dna, rotation_hex, 
    rotation_count, payload_hash, is_constrained.
    """
    if not os.path.exists(dna_path):
        raise FileNotFoundError(f"DNA file not found: {dna_path}")

    with open(dna_path, "r") as f:
        lines = f.readlines()

    fingerprint = ""
    payload_dna = ""
    rotation_hex = ""
    rotation_count = 0
    payload_hash = ""
    payload_started = False

    for line in lines:
        line = line.strip()
        if line.startswith("FINGERPRINT:"):
            fingerprint = line.split("FINGERPRINT:", 1)[1]
        elif line.startswith("ROTATIONS:"):
            rotation_hex = line.split("ROTATIONS:", 1)[1]
        elif line.startswith("ROTATION_COUNT:"):
            rotation_count = int(line.split("ROTATION_COUNT:", 1)[1])
        elif line.startswith("HASH:"):
            payload_hash = line.split("HASH:", 1)[1]
        elif line == "PAYLOAD:":
            payload_started = True
            continue
        elif payload_started:
            payload_dna += line

    is_constrained = bool(rotation_hex and rotation_count > 0)

    return {
        "fingerprint": fingerprint,
        "payload_dna": payload_dna,
        "rotation_hex": rotation_hex,
        "rotation_count": rotation_count,
        "payload_hash": payload_hash,
        "is_constrained": is_constrained,
    }


def decode_dna_to_file(dna_path: str, key_path: str, output_path: str) -> dict:
    """
    Full decoding pipeline with novel integrity verification:
      DNA -> Binary (constrained or naive) -> ECC -> AES -> File.
    
    Returns metadata dict with decoding statistics and integrity check.
    """
    # 1. Parse DNA file
    parsed = parse_dna_file(dna_path)
    payload_dna = parsed["payload_dna"]
    fingerprint = parsed["fingerprint"]

    if not payload_dna:
        raise ValueError("No DNA payload found in file")

    logger.info(
        f"Payload: {len(payload_dna)} bases, "
        f"Fingerprint: {len(fingerprint)} bases, "
        f"Constrained: {parsed['is_constrained']}"
    )

    # 2. Read AES key
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Key file not found: {key_path}")
    with open(key_path, "rb") as f:
        key = f.read()

    # 3. DNA -> Binary (constrained or naive depending on file format)
    if parsed["is_constrained"]:
        rotations = decode_rotations(parsed["rotation_hex"], parsed["rotation_count"])
        binary = constrained_dna_to_binary(payload_dna, rotations)
        logger.info("Using constrained decoding with rotation flags")
    else:
        binary = dna_to_binary(payload_dna)
        logger.info("Using naive decoding (legacy format)")

    # 4. Binary -> ECC bytes
    ecc_bytes = binary_to_bytes(binary)

    # 5. ECC decode (error correction)
    encrypted_bytes = ecc_decode(ecc_bytes)

    # 6. AES decrypt
    original_bytes = decrypt_bytes(encrypted_bytes, key)

    # 7. Write recovered file
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(original_bytes)

    logger.info(f"Decoding complete -> {output_path}")

    # 8. Integrity verification (NOVEL - tamper detection)
    integrity = {"valid": False, "tampered": False, "hash_found": False}
    if fingerprint and payload_dna:
        integrity = verify_integrity(fingerprint, payload_dna)
        if integrity["valid"]:
            logger.info("Integrity check PASSED — payload not tampered")
        elif integrity["hash_found"]:
            logger.warning("Integrity check FAILED — possible tampering detected!")

    # 9. Constraint compliance of the payload
    constraint_stats = compute_constraint_stats(payload_dna)

    return {
        "payload_bases": len(payload_dna),
        "fingerprint_bases": len(fingerprint),
        "fingerprint": fingerprint,
        "recovered_size": len(original_bytes),
        "encoding_mode": "constrained" if parsed["is_constrained"] else "naive",
        # Novel: integrity verification
        "integrity": integrity,
        # Novel: constraint analysis
        "constraint_compliant": constraint_stats["constraint_compliant"],
        "max_homopolymer": constraint_stats["max_homopolymer"],
    }


if __name__ == "__main__":
    stats = decode_dna_to_file(
        "../data/output/sample_encoded.dna.txt",
        "../data/output/aes.key",
        "../data/output/recovered_sample.txt"
    )
    print("Decoding completed successfully")
    print(f"Stats: {stats}")
