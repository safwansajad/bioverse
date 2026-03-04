"""End-to-end pipeline test for BioVerse (with novel-feature validation)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a test file
test_content = b"BioVerse end-to-end test! This file should survive the full pipeline."
os.makedirs("data/input", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
with open("data/input/test_e2e.txt", "wb") as f:
    f.write(test_content)

from core.encoder import encode_file_to_dna
from core.decoder import decode_dna_to_file

# ===== ENCODE =====
stats = encode_file_to_dna(
    "data/input/test_e2e.txt",
    "data/output/test_e2e.dna.txt",
    "data/output/test_e2e.key"
)
print(f"Encoded: {stats['original_size']}B -> {stats['dna_length']} DNA bases")
print(f"GC Content: {stats['gc_content']:.2%}, Entropy: {stats['entropy']:.3f}")
print(f"Fingerprint: {stats['fingerprint_length']} bases, FP-GC: {stats['fp_gc_content']:.2%}")

# Novel: constraint compliance
print(f"\n--- Novel Feature Checks ---")
print(f"Constrained compliant: {stats['constraint_compliant']}")
print(f"Max homopolymer:       {stats['max_homopolymer']}")
print(f"Rotations applied:     {stats['rotations_applied']} ({stats['rotation_rate']}%)")
print(f"Realism:               {stats['realism_score']}% (naive: {stats['naive_realism_score']}%)")
print(f"Integrity hash:        {stats['payload_hash'][:16]}...")
print(f"Camouflage GC delta:   {stats['camouflage'].get('gc_delta', 'N/A')}")

assert stats['constraint_compliant'], "Encoding should be constraint-compliant"
assert stats['max_homopolymer'] <= 3, f"Homopolymer run {stats['max_homopolymer']} > 3"
assert stats['payload_hash'], "Integrity hash should be non-empty"

# ===== DECODE =====
ds = decode_dna_to_file(
    "data/output/test_e2e.dna.txt",
    "data/output/test_e2e.key",
    "data/output/test_e2e_recovered.txt"
)
print(f"\nDecoded: {ds['recovered_size']}B recovered, Fingerprint: {ds['fingerprint_bases']} bases")
print(f"Encoding mode: {ds['encoding_mode']}")
print(f"Integrity valid: {ds['integrity']['valid']}")
print(f"Tampered:        {ds['integrity']['tampered']}")

assert ds['encoding_mode'] == 'constrained', "Should detect constrained encoding"
assert ds['integrity']['valid'], "Integrity check should PASS"
assert not ds['integrity']['tampered'], "Tamper flag should be False"

# ===== LOSSLESS CHECK =====
with open("data/input/test_e2e.txt", "rb") as f:
    original = f.read()
with open("data/output/test_e2e_recovered.txt", "rb") as f:
    recovered = f.read()

assert original == recovered, f"MISMATCH! {len(original)} vs {len(recovered)}"
print(f"\nE2E PASS: Files match perfectly ({len(original)} bytes)")
print("All novel features validated!")
