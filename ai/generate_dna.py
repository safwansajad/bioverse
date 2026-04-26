import os
import numpy as np
import random
import logging

logger = logging.getLogger(__name__)

# Resolve path relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "dna_lstm_model.h5")

# DNA mappings
mapping = {'A': 0, 'T': 1, 'G': 2, 'C': 3}
reverse_mapping = {v: k for k, v in mapping.items()}

# Check TensorFlow availability once
_tf_available = None
_model = None


def _check_tensorflow():
    """Check if TensorFlow is installed and usable."""
    global _tf_available
    if _tf_available is None:
        try:
            import tensorflow  # noqa: F401
            _tf_available = True
            logger.info("TensorFlow available — using LSTM model")
        except ImportError:
            _tf_available = False
            logger.warning(
                "TensorFlow not installed — using statistical fallback "
                "for DNA fingerprint generation"
            )
    return _tf_available


def _get_model():
    """Load LSTM model on first use (lazy initialization).

    Returns None if the model cannot be loaded (e.g. Keras version mismatch
    between training and runtime). Callers should fall back to the Markov
    generator in that case.
    """
    global _model, _tf_available
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"LSTM model not found at {MODEL_PATH}. "
                f"Run 'python ai/train_lstm.py' first."
            )
        try:
            from tensorflow.keras.models import load_model
            _model = load_model(MODEL_PATH, compile=False)
            logger.info("LSTM DNA model loaded successfully")
        except Exception as e:
            logger.warning(
                "Failed to load LSTM model (%s); falling back to Markov generator.",
                e,
            )
            _tf_available = False
            return None
    return _model


def sample(preds, temperature=0.8):
    """Sample an index from a probability distribution with temperature."""
    preds = np.asarray(preds).astype("float64")
    preds = np.log(preds + 1e-8) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    return np.random.choice(len(preds), p=preds)


def _generate_dna_fallback(length=300, temperature=0.8):
    """
    Statistical fallback for DNA generation when TensorFlow is unavailable.
    Uses Markov-chain-like transition probabilities based on real genomic patterns
    to produce biologically plausible sequences (balanced GC content ~40-60%).
    """
    # Transition probabilities inspired by real genomic dinucleotide frequencies
    transitions = {
        'A': {'A': 0.30, 'T': 0.22, 'G': 0.28, 'C': 0.20},
        'T': {'A': 0.24, 'T': 0.28, 'G': 0.20, 'C': 0.28},
        'G': {'A': 0.22, 'T': 0.20, 'G': 0.30, 'C': 0.28},
        'C': {'A': 0.20, 'T': 0.28, 'G': 0.24, 'C': 0.28},
    }
    bases = list(mapping.keys())
    seed = random.choice(bases)
    sequence = seed

    for _ in range(length - 1):
        prev = sequence[-1]
        probs = [transitions[prev][b] for b in bases]

        # Apply temperature
        probs = np.array(probs, dtype="float64")
        probs = np.log(probs + 1e-8) / temperature
        probs = np.exp(probs)
        probs = probs / probs.sum()

        next_base = np.random.choice(bases, p=probs)
        sequence += next_base

    return sequence


def generate_dna(length=300, temperature=0.8):
    """
    Generate a biologically realistic DNA sequence.

    Uses the LSTM model when TensorFlow is available, otherwise falls back
    to a statistical Markov-chain generator.

    Args:
        length: Number of nucleotides to generate.
        temperature: Sampling temperature (higher = more random).

    Returns:
        A string of DNA bases (A, T, G, C).
    """
    if not _check_tensorflow():
        return _generate_dna_fallback(length, temperature)

    from tensorflow.keras.utils import to_categorical

    model = _get_model()
    if model is None:
        return _generate_dna_fallback(length, temperature)
    seed = random.choice(list(mapping.keys()))
    sequence = seed

    for _ in range(length - 1):
        x = [mapping[c] for c in sequence[-1:]]
        x = to_categorical(x, num_classes=4)
        x = x.reshape((1, 1, 4))

        prediction = model.predict(x, verbose=0)
        index = sample(prediction[0], temperature)
        next_base = reverse_mapping[index]

        sequence += next_base

    return sequence


if __name__ == "__main__":
    dna = generate_dna(200, temperature=1.0)
    print(f"Generated DNA ({len(dna)} bases): {dna[:60]}...")
