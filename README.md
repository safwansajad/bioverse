# BioVerse – AI-Driven Secure DNA Encoding System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.13%2B-orange?logo=tensorflow&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

BioVerse is an AI-assisted DNA data encoding system that converts digital files into DNA nucleotide sequences while ensuring **security**, **reliability**, and **biological realism**. The system integrates cryptography, error correction, bio-inspired encoding, and artificial intelligence.

---

## Table of Contents

- [Novel Contributions (IEEE)](#novel-contributions-ieee)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [DNA File Format](#dna-file-format)
- [Technology Stack](#technology-stack)
- [Contributing](#contributing)
- [Authors](#authors)
- [License](#license)

---

## Novel Contributions (IEEE)

BioVerse introduces **three novel contributions** to the field of DNA data storage:

### 1. Biologically-Constrained DNA Encoding

Unlike naive 2-bit mapping (00→A, 01→T, 10→G, 11→C), BioVerse uses a **rotation cipher** that enforces real biological constraints on the encoded DNA:

| Constraint | Description | Threshold |
|---|---|---|
| **Homopolymer Run Limit** | Maximum consecutive identical bases | ≤ 3 |
| **GC-Content Balance** | Stable GC ratio in sliding windows | 30–70% per 20-base window |
| **Restriction Site Avoidance** | Avoids restriction enzyme recognition sites | EcoRI, BamHI, HindIII, XhoI, EcoRV |

When a naive mapping would violate a constraint, the base is **rotated** (A→T→G→C→A) until the constraint is satisfied. Rotation flags are stored alongside the DNA for lossless reversal.

### 2. Dual-Purpose AI Watermark System

The AI-generated DNA fingerprint serves a **dual purpose**:
- **Biological Camouflage** — LSTM-generated sequences make synthetic DNA indistinguishable from real genomic DNA
- **Integrity Verification** — A SHA-256 hash of the payload is embedded within the fingerprint using a DNA-encoded hash scheme, enabling tamper detection without external checksums

### 3. Quantitative Evaluation Framework

A formal benchmarking module that produces **IEEE-ready metrics** comparing naive vs. constrained encoding across five dimensions:
- Security analysis (key space, brute-force resistance)
- Error correction resilience (correctable errors, overhead)
- Encoding density (bits/base, efficiency ratio)
- Biological realism (GC balance, entropy, constraint compliance)
- Pipeline performance (throughput, latency, lossless verification)

---

## Features

| Feature | Description |
|---|---|
| **AES-128 Encryption** | Confidential encoding — DNA cannot be decoded without the key |
| **Reed–Solomon ECC** | Error-correcting codes for robust data recovery (32 parity bytes) |
| **Constrained DNA Encoding** | Bio-aware rotation cipher with homopolymer/GC/motif constraints |
| **AI DNA Fingerprinting** | LSTM-generated biologically realistic watermarks |
| **Integrity Hashing** | SHA-256 payload hash embedded in fingerprint for tamper detection |
| **DNA Realism Scoring** | GC-content, entropy, and base-frequency analysis |
| **Evaluation Framework** | Quantitative benchmarks for IEEE-format reporting |
| **Streamlit Web UI** | Encode, decode, analyze, and evaluate with real-time statistics |
| **Fully Reversible Pipeline** | End-to-end file recovery with integrity verification |

---

## Architecture

```
File → AES Encrypt → Reed-Solomon ECC → Binary
                                          ↓
                              Constraint-Aware DNA Encoding (rotation cipher)
                                          ↓
                                     DNA Payload
                                          ↓
              AI Fingerprint (LSTM) + Integrity Hash → DNA File (.dna.txt)
```

### Decoding

```
DNA File → Parse Metadata → Constrained DNA → Binary (undo rotations)
    → ECC Decode → AES Decrypt → Original File
    → Verify Integrity Hash (tamper detection)
```

---

## Project Structure

```
bioverse/
├── ai/                       # AI components
│   ├── dataset.py            # DNA sequence dataset loader
│   ├── dna_analysis.py       # Realism scoring (GC, entropy, freq)
│   ├── dna_data.txt          # Training data (real genomic sequences)
│   ├── generate_dna.py       # LSTM + Markov fallback DNA generator
│   ├── train_lstm.py         # Model training script
│   ├── watermark.py          # Dual-purpose watermark (integrity + camouflage)
│   └── test_watermark.py     # Watermark test script
├── core/                     # Core encoding pipeline
│   ├── bio_constraints.py    # ★ NOVEL: Biologically-constrained encoding
│   ├── crypto.py             # AES encryption/decryption
│   ├── ecc.py                # Reed-Solomon error correction
│   ├── encoder.py            # File → Constrained DNA encoding
│   ├── decoder.py            # DNA → File decoding (integrity check)
│   └── evaluation.py         # ★ NOVEL: Quantitative evaluation framework
├── ui/
│   └── app.py                # Streamlit web interface (4 tabs)
├── data/
│   ├── input/                # Uploaded files
│   └── output/               # Encoded DNA files, keys, recovered files
├── paper/
│   └── bioverse_ieee.tex     # IEEE-format research paper
├── test_core.py              # Unit tests (8 tests incl. novel features)
├── test_e2e.py               # End-to-end pipeline test
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/safwansajad/bioverse.git
cd bioverse

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Launch the Web Interface

```bash
streamlit run ui/app.py
```

The UI has **four tabs**:
1. **Encode** — Upload a file, encode to DNA, view constraint compliance and camouflage metrics
2. **Decode** — Decode a DNA file, verify integrity, recover original file
3. **Analyze** — Analyze any DNA sequence for realism and base distribution
4. **Evaluation** — Run full benchmarks with IEEE-ready metrics

### Encode a File (CLI)

```python
from core.encoder import encode_file_to_dna
stats = encode_file_to_dna("data/input/file.txt", "data/output/file.dna.txt", "data/output/aes.key")
print(f"Constrained: {stats['constraint_compliant']}, Realism: {stats['realism_score']}%")
```

### Decode a File (CLI)

```python
from core.decoder import decode_dna_to_file
stats = decode_dna_to_file("data/output/file.dna.txt", "data/output/aes.key", "data/output/recovered.txt")
print(f"Integrity: {stats['integrity']['valid']}, Mode: {stats['encoding_mode']}")
```

### Run Evaluation Benchmark

```python
from core.evaluation import full_evaluation_report
report = full_evaluation_report("data/input/file.txt")
print(report["naive_vs_constrained"]["improvement"])
```

### Run Tests

```bash
python test_core.py    # 8 unit tests
python test_e2e.py     # End-to-end pipeline
```

### Train the LSTM Model

```bash
cd ai
python train_lstm.py
```

---

## DNA File Format

```
FINGERPRINT:GATTACAGCTTAGCTA...{embedded SHA-256 hash}...
ROTATIONS:0a1b2f...
ROTATION_COUNT:1200
HASH:a3f7c9e1b2d4...
PAYLOAD:
ATGCGTATCGATCGATCG...
```

| Field | Description |
|---|---|
| **FINGERPRINT** | AI-generated DNA watermark with embedded integrity hash |
| **ROTATIONS** | Hex-encoded rotation flags for constrained decoding |
| **ROTATION_COUNT** | Total number of encoded positions |
| **HASH** | SHA-256 hash of payload for external verification |
| **PAYLOAD** | Encrypted + ECC-encoded file data as DNA nucleotides |

---

## Screenshots

> _Launch the Streamlit UI (`streamlit run ui/app.py`) to explore the four tabs: **Encode**, **Decode**, **Analyze**, and **Evaluation**._

<!-- Add screenshots here -->
<!-- ![Encode Tab](docs/screenshots/encode.png) -->
<!-- ![Decode Tab](docs/screenshots/decode.png) -->
<!-- ![Evaluate Tab](docs/screenshots/evaluate.png) -->

---

## Technology Stack

- **Python 3.10+**
- **Streamlit** — Web interface
- **TensorFlow / Keras** — LSTM DNA fingerprint generation (with Markov-chain fallback)
- **PyCryptodome** — AES symmetric encryption
- **reedsolo** — Reed–Solomon error correction
- **NumPy** — Numerical computation
- **Matplotlib** — DNA visualization

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## Authors

- **Safwan** — [safwansajad11@gmail.com](mailto:safwansajad11@gmail.com) — [GitHub](https://github.com/safwansajad)

---

## License

This project is licensed under the [MIT License](LICENSE).
