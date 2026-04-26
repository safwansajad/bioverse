"""
BioVerse — Benchmark Suite for IEEE Paper.

Produces measured numbers for:
  1. Pipeline performance (encode/decode time, throughput) over multiple
     file sizes, reported as mean +/- std over N runs.
  2. Constraint compliance (naive vs constrained) on real input data.
  3. Error-injection resilience: inject random base substitutions into the
     payload at increasing rates and report Reed-Solomon recovery success.
  4. Integrity (tamper) detection: flip bases and confirm the embedded
     hash check fires.

Outputs:
  - benchmarks/results.json   (raw numbers)
  - benchmarks/tables.tex     (LaTeX-ready table fragments)

Usage:
  python -m benchmarks.run_benchmarks
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

# Make the project root importable when invoked as a script.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.encoder import encode_file_to_dna, bytes_to_binary  # noqa: E402
from core.decoder import decode_dna_to_file, parse_dna_file  # noqa: E402
from core.evaluation import compare_naive_vs_constrained  # noqa: E402
from ai.watermark import verify_integrity  # noqa: E402


SIZES = [128, 1024, 8 * 1024, 64 * 1024]   # bytes
RUNS = 5                                    # repetitions per size
ERROR_RATES = [0.000, 0.001, 0.005, 0.010, 0.020, 0.050]
TAMPER_TRIALS = 50

OUT_DIR = ROOT / "benchmarks"
OUT_DIR.mkdir(exist_ok=True)
WORK_DIR = OUT_DIR / "_work"
WORK_DIR.mkdir(exist_ok=True)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _make_input(size: int, seed: int = 0) -> Path:
    """Create a deterministic pseudo-random input file of the given size."""
    rng = random.Random(seed)
    path = WORK_DIR / f"input_{size}_{seed}.bin"
    path.write_bytes(bytes(rng.randrange(256) for _ in range(size)))
    return path


def _time(fn: Callable, *args, **kwargs):
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, time.perf_counter() - t0


def _mutate_dna(dna: str, rate: float, seed: int) -> str:
    """Substitute each base independently with prob `rate` to a different base."""
    if rate <= 0:
        return dna
    rng = random.Random(seed)
    bases = "ATGC"
    out = []
    for b in dna:
        if rng.random() < rate:
            choices = bases.replace(b, "")
            out.append(rng.choice(choices))
        else:
            out.append(b)
    return "".join(out)


def _rewrite_dna_file(src: Path, dst: Path, new_payload: str) -> None:
    """Rewrite a DNA file replacing only the PAYLOAD section."""
    text = src.read_text().splitlines()
    out_lines, in_payload = [], False
    for line in text:
        if line == "PAYLOAD:":
            out_lines.append(line)
            in_payload = True
            continue
        if in_payload:
            continue
        out_lines.append(line)
    out_lines.append(new_payload)
    dst.write_text("\n".join(out_lines))


# --------------------------------------------------------------------------
# 1. Pipeline performance
# --------------------------------------------------------------------------

def bench_performance() -> list[dict]:
    rows = []
    for size in SIZES:
        encode_times, decode_times, dna_lengths = [], [], []
        lossless_runs = 0
        for run in range(RUNS):
            inp = _make_input(size, seed=run)
            dna = WORK_DIR / f"perf_{size}_{run}.dna.txt"
            key = WORK_DIR / f"perf_{size}_{run}.key"
            rec = WORK_DIR / f"perf_{size}_{run}.recovered"

            stats, t_enc = _time(encode_file_to_dna, str(inp), str(dna), str(key))
            _, t_dec = _time(decode_dna_to_file, str(dna), str(key), str(rec))

            encode_times.append(t_enc)
            decode_times.append(t_dec)
            dna_lengths.append(stats["dna_length"])
            if rec.read_bytes() == inp.read_bytes():
                lossless_runs += 1

        bits_per_base = (size * 8) / statistics.mean(dna_lengths)
        rows.append({
            "size_bytes": size,
            "runs": RUNS,
            "encode_mean_s": statistics.mean(encode_times),
            "encode_std_s": statistics.stdev(encode_times) if RUNS > 1 else 0.0,
            "decode_mean_s": statistics.mean(decode_times),
            "decode_std_s": statistics.stdev(decode_times) if RUNS > 1 else 0.0,
            "throughput_Bps": size / statistics.mean(encode_times),
            "dna_bases_mean": statistics.mean(dna_lengths),
            "bits_per_base": bits_per_base,
            "encoding_efficiency_pct": bits_per_base / 2.0 * 100.0,
            "lossless_runs": lossless_runs,
        })
        print(f"[perf] size={size}B  enc={rows[-1]['encode_mean_s']*1000:.1f}ms  "
              f"dec={rows[-1]['decode_mean_s']*1000:.1f}ms  "
              f"bits/base={bits_per_base:.3f}  lossless={lossless_runs}/{RUNS}")
    return rows


# --------------------------------------------------------------------------
# 2. Constraint compliance (naive vs constrained)
# --------------------------------------------------------------------------

def bench_constraints() -> dict:
    """Compare naive vs constrained on a fixed 8 KB random input."""
    inp = _make_input(8 * 1024, seed=42)
    raw = inp.read_bytes()
    binary = bytes_to_binary(raw)
    cmp = compare_naive_vs_constrained(binary)
    print(f"[cmp]  naive realism={cmp['naive']['realism_score']:.1f}  "
          f"constrained={cmp['constrained']['realism_score']:.1f}  "
          f"rotation rate={cmp['constrained']['rotation_rate']:.1f}%")
    return cmp


# --------------------------------------------------------------------------
# 3. Error injection
# --------------------------------------------------------------------------

def bench_error_injection(trials_per_rate: int = 20) -> list[dict]:
    """For each error rate, mutate the payload and measure recovery rate."""
    base_size = 1024
    inp = _make_input(base_size, seed=7)

    # Encode once, reuse across error rates.
    dna = WORK_DIR / "err_base.dna.txt"
    key = WORK_DIR / "err_base.key"
    encode_file_to_dna(str(inp), str(dna), str(key))
    parsed = parse_dna_file(str(dna))
    payload = parsed["payload_dna"]

    rows = []
    for rate in ERROR_RATES:
        ok = 0
        for trial in range(trials_per_rate):
            mutated = _mutate_dna(payload, rate, seed=trial * 31 + 1)
            mut_dna = WORK_DIR / f"err_{int(rate*1000)}_{trial}.dna.txt"
            rec = WORK_DIR / f"err_{int(rate*1000)}_{trial}.recovered"
            _rewrite_dna_file(dna, mut_dna, mutated)
            try:
                decode_dna_to_file(str(mut_dna), str(key), str(rec))
                if rec.read_bytes() == inp.read_bytes():
                    ok += 1
            except Exception:
                pass
        rows.append({
            "error_rate": rate,
            "trials": trials_per_rate,
            "recovered": ok,
            "success_pct": ok / trials_per_rate * 100.0,
        })
        print(f"[ecc]  rate={rate*100:.1f}%  recovered={ok}/{trials_per_rate}")
    return rows


# --------------------------------------------------------------------------
# 4. Tamper detection
# --------------------------------------------------------------------------

def bench_tamper_detection(trials: int = TAMPER_TRIALS) -> dict:
    inp = _make_input(1024, seed=13)
    dna = WORK_DIR / "tamper.dna.txt"
    key = WORK_DIR / "tamper.key"
    encode_file_to_dna(str(inp), str(dna), str(key))
    parsed = parse_dna_file(str(dna))

    # Baseline integrity (no tampering)
    baseline = verify_integrity(parsed["fingerprint"], parsed["payload_dna"])

    detected = 0
    rng = random.Random(2026)
    payload = parsed["payload_dna"]
    bases = "ATGC"
    for _ in range(trials):
        i = rng.randrange(len(payload))
        new_b = rng.choice(bases.replace(payload[i], ""))
        mutated = payload[:i] + new_b + payload[i+1:]
        result = verify_integrity(parsed["fingerprint"], mutated)
        if result["tampered"]:
            detected += 1

    print(f"[tmp]  baseline_valid={baseline['valid']}  "
          f"single-base detected={detected}/{trials}")
    return {
        "baseline_valid": baseline["valid"],
        "single_base_trials": trials,
        "single_base_detected": detected,
        "single_base_detection_pct": detected / trials * 100.0,
    }


# --------------------------------------------------------------------------
# LaTeX table emission
# --------------------------------------------------------------------------

def emit_latex(perf, cmp, ecc, tamper) -> str:
    lines = []
    lines.append("% Auto-generated by benchmarks/run_benchmarks.py")
    lines.append("% Do not edit by hand.\n")

    # Performance table
    lines.append("% --- Performance ---")
    lines.append("\\begin{tabular}{|r|c|c|c|c|c|}")
    lines.append("\\hline")
    lines.append("\\textbf{Size (B)} & \\textbf{Encode (ms)} & "
                 "\\textbf{Decode (ms)} & \\textbf{Throughput (B/s)} & "
                 "\\textbf{Bits/base} & \\textbf{Lossless} \\\\")
    lines.append("\\hline")
    for r in perf:
        lines.append(
            f"{r['size_bytes']} & "
            f"{r['encode_mean_s']*1000:.1f} $\\pm$ {r['encode_std_s']*1000:.1f} & "
            f"{r['decode_mean_s']*1000:.1f} $\\pm$ {r['decode_std_s']*1000:.1f} & "
            f"{r['throughput_Bps']:,.0f} & "
            f"{r['bits_per_base']:.3f} & "
            f"{r['lossless_runs']}/{r['runs']} \\\\"
        )
        lines.append("\\hline")
    lines.append("\\end{tabular}\n")

    # Constraints table
    lines.append("% --- Naive vs Constrained ---")
    n, c = cmp["naive"], cmp["constrained"]
    lines.append("\\begin{tabular}{|l|c|c|}")
    lines.append("\\hline")
    lines.append("\\textbf{Metric} & \\textbf{Naive} & \\textbf{Constrained} \\\\")
    lines.append("\\hline")
    lines.append(f"Realism score (\\%) & {n['realism_score']:.1f} & {c['realism_score']:.1f} \\\\\\hline")
    lines.append(f"GC content & {n['gc_content']:.3f} & {c['gc_content']:.3f} \\\\\\hline")
    lines.append(f"Shannon entropy & {n['entropy']:.3f} & {c['entropy']:.3f} \\\\\\hline")
    lines.append(f"Max homopolymer & {n['max_homopolymer']} & {c['max_homopolymer']} \\\\\\hline")
    lines.append(f"GC windows in range & {n['gc_windows_ok']:.3f} & {c['gc_windows_ok']:.3f} \\\\\\hline")
    lines.append(f"Restriction sites & {n['forbidden_motifs']} & {c['forbidden_motifs']} \\\\\\hline")
    lines.append(f"Constraint compliant & {n['constraint_compliant']} & {c['constraint_compliant']} \\\\\\hline")
    lines.append(f"Rotation rate (\\%) & -- & {c['rotation_rate']:.2f} \\\\\\hline")
    lines.append("\\end{tabular}\n")

    # ECC table
    lines.append("% --- Error injection ---")
    lines.append("\\begin{tabular}{|c|c|c|}")
    lines.append("\\hline")
    lines.append("\\textbf{Sub. rate (\\%)} & \\textbf{Trials} & \\textbf{Recovery (\\%)} \\\\")
    lines.append("\\hline")
    for r in ecc:
        lines.append(f"{r['error_rate']*100:.1f} & {r['trials']} & {r['success_pct']:.1f} \\\\\\hline")
    lines.append("\\end{tabular}\n")

    # Tamper table
    lines.append("% --- Tamper detection ---")
    lines.append("\\begin{tabular}{|l|c|}")
    lines.append("\\hline")
    lines.append(f"Baseline valid & {tamper['baseline_valid']} \\\\\\hline")
    lines.append(f"Single-base trials & {tamper['single_base_trials']} \\\\\\hline")
    lines.append(f"Detected (\\%) & {tamper['single_base_detection_pct']:.1f} \\\\\\hline")
    lines.append("\\end{tabular}\n")

    return "\n".join(lines)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    print("== BioVerse benchmarks ==")
    perf = bench_performance()
    cmp = bench_constraints()
    ecc = bench_error_injection(trials_per_rate=20)
    tamper = bench_tamper_detection(trials=TAMPER_TRIALS)

    results = {
        "performance": perf,
        "naive_vs_constrained": cmp,
        "error_injection": ecc,
        "tamper_detection": tamper,
    }
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))
    (OUT_DIR / "tables.tex").write_text(emit_latex(perf, cmp, ecc, tamper))
    print(f"\nWrote {OUT_DIR/'results.json'}")
    print(f"Wrote {OUT_DIR/'tables.tex'}")


if __name__ == "__main__":
    main()
