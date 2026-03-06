import streamlit as st
import os
from pathlib import Path

# --- CONFIG ---
RESULTS_DIR = Path(__file__).parent / "results_V01"

st.set_page_config(page_title="Motif-Stroke | 7T fMRI", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🧠 Motif-Stroke")
page = st.sidebar.radio("Navigation", ["Welcome", "Analysis Dashboard"])

# --- PAGE 1: WELCOME HOME ---
if page == "Welcome":
    st.title("🏥 Motif-Stroke: 7T Data Analysis Explorer")
    
    st.markdown("""
    ### Welcome! 👋
    This application allows to explore the results generated for the **Motif-Stroke** project. 
    
    The platform provides access to the statistical analyses performed on the fMRI data of the subjects and patients.
    """)

    st.info("""
    **🏗 Project Status:** If you don't see a specific result yet, it's likely still being processed!
    """)

    st.divider()

    st.subheader("🚀 How to get started")
    st.markdown("""
    1. Click on **Analysis Dashboard** in the left sidebar.
    2. Pick a **Subject** and the **Design Method** you want to compare.
    3. Explore the **Total Z-Map** for the big picture, or dive into **Run Details** for a closer look.
    """)
    
    

# --- PAGE 2: ANALYSIS DASHBOARD ---
else:
    if not RESULTS_DIR.exists():
        st.warning("### 🚧 Analysis in progress\nThe results directory is currently being updated. Please check back later.")
        st.stop()

    # --- SIDEBAR SELECTION ---
    subjects = sorted([d.name for d in RESULTS_DIR.glob("sub-*")])
    selected_sub = st.sidebar.selectbox("👤 Select a Subject", subjects)

    sub_path = RESULTS_DIR / selected_sub
    
    if not sub_path.exists():
        st.info(f"### ⏳ Subject {selected_sub} analysis is ongoing.")
        st.stop()

    methods = sorted([d.name for d in sub_path.iterdir() if d.is_dir()])
    selected_method = st.sidebar.selectbox("📐 Select Design Method", methods)

    method_path = sub_path / selected_method
    contrasts = sorted([d.name for d in method_path.iterdir() if d.is_dir()])
    selected_contrast = st.sidebar.selectbox("🎯 Select Contrast", contrasts)

    # --- MAIN CONTENT ---
    st.title(f"📊 Results: {selected_sub}")
    
    # User-Friendly Interpretation Guide
    guide_col1, guide_col2 = st.columns(2)
    with guide_col1:
        st.subheader("🎨 Color Guide")
        st.markdown("""
        * **🔴 Red Areas**: The brain was more active for the **first** part of your selection.
        * **🔵 Blue Areas**: The brain was more active for the **second** (subtracted) part.
        """)

    with guide_col2:
        st.subheader("📊 What does this map show?")
        st.markdown("""
        We use an **FDR threshold (0.01)**. In simple terms: there is a **99% confidence** that the displayed activations represent true neural 
        responses..
        The maps represent Z-scores thresholded using **False Discovery Rate (FDR)** at $q < 0.01$. 

        """)
    
    

    st.divider()
    
    # Clear Context Label
    st.markdown(f"**Current View:** {selected_contrast.replace('_', ' ').upper()} | **Model:** {selected_method.replace('_', ' ').upper()}")
    
    total_dir = method_path / selected_contrast / "combined_total"
    tab_total, tab_runs = st.tabs(["🎯 Total Summary Map", "🔎 Detailed Run-by-Run"])

    with tab_total:
        if total_dir.exists():
            fdr_png = total_dir / "TOTAL_05_zmap_FDR_q0.001.png"
            bonf_png = total_dir / "TOTAL_06_zmap_BONF_a0.05.png"

            st.subheader("Combined Statistical Results")
            st.write("Side-by-side comparison of the thresholding methods.")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### FDR (q < 0.001)")
                if fdr_png.exists():
                    st.image(str(fdr_png), use_container_width=True)
                    st.caption("False Discovery Rate thresholded map.")
                else:
                    st.info("FDR map is not available yet.")

            with col2:
                st.markdown("### Bonferroni (α < 0.05)")
                if bonf_png.exists():
                    st.image(str(bonf_png), use_container_width=True)
                    st.caption("Bonferroni corrected statistical map.")
                else:
                    st.info("Bonferroni map is not available yet.")

        else:
            st.info("### ⏳ The combined analysis for this contrast is ongoing.")

    # with tab_runs:
    #     st.subheader("Individual Run Snapshots")
    #     st.write("Examine these to see how consistent the brain activity was during each part of the session.")
        
    #     run_path = method_path / selected_contrast
    #     run_dirs = sorted([d for d in run_path.iterdir() if d.is_dir() and "run-" in d.name])
        
    #     if run_dirs:
    #         cols = st.columns(2)
    #         for i, run_p in enumerate(run_dirs):
    #             run_png = run_p / f"{selected_contrast}_run_viz.png"
    #             with cols[i % 2]:
    #                 if run_png.exists():
    #                     st.image(str(run_png), caption=f"Session: {run_p.name}", use_container_width=True)
    #                 else:
    #                     st.caption(f"🕒 Run {run_p.name} visualization is ongoing.")
    #     else:
    #         st.info("### ⏳ Individual run visualizations are ongoing.")