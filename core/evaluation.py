"""
BioVerse — Quantitative Evaluation Framework.

Novel contribution: A formal evaluation framework for DNA data encoding
systems that measures the tradeoff between:
  1. Data security (encryption strength, key space)
  2. Error resilience (ECC overhead, correctable error rate)
  3. Biological realism (GC balance, entropy, constraint compliance)
  4. Storage efficiency (encoding density, overhead ratio)

This module provides standardized benchmarks that can be reported in 
IEEE-format papers, comparing BioVerse's approach against baseline methods.
"""

import time
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def evaluate_encoding_density(original_bytes: int, dna_length: int) -> dict:
    """
    Evaluate storage efficiency of the DNA encoding.

    Theoretical maximum: 2 bits per nucleotide (4 bases → 2 bits).
    Practical density is lower due to encryption overhead, ECC, and
    constraint-aware encoding rotations.

    Returns:
        dict with density metrics.
    """
    theoretical_max_bits_per_base = 2.0
    original_bits = original_bytes * 8
    actual_bits_per_base = original_bits / max(dna_length, 1)
    efficiency = actual_bits_per_base / theoretical_max_bits_per_base

    return {
        "original_bits": original_bits,
        "dna_bases": dna_length,
        "bits_per_base": round(actual_bits_per_base, 4),
        "theoretical_max": theoretical_max_bits_per_base,
        "encoding_efficiency": round(efficiency * 100, 2),  # percentage
        "overhead_ratio": round(dna_length / max(original_bits / 2, 1), 4),
    }


def evaluate_security(key_size_bytes: int = 16) -> dict:
    """
    Evaluate security parameters of the encoding system.

    Reports key space size, encryption algorithm, and brute-force
    resistance estimate.
    """
    key_bits = key_size_bytes * 8
    key_space = 2 ** key_bits

    # Rough brute-force estimate: 10^9 keys/sec on modern hardware
    brute_force_years = key_space / (1e9 * 3600 * 24 * 365.25)

    return {
        "algorithm": "AES-CBC",
        "key_size_bits": key_bits,
        "key_space": f"2^{key_bits}",
        "brute_force_years": f"{brute_force_years:.2e}",
        "padding": "PKCS7",
        "mode": "CBC (with random IV)",
    }


def evaluate_ecc_resilience(ecc_symbols: int = 32) -> dict:
    """
    Evaluate error correction capability.

    Reed-Solomon with N parity symbols can correct up to N/2 symbol errors
    and detect up to N symbol errors.
    """
    correctable = ecc_symbols // 2
    detectable = ecc_symbols

    return {
        "algorithm": "Reed-Solomon",
        "parity_symbols": ecc_symbols,
        "max_correctable_errors": correctable,
        "max_detectable_errors": detectable,
        "overhead_bytes": ecc_symbols,
        "overhead_description": f"{ecc_symbols} parity bytes per block",
    }


def evaluate_biological_realism(dna_sequence: str) -> dict:
    """
    Comprehensive biological realism evaluation.

    Evaluates multiple criteria that determine if a DNA sequence
    would be viable for actual biological synthesis and sequencing.
    """
    from ai.dna_analysis import analyze_dna, realism_score
    from core.bio_constraints import compute_constraint_stats

    # Basic analysis
    freq, gc_content, entropy = analyze_dna(dna_sequence)
    realism = realism_score(dna_sequence)
    constraints = compute_constraint_stats(dna_sequence)

    # Dinucleotide frequency analysis (biological DNA has non-uniform dinuc freq)
    dinuc_counts = Counter()
    for i in range(len(dna_sequence) - 1):
        dinuc = dna_sequence[i:i+2]
        dinuc_counts[dinuc] += 1
    total_dinucs = max(sum(dinuc_counts.values()), 1)
    dinuc_freq = {k: round(v / total_dinucs, 4) for k, v in sorted(dinuc_counts.items())}

    # CpG ratio — in real DNA, CG dinucleotide is suppressed (~0.25x expected)
    expected_cg = freq.get('C', 0.25) * freq.get('G', 0.25)
    observed_cg = dinuc_freq.get('CG', 0)
    cpg_ratio = round(observed_cg / max(expected_cg, 1e-8), 3)

    return {
        "length": len(dna_sequence),
        "gc_content": round(gc_content, 4),
        "shannon_entropy": round(entropy, 4),
        "max_entropy": 2.0,
        "entropy_ratio": round(entropy / 2.0, 4),
        "base_frequency": freq,
        "realism_score": realism["overall_realism"],
        "gc_score": realism["gc_score"],
        "entropy_score": realism["entropy_score"],
        "balance_score": realism["balance_score"],
        "max_homopolymer_run": constraints["max_homopolymer"],
        "gc_windows_in_range": constraints["gc_windows_in_range"],
        "forbidden_motifs": constraints["forbidden_motifs_found"],
        "constraint_compliant": constraints["constraint_compliant"],
        "dinucleotide_freq": dinuc_freq,
        "cpg_ratio": cpg_ratio,
    }


def evaluate_pipeline_performance(
    input_path: str,
    dna_path: str,
    key_path: str,
    output_path: str,
) -> dict:
    """
    Full pipeline benchmark: encode → decode, measuring time and correctness.

    Returns comprehensive performance metrics.
    """
    import os
    from core.encoder import encode_file_to_dna
    from core.decoder import decode_dna_to_file

    # Encoding benchmark
    t0 = time.time()
    encode_stats = encode_file_to_dna(input_path, dna_path, key_path)
    encode_time = time.time() - t0

    # Decoding benchmark
    t0 = time.time()
    decode_stats = decode_dna_to_file(dna_path, key_path, output_path)
    decode_time = time.time() - t0

    # Verify correctness
    with open(input_path, "rb") as f:
        original = f.read()
    with open(output_path, "rb") as f:
        recovered = f.read()

    files_match = original == recovered

    return {
        "input_file": os.path.basename(input_path),
        "original_size_bytes": len(original),
        "dna_length_bases": encode_stats["dna_length"],
        "encode_time_sec": round(encode_time, 4),
        "decode_time_sec": round(decode_time, 4),
        "total_time_sec": round(encode_time + decode_time, 4),
        "encode_throughput_bps": round(len(original) / max(encode_time, 0.001), 1),
        "files_match": files_match,
        "lossless": files_match,
    }


def compare_naive_vs_constrained(binary_data: str) -> dict:
    """
    Compare naive 2-bit encoding vs. biologically-constrained encoding.

    This is a key comparison for the IEEE paper — demonstrates the
    improvement in biological realism with the constrained approach.
    """
    from core.bio_constraints import (
        constrained_binary_to_dna,
        compute_constraint_stats,
        NAIVE_MAP,
    )
    from ai.dna_analysis import realism_score

    # Ensure even length
    if len(binary_data) % 2 != 0:
        binary_data += '0'

    # Naive encoding
    naive_dna = ''.join(
        NAIVE_MAP[binary_data[i:i+2]]
        for i in range(0, len(binary_data), 2)
    )

    # Constrained encoding
    constrained_dna, rotations = constrained_binary_to_dna(binary_data)
    rotation_count = sum(1 for r in rotations if r > 0)

    # Analyze both
    naive_realism = realism_score(naive_dna)
    naive_constraints = compute_constraint_stats(naive_dna)

    constrained_realism = realism_score(constrained_dna)
    constrained_constraints = compute_constraint_stats(constrained_dna)

    return {
        "sequence_length": len(naive_dna),
        "naive": {
            "realism_score": naive_realism["overall_realism"],
            "gc_content": naive_realism["gc_content"],
            "entropy": naive_realism["entropy"],
            "max_homopolymer": naive_constraints["max_homopolymer"],
            "gc_windows_ok": naive_constraints["gc_windows_in_range"],
            "forbidden_motifs": len(naive_constraints["forbidden_motifs_found"]),
            "constraint_compliant": naive_constraints["constraint_compliant"],
        },
        "constrained": {
            "realism_score": constrained_realism["overall_realism"],
            "gc_content": constrained_realism["gc_content"],
            "entropy": constrained_realism["entropy"],
            "max_homopolymer": constrained_constraints["max_homopolymer"],
            "gc_windows_ok": constrained_constraints["gc_windows_in_range"],
            "forbidden_motifs": len(constrained_constraints["forbidden_motifs_found"]),
            "constraint_compliant": constrained_constraints["constraint_compliant"],
            "rotations_applied": rotation_count,
            "rotation_rate": round(rotation_count / max(len(rotations), 1) * 100, 2),
        },
        "improvement": {
            "realism_delta": round(
                constrained_realism["overall_realism"] - naive_realism["overall_realism"], 1
            ),
            "homopolymer_reduction": (
                naive_constraints["max_homopolymer"] - constrained_constraints["max_homopolymer"]
            ),
            "motifs_eliminated": (
                len(naive_constraints["forbidden_motifs_found"])
                - len(constrained_constraints["forbidden_motifs_found"])
            ),
        },
    }


def full_evaluation_report(input_path: str) -> dict:
    """
    Generate a complete evaluation report for IEEE paper.

    Runs all evaluation metrics and returns a consolidated report.
    """
    import os
    import tempfile
    from core.encoder import file_to_bytes, bytes_to_binary

    # Setup temp paths
    base = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = os.path.join(os.path.dirname(input_path), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    dna_path = os.path.join(output_dir, f"{base}_eval.dna.txt")
    key_path = os.path.join(output_dir, f"{base}_eval.key")
    out_path = os.path.join(output_dir, f"{base}_eval_recovered")

    # Read source data for comparison
    raw_bytes = file_to_bytes(input_path)
    binary = bytes_to_binary(raw_bytes)

    report = {
        "file": os.path.basename(input_path),
        "file_size_bytes": len(raw_bytes),
        "security": evaluate_security(),
        "ecc": evaluate_ecc_resilience(),
        "performance": evaluate_pipeline_performance(
            input_path, dna_path, key_path, out_path
        ),
    }

    # Read the generated DNA for realism analysis
    with open(dna_path, "r") as f:
        content = f.read()
    # Extract payload
    lines = content.split("\n")
    payload = ""
    started = False
    for line in lines:
        line = line.strip()
        if line == "PAYLOAD:":
            started = True
        elif started:
            payload += line

    report["biological_realism"] = evaluate_biological_realism(payload)
    report["encoding_density"] = evaluate_encoding_density(len(raw_bytes), len(payload))
    report["naive_vs_constrained"] = compare_naive_vs_constrained(binary)

    return report


if __name__ == "__main__":
    import json
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    # Create test file
    test_path = "data/input/eval_test.txt"
    os.makedirs("data/input", exist_ok=True)
    with open(test_path, "w") as f:
        f.write("BioVerse Evaluation Framework Test Data. " * 20)

    report = full_evaluation_report(test_path)
    print(json.dumps(report, indent=2, default=str))
