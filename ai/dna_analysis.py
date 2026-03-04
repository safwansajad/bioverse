from collections import Counter
import math


def analyze_dna(sequence: str) -> tuple:
    """
    Compute base frequency, GC content, and Shannon entropy of a DNA sequence.
    
    Returns:
        (base_freq_dict, gc_content, entropy)
    """
    sequence = sequence.upper()
    length = len(sequence)
    if length == 0:
        return {b: 0.0 for b in "ATGC"}, 0.0, 0.0

    counts = Counter(sequence)
    freq = {base: counts.get(base, 0) / length for base in "ATGC"}

    gc_content = (counts.get("G", 0) + counts.get("C", 0)) / length

    entropy = 0.0
    for base in "ATGC":
        p = freq[base]
        if p > 0:
            entropy -= p * math.log2(p)

    return freq, gc_content, entropy


def realism_score(sequence: str) -> dict:
    """
    Score a DNA sequence for biological realism.
    
    Criteria:
    - GC content between 0.35-0.65 (typical for most organisms)
    - Shannon entropy close to 2.0 (maximum for 4 bases)
    - Balanced base distribution
    
    Returns a dict with individual scores and an overall realism percentage.
    """
    freq, gc_content, entropy = analyze_dna(sequence)
    
    # GC content score (ideal range: 0.35-0.65)
    if 0.35 <= gc_content <= 0.65:
        gc_score = 1.0
    elif gc_content < 0.35:
        gc_score = max(0.0, gc_content / 0.35)
    else:
        gc_score = max(0.0, 1.0 - (gc_content - 0.65) / 0.35)

    # Entropy score (max possible = 2.0 for 4 equiprobable bases)
    entropy_score = min(1.0, entropy / 2.0)

    # Balance score: how evenly distributed are the 4 bases?
    # Perfect balance = each at 0.25; worst = one base at 1.0
    balance_deviation = sum(abs(freq[b] - 0.25) for b in "ATGC") / 4.0
    balance_score = max(0.0, 1.0 - balance_deviation * 4)

    # Weighted overall score
    overall = (gc_score * 0.4 + entropy_score * 0.35 + balance_score * 0.25)

    return {
        "gc_content": gc_content,
        "entropy": entropy,
        "base_freq": freq,
        "gc_score": round(gc_score, 3),
        "entropy_score": round(entropy_score, 3),
        "balance_score": round(balance_score, 3),
        "overall_realism": round(overall * 100, 1),  # percentage
    }


if __name__ == "__main__":
    # Example DNA strings
    real_dna = "ATGCGTACGTTAGCTAGGCTAGCTAGGAC" * 10
    ai_dna = "ATGCGTACGTTAGCTAGGCTAGCTAGGAC" * 10
    plain_dna = "ATATATATATATATATATATATATATAT" * 10

    for label, seq in [("Real DNA", real_dna), ("AI DNA", ai_dna), ("Plain DNA", plain_dna)]:
        score = realism_score(seq)
        print(f"{label}: Realism={score['overall_realism']}%, "
              f"GC={score['gc_content']:.2f}, Entropy={score['entropy']:.2f}")
