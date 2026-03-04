import sys
import os
import glob

# Add project root to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

import streamlit as st
from core.encoder import encode_file_to_dna
from core.decoder import decode_dna_to_file
from ai.dna_analysis import analyze_dna, realism_score
from ai.watermark import verify_fingerprint, verify_integrity

UPLOAD_DIR = "data/input"
OUTPUT_DIR = "data/output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _clean_output_dir():
    """Remove all files from the output directory (auto-clean previous session)."""
    for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
        try:
            os.remove(f)
        except OSError:
            pass

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="BioVerse",
    page_icon="🧬",
    layout="centered"
)

# ---------- CUSTOM CSS ----------
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }
    .title {
        font-size: 42px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 18px;
        color: #9aa0a6;
        text-align: center;
        margin-bottom: 10px;
    }
    .card {
        background-color: #161b22;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .section-title {
        font-size: 24px;
        font-weight: 600;
        color: #58a6ff;
        margin-bottom: 15px;
    }
    .stButton>button {
        width: 100%;
        height: 48px;
        border-radius: 10px;
        font-size: 16px;
        font-weight: 600;
        background-color: #238636;
        color: white;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    .stat-label {
        color: #8b949e;
        font-size: 13px;
        margin-bottom: 2px;
    }
    .stat-value {
        color: #f0f6fc;
        font-size: 20px;
        font-weight: 600;
    }
    .fingerprint-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 12px;
        color: #7ee787;
        word-break: break-all;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- HEADER ----------
st.markdown('<div class="title">🧬 BioVerse</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-Driven Secure DNA Encoding and Decoding System</div>',
    unsafe_allow_html=True
)

# ---------- PIPELINE DIAGRAM ----------
with st.expander("📐 System Architecture", expanded=False):
    st.markdown("""
    ```
    ┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌─────────────────────┐
    │   File   │ ──▶ │ AES Encrypt  │ ──▶ │ RS ECC   │ ──▶ │ Bio-Constrained DNA │
    └──────────┘     └──────────────┘     └──────────┘     └─────────────────────┘
                                                                      │
                         AI Fingerprint + Integrity Hash ──▶ DNA File (.dna.txt)
    ```
    
    **Novel Features:**
    - **Biologically-Constrained Encoding** — avoids homopolymer runs, GC imbalance, restriction enzyme sites
    - **Dual-Purpose AI Watermark** — authenticity verification + biological camouflage
    - **Tamper Detection** — SHA-256 integrity hash embedded in fingerprint
    - **Quantitative Realism Scoring** — GC, entropy, constraint compliance metrics
    """)

# ---------- TABS ----------
tab_encode, tab_decode, tab_analyze, tab_evaluate = st.tabs([
    "🔒 Encode", "🔓 Decode", "📊 Analyze DNA", "📋 Evaluation"
])

# ========== ENCODE TAB ==========
with tab_encode:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Encode File to DNA</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload any file (text, image, audio, video, PDF)",
        type=None,
        key="encode_upload"
    )

    if uploaded_file:
        file_size = len(uploaded_file.getvalue())
        st.info(f"📄 **{uploaded_file.name}** — {file_size:,} bytes")

        input_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        dna_path = os.path.join(OUTPUT_DIR, uploaded_file.name + ".dna.txt")
        key_path = os.path.join(OUTPUT_DIR, "aes.key")

        if st.button("⚡ Encode File", key="encode_btn"):
            try:
                _clean_output_dir()  # auto-clean previous session output
                # Write uploaded file to disk only when encoding
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                with st.spinner("Encrypting → ECC → DNA encoding → AI fingerprinting..."):
                    stats = encode_file_to_dna(input_path, dna_path, key_path)

                with open(dna_path, "r") as f:
                    st.session_state["dna_data"] = f.read()

                with open(key_path, "rb") as f:
                    st.session_state["aes_key"] = f.read()

                st.session_state["dna_filename"] = os.path.basename(dna_path)
                st.session_state["original_filename"] = uploaded_file.name
                st.session_state["encode_stats"] = stats

                st.success("✅ File encoded successfully!")

                # Auto-delete uploaded file after encoding
                if os.path.exists(input_path):
                    os.remove(input_path)

            except Exception as e:
                st.error(f"❌ Encoding failed: {e}")

    # Show stats and download buttons after encoding
    if "encode_stats" in st.session_state:
        stats = st.session_state["encode_stats"]

        # Encoding statistics
        st.markdown("---")
        st.markdown("#### 📈 Encoding Statistics")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Original Size", f"{stats['original_size']:,} B")
        with col2:
            st.metric("Encrypted Size", f"{stats['encrypted_size']:,} B")
        with col3:
            st.metric("DNA Length", f"{stats['dna_length']:,} bp")
        with col4:
            st.metric("Fingerprint", f"{stats['fingerprint_length']} bp")

        # Novel: Biological Constraint Compliance
        st.markdown("#### 🧬 Biological Constraint Compliance (Novel)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            compliant = stats.get("constraint_compliant", False)
            st.metric("Compliant", "✅ Yes" if compliant else "❌ No")
        with col2:
            st.metric("Max Homopolymer", f"{stats.get('max_homopolymer', '?')}")
        with col3:
            gc_win = stats.get("gc_windows_in_range", 0)
            st.metric("GC Windows OK", f"{gc_win:.1%}")
        with col4:
            motifs = stats.get("forbidden_motifs", [])
            st.metric("Restriction Sites", f"{len(motifs)} found")

        # Novel: Naive vs Constrained Comparison
        st.markdown("#### ⚖️ Naive vs. Constrained Encoding (Novel)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Constrained Realism",
                f"{stats.get('realism_score', 0)}%",
                delta=f"+{stats.get('realism_improvement', 0)}%"
            )
        with col2:
            st.metric(
                "Naive Realism",
                f"{stats.get('naive_realism_score', 0)}%",
            )
        with col3:
            st.metric(
                "Rotations Applied",
                f"{stats.get('rotations_applied', 0)}",
                delta=f"{stats.get('rotation_rate', 0)}% of bases"
            )

        # Camouflage metrics
        camouflage = stats.get("camouflage", {})
        if camouflage:
            st.markdown("#### 🎭 AI Camouflage Effect (Novel)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Payload Realism", f"{camouflage.get('payload_realism', 0)}%")
            with col2:
                st.metric("With Fingerprint", f"{camouflage.get('combined_realism', 0)}%")
            with col3:
                imp = camouflage.get('realism_improvement', 0)
                st.metric("Improvement", f"{imp:+.1f}%")

        # DNA Quality Metrics
        st.markdown("#### 🧪 DNA Quality Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("GC Content", f"{stats['gc_content']:.2%}")
        with col2:
            st.metric("Shannon Entropy", f"{stats['entropy']:.3f}")
        with col3:
            st.metric("FP GC Content", f"{stats['fp_gc_content']:.2%}")

        # Base frequency chart
        st.markdown("#### 🔬 Base Frequency Distribution")
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))
        fig.patch.set_facecolor('#0e1117')

        bases = list(stats['base_freq'].keys())
        freqs = list(stats['base_freq'].values())
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24']

        # Payload bar chart
        ax1.bar(bases, freqs, color=colors, edgecolor='white', linewidth=0.5)
        ax1.set_title('Payload Base Distribution', color='white', fontsize=12)
        ax1.set_ylabel('Frequency', color='white')
        ax1.set_ylim(0, 0.5)
        ax1.set_facecolor('#161b22')
        ax1.tick_params(colors='white')
        for spine in ax1.spines.values():
            spine.set_color('#30363d')

        # Ideal vs actual comparison
        ideal = [0.25, 0.25, 0.25, 0.25]
        x = range(len(bases))
        width = 0.35
        ax2.bar([i - width/2 for i in x], freqs, width, label='Actual', color='#58a6ff')
        ax2.bar([i + width/2 for i in x], ideal, width, label='Ideal (25%)', color='#30363d')
        ax2.set_xticks(list(x))
        ax2.set_xticklabels(bases)
        ax2.set_title('Actual vs Ideal', color='white', fontsize=12)
        ax2.set_ylim(0, 0.5)
        ax2.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')
        ax2.set_facecolor('#161b22')
        ax2.tick_params(colors='white')
        for spine in ax2.spines.values():
            spine.set_color('#30363d')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Download buttons
    if "dna_data" in st.session_state and "aes_key" in st.session_state:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download DNA File",
                data=st.session_state["dna_data"],
                file_name=st.session_state["dna_filename"],
                mime="text/plain"
            )
        with col2:
            st.download_button(
                "🔑 Download AES Key",
                data=st.session_state["aes_key"],
                file_name="aes.key",
                mime="application/octet-stream"
            )

    st.markdown('</div>', unsafe_allow_html=True)

# ========== DECODE TAB ==========
with tab_decode:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Decode DNA to Original File</div>', unsafe_allow_html=True)

    dna_file = st.file_uploader("Upload DNA file (.dna.txt)", key="dna")
    key_file = st.file_uploader("Upload AES key (.key)", key="key")

    if dna_file and key_file:
        dna_path = os.path.join(OUTPUT_DIR, "input.dna.txt")
        key_path = os.path.join(OUTPUT_DIR, "input.key")

        # Try to recover original filename from the DNA filename
        dna_name = dna_file.name
        if dna_name.endswith(".dna.txt"):
            original_name = dna_name[:-8]  # strip ".dna.txt"
        else:
            original_name = st.session_state.get("original_filename", "recovered_file")

        output_path = os.path.join(OUTPUT_DIR, original_name)

        st.info(f"📄 DNA file: **{dna_file.name}** ({len(dna_file.getvalue()):,} bytes)")

        if st.button("⚡ Decode File", key="decode_btn"):
            try:
                _clean_output_dir()  # auto-clean previous session output
                # Write uploaded files to disk only when decoding
                with open(dna_path, "wb") as f:
                    f.write(dna_file.getbuffer())
                with open(key_path, "wb") as f:
                    f.write(key_file.getbuffer())
                with st.spinner("DNA → Binary → ECC → AES decryption..."):
                    decode_stats = decode_dna_to_file(dna_path, key_path, output_path)

                # Clean up intermediary decode files (keep only recovered file)
                for tmp in [dna_path, key_path]:
                    if os.path.exists(tmp):
                        os.remove(tmp)

                st.success("✅ File decoded successfully!")

                # Show decode stats
                st.markdown("---")
                st.markdown("#### 📈 Decoding Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Payload Bases", f"{decode_stats['payload_bases']:,} bp")
                with col2:
                    st.metric("Fingerprint Bases", f"{decode_stats['fingerprint_bases']} bp")
                with col3:
                    st.metric("Recovered Size", f"{decode_stats['recovered_size']:,} B")

                # Novel: Encoding mode
                enc_mode = decode_stats.get("encoding_mode", "unknown")
                st.info(f"📎 Encoding mode: **{enc_mode.upper()}**")

                # Novel: Integrity Verification (Tamper Detection)
                integrity = decode_stats.get("integrity", {})
                if integrity.get("hash_found"):
                    st.markdown("#### 🛡️ Integrity Verification (Novel)")
                    if integrity.get("valid"):
                        st.success("✅ Payload integrity verified — no tampering detected")
                    else:
                        st.error("🚨 TAMPER DETECTED — payload hash mismatch!")
                
                # Novel: Constraint compliance
                if decode_stats.get("constraint_compliant") is not None:
                    st.markdown("#### 🧬 Constraint Compliance")
                    col1, col2 = st.columns(2)
                    with col1:
                        cc = decode_stats.get("constraint_compliant", False)
                        st.metric("Bio-Compliant", "✅ Yes" if cc else "❌ No")
                    with col2:
                        st.metric("Max Homopolymer", str(decode_stats.get("max_homopolymer", "?")))

                # Fingerprint verification
                fp = decode_stats.get("fingerprint", "")
                if fp:
                    is_valid = verify_fingerprint(fp)
                    st.markdown("#### 🔍 Fingerprint Verification")
                    if is_valid:
                        st.success(f"✅ Valid AI fingerprint detected ({len(fp)} bases)")
                    else:
                        st.warning("⚠️ Fingerprint missing or invalid")
                    st.markdown(
                        f'<div class="fingerprint-box">{fp}</div>',
                        unsafe_allow_html=True
                    )

                # Download recovered file
                with open(output_path, "rb") as f:
                    recovered_data = f.read()

                st.download_button(
                    "📥 Download Recovered File",
                    data=recovered_data,
                    file_name=original_name,
                    mime="application/octet-stream"
                )

            except Exception as e:
                st.error(f"❌ Decoding failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# ========== ANALYZE TAB ==========
with tab_analyze:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">DNA Realism Analyzer</div>', unsafe_allow_html=True)

    st.markdown(
        "Paste or upload a DNA sequence to analyze its biological realism — "
        "evaluating GC content, Shannon entropy, and base balance."
    )

    analyze_source = st.radio(
        "Input method:",
        ["Paste DNA sequence", "Upload DNA file"],
        horizontal=True,
        key="analyze_source"
    )

    dna_to_analyze = ""

    if analyze_source == "Paste DNA sequence":
        dna_to_analyze = st.text_area(
            "DNA Sequence",
            height=120,
            placeholder="ATGCGTACGTTAGCTAGGCTAGCTAGGAC..."
        )
    else:
        analyze_file = st.file_uploader("Upload DNA file", key="analyze_upload")
        if analyze_file:
            content = analyze_file.getvalue().decode("utf-8", errors="ignore")
            # Extract payload if it's a BioVerse file
            lines = content.split("\n")
            payload_started = False
            payload = ""
            for line in lines:
                line = line.strip()
                if line == "PAYLOAD:":
                    payload_started = True
                    continue
                elif payload_started:
                    payload += line
                elif line.startswith("FINGERPRINT:"):
                    pass  # skip
                else:
                    payload += line  # plain DNA file
            dna_to_analyze = payload if payload else content

    if dna_to_analyze:
        # Clean input
        clean_dna = ''.join(c for c in dna_to_analyze.upper() if c in "ATGC")

        if len(clean_dna) < 10:
            st.warning("⚠️ DNA sequence too short for meaningful analysis (min 10 bases)")
        else:
            st.markdown(f"**Sequence length:** {len(clean_dna):,} bases")

            score = realism_score(clean_dna)

            # Score gauges
            st.markdown("---")
            st.markdown("#### 🏆 Realism Scores")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Realism", f"{score['overall_realism']}%")
            with col2:
                st.metric("GC Score", f"{score['gc_score']:.1%}")
            with col3:
                st.metric("Entropy Score", f"{score['entropy_score']:.1%}")
            with col4:
                st.metric("Balance Score", f"{score['balance_score']:.1%}")

            # Detailed metrics
            st.markdown("#### 📊 Detailed Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("GC Content", f"{score['gc_content']:.2%}")
                st.caption("Typical biological range: 35%–65%")
            with col2:
                st.metric("Shannon Entropy", f"{score['entropy']:.4f} bits")
                st.caption("Maximum possible: 2.0 bits (4 equiprobable bases)")

            # Base distribution chart
            st.markdown("#### 🔬 Base Distribution")
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')

            fig, ax = plt.subplots(figsize=(6, 3.5))
            fig.patch.set_facecolor('#0e1117')

            bases = list(score['base_freq'].keys())
            freqs = list(score['base_freq'].values())
            colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24']

            bars = ax.bar(bases, freqs, color=colors, edgecolor='white', linewidth=0.5)
            ax.axhline(y=0.25, color='#58a6ff', linestyle='--', alpha=0.5, label='Ideal (25%)')
            ax.set_title('Nucleotide Frequency', color='white', fontsize=14)
            ax.set_ylabel('Frequency', color='white')
            ax.set_ylim(0, max(0.5, max(freqs) + 0.05))
            ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')
            ax.set_facecolor('#161b22')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('#30363d')

            # Add value labels on bars
            for bar, freq in zip(bars, freqs):
                ax.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f'{freq:.1%}', ha='center', va='bottom', color='white', fontsize=10
                )

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    st.markdown('</div>', unsafe_allow_html=True)

# ========== EVALUATION TAB (NOVEL) ==========
with tab_evaluate:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Quantitative Evaluation Framework</div>', unsafe_allow_html=True)
    st.markdown(
        "Run a comprehensive evaluation benchmark comparing naive vs. "
        "biologically-constrained encoding. Generates IEEE-ready metrics."
    )

    eval_file = st.file_uploader(
        "Upload a file to benchmark",
        type=None,
        key="eval_upload"
    )

    if eval_file:
        eval_input = os.path.join(UPLOAD_DIR, "eval_" + eval_file.name)
        with open(eval_input, "wb") as f:
            f.write(eval_file.getbuffer())

        if st.button("🔬 Run Full Evaluation", key="eval_btn"):
            try:
                with st.spinner("Running evaluation benchmark..."):
                    from core.evaluation import (
                        evaluate_security,
                        evaluate_ecc_resilience,
                        evaluate_encoding_density,
                        evaluate_biological_realism,
                        evaluate_pipeline_performance,
                        compare_naive_vs_constrained,
                    )
                    from core.encoder import file_to_bytes, bytes_to_binary

                    eval_dna = os.path.join(OUTPUT_DIR, "eval.dna.txt")
                    eval_key = os.path.join(OUTPUT_DIR, "eval.key")
                    eval_out = os.path.join(OUTPUT_DIR, "eval_recovered")

                    # Pipeline performance
                    perf = evaluate_pipeline_performance(
                        eval_input, eval_dna, eval_key, eval_out
                    )

                    # Read generated DNA for analysis
                    with open(eval_dna, "r") as f:
                        content = f.read()
                    lines = content.split("\n")
                    payload = ""
                    started = False
                    for line in lines:
                        line = line.strip()
                        if line == "PAYLOAD:":
                            started = True
                        elif started:
                            payload += line

                    # All evaluations
                    security = evaluate_security()
                    ecc = evaluate_ecc_resilience()
                    density = evaluate_encoding_density(len(eval_file.getvalue()), len(payload))
                    bio = evaluate_biological_realism(payload)

                    raw = file_to_bytes(eval_input)
                    binary = bytes_to_binary(raw)
                    comparison = compare_naive_vs_constrained(binary[:2000])  # sample

                st.success("✅ Evaluation complete!")

                # Auto-delete uploaded file after evaluation
                if os.path.exists(eval_input):
                    os.remove(eval_input)

                # Performance
                st.markdown("---")
                st.markdown("#### ⏱️ Pipeline Performance")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Encode Time", f"{perf['encode_time_sec']:.3f}s")
                with col2:
                    st.metric("Decode Time", f"{perf['decode_time_sec']:.3f}s")
                with col3:
                    st.metric("Throughput", f"{perf['encode_throughput_bps']:.0f} B/s")
                with col4:
                    st.metric("Lossless", "✅" if perf["lossless"] else "❌")

                # Security
                st.markdown("#### 🔐 Security Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Algorithm", security["algorithm"])
                with col2:
                    st.metric("Key Size", f"{security['key_size_bits']} bits")
                with col3:
                    st.metric("Brute Force", f"{security['brute_force_years']} yrs")

                # ECC
                st.markdown("#### 🛡️ Error Correction")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Algorithm", ecc["algorithm"])
                with col2:
                    st.metric("Correctable Errors", str(ecc["max_correctable_errors"]))
                with col3:
                    st.metric("Parity Overhead", f"{ecc['overhead_bytes']} bytes")

                # Encoding Density
                st.markdown("#### 📦 Storage Efficiency")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Bits/Base", f"{density['bits_per_base']:.3f}")
                with col2:
                    st.metric("Efficiency", f"{density['encoding_efficiency']}%")
                with col3:
                    st.metric("Overhead Ratio", f"{density['overhead_ratio']:.2f}x")

                # Biological Realism
                st.markdown("#### 🧬 Biological Realism")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Realism Score", f"{bio['realism_score']}%")
                with col2:
                    st.metric("GC Content", f"{bio['gc_content']:.2%}")
                with col3:
                    st.metric("Entropy", f"{bio['shannon_entropy']:.3f}")
                with col4:
                    st.metric("Compliant", "✅" if bio["constraint_compliant"] else "❌")

                # Novel: Naive vs Constrained Comparison Table
                st.markdown("#### ⚖️ Naive vs. Constrained Comparison (Novel)")
                naive = comparison["naive"]
                constr = comparison["constrained"]
                improv = comparison["improvement"]

                import pandas as pd
                comp_data = {
                    "Metric": [
                        "Realism Score",
                        "GC Content",
                        "Entropy",
                        "Max Homopolymer Run",
                        "GC Windows OK",
                        "Restriction Sites",
                        "Constraint Compliant",
                    ],
                    "Naive Encoding": [
                        f"{naive['realism_score']}%",
                        f"{naive['gc_content']:.2%}",
                        f"{naive['entropy']:.3f}",
                        str(naive["max_homopolymer"]),
                        f"{naive['gc_windows_ok']:.1%}",
                        str(naive["forbidden_motifs"]),
                        "✅" if naive["constraint_compliant"] else "❌",
                    ],
                    "Constrained (Ours)": [
                        f"{constr['realism_score']}%",
                        f"{constr['gc_content']:.2%}",
                        f"{constr['entropy']:.3f}",
                        str(constr["max_homopolymer"]),
                        f"{constr['gc_windows_ok']:.1%}",
                        str(constr["forbidden_motifs"]),
                        "✅" if constr["constraint_compliant"] else "❌",
                    ],
                }
                st.table(pd.DataFrame(comp_data))

                st.caption(
                    f"Realism improvement: **+{improv['realism_delta']}%** | "
                    f"Homopolymer reduction: **{improv['homopolymer_reduction']}** bases | "
                    f"Motifs eliminated: **{improv['motifs_eliminated']}** | "
                    f"Rotation rate: {constr['rotation_rate']}%"
                )

            except Exception as e:
                st.error(f"❌ Evaluation failed: {e}")
                import traceback
                st.code(traceback.format_exc())

    st.markdown('</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#484f58; font-size:13px;">'
    'BioVerse • AI-Driven Secure DNA Encoding System • 2025-2026'
    '</p>',
    unsafe_allow_html=True
)
