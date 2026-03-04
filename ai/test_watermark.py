from generate_dna import generate_dna
from watermark import embed_payload, extract_payload

# Simulated encrypted DNA payload
payload_dna = "ATCGATCGATCGATCG"

# Generate AI DNA host
ai_dna = generate_dna(300)

# Embed payload
watermarked_dna, index = embed_payload(ai_dna, payload_dna)

# Extract payload
recovered_payload = extract_payload(
    watermarked_dna,
    len(payload_dna),
    index
)

print("Original payload:", payload_dna)
print("Recovered payload:", recovered_payload)
print("Match:", payload_dna == recovered_payload)
