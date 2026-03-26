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
BASE = Path(__file__).parent
MOTIF_DIRS    = [BASE / "results_motif4limbs_V01"]
JOYSTICK_DIRS = [BASE / "results_joystick_V01"]
EXCLUDED_CONTRASTS = {"foot_vs_hand", "hand_vs_foot"}

# ─── SCIENTIFIC METADATA ──────────────────────────────────────────────────────
CONTRAST_INFO = {
    # ── Shared ──
    "task_gt_baseline": {
        "label": "Task > Baseline",
        "phrase": "Global engagement of the motor strip compared to resting baseline. This is the foundational contrast — it maps every region that is more active during the task than at rest.",
        "decode": "🔴 **Red** = Active during task &nbsp;|&nbsp; 🔵 **Blue** = More active at rest",
    },
    "right_vs_left": {
        "label": "Right > Left  (all limbs)",
        "phrase": "Compares right-side vs left-side motor activity across all limbs. Tests hemispheric lateralization: the left hemisphere should dominate for right-side movements.",
        "decode": "🔴 **Red** = Right limbs / Left hemisphere dominant &nbsp;|&nbsp; 🔵 **Blue** = Left limbs / Right hemisphere dominant",
    },
    # ── Motif4Limbs ──
    "right_vs_left_hand": {
        "label": "Right Hand > Left Hand",
        "phrase": "Fine-grained lateralization of hand representations in primary motor cortex (hand-knob area). Isolates the hand region only.",
        "decode": "🔴 **Red** = Right hand &nbsp;|&nbsp; 🔵 **Blue** = Left hand",
    },
    "right_vs_left_foot": {
        "label": "Right Foot > Left Foot",
        "phrase": "Lateralization of foot representations in the medial motor wall (paracentral lobule). Isolates the foot region only.",
        "decode": "🔴 **Red** = Right foot &nbsp;|&nbsp; 🔵 **Blue** = Left foot",
    },
    "global_right_vs_left": {
        "label": "Global Right > Left  (all four limbs)",
        "phrase": "Hemispheric dominance pooled across all four limbs simultaneously. Provides a broad view of motor lateralization.",
        "decode": "🔴 **Red** = Right-side movements / Left hemisphere &nbsp;|&nbsp; 🔵 **Blue** = Left-side movements / Right hemisphere",
    },
    # ── Joystick — Events Method ──
    "left_vs_right": {
        "label": "Left > Right  (joystick direction)",
        "phrase": "Compares leftward joystick pushes to rightward pushes. Involves contralateral motor and parietal regions.",
        "decode": "🔴 **Red** = Aiming Left &nbsp;|&nbsp; 🔵 **Blue** = Aiming Right",
        "joystick_method": "events",
    },
    "active_effort_vs_passive": {
        "label": "Active Effort > Passive",
        "phrase": "Active volitional motor effort versus passive joystick displacement. Isolates top-down motor drive from sensory feedback.",
        "decode": "🔴 **Red** = Active volitional push &nbsp;|&nbsp; 🔵 **Blue** = Passive movement",
        "joystick_method": "events",
    },
    "push_right_vs_left": {
        "label": "Push Right > Push Left",
        "phrase": "Directional specificity: rightward versus leftward pushes. Engages contralateral M1 and parietal areas.",
        "decode": "🔴 **Red** = Pushing Right &nbsp;|&nbsp; 🔵 **Blue** = Pushing Left",
        "joystick_method": "events",
    },
    "goal_attained_feedback": {
        "label": "Goal Attained (Feedback)",
        "phrase": "Event-related BOLD response time-locked to the moment the joystick cursor reaches the target. Captures reward/stop processing.",
        "decode": "🔴 **Red** = Goal achieved (reward signal) &nbsp;|&nbsp; 🔵 **Blue** = In-motion (execution phase)",
        "joystick_method": "events",
    },
    "return_gt_move": {
        "label": "Return > Move",
        "phrase": "Inhibitory motor control: the neural cost of stopping and returning to center versus continuing to push outward.",
        "decode": "🔴 **Red** = Re-centering / the stop &nbsp;|&nbsp; 🔵 **Blue** = Outward push / the go",
        "joystick_method": "events",
    },
    # ── Joystick — Motions Method ──
    "speed_gt_baseline": {
        "label": "Speed > Baseline",
        "phrase": "Parametric modulation by cursor speed: regions whose BOLD signal scales with how fast the joystick is moved.",
        "decode": "🔴 **Red** = Higher speed correlates with more activation &nbsp;|&nbsp; 🔵 **Blue** = Inversely related to speed",
        "joystick_method": "motions",
    },
    "displacement_gt_baseline": {
        "label": "Displacement > Baseline",
        "phrase": "Parametric modulation by joystick displacement amplitude: regions encoding how far the cursor travels.",
        "decode": "🔴 **Red** = Greater displacement = more activation &nbsp;|&nbsp; 🔵 **Blue** = Inversely related to amplitude",
        "joystick_method": "motions",
    },
    "direction_right_gt_left": {
        "label": "Direction Right > Left (continuous)",
        "phrase": "Continuous directional regressor: regions encoding rightward vs leftward movement angle in a parametric model.",
        "decode": "🔴 **Red** = Rightward direction preference &nbsp;|&nbsp; 🔵 **Blue** = Leftward direction preference",
        "joystick_method": "motions",
    },
    "velocity_x_gt_baseline": {
        "label": "Velocity X (horizontal)",
        "phrase": "Parametric regressor tracking the horizontal velocity component of the joystick cursor.",
        "decode": "🔴 **Red** = Rightward velocity &nbsp;|&nbsp; 🔵 **Blue** = Leftward velocity",
        "joystick_method": "motions",
    },
}

METHOD_INFO = {
    # Joystick methods — maps folder name fragments → display info
    "events":   {
        "label": "Events Method",
        "icon": "📅",
        "desc": (
            "The GLM is built from **discrete task events**: push onset, target reached, "
            "return onset. Each event is modelled as an impulse convolved with the HRF. "
            "This captures *what happens* at each phase of the trial."
        ),
    },
    "motions":  {
        "label": "Motions Method",
        "icon": "📈",
        "desc": (
            "The GLM uses **continuous kinematic regressors** derived from the joystick "
            "sensor (speed, displacement, velocity X/Y). This captures *how* the movement "
            "is executed and which regions encode movement quality."
        ),
    },
    # Motif4Limbs methods
    "behavioral": {
        "label": "Behavioral Method",
        "icon": "🧪",
        "desc": "GLM built from the task timing file (button-press / cue onsets). Standard event-based approach.",
    },
    "sequence":   {
        "label": "Sequence Method",
        "icon": "🔢",
        "desc": "GLM exploiting the fixed motif order of limb movements as a sequence-level regressor.",
    },
}

def method_display(folder_name: str) -> str:
    """Return a pretty label for a method folder name."""
    fl = folder_name.lower()
    for key, info in METHOD_INFO.items():
        if key in fl:
            return f"{info['icon']} {info['label']}"
    return folder_name.replace("_", " ").title()

def method_description(folder_name: str) -> str | None:
    fl = folder_name.lower()
    for key, info in METHOD_INFO.items():
        if key in fl:
            return info["desc"]
    return None

ROI_INFO = {
    "overview":      ("Overview",               "Global whole-brain distribution across the motor strip. Best starting point to identify which regions are active."),
    "SMA":           ("SMA — Supplementary Motor Area", "Medial premotor region crucial for motor planning and sequencing. Active in both tasks. Often the first region to recruit."),
    "M1_hand_L":     ("M1 Left — Hand Knob",    "Primary motor cortex for the right hand. Located on the lateral convexity of the left hemisphere."),
    "M1_hand_R":     ("M1 Right — Hand Knob",   "Primary motor cortex for the left hand. Mirror of M1_hand_L in the right hemisphere."),
    "M1_foot_medial":("M1 — Foot (Medial Wall)","Medial motor strip for lower-limb representation in the paracentral lobule."),
    "IPS_L":         ("Left IPS — Parietal GPS", "Left intraparietal sulcus: integrates visual and motor signals for rightward spatial targets."),
    "IPS_R":         ("Right IPS — Parietal GPS","Right intraparietal sulcus: integrates visual and motor signals for leftward spatial targets."),
    "Visual_V5":     ("Visual V5 / MT+",         "Motion-processing cortex tracking the joystick cursor on screen. Strong in joystick directional contrasts."),
    "AUTO_PEAK":     ("Auto-Peak (subject hotspot)", "Centered automatically on the single strongest activation voxel for this individual subject."),
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def extract_view(filename: str) -> str | None:
    """Extract ROI/view name from a PNG filename — handles both V01 and V02 naming."""
    stem = Path(filename).stem
    for marker in ("_FDR_", "_BONF_"):
        if marker in stem:
            after = stem.split(marker)[-1]
            # Strip threshold prefix: q0.001_, a0.05_, q0.05_, a0.2_, …
            view = re.sub(r"^[qa][\d.]+_", "", after)
            return view
    return None

def get_views(combined_dir: Path) -> list[str]:
    """Return sorted unique view names available in a combined_total directory."""
    views = set()
    for png in combined_dir.glob("*.png"):
        v = extract_view(png.name)
        if v:
            views.add(v)
    return sorted(views)

def find_img(directory: Path, *keywords) -> Path | None:
    """Return first PNG whose name contains ALL keywords (case-insensitive)."""
    for png in sorted(directory.glob("*.png")):
        name = png.name.lower()
        if all(k.lower() in name for k in keywords):
            return png
    return None

def roi_label(view: str) -> str:
    """Pretty display label for a view name."""
    if view in ROI_INFO:
        return ROI_INFO[view][0]
    if view.lower().startswith("peak_") or view.lower() == "auto_peak":
        return "Auto-Peak (hotspot)"
    return view.replace("_", " ")

def roi_description(view: str) -> str:
    """Scientific description for a view name."""
    if view in ROI_INFO:
        return ROI_INFO[view][1]
    if view.lower().startswith("peak_"):
        coords = view.replace("peak_", "").replace("_", ", ")
        return f"Auto-peak view centered on the global maximum activation at MNI coordinates ({coords})."
    return "Brain region of interest."

def get_subjects(dirs: list[Path]) -> dict[str, Path]:
    """Collect {{display_name: path}} for all sub-* folders across given directories."""
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
    """Display an image if it exists, otherwise show a compact placeholder."""
    if img_path and img_path.exists():
        st.image(str(img_path), caption=caption, use_container_width=True)
    else:
        st.markdown(
            "<div style='border:1px dashed #888;border-radius:6px;padding:20px;"
            "text-align:center;color:#888;font-size:0.85em;'>"
            "🚧 Not yet available</div>",
            unsafe_allow_html=True,
        )
        if caption:
            st.caption(caption)

# ─── SIDEBAR NAVIGATION ──────────────────────────────────────────────────────
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

    st.title("🧠 Motif-Stroke — 7T fMRI Analysis Explorer")
    st.markdown(
        "Welcome to the **Motif-Stroke** analysis platform. This tool lets you explore "
        "high-resolution statistical brain maps generated from **7 Tesla fMRI** data "
        "in patients recovering from stroke."
    )
    st.info(
        "**🏗 Pipeline Status:** If a map is missing for a subject or contrast, it is "
        "still being processed — the dashboard will show a placeholder automatically.",
        icon="ℹ️",
    )

    st.markdown("---")

    # ── SECTION 1: The two tasks ───────────────────────────────────────────────
    st.header("📋 The Two Tasks")

    col_m, col_j = st.columns(2, gap="large")

    with col_m:
        st.subheader("🦵 Task 1 — Motif4Limbs")
        st.markdown(
            "A **somatotopic mapping** paradigm. The participant performs sequential "
            "movements of all four limbs (right hand, left hand, right foot, left foot) "
            "in a fixed order ('motif'). \n\n"
            "**Goal:** Map the body representation in primary motor cortex (M1) and "
            "supplementary motor area (SMA) at ultra-high field resolution, and quantify "
            "any reorganisation due to stroke."
        )

    with col_j:
        st.subheader("🕹️ Task 2 — Joystick")
        st.markdown(
            "A **visually-guided joystick** task. The participant pushes a joystick "
            "to move a cursor toward a spatial target, holds it, then returns to centre. "
            "\n\n"
            "**Goal:** Probe the dorsal visuomotor stream (M1, SMA, IPS, V5) and "
            "measure directional specificity, effort, and feedback processing during "
            "goal-directed reaching.\n\n"
            "This task is analysed with **two complementary GLM approaches:**"
        )
        st.markdown(
            "- 📅 **Events Method** — discrete trial phases (push / target hit / return) "
            "modelled as HRF-convolved impulses\n"
            "- 📈 **Motions Method** — continuous kinematic regressors (speed, displacement, "
            "velocity X/Y) derived from the joystick sensor"
        )

    st.markdown("---")

    # ── SECTION 2: Contrasts explained ────────────────────────────────────────
    st.header("🎯 Contrasts — What Each Comparison Tests")

    with st.expander("🦵  Motif4Limbs contrasts", expanded=True):
        motif_contrasts = [
            "task_gt_baseline", "right_vs_left", "right_vs_left_hand",
            "right_vs_left_foot", "global_right_vs_left",
        ]
        for key in motif_contrasts:
            info = CONTRAST_INFO[key]
            st.markdown(f"**{info['label']}**")
            st.markdown(f"&nbsp;&nbsp;&nbsp;{info['phrase']}")
            st.caption(f"&nbsp;&nbsp;&nbsp;{info['decode']}")
            st.markdown("")

    with st.expander("🕹️  Joystick contrasts", expanded=True):
        # ── Events Method contrasts ──
        st.markdown("##### 📅 Events Method")
        st.caption("Contrasts derived from discrete task phases (push / target hit / return to centre)")
        events_contrasts = [
            "task_gt_baseline", "right_vs_left", "left_vs_right",
            "return_gt_move", "active_effort_vs_passive",
            "push_right_vs_left", "goal_attained_feedback",
        ]
        seen = set()
        for key in events_contrasts:
            if key in CONTRAST_INFO and key not in seen:
                seen.add(key)
                info = CONTRAST_INFO[key]
                st.markdown(f"**{info['label']}**")
                st.markdown(f"&nbsp;&nbsp;&nbsp;{info['phrase']}")
                st.caption(f"&nbsp;&nbsp;&nbsp;{info['decode']}")
                st.markdown("")

        st.markdown("---")

        # ── Motions Method contrasts ──
        st.markdown("##### 📈 Motions Method")
        st.caption("Contrasts derived from continuous kinematic regressors (speed, displacement, velocity)")
        motions_contrasts = [
            "speed_gt_baseline", "displacement_gt_baseline",
            "direction_right_gt_left", "velocity_x_gt_baseline",
        ]
        for key in motions_contrasts:
            if key in CONTRAST_INFO:
                info = CONTRAST_INFO[key]
                st.markdown(f"**{info['label']}**")
                st.markdown(f"&nbsp;&nbsp;&nbsp;{info['phrase']}")
                st.caption(f"&nbsp;&nbsp;&nbsp;{info['decode']}")
                st.markdown("")
        st.caption("🏗 Motions Method results are being processed — maps will appear automatically when ready.")

    st.markdown("---")

    # ── SECTION 3: Statistical thresholds ─────────────────────────────────────
    st.header("📊 The Two Statistical Thresholds")

    th1, th2 = st.columns(2, gap="large")

    with th1:
        st.subheader("FDR — False Discovery Rate")
        st.markdown(
            "Controls the **expected proportion of false positives** across all "
            "voxels tested simultaneously. \n\n"
            "- More **sensitive** (liberal): shows the extended functional network\n"
            "- Typical setting: *q < 0.05* or *q < 0.001*\n"
            "- Good for: exploring which regions participate\n\n"
            "> _Use FDR to see the full picture._"
        )

    with th2:
        st.subheader("Bonferroni — Family-Wise Error Rate")
        st.markdown(
            "Divides the significance level by the number of tests — the most "
            "**conservative** multiple-comparison correction. \n\n"
            "- More **specific** (strict): only the absolute core survives\n"
            "- Typical setting: *α < 0.05* or *α < 0.2* (for 7T high-SNR)\n"
            "- Good for: confirming the strongest activation epicentres\n\n"
            "> _Use Bonferroni to trust the peaks._"
        )

    st.info(
        "**How to read the dashboards:** Each contrast is shown side-by-side "
        "with FDR (left) and Bonferroni (right). Regions that survive both are "
        "the most reliable activations.",
        icon="💡",
    )

    st.markdown("---")

    # ── SECTION 4: Brain cuts / ROIs ──────────────────────────────────────────
    st.header("📍 Brain Views — What Each 'Cut' Shows")
    st.markdown(
        "In each dashboard you can select different **anatomical views** (brain slices "
        "centred on specific regions of interest). Here is what each one represents:"
    )

    roi_cols = st.columns(2)
    roi_items = list(ROI_INFO.items())
    for i, (key, (label, desc)) in enumerate(roi_items):
        with roi_cols[i % 2]:
            st.markdown(f"**{label}**")
            st.caption(desc)
            st.markdown("")

    st.markdown("---")

    # ── SECTION 5: How to use ─────────────────────────────────────────────────
    st.header("🚀 How to Use the Dashboards")
    st.markdown(
        "1. **Pick a task** using the left sidebar (Motif4Limbs or Joystick)\n"
        "2. **Select a subject** from the dropdown\n"
        "3. **Select the GLM method** (behavioral / sequence)\n"
        "4. **Select a contrast** — a short interpretation is shown automatically\n"
        "5. **Choose a brain view** to zoom into a specific region\n"
        "6. Switch between the **Total Summary** tab (combined runs) and "
        "the **Run-by-Run** tab (quality check per acquisition)"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SHARED DASHBOARD LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
else:
    is_motif = "Motif" in page

    task_dirs = MOTIF_DIRS if is_motif else JOYSTICK_DIRS
    task_label = "🦵 Motif4Limbs" if is_motif else "🕹️ Joystick"

    # ── Sidebar: Subject ───────────────────────────────────────────────────────
    with st.sidebar:
        subjects = get_subjects(task_dirs)
        if not subjects:
            st.error("No subjects found.")
            st.stop()

        selected_sub_label = st.selectbox("👤 Subject", list(subjects.keys()))
        sub_path = subjects[selected_sub_label]

        # ── Sidebar: Method ────────────────────────────────────────────────────
        methods = [d.name for d in sorted(sub_path.iterdir()) if d.is_dir()]
        if not methods:
            st.error("No analysis methods found for this subject.")
            st.stop()
        selected_method = st.selectbox(
            "📐 Method",
            methods,
            format_func=method_display,
        )
        method_path = sub_path / selected_method

        # ── Sidebar: Contrast ──────────────────────────────────────────────────
        contrasts = [
            d.name for d in sorted(method_path.iterdir())
            if d.is_dir() and d.name not in EXCLUDED_CONTRASTS
        ]
        if not contrasts:
            st.error("No contrasts found.")
            st.stop()

        contrast_display = {
            c: CONTRAST_INFO.get(c, {}).get("label", c.replace("_", " ").title())
            for c in contrasts
        }
        selected_contrast = st.selectbox(
            "🎯 Contrast",
            contrasts,
            format_func=lambda c: contrast_display[c],
        )

    contrast_path = method_path / selected_contrast
    combined_dir   = contrast_path / "combined_total"

    # ── Header ─────────────────────────────────────────────────────────────────
    st.title(f"📊 {task_label} Dashboard")
    st.caption(
        f"Subject: **{selected_sub_label}** &nbsp;|&nbsp; "
        f"Method: **{method_display(selected_method)}** &nbsp;|&nbsp; "
        f"Contrast: **{contrast_display[selected_contrast]}**"
    )
    meth_desc = method_description(selected_method)
    if meth_desc:
        st.info(meth_desc, icon=METHOD_INFO.get(
            next((k for k in METHOD_INFO if k in selected_method.lower()), ""), {}
        ).get("icon", "ℹ️"))

    # ── Contrast interpretation banner ─────────────────────────────────────────
    c_info = CONTRAST_INFO.get(selected_contrast)
    if c_info:
        with st.container(border=True):
            st.markdown(f"##### 🎯 {c_info['label']}")
            st.markdown(c_info["phrase"])
            st.markdown(c_info["decode"])
    else:
        st.info(f"Contrast: `{selected_contrast}`")

    st.markdown("---")

    # ── Statistical thresholds reminder ───────────────────────────────────────
    with st.expander("🔬 Statistical thresholds — quick reminder", expanded=False):
        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown("**FDR (Exploratory)**")
            st.caption("Sensitive — shows the extended network. Controls the false-discovery proportion.")
        with tc2:
            st.markdown("**Bonferroni (Strict)**")
            st.caption("Conservative — shows only the strongest epicentres. Divides α by number of voxels.")

    st.markdown("---")

    # ── Brain area selector ────────────────────────────────────────────────────
    views = get_views(combined_dir) if combined_dir.exists() else []

    if not views:
        st.warning("⏳ No brain maps are available yet for this selection.")
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
        lbl = roi_label(selected_view)
        dsc = roi_description(selected_view)
        st.markdown(f"**{lbl}**")
        st.markdown(dsc)

    st.markdown("---")

    # ── Tabs: Total summary vs Run-by-run ──────────────────────────────────────
    tab_total, tab_runs = st.tabs(["🎯 Total Summary Map", "🔎 Run-by-Run Consistency"])

    # ── TAB 1: Total summary ───────────────────────────────────────────────────
    with tab_total:
        fdr_img  = find_img(combined_dir, "fdr",  selected_view)
        bonf_img = find_img(combined_dir, "bonf", selected_view)

        img_col1, img_col2 = st.columns(2, gap="medium")
        with img_col1:
            st.markdown("#### FDR — Exploratory")
            show_image_or_missing(fdr_img, "FDR-corrected")
        with img_col2:
            st.markdown("#### Bonferroni — Strict")
            show_image_or_missing(bonf_img, "Bonferroni-corrected")

    # ── TAB 2: Run-by-run ──────────────────────────────────────────────────────
    with tab_runs:
        st.markdown(
            "Individual run overviews let you check **run-to-run consistency** "
            "and spot potential motion artefacts or data quality issues."
        )

        run_dirs = sorted(
            [d for d in contrast_path.iterdir() if d.is_dir() and "run" in d.name]
        )

        if not run_dirs:
            st.info("No individual run folders found for this contrast.")
        else:
            run_cols = st.columns(min(len(run_dirs), 3), gap="medium")
            for i, run_p in enumerate(run_dirs):
                run_label = run_p.name
                # Try to find the selected view first, fall back to overview
                run_img = find_img(run_p, selected_view) or find_img(run_p, "overview")
                with run_cols[i % len(run_cols)]:
                    st.markdown(f"**{run_label}**")
                    show_image_or_missing(run_img, run_label)
