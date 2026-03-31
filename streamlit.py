import streamlit as st
import re
from pathlib import Path

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Motif-Stroke | 7T Explorer",
    page_icon="🧠",
    layout="wide",
)

# ─── PATHS ────────────────────────────────────────────────────────────────────
BASE          = Path(__file__).parent
MOTIF_DIRS    = [BASE / "results_motif4limbs_V01"]
JOYSTICK_DIRS = [BASE / "results_joystick_V01"]

# ─── CONTRAST METADATA ────────────────────────────────────────────────────────
# Covers every contrast folder that exists (or will exist) on disk.
CONTRAST_INFO = {

    # ── Shared (both tasks) ───────────────────────────────────────────────────
    "task_gt_baseline": {
        "label":  "Task > Baseline",
        "phrase": "Global engagement of the motor network compared to rest. "
                  "Maps every region more active during the task than at baseline. "
                  "This is the foundational contrast — always the starting point.",
        "decode": "🔴 Red = Active during task &nbsp;|&nbsp; 🔵 Blue = More active at rest",
    },
    "right_vs_left": {
        "label":  "Right > Left  (all limbs)",
        "phrase": "Hemispheric lateralization across all limbs: right-side movements "
                  "versus left-side movements. The left hemisphere should dominate "
                  "for right-side movements in healthy subjects.",
        "decode": "🔴 Red = Right limbs dominant &nbsp;|&nbsp; 🔵 Blue = Left limbs dominant",
    },

    # ── Motif4Limbs ───────────────────────────────────────────────────────────
    "hand_vs_foot": {
        "label":  "Hand > Foot",
        "phrase": "Primary motor cortex hand area (lateral M1, hand-knob) versus "
                  "foot area (medial M1, paracentral lobule). Tests the somatotopic "
                  "gradient along the motor strip.",
        "decode": "🔴 Red = Hand representation &nbsp;|&nbsp; 🔵 Blue = Foot representation",
    },
    "foot_vs_hand": {
        "label":  "Foot > Hand",
        "phrase": "Inverse of hand_vs_foot. Highlights the medial motor wall "
                  "(paracentral lobule) and SMA where foot movements are represented.",
        "decode": "🔴 Red = Foot representation &nbsp;|&nbsp; 🔵 Blue = Hand representation",
    },
    "right_vs_left_hand": {
        "label":  "Right Hand > Left Hand",
        "phrase": "Fine-grained lateralization of hand representations in primary "
                  "motor cortex. Isolates the hand-knob area only — contralateral "
                  "left M1 should dominate for right-hand movements.",
        "decode": "🔴 Red = Right hand (left M1) &nbsp;|&nbsp; 🔵 Blue = Left hand (right M1)",
    },
    "right_vs_left_foot": {
        "label":  "Right Foot > Left Foot",
        "phrase": "Lateralization of foot representations in the medial motor wall "
                  "(paracentral lobule). Contralateral hemisphere should dominate.",
        "decode": "🔴 Red = Right foot &nbsp;|&nbsp; 🔵 Blue = Left foot",
    },

    # ── Joystick — Events Method ──────────────────────────────────────────────
    "push_right_vs_left": {
        "label":  "Push Right > Left",
        "phrase": "Rightward joystick pushes versus leftward pushes. Tests directional "
                  "lateralisation of motor cortex: contralateral left M1 should dominate "
                  "for rightward pushes, contralateral right M1 for leftward pushes.",
        "decode": "🔴 Red = Rightward push (left M1 dominant) &nbsp;|&nbsp; 🔵 Blue = Leftward push (right M1 dominant)",
    },

    # ── Joystick — Motion Method ──────────────────────────────────────────────
    "amplitude_modulation": {
        "label":  "Amplitude Modulation (parametric)",
        "phrase": "Parametric contrast: regions where BOLD signal scales "
                  "proportionally with the peak joystick displacement across "
                  "all movement phases. Identifies areas encoding movement effort "
                  "and kinematics — typically M1, SMA, and cerebellum.",
        "decode": "🔴 Red = BOLD increases with greater amplitude &nbsp;|&nbsp; 🔵 Blue = Inversely related",
    },
    "amplitude_right_vs_left": {
        "label":  "Amplitude Right > Left (parametric)",
        "phrase": "Does amplitude tracking lateralize by direction? Compares the "
                  "parametric amplitude effect for rightward pushes versus leftward "
                  "pushes. Tests whether effort encoding is direction-specific.",
        "decode": "🔴 Red = Rightward amplitude stronger &nbsp;|&nbsp; 🔵 Blue = Leftward amplitude stronger",
    },
}

# ─── METHOD METADATA ──────────────────────────────────────────────────────────
METHOD_INFO = {
    "events": {
        "label": "Events Method",
        "icon":  "📅",
        "desc":  (
            "The GLM models **discrete push phases** from the events.tsv file: "
            "push onset (`left`/`right`) and return to rest (`center`). "
            "`*_reached` events are excluded (collinear with push onset, r=0.92). "
            "**Modulation = 1.0 for all trials** — this method asks *where is the brain active?*"
        ),
    },
    "motion": {
        "label": "Motion Method",
        "icon":  "📈",
        "desc":  (
            "A **parametric GLM**: same trial timing as the events method, but each "
            "trial is weighted by the **peak Euclidean joystick displacement** recorded "
            "during that trial. This method asks *where does BOLD scale proportionally "
            "with how hard the subject pushed?* Typical activations: M1, cerebellum, putamen."
        ),
    },
    "sequence": {
        "label": "Sequence Method",
        "icon":  "🔢",
        "desc":  (
            "The GLM is built by reconstructing trial onsets from the **fixed stimulus "
            "sequence CSV** (block order + timing constants). Each limb movement is "
            "modelled as a 2.2 s boxcar convolved with the HRF."
        ),
    },
    "behavioral": {
        "label": "Behavioral Method",
        "icon":  "🧪",
        "desc":  (
            "The GLM is built from the **raw behavioral log file**: keypresses anchored "
            "to the TTL scanner trigger pulse. Each keypress is modelled as a 0.5 s "
            "event. This method uses actual response times rather than the nominal sequence."
        ),
    },
}

# ─── ROI METADATA ─────────────────────────────────────────────────────────────
ROI_INFO = {
    "overview":       ("Overview",                    "Whole-brain ortho view centred on the motor strip. Best starting point."),
    "SMA":            ("SMA — Supplementary Motor Area", "Medial premotor region for motor planning and sequencing. Active in all motor tasks."),
    "M1_hand_L":      ("Left M1 — Hand Knob",         "Primary motor cortex for the right hand (contralateral). Lateral convexity of left hemisphere."),
    "M1_hand_R":      ("Right M1 — Hand Knob",        "Primary motor cortex for the left hand (contralateral). Mirror of M1_hand_L."),
    "M1_foot_medial": ("M1 — Foot (Medial Wall)",     "Medial motor strip for lower-limb representation, paracentral lobule."),
    "IPS_L":          ("Left IPS — Parietal",         "Left intraparietal sulcus: visuomotor integration for rightward targets."),
    "Visual_V5":      ("Visual V5 / MT+",             "Motion-sensitive visual cortex tracking the joystick cursor on screen."),
    "Cerebellum":     ("Cerebellum",                  "Coordinates movement timing and amplitude. Key region in parametric motion contrasts."),
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def method_display(folder_name: str) -> str:
    info = METHOD_INFO.get(folder_name.lower())
    if info:
        return f"{info['icon']} {info['label']}"
    return folder_name.replace("_", " ").title()

def method_description(folder_name: str) -> str | None:
    info = METHOD_INFO.get(folder_name.lower())
    return info["desc"] if info else None

def extract_view(filename: str) -> str | None:
    stem = Path(filename).stem
    for marker in ("_FDR_", "_BONF_"):
        if marker in stem:
            after = stem.split(marker)[-1]
            view = re.sub(r"^[qa][\d.]+_", "", after)
            return view
    return None

def get_views(combined_dir: Path) -> list[str]:
    views = set()
    for png in combined_dir.glob("*.png"):
        v = extract_view(png.name)
        if v:
            views.add(v)
    return sorted(views)

def find_img(directory: Path, *keywords) -> Path | None:
    for png in sorted(directory.glob("*.png")):
        name = png.name.lower()
        if all(k.lower() in name for k in keywords):
            return png
    return None

def roi_label(view: str) -> str:
    if view in ROI_INFO:
        return ROI_INFO[view][0]
    if view.lower().startswith("peak_"):
        coords = view.replace("peak_", "").replace("_", ", ")
        return f"Peak ({coords})"
    return view.replace("_", " ")

def roi_description(view: str) -> str:
    if view in ROI_INFO:
        return ROI_INFO[view][1]
    if view.lower().startswith("peak_"):
        coords = view.replace("peak_", "").replace("_", ", ")
        return f"Auto-peak: centered on the strongest activation voxel at MNI ({coords})."
    return ""

def get_subjects(dirs: list[Path]) -> dict[str, Path]:
    raw: dict[str, list[Path]] = {}
    for base in dirs:
        if not base.exists():
            continue
        for s in sorted(base.glob("sub-*")):
            if s.is_dir():
                raw.setdefault(s.name, []).append(s)
    result = {}
    for sub, paths in sorted(raw.items()):
        if len(paths) == 1:
            result[sub] = paths[0]
        else:
            for p in paths:
                result[f"{sub}  ({p.parent.name})"] = p
    return result

def show_image_or_missing(img_path: Path | None, caption: str = ""):
    if img_path and img_path.exists():
        st.image(str(img_path), caption=caption, use_container_width=True)
    else:
        st.markdown(
            "<div style='border:1px dashed #888;border-radius:6px;padding:20px;"
            "text-align:center;color:#888;font-size:0.85em;'>"
            "🚧 Not yet computed</div>",
            unsafe_allow_html=True,
        )
        if caption:
            st.caption(caption)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🧠 Motif-Stroke 7T")
    st.markdown("---")
    page = st.radio(
        "**Navigate to:**",
        ["🏠  Overview", "🦵  Motif4Limbs Dashboard", "🕹️  Joystick Dashboard"],
        label_visibility="collapsed",
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — WELCOME / OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Overview":

    import pandas as pd

    st.title("🧠 Motif-Stroke — 7T fMRI Explorer")
    st.markdown(
        "First-level GLM results from two motor tasks acquired at 7 Tesla in stroke patients. "
        "Each page displays thresholded Z-score maps (FDR and Bonferroni) for a given subject, "
        "method, and contrast. Select a task in the sidebar to begin."
    )
    st.markdown("---")

    # ── Tasks ──────────────────────────────────────────────────────────────────
    st.header("Tasks")
    col_m, col_j = st.columns(2, gap="large")
    with col_m:
        st.markdown("##### 🦵 Motif4Limbs")
        st.markdown(
            "Block-design somatotopic mapping. The subject performs sequential movements "
            "of each limb (right hand → left hand → right foot → left foot) in a fixed motif. "
            "Goal: characterise the somatotopic organisation of primary motor cortex "
            "and SMA, and detect post-stroke reorganisation."
        )
    with col_j:
        st.markdown("##### 🕹️ Joystick")
        st.markdown(
            "Visually-guided reaching task. The subject deflects a joystick to move a cursor "
            "toward left or right targets on screen, holds on reaching, then returns to centre. "
            "Goal: characterise goal-directed motor control, directional lateralisation, "
            "and effort-related BOLD responses."
        )

    st.markdown("---")

    # ── Methods ────────────────────────────────────────────────────────────────
    st.header("Analysis Methods")
    methods_table = pd.DataFrame([
        ["🦵 Motif4Limbs", "🔢 Sequence",   "GLM regressors derived from the fixed stimulus sequence (known block order + TR-locked timing). Modulation = 1."],
        ["🦵 Motif4Limbs", "🧪 Behavioral", "GLM regressors derived from logged keypress times, anchored to the TTL trigger. Captures actual response latencies."],
        ["🕹️ Joystick",    "📅 Events",     "Each trial phase (push, reached, return) modelled as a boxcar with constant amplitude (modulation = 1). Tests where BOLD is phase-specific."],
        ["🕹️ Joystick",    "📈 Motion",     "Parametric GLM: same trial timing as Events, but amplitude = peak Euclidean joystick displacement. Tests where BOLD scales with movement magnitude."],
    ], columns=["Task", "Method", "Description"])
    st.table(methods_table)

    st.markdown("---")

    # ── Contrasts ──────────────────────────────────────────────────────────────
    st.header("Contrasts")

    with st.expander("🦵 Motif4Limbs", expanded=False):
        st.table(pd.DataFrame([
            ["task_gt_baseline",   "0.25×(LH+RH+LF+RF)",        "Any limb movement drives greater BOLD than rest",                        "overview · SMA · M1_hand_L · M1_hand_R · M1_foot_medial"],
            ["hand_vs_foot",       "0.5×(LH+RH) − 0.5×(LF+RF)", "Hand movements drive greater BOLD than foot movements",                  "M1_hand_L · M1_hand_R · SMA"],
            ["foot_vs_hand",       "0.5×(LF+RF) − 0.5×(LH+RH)", "Foot movements drive greater BOLD than hand movements",                  "M1_foot_medial · SMA"],
            ["right_vs_left",      "0.5×(RH+RF) − 0.5×(LH+LF)", "Right-side limb movements drive greater BOLD than left-side",           "M1_hand_L · M1_hand_R · SMA"],
            ["right_vs_left_hand", "RH − LH",                    "Right-hand movements drive greater BOLD than left-hand movements",       "M1_hand_L · M1_hand_R"],
            ["right_vs_left_foot", "RF − LF",                    "Right-foot movements drive greater BOLD than left-foot movements",       "M1_foot_medial · SMA"],
        ], columns=["Contrast", "Formula", "Interpretation", "Where to look"]))

    with st.expander("🕹️ Joystick — Events", expanded=False):
        st.table(pd.DataFrame([
            ["task_gt_baseline",   "L + R + C",  "Any push phase drives greater BOLD than rest",       "overview · SMA · M1_hand_L · Visual_V5"],
            ["push_right_vs_left", "R − L",      "Rightward pushes drive greater BOLD than leftward",  "M1_hand_L · M1_hand_R · overview"],
        ], columns=["Contrast", "Formula", "Interpretation", "Where to look"]))
        st.caption("L=left push, R=right push, C=center return. *_reached events excluded (collinear, r=0.92).")

    with st.expander("🕹️ Joystick — Motion (parametric)", expanded=False):
        st.table(pd.DataFrame([
            ["amplitude_modulation",    "L + R + C", "BOLD scales proportionally with peak joystick displacement",               "M1_hand_L · SMA · Cerebellum"],
            ["amplitude_right_vs_left", "R − L",     "BOLD–amplitude coupling is stronger for rightward than leftward movements", "M1_hand_L · M1_hand_R"],
        ], columns=["Contrast", "Formula", "Interpretation", "Where to look"]))
        st.caption("Amplitude = peak Euclidean joystick displacement × 100 per trial.")

    st.markdown("---")

    # ── Thresholds ─────────────────────────────────────────────────────────────
    st.header("Statistical Thresholds")
    st.table(pd.DataFrame([
        ["FDR",        "Controls expected proportion of false positives among suprathreshold voxels",         "q < 0.05 (joystick) · q < 0.001 (motif4limbs)",  "Sensitive — reveals full extent of activation"],
        ["Bonferroni", "Controls family-wise error rate: P(any false positive in image) < α",                "α < 0.2 (joystick) · α < 0.05 (motif4limbs)",    "Conservative — confirms focal peaks only"],
    ], columns=["Method", "Correction principle", "Setting", "Use"]))
    st.info("Regions surviving both FDR and Bonferroni are the most robust findings.", icon="💡")

    st.markdown("---")

    # ── Brain views ────────────────────────────────────────────────────────────
    st.header("Brain Views")
    st.caption("Each map is displayed as three orthogonal slices centred on a predefined MNI coordinate.")
    st.table(pd.DataFrame([
        ["overview",        "(0, −20, 60)",   "Mid-motor strip orthoview — starting point for any contrast"],
        ["SMA",             "(0, −5, 65)",    "Supplementary Motor Area — motor planning, sequencing"],
        ["M1_hand_L",       "(−38, −22, 56)", "Left primary motor cortex, hand knob — contralateral right-hand control"],
        ["M1_hand_R",       "(38, −22, 56)",  "Right primary motor cortex, hand knob — contralateral left-hand control"],
        ["M1_foot_medial",  "(0, −30, 70)",   "Medial motor strip — foot/lower-limb representation"],
        ["IPS_L",           "(−26, −64, 48)", "Left intraparietal sulcus — visuomotor integration"],
        ["Visual_V5",       "(45, −75, 5)",   "Area V5/MT+ — motion-sensitive visual cortex, cursor tracking"],
        ["Cerebellum",      "(18, −52, −18)", "Cerebellum — movement timing and amplitude coordination"],
        ["peak_X_Y_Z",      "auto",           "Centred on the peak surviving voxel for this subject and contrast"],
    ], columns=["View", "MNI centre", "Region / interpretation"]))

# ═══════════════════════════════════════════════════════════════════════════════
# PAGES 2 & 3 — DASHBOARDS
# ═══════════════════════════════════════════════════════════════════════════════
else:
    is_motif   = "Motif" in page
    task_dirs  = MOTIF_DIRS if is_motif else JOYSTICK_DIRS
    task_label = "🦵 Motif4Limbs" if is_motif else "🕹️ Joystick"

    # ── Sidebar controls ───────────────────────────────────────────────────────
    with st.sidebar:
        subjects = get_subjects(task_dirs)
        if not subjects:
            st.error("No subjects found.")
            st.stop()

        selected_sub_label = st.selectbox("👤 Subject", list(subjects.keys()))
        sub_path = subjects[selected_sub_label]

        methods = [d.name for d in sorted(sub_path.iterdir()) if d.is_dir()]
        if not methods:
            st.error("No analysis methods found.")
            st.stop()
        selected_method = st.selectbox("📐 Method", methods, format_func=method_display)
        method_path = sub_path / selected_method

        contrasts = [d.name for d in sorted(method_path.iterdir()) if d.is_dir()]
        if not contrasts:
            st.error("No contrasts found.")
            st.stop()

        selected_contrast = st.selectbox(
            "🎯 Contrast",
            contrasts,
            format_func=lambda c: CONTRAST_INFO.get(c, {}).get("label", c.replace("_", " ").title()),
        )

    contrast_path = method_path / selected_contrast
    combined_dir  = contrast_path / "combined_total"

    # ── Page header ────────────────────────────────────────────────────────────
    st.title(f"📊 {task_label} Dashboard")
    st.caption(
        f"Subject: **{selected_sub_label}** &nbsp;|&nbsp; "
        f"Method: **{method_display(selected_method)}** &nbsp;|&nbsp; "
        f"Contrast: **{CONTRAST_INFO.get(selected_contrast, {}).get('label', selected_contrast)}**"
    )

    meth_desc = method_description(selected_method)
    if meth_desc:
        icon = METHOD_INFO.get(selected_method.lower(), {}).get("icon", "ℹ️")
        st.info(meth_desc, icon=icon)

    # ── Contrast interpretation ────────────────────────────────────────────────
    c_info = CONTRAST_INFO.get(selected_contrast)
    if c_info:
        with st.container(border=True):
            st.markdown(f"##### 🎯 {c_info['label']}")
            st.markdown(c_info["phrase"])
            st.markdown(c_info["decode"])
    else:
        st.info(f"Contrast: `{selected_contrast}`")

    st.markdown("---")

    # ── Threshold reminder ─────────────────────────────────────────────────────
    with st.expander("🔬 Statistical thresholds — quick reminder", expanded=False):
        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown("**FDR** — sensitive, shows the full network")
            st.caption("Controls the proportion of false positives among significant voxels.")
        with tc2:
            st.markdown("**Bonferroni** — strict, shows only the strongest peaks")
            st.caption("Controls the probability of even one false positive in the whole brain.")

    st.markdown("---")

    # ── Brain view selector ────────────────────────────────────────────────────
    views = get_views(combined_dir) if combined_dir.exists() else []

    if not views:
        st.warning("⏳ No brain maps available yet for this selection.")
        st.stop()

    st.subheader("📍 Select Brain View")
    sel_col, desc_col = st.columns([1, 2], gap="large")

    with sel_col:
        selected_view = st.radio(
            "Available views:",
            views,
            format_func=roi_label,
            label_visibility="collapsed",
        )

    with desc_col:
        st.markdown(f"**{roi_label(selected_view)}**")
        dsc = roi_description(selected_view)
        if dsc:
            st.markdown(dsc)

    st.markdown("---")

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_total, tab_runs = st.tabs(["🎯 Total Summary Map", "🔎 Run-by-Run Consistency"])

    with tab_total:
        fdr_img  = find_img(combined_dir, "fdr",  selected_view)
        bonf_img = find_img(combined_dir, "bonf", selected_view)

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.markdown("#### FDR — Exploratory")
            show_image_or_missing(fdr_img, "FDR-corrected")
        with col2:
            st.markdown("#### Bonferroni — Strict")
            show_image_or_missing(bonf_img, "Bonferroni-corrected")

    with tab_runs:
        st.markdown(
            "Individual runs let you check **run-to-run consistency** "
            "and spot motion artefacts or data quality issues."
        )
        run_dirs = sorted(
            [d for d in contrast_path.iterdir() if d.is_dir() and "run" in d.name]
        )
        if not run_dirs:
            st.info("No individual run folders found for this contrast.")
        else:
            run_cols = st.columns(min(len(run_dirs), 3), gap="medium")
            for i, run_p in enumerate(run_dirs):
                run_img = find_img(run_p, selected_view) or find_img(run_p, "overview")
                with run_cols[i % len(run_cols)]:
                    st.markdown(f"**{run_p.name}**")
                    show_image_or_missing(run_img, run_p.name)
