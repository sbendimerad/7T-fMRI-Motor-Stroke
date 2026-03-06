import streamlit as st
import os
from pathlib import Path

# --- CONFIG ---
RESULTS_DIR = Path(__file__).parent / "results_V02"

st.set_page_config(page_title="Motif-Stroke | 7T fMRI", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🧠 Motif-Stroke")
page = st.sidebar.radio("Navigation", ["Welcome", "Analysis Dashboard"])

# --- PAGE 1: WELCOME ---
if page == "Welcome":
    st.title("🏥 Motif-Stroke: 7T Data Analysis Explorer")
    st.markdown("""
    ### Welcome! 👋
    This application allows you to explore the results generated for the **Motif-Stroke** project. 
    
    The platform provides access to the statistical analyses performed on the fMRI data of the subjects and patients.
    """)
    st.info("**🏗 Project Status:** If you don't see a specific result yet, it's likely still being processed!")
    st.divider()
    st.subheader("🚀 How to get started")
    st.markdown("""
    1. Click on **Analysis Dashboard** in the left sidebar.
    2. Pick a **Subject** and the **Design Method**.
    3. Use the **Anatomical Selection** in the body to choose your view.
    """)

# --- PAGE 2: ANALYSIS DASHBOARD ---
else:
    if not RESULTS_DIR.exists():
        st.warning("### 🚧 Analysis in progress")
        st.stop()

    # --- SIDEBAR SELECTION ---
    subjects = sorted([d.name for d in RESULTS_DIR.glob("sub-*")])
    selected_sub = st.sidebar.selectbox("👤 Select a Subject", subjects)

    sub_path = RESULTS_DIR / selected_sub
    if not sub_path.exists():
        st.info(f"### ⏳ Subject {selected_sub} analysis ongoing.")
        st.stop()

    methods = sorted([d.name for d in sub_path.iterdir() if d.is_dir()])
    selected_method = st.sidebar.selectbox("📐 Select Design Method", methods)

    method_path = sub_path / selected_method
    contrasts = sorted([d.name for d in method_path.iterdir() if d.is_dir()])
    selected_contrast = st.sidebar.selectbox("🎯 Select Contrast", contrasts)

    # --- MAIN CONTENT ---
    st.title(f"📊 Results: {selected_sub}")
    
    # --- COLOR & STATS GUIDE ---
    guide_col1, guide_col2 = st.columns(2)
    with guide_col1:
        st.subheader("🎨 Color Guide")
        st.markdown("""
        * **🔴 Red Areas**: Higher brain activity for the **first** part of the contrast.
        * **🔵 Blue Areas**: Higher brain activity for the **second** part (subtracted).
        """)

    with guide_col2:
        st.subheader("📊 Statistical Methods")
        st.markdown("""
        * **FDR (False Discovery Rate):** This method controls the expected proportion of "false" positives among all discoveries. It is more flexible than Bonferroni, making it ideal for identifying smaller but consistent brain activations.
        * **Bonferroni Correction:** This is the most stringent correction method that treats every voxel as an independent test. It ensures almost zero false positives but is very conservative, often hiding real but weaker signals.
        """)

    st.divider()

    # --- ANATOMICAL SELECTION ZONE ---
    st.subheader("📍 Anatomical Selection")
    st.markdown("Please choose between the following views to inspect different motor circuits:")
    
    total_dir = method_path / selected_contrast / "combined_total"
    view_files = list(total_dir.glob("TOTAL_05_zmap_FDR_*.png"))
    view_names = sorted([f.name.split("FDR_")[-1].replace(".png", "") for f in view_files])
    
    if not view_names:
        st.warning("No anatomical views found for this contrast yet.")
        st.stop()

    select_col, explain_col = st.columns([1, 2])

    with select_col:
        # Clear instructional choice
        selected_view = st.radio("**Select the brain area to display:**", view_names)

    with explain_col:
        st.info("💡 **Anatomical Definition**")
        if "SMA" in selected_view:
            st.markdown("""
            **SMA (Supplementary Motor Area):** Located on the **midline** (medial wall). 
            It is the "architect" of movement, responsible for **planning** and coordinating complex or internally-timed sequences.
            """)
        elif "M1_hand" in selected_view:
            st.markdown("""
            **M1 Hand (Primary Motor Cortex):** Located on the **lateral** sides of the brain in the 'Hand Knob'. 
            It is the "executor," sending the final neural commands to move the **fingers and wrists**.
            """)
        elif "M1_foot" in selected_view:
            st.markdown("""
            **M1 Foot (Primary Motor Foot Area):** Located at the very **top/back of the midline**. 
            It is a deep structure that becomes highly visible and precise with **7 Tesla** resolution.
            """)
        else:
            st.markdown("**Overview:** A wide-angle view used to verify the global distribution of activity across the motor strip.")

    st.divider()

    # --- TABS FOR MAPS ---
    tab_total, tab_runs = st.tabs(["🎯 Total Summary Map", "🔎 Detailed Run-by-Run"])

    with tab_total:
        fdr_png = total_dir / f"TOTAL_05_zmap_FDR_{selected_view}.png"
        bonf_png = total_dir / f"TOTAL_06_zmap_BONF_{selected_view}.png"

        st.subheader(f"Fused Subject Results - Focus: {selected_view}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### FDR Correction (q < 0.001)")
            if fdr_png.exists(): st.image(str(fdr_png), use_container_width=True)
            else: st.info(f"FDR image for {selected_view} is still processing.")
        with c2:
            st.markdown("### Bonferroni Correction (α < 0.05)")
            if bonf_png.exists(): st.image(str(bonf_png), use_container_width=True)
            else: st.info(f"Bonferroni image for {selected_view} is still processing.")

    with tab_runs:
        st.subheader(f"Per-Run Snapshots - Focus: {selected_view}")
        st.write("Checking consistency across sessions. **Threshold set to Z > 3.1** (High Rigor).")
        
        run_path = method_path / selected_contrast
        run_dirs = sorted([d for d in run_path.iterdir() if d.is_dir() and "run-" in d.name])
        
        if run_dirs:
            cols = st.columns(2)
            for i, run_p in enumerate(run_dirs):
                run_id = run_p.name.split("run-")[-1].split("_")[0]
                run_png = run_p / f"{selected_contrast}_run-{run_id}_{selected_view}_viz.png"
                with cols[i % 2]:
                    if run_png.exists():
                        st.image(str(run_png), caption=f"Run {run_id}", use_container_width=True)
                    else:
                        st.caption(f"Run {run_id} ({selected_view}) visualization is pending.")
        else:
            st.info("Individual run visualizations have not been generated for this subject yet.")