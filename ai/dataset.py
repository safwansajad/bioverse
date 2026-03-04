def load_dna_sequences(path, seq_length=50):
    with open(path, "r") as f:
        data = f.read().upper()

    # Keep only valid DNA bases
    data = ''.join(c for c in data if c in "ATGC")

    sequences = []
    next_chars = []

    for i in range(len(data) - seq_length):
        sequences.append(data[i:i+seq_length])
        next_chars.append(data[i+seq_length])

    return sequences, next_chars
