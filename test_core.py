"""Quick smoke test for BioVerse core modules (includes novel features)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test 1: Crypto
from core.crypto import generate_key, encrypt_bytes, decrypt_bytes
key = generate_key()
enc = encrypt_bytes(b"Hello BioVerse!", key)
dec = decrypt_bytes(enc, key)
assert dec == b"Hello BioVerse!", "Crypto round-trip failed"
print("1. Crypto:       OK")

# Test 2: ECC
from core.ecc import ecc_encode, ecc_decode
ecc = ecc_encode(b"test-data")
orig = ecc_decode(ecc)
assert orig == b"test-data", "ECC round-trip failed"
print("2. ECC:          OK")

# Test 3: DNA analysis & realism scoring
from ai.dna_analysis import analyze_dna, realism_score
freq, gc, entropy = analyze_dna("ATGCGTACG" * 20)
assert 0 < gc < 1, "GC content out of range"
assert 0 < entropy <= 2.0, "Entropy out of range"
score = realism_score("ATGCGTACG" * 20)
assert 0 <= score["overall_realism"] <= 100
print(f"3. Analysis:     OK (GC={gc:.2f}, Entropy={entropy:.3f}, Realism={score['overall_realism']}%)")

# Test 4: Watermark (basic embed/extract)
from ai.watermark import embed_payload, extract_payload, verify_fingerprint
host = "ATGC" * 50
payload = "GGGCCC"
wm, idx = embed_payload(host, payload)
recovered = extract_payload(wm, len(payload), idx)
assert recovered == payload, "Watermark round-trip failed"
assert verify_fingerprint("ATGCATGC" * 5) == True
print("4. Watermark:    OK")

# Test 5: Encoder/Decoder binary-DNA round-trip (naive)
from core.encoder import bytes_to_binary, binary_to_dna
from core.decoder import dna_to_binary, binary_to_bytes
data = b"\x00\xff\x42\xab"
binary = bytes_to_binary(data)
dna = binary_to_dna(binary)
back_bin = dna_to_binary(dna)
back_bytes = binary_to_bytes(back_bin)
assert back_bytes == data, f"DNA round-trip failed: {back_bytes} != {data}"
print("5. DNA codec:    OK")

# Test 6: Bio-constrained encoding (NOVEL)
from core.bio_constraints import (
    constrained_binary_to_dna,
    constrained_dna_to_binary,
    encode_rotations,
    decode_rotations,
    compute_constraint_stats,
)
test_binary = bytes_to_binary(b"Hello, BioVerse! Bio-constrained DNA encoding test." * 3)
dna_c, rotations = constrained_binary_to_dna(test_binary)
stats = compute_constraint_stats(dna_c)
assert stats["constraint_compliant"], f"Constrained encoding not compliant: {stats}"
assert stats["max_homopolymer"] <= 3, f"Homopolymer {stats['max_homopolymer']} > 3"
# Round-trip check
rot_hex = encode_rotations(rotations)
rot_back = decode_rotations(rot_hex, len(rotations))
assert rot_back == rotations, "Rotation encode/decode round-trip failed"
binary_back = constrained_dna_to_binary(dna_c, rotations)
assert binary_back == test_binary, "Constrained DNA round-trip failed"
print(f"6. Constraints:  OK (compliant={stats['constraint_compliant']}, max_homo={stats['max_homopolymer']})")

# Test 7: Integrity hash (NOVEL)
from ai.watermark import embed_integrity_hash, verify_integrity
fp = "ATGCGTACGATGCGTACGATGCGTACGATGCGTACGATGCGTACGATGCGTACG" * 5
test_payload = "ATGCGTACGATGCGTACGATGCGATCGATCGATCGATCGATCG"
fp_with_hash, hash_val = embed_integrity_hash(fp, test_payload)
assert hash_val, "Hash should be non-empty"
check = verify_integrity(fp_with_hash, test_payload)
assert check["valid"], "Integrity should be valid for same payload"
assert not check["tampered"], "Should not be tampered"
# Tamper test
tampered_payload = test_payload.replace("A", "T", 1)
check_t = verify_integrity(fp_with_hash, tampered_payload)
if check_t["hash_found"]:
    assert check_t["tampered"], "Should detect tampering"
print(f"7. Integrity:    OK (hash={hash_val[:12]}...)")

# Test 8: Evaluation framework (NOVEL)
from core.evaluation import (
    evaluate_security,
    evaluate_ecc_resilience,
    evaluate_encoding_density,
    evaluate_biological_realism,
    compare_naive_vs_constrained,
)
sec = evaluate_security()
assert sec["key_size_bits"] == 128
ecc_eval = evaluate_ecc_resilience()
assert ecc_eval["max_correctable_errors"] == 16
density = evaluate_encoding_density(100, 2000)
assert 0 < density["bits_per_base"] < 2
bio = evaluate_biological_realism(dna_c)
assert 0 <= bio["realism_score"] <= 100
comp = compare_naive_vs_constrained(test_binary[:500])
assert "naive" in comp and "constrained" in comp and "improvement" in comp
print(f"8. Evaluation:   OK (security={sec['algorithm']}, density={density['bits_per_base']:.3f} b/base)")

print("\nAll core tests passed (including novel features)!")
