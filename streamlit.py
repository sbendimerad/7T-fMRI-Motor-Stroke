import streamlit as st
import os
from pathlib import Path
import numpy as np

# --- CONFIG ---
BASE_RESULTS_DIR = Path(__file__).parent / "results_V02"
st.set_page_config(page_title="Motif-Stroke | 7T Explorer", layout="wide")

# --- SCIENTIFIC KNOWLEDGE BASE ---
TASK_METADATA = {
    "Motif4Lambs": {
        "title": "🦵 Motif4Lambs (Somatotopic Mapping)",
        "subfolder": "lambs",
        "contrasts": {
            "task_gt_baseline": {
                "phrase": "This contrast evaluates the global engagement of the motor strip compared to resting baseline.",
                "decode": "🔴 RED indicates limb movement; 🔵 BLUE indicates resting state."
            },
            "hand_vs_foot": {
                "phrase": "This comparison maps the somatotopic organization of the upper vs. lower limbs.",
                "decode": "🔴 RED identifies Hand areas (Lateral); 🔵 BLUE identifies Foot areas (Medial)."
            },
            "global_right_vs_left": {
                "phrase": "This analysis checks for hemispheric dominance during bilateral motor execution.",
                "decode": "🔴 RED indicates Right limbs (Left Hemisphere); 🔵 BLUE indicates Left limbs (Right Hemisphere)."
            },
            "right_vs_left_hand": {
                "phrase": "A high-resolution comparison between contralateral and ipsilateral hand representations.",
                "decode": "🔴 RED indicates Right Hand activity; 🔵 BLUE indicates Left Hand activity."
            },
            "right_vs_left_foot": {
                "phrase": "Investigating the medial motor wall for foot-specific lateralization.",
                "decode": "🔴 RED indicates Right Foot activity; 🔵 BLUE indicates Left Foot activity."
            }
        }
    },
    "Joystick": {
        "title": "🕹️ Joystick Task (Directional & Spatial)",
        "subfolder": "joystick",
        "contrasts": {
            "task_gt_baseline": {
                "phrase": "This contrast highlights the primary motor and visual effort required to move the joystick.",
                "decode": "🔴 RED indicates Joystick movement; 🔵 BLUE indicates resting baseline."
            },
            "right_vs_left": {
                "phrase": "Compares moving Right vs. moving Left. Because the brain is 'crossed', look for activity on the Left side of the brain.",
                "decode": "🔴 RED = Aiming Right; 🔵 BLUE = Aiming Left."
            },
            "left_vs_right": {
                "phrase": "Compares moving Left vs. moving Right. Because the brain is 'crossed', look for activity on the Right side of the brain.",
                "decode": "🔴 RED = Aiming Left; 🔵 BLUE = Aiming Right."
            },
            "target_achieved": {
                "phrase": "This event-related model captures the transition from movement execution to target success.",
                "decode": "🔴 RED identifies the 'Goal Hit' (Success/Stop); 🔵 BLUE identifies 'Travel' (Execution)."
            },
            "return_gt_move": {
                "phrase": "This evaluates the inhibitory control required to stop the joystick and return to the origin.",
                "decode": "🔴 RED indicates Re-centering (The Stop); 🔵 BLUE indicates the Outward Push (The Go)."
            }
        }
    }
}

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🧠 Motif-Stroke 7T")
page = st.sidebar.radio("Navigation", ["Welcome", "Motif4Lambs Dashboard", "Joystick Dashboard"])

# --- PAGE 1: WELCOME ---
if page == "Welcome":
    st.title("🏥 Motif-Stroke: 7T Analysis Explorer")
    st.markdown("""
    ### Welcome! 👋
    This application allows you to explore the results generated for the **Motif-Stroke** project. 
    The platform provides access to high-resolution statistical analyses performed on 7 Tesla fMRI data.
    """)
    st.info("**🏗 Project Status:** If you don't see a specific result yet, it's likely still being processed in the pipeline!")
    st.divider()
    st.subheader("🚀 How to use this platform")
    st.markdown("""
    To inspect the brain activation maps, follow these steps in order:
    1. **Pick your Project:** Use the sidebar to choose between **Motif4Lambs** or **Joystick**.
    2. **Select a Subject:** Choose the specific **Subject ID** from the subdirectory.
    3. **Choose the Design Method:** Select the GLM modeling approach (e.g., `behavioral_method`).
    4. **Select the Contrast:** Pick the specific neural comparison you wish to inspect.
    5. **Inspect Anatomy:** Use the **Anatomical Selection** area to toggle between specific ROIs.
    """)
    st.success("💡 **Pro Tip:** Use the tabs at the bottom to switch between the **Total Summary Map** and **Detailed Run-by-Run** consistency views.")

# --- THE DASHBOARDS ---
else:
    task_key = "Motif4Lambs" if "Motif" in page else "Joystick"
    meta = TASK_METADATA[task_key]
    CURRENT_TASK_DIR = BASE_RESULTS_DIR / meta['subfolder']

    if not CURRENT_TASK_DIR.exists():
        st.error(f"### 🚧 Directory Not Found: `{meta['subfolder']}`")
        st.stop()

    subjects = sorted([d.name for d in CURRENT_TASK_DIR.glob("sub-*")])
    if not subjects:
        st.warning(f"No subjects found in {meta['subfolder']}.")
        st.stop()
    selected_sub = st.sidebar.selectbox("👤 Select Subject", subjects)

    sub_path = CURRENT_TASK_DIR / selected_sub
    methods = sorted([d.name for d in sub_path.iterdir() if d.is_dir()])
    selected_method = st.sidebar.selectbox("📐 Select Method", methods)

    method_path = sub_path / selected_method
    contrasts = sorted([d.name for d in method_path.iterdir() if d.is_dir()])
    selected_contrast = st.sidebar.selectbox("🎯 Select Contrast", contrasts)

    # --- MAIN CONTENT ---
    st.title(f"📊 {meta['title']}")
    st.caption(f"Subject: {selected_sub} | Method: {selected_method}")
    
    # --- DYNAMIC INTERPRETATION SECTION ---
    c_info = meta['contrasts'].get(selected_contrast, {"phrase": "N/A", "decode": "🔴 RED vs 🔵 BLUE"})
    st.markdown(f"### 🎯 Current Analysis: `{selected_contrast}`")
    st.markdown(f"**Interpretation:** {c_info['phrase']}")
    st.success(f"**Decoding the Map:** {c_info['decode']}")

    st.divider()

    # --- SCIENTIFIC THRESHOLD SECTION (PERMANENT) ---
    st.subheader("🔬 Statistical Rigor & Thresholding")
    t_col1, t_col2, t_col3 = st.columns(3)
    
    with t_col1:
        st.markdown("**FDR Correction**")
        st.caption("Standard for **Sensitivity**. Controls the proportion of false positives to visualize the extended functional network (IPS, SMA).")
        
    with t_col2:
        st.markdown("**Bonferroni Correction**")
        st.caption("Standard for **Specificity**. The strictest control; surviving signals represent the absolute core 'Activation Epicenters'.")

    with t_col3:
        st.markdown("**Auto-Peak Discovery**")
        st.caption("A dynamic subject-specific view. Centers on the **Global Maximum** of activity to account for anatomical variability.")

    st.divider()

    # --- ANATOMICAL SELECTION ---
    total_dir = method_path / selected_contrast / "combined_total"
    view_files = list(total_dir.glob("*.png"))
    view_names = sorted(list(set([f.name.split("FDR_")[-1].replace(".png", "") for f in view_files if "FDR" in f.name])))

    if not view_names:
        st.warning("No anatomical views found for this selection yet.")
        st.stop()

    select_col, explain_col = st.columns([1, 2])
    with select_col:
        selected_view = st.radio("**Select Brain Area:**", view_names)

    with explain_col:
        st.markdown("### 📍 ROI Anatomy")
        if "SMA" in selected_view:
            st.write("**SMA (Supplementary Motor Area):** Planning and sequencing center. Active in both motor tasks.")
        elif "M1_hand" in selected_view:
            st.write("**M1 Hand Knob:** Primary motor executor for finger and joystick movements.")
        elif "M1_foot" in selected_view:
            st.write("**M1 Foot:** Medial motor strip specialized for lower limb mapping in Motif4Lambs.")
        elif "IPS_L" in selected_view:
            st.write("**Left IPS:** Specialized for spatial reach calculation in the **Right** visual field.")
        elif "IPS_R" in selected_view:
            st.write("**Right IPS:** Specialized for spatial reach calculation in the **Left** visual field.")
        elif "IPS" in selected_view:
            st.write("**IPS (Parietal GPS):** The hub for integrating visual and motor spatial information.")
        elif "V5" in selected_view:
            st.write("**Visual V5:** Motion processing center that tracks the movement of the joystick cursor.")
        elif "PEAK" in selected_view:
            st.write("**Auto-Peak:** The absolute statistical center of activation for this individual.")
        else:
            st.write("**Overview:** Global distribution view across the motor strip.")

    st.divider()

    # --- TABS FOR MAPS ---
    tab_total, tab_runs = st.tabs(["🎯 Total Summary Map", "🔎 Detailed Run-by-Run"])

    with tab_total:
        fdr_png = next(total_dir.glob(f"*FDR_{selected_view}.png"), None)
        bonf_png = next(total_dir.glob(f"*BONF_{selected_view}.png"), None)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### FDR-Corrected (Exploratory)")
            if fdr_png: st.image(str(fdr_png), use_container_width=True)
        with c2:
            st.markdown("#### Bonferroni-Corrected (Strict)")
            if bonf_png: st.image(str(bonf_png), use_container_width=True)

    with tab_runs:
        run_path = method_path / selected_contrast
        run_dirs = sorted([d for d in run_path.iterdir() if d.is_dir() and "run-" in d.name])
        if run_dirs:
            cols = st.columns(2)
            for i, run_p in enumerate(run_dirs):
                run_png = next(run_p.glob(f"*{selected_view}*.png"), None)
                with cols[i % 2]:
                    if run_png: st.image(str(run_png), caption=f"Run Snapshot", use_container_width=True)