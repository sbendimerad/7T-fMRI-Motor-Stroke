import streamlit as st
import os
from pathlib import Path

# --- CONFIG ---
# Setting the root to your absolute path provided
RESULTS_DIR = Path("/volatile/home/sb283337/Bureau/7T-fMRI-Motor-Stroke/results_V01")
st.set_page_config(page_title="Motif-Stroke Viewer", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🚀 Motif-Stroke Explorer")
page = st.sidebar.radio("Navigation", ["Home", "Analysis Dashboard"])

if page == "Home":
    st.title("🧠 Motif-Stroke Explorer: User Guide")
    
    st.markdown("""
    This application is a visual interface for 7T fMRI motor mapping. 
    Follow the steps below to navigate the data and interpret the statistical results.
    """)

    # --- SECTION 1: SELECTION ---
    st.header("1️⃣ How to Select Data")
    col1, col2 = st.columns(2)
    with col1:
        st.write("""
        **Sidebar Navigation:**
        - **Subject**: Choose the patient ID.
        - **Method**: Choose the Matrix Design. 
            - *Sequence*: Theoretical task timing.
            - *Behavioral*: Timing adjusted by patient response.
        - **Contrast**: Choose the limb comparison (e.g., `hand_vs_foot`).
        """)
    with col2:
        st.info("""
        **Pro Tip:** If you change the Subject, the 'Method' and 'Contrast' lists will update automatically to show only what is available for that specific patient.
        """)

    st.divider()

    # --- SECTION 2: INTERPRETATION ---
    st.header("2️⃣ What am I looking at?")
    
    st.markdown("""
    When you open the **Results Gallery**, you see five diagnostic maps. Here is how to interpret them:
    """)

    # Using a table for clear interpretation logic
    st.table([
        {"Map": "Beta", "Description": "Effect Size", "Interpretation": "Shows the 'strength' of the BOLD signal. Higher = more oxygenated blood flow."},
        #{"Map": "TOTAL_02_variance", "Description": "Noise/Error", "Interpretation": "Shows where the data is 'messy'. High variance in motor cortex suggests motion artifacts."},
        {"Map": "Tstat", "Description": "Signal-to-Noise", "Interpretation": "The Ratio of Beta/Variance. Shows how reliable the activation is."},
        {"Map": "Zmap (FDR)", "Description": "The 'Truth'", "Interpretation": "Corrected for thousands of tests. If you see color here, it is statistically significant (q < 0.05)."}
    ])

    # --- SECTION 3: MOTOR ANATOMY ---
    st.header("3️⃣ Anatomical Verification")
    st.write("""
    For motor tasks, check for activation along the **Precentral Gyrus**. 
    - **Hands**: Look for the 'Hand Knob' in the middle of the motor strip.
    - **Feet**: Look at the medial wall (top-middle of the brain).
    """)
    
    

    st.success("🚀 Ready? Select 'Analysis Dashboard' in the sidebar to begin.")

else:
    if not RESULTS_DIR.exists():
        st.error(f"Directory not found: {RESULTS_DIR}")
        st.stop()

    # --- SELECTION ---
    subjects = sorted([d.name for d in RESULTS_DIR.glob("sub-*")])
    selected_sub = st.sidebar.selectbox("Patient", subjects)

    sub_path = RESULTS_DIR / selected_sub
    methods = sorted([d.name for d in sub_path.iterdir() if d.is_dir()])
    selected_method = st.sidebar.selectbox("Method", methods)

    contrast_path = sub_path / selected_method
    contrasts = sorted([d.name for d in contrast_path.iterdir() if d.is_dir()])
    selected_contrast = st.sidebar.selectbox("Contrast", contrasts)

    # --- PATHS ---
    # Path: sub-02 / sequence_method / global_right_vs_left / combined_total
    total_dir = contrast_path / selected_contrast / "combined_total"

    st.title(f"📊 {selected_sub} Results")
    
    tab_fusion, tab_runs = st.tabs(["🎯 Total", "🔎 By Run"])

    with tab_fusion:
        if total_dir.exists():
            st.subheader("Diagnostic Maps")
            
            # We map your 01-05 naming convention
            diagnostic_maps = {
                "01 - Beta (Effect Size)": "TOTAL_01_beta.png",
                "02 - Variance (Noise)": "TOTAL_02_variance.png",
                "03 - T-Stat (Reliability)": "TOTAL_03_tstat.png",
               # "04 - Z-Map (Uncorrected)": "TOTAL_04_zmap_uncorrected.png",
                "04 - Z-Map (FDR Corrected)": "TOTAL_05_zmap_FDR.png"
            }

            # Select which PNG to show
            choice = st.selectbox("Select Diagnostic Map", list(diagnostic_maps.keys()))
            target_png = total_dir / diagnostic_maps[choice]

            if target_png.exists():
                # We use st.image because these are static PNG files
                st.image(str(target_png), use_container_width=True, caption=choice)
            else:
                st.error(f"PNG not found: {target_png.name}")
                st.info(f"Full path tried: {target_png}")
        else:
            st.error(f"Folder not found: {total_dir}")

    with tab_runs:
        st.subheader("Individual Run")
        # Finds run folders like run-01_dir-ap
        run_dirs = sorted([d for d in (contrast_path / selected_contrast).iterdir() 
                          if d.is_dir() and "run-" in d.name])
        
        if run_dirs:
            cols = st.columns(2)
            for i, run_p in enumerate(run_dirs):
                # Your script saves: {c_name}_run_viz.png
                run_png = run_p / f"{selected_contrast}_run_viz.png"
                
                with cols[i % 2]:
                    if run_png.exists():
                        st.image(str(run_png), caption=f"QC: {run_p.name}")
                    else:
                        st.caption(f"No PNG found for {run_p.name}")
        else:
            st.info("No run directories found.")