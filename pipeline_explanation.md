# Pipeline Explanation — 7T fMRI Motor Stroke Analysis

This document explains everything done in `optimize.ipynb`: what files are read,
how the brain model is built, what each contrast tests, and what each statistical
threshold means.

---

## 1. Your Input Files

### events.tsv — What happened and when

This file records every event in the task with millisecond timestamps.

**Real example from sub-06, run-1:**

| onset | duration | trial_type     |
|-------|----------|----------------|
| 0     | 10       | MR_trigger     |
| 19    | 3222     | center         |
| 19    | 3222     | center_reached |
| 3241  | 2850     | left           |
| 5910  | 155      | left_reached   |
| 6091  | 1438     | center         |

- `onset` and `duration` are in **milliseconds** (the code converts them to seconds by dividing by 1000).
- **trial_type** describes what happened:
  - `left` / `right` = the subject is pushing the joystick toward a target
  - `left_reached` / `right_reached` = the target was reached (goal attainment moment)
  - `center` / `center_reached` = returning the joystick to rest position
  - `MR_trigger`, `fixation`, `rest`, `Start`, `End` = scanner/protocol markers, **ignored** by the GLM

### motion.tsv — Where the joystick was at every moment

This file records the joystick position continuously (~13 ms sampling rate).

**Real example from sub-06, run-1:**

| time | gamepad_posx | gamepad_posy | screen_posx | screen_posy | reached |
|------|-------------|-------------|------------|------------|---------|
| 19   | 0.009       | -0.047      | 9          | -11        | 3       |
| 3241 | 0.009       | -0.047      | 9          | -11        | 0       |
| 4183 | 0.007       | -0.047      | 6          | -11        | 0       |
| 4247 | -0.083      | -0.047      | -80        | -11        | 0       |

- `gamepad_posx` / `gamepad_posy` = joystick deflection (range roughly -1 to +1)
- The code computes **Euclidean distance** from center: `dist = sqrt(posx² + posy²)`
- This distance becomes the **modulation** value in the parametric GLM

---

## 2. The Two Methods for the Joystick Task

### Method A — Events Method (`METHOD = "events"`)

**What it does:**
Each trial is modelled as a boxcar (on/off) with **constant amplitude = 1.0**.
The GLM asks: *"Is there more brain activation during this phase than at rest?"*

**How the events are built (`_events_joystick`):**
1. Load the events.tsv file
2. Remove scanner/protocol markers (MR_trigger, fixation, rest…)
3. Assign `modulation = 1.0` to every remaining trial
4. Return a table: `onset (s) | duration (s) | trial_type | modulation`

**Example of what the design matrix looks like:**

```
Time →
left        |████░░░░░░░████░░░░░░░████|   (1.0 during each left push)
left_reached|░░░░░░████░░░░░░████░░░░░░|   (1.0 at goal attainment)
right       |░░░░░░░░░░░░░░░░░░░░░░░░░|
center      |░░████████░░░████████░░░░░|
```

### Method B — Motion Method (`METHOD = "motion"`)

**What it does:**
Same timing as the events method, but the amplitude of each trial = **peak joystick
displacement** during that trial. The GLM asks: *"Is there more brain activation
when the subject moves MORE?"*

**How the events are built (`_events_joystick_motion`):****How the events are built (`_events_joystick_motion`):**
**How the events are built (`_events_joystick_motion`):**

1. Load both events.tsv and motion.tsv
2. For each push trial (left/right/center):
   - **Onset**: taken from events.tsv
   - **Duration**: time from `left` onset to `left_reached` onset (real movement time)
   - **Modulation**: `max(sqrt(posx² + posy²)) × 100` during that window
3. Return the same table format

**Example: a single trial**

```
events.tsv shows:
  onset=3241ms  trial_type=left
  onset=5910ms  trial_type=left_reached
  → duration = (5910 - 3241) / 1000 = 2.669 s

motion.tsv during that window:
  dist values: 0.009, 0.083, 0.144, 0.312, 0.498, 0.601 ...
  → peak_dist = 0.601
  → modulation = 0.601 × 100 = 60.1

Result row: onset=3.241s, duration=2.669s, trial_type=left, modulation=60.1
```

This means a trial where the subject barely moved (modulation ≈ 5) barely
contributes to the model, while a trial where they pushed hard (modulation ≈ 80)
contributes strongly. The brain map then shows **which voxels track effort**.

---

## 3. The GLM — How the Brain Model is Built

For each run:
1. **Frame times** are computed: `[0, TR, 2*TR, ..., (n_scans-1)*TR]`
2. The events table is convolved with a **Glover HRF** (haemodynamic response
   function) — this turns the boxcar events into the slow BOLD shape the scanner
   actually sees
3. **6 motion confound regressors** are added (translations X/Y/Z, rotations X/Y/Z)
   to remove variance from head movement
4. **Cosine drift regressors** (high-pass filter > 0.01 Hz) remove slow scanner drift
5. The model is fit with `noise_model='ar1'` to handle temporal autocorrelation
   in the fMRI signal

Each fitted run produces:
- `*_beta.nii.gz` — effect size (signal strength)
- `*_variance.nii.gz` — noise estimate
- `*_zmap.nii.gz` — Z-score map (beta / noise)

Runs are then **combined** using fixed-effects fusion (`compute_fixed_effects`),
which weights each run by the inverse of its variance.

---

## 4. All Contrasts Explained

### 4.1 Joystick — Events Method

The conditions (columns in the design matrix) are:
`left`, `left_reached`, `right`, `right_reached`, `center`

| Contrast | Formula | What it tests |
|----------|---------|---------------|
| `task_gt_baseline` | `0.2*(left + left_reached + right + right_reached + center)` | Any part of the task vs. rest. Shows the full motor network. |
| `push_right_vs_left` | `(right + right_reached) - (left + left_reached)` | Brain regions **preferring rightward** movement. The opposite of this map = leftward preference. Lateralization test. |
| `active_effort_vs_passive` | `0.5*(left + right) - center` | Active pushing toward target vs. passive return to center. Tests **voluntary motor control** vs. semi-passive return. |
| `goal_attained_feedback` | `0.5*(left_reached + right_reached) - 0.5*(left + right)` | The moment the target is reached vs. the effort phase. Tests **reward/feedback processing** (visual, SMA, striatum). |

### 4.2 Joystick — Motion Method

The conditions are the same (`left`, `right`, `center`) but each is **amplitude-modulated**.
The GLM estimates two betas per condition: one for the mean activation
(intercept) and one for the modulation slope (the parametric effect).

| Contrast | Formula | What it tests |
|----------|---------|---------------|
| `task_gt_baseline` | `left + right + center` | Mean activation across all movements. Same interpretation as the events method, but estimated from the parametric model. |
| `weighted_amplitude` | `left + right + center` | **Where does BOLD scale with effort?** (Uses the modulation regressor.) Voxels that respond more when the joystick is pushed further. Typically: M1, cerebellum, putamen. |
| `right_vs_left` | `right - left` | Directional preference, controlling for amplitude. |
| `push_vs_return` | `0.5*(left + right) - center` | Effortful outward push vs. passive return, controlling for amplitude. |

> **Why are `task_gt_baseline` and `weighted_amplitude` the same formula?**
> They use the same linear combination but different regressors: the first uses the
> *mean* regressor (constant modulation), the second uses the *parametric* regressor
> (modulation = peak distance). Nilearn picks the right one based on the design matrix
> column that was built with that modulation.

### 4.3 Motif4Limbs — Sequence Method

Conditions: `main_gauche` (left hand), `main_droite` (right hand),
`pied_gauche` (left foot), `pied_droit` (right foot).

| Contrast | Formula | What it tests |
|----------|---------|---------------|
| `task_gt_baseline` | `0.25*(main_gauche + main_droite + pied_gauche + pied_droit)` | Full motor task vs. rest. Shows the entire somatomotor network. |
| `hand_vs_foot` | `0.5*(main_gauche + main_droite) - 0.5*(pied_gauche + pied_droit)` | Hand areas (lateral M1) more active than foot areas (medial M1/SMA). |
| `foot_vs_hand` | `0.5*(pied_gauche + pied_droit) - 0.5*(main_gauche + main_droite)` | The reverse: foot areas more active than hand areas. |
| `right_vs_left` | `0.5*(main_droite + pied_droit) - 0.5*(main_gauche + pied_gauche)` | Right limbs vs. left limbs (both hand and foot). Tests hemispheric lateralization across the full body. |
| `right_vs_left_hand` | `main_droite - main_gauche` | Right hand vs. left hand only. Should activate contralateral M1 (left M1 for right hand). |
| `right_vs_left_foot` | `pied_droit - pied_gauche` | Right foot vs. left foot only. Should activate medial M1/SMA contralaterally. |

---

## 5. Statistical Thresholds

After computing the Z-map, two correction methods are applied:

### FDR (False Discovery Rate) — `ALPHA_FDR`

Controls the **proportion of false positives** among all significant voxels.
`q = 0.05` means: "at most 5% of the voxels I call significant are expected to
be noise."

- More **permissive** than Bonferroni — it adapts to the data
- Good for **exploratory** analyses and when you expect widespread activation
- Threshold is data-dependent: if many voxels survive, the threshold is lower

### Bonferroni — `ALPHA_BONF`

Controls the **family-wise error rate**: probability that *even one* false
positive exists in the whole image.
`α = 0.2` means: "20% chance of at least one false positive in the whole brain."

- More **conservative** than FDR
- With 1.35M voxels at 7T, Bonferroni requires Z > 5.13 (α=0.05) — very strict
- Using α=0.2 relaxes this to a more achievable threshold
- Good for confirming **strong, focal** effects

### Cluster threshold

After FDR/Bonferroni thresholding, only clusters with at least
`CLUSTER_THRESHOLD` voxels are kept.

- **Events method**: `CLUSTER_THRESHOLD = 10` — removes tiny isolated voxels
- **Motion method**: `CLUSTER_THRESHOLD = 0` — no cluster filter, because
  parametric amplitude effects are spatially smaller (a few voxels is real signal)

### Summary table (recommended settings)

| Task | Method | ALPHA_FDR | ALPHA_BONF | Cluster |
|------|--------|-----------|------------|---------|
| motif4limbs | sequence | 0.001 | 0.05 | 10 |
| joystick | events | 0.05 | 0.2 | 10 |
| joystick | motion | 0.05 | 0.2 | 0 |

---

## 6. Output Structure

Results are saved to `results_{TASK}_V01/sub-{SUB}/{METHOD}/{contrast}/`

For each contrast, per run:
```
run-1_dir-AP/
  sub-06_joystick_motion_task_gt_baseline_run-1_M1_hand_L.png
  task_gt_baseline_zmap.nii.gz
  task_gt_baseline_beta.nii.gz
  task_gt_baseline_variance.nii.gz
```

After combining all runs:
```
combined_total/
  sub-06_joystick_motion_task_gt_baseline_FDR_q0.05_overview.png
  sub-06_joystick_motion_task_gt_baseline_BONF_a0.2_M1_hand_L.png
  sub-06_joystick_motion_task_gt_baseline_BONF_a0.2_peak_-38_-22_56.png
  task_gt_baseline_TOTAL_zmap_uncorrected.nii.gz
  task_gt_baseline_TOTAL_zmap_fdr.nii.gz
  task_gt_baseline_TOTAL_zmap_bonf.nii.gz
```

The `peak_X_Y_Z` image is automatically centered on the strongest surviving
voxel (found by `find_xyz_cut_coords`).

---

## 7. How to Switch Between Methods

Change only **Section 1** of the notebook:

```python
# To run the events method:
TASK    = "joystick"
METHOD  = "events"
ALPHA_FDR         = 0.05
ALPHA_BONF        = 0.2
CLUSTER_THRESHOLD = 10

# To run the motion method:
TASK    = "joystick"
METHOD  = "motion"
ALPHA_FDR         = 0.05
ALPHA_BONF        = 0.2
CLUSTER_THRESHOLD = 0    # ← important: set to 0 for motion
```

Then re-run all cells and call `run_pipeline()`.
Results from each method go into separate folders (`events/` vs `motion/`)
so they never overwrite each other.
