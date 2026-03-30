# Design Matrices & Contrasts — 7T Motor Stroke Study

This document explains how each design matrix is built and what each contrast means,
so you can decide what you want to see in the brain maps.

---

## How a Design Matrix Works (general)

A design matrix has **one column per regressor** and **one row per TR** (volume acquired).
The GLM finds the weight of each column that best explains the BOLD signal at every voxel.
A **contrast** is a linear combination of those weights — it asks:
*"Is the weight for condition A significantly larger than for condition B?"*

Every design matrix here shares the same **nuisance regressors** added automatically:
- **6 motion parameters** (trans_x/y/z, rot_x/y/z) from fMRIPrep confounds
- **Cosine drift regressors** (high-pass filter, cut-off 0.01 Hz)
- **Constant** (intercept)

The condition regressors are all convolved with a **Glover HRF** before entering the model.

---

## Task 1 — Motif4Limbs

### What was the task?
The subject saw a cue indicating a limb, then performed a brief movement:
- `main_droite` — right hand
- `main_gauche` — left hand
- `pied_droit` — right foot
- `pied_gauche` — left foot

There are **2 runs** per subject.

---

### Method A — `sequence`

**How the design matrix is built:**
Events are reconstructed from the **stimulus sequence CSV** using fixed timing:

```
onset of trial n = cumulative time using:
  BLANK_S = 1.0 s  (pre-stimulus blank)
  STIM_S  = 2.2 s  (stimulus duration)
  PAUSE_S = 4.8 s  (between blocks)
```

This gives 4 HRF-convolved regressors, one per limb.
Each trial has `modulation = 1.0` (constant amplitude).

**When to use it:** When you trust the timing from the stimulus delivery log
and do not have key-press recordings.

---

### Method B — `behavioral`

**How the design matrix is built:**
Events are extracted from the **raw key-press log CSV**.

- *Old format (sub-01 → 05):* the onset is taken from the **key code** event
  (`key:49` = right foot, `key:50` = left foot, `key:98` = right hand, `key:121` = left hand).
  The logged time is when the **subject pressed the button**, not when the stimulus appeared.
- *New format (sub-06 → 07):* the log records stimulus names directly
  (`pied_droit`, `pied_gauche`, `main_droite`, `main_gauche`).

In both cases each event gets `duration = 0.5 s` and `modulation = 1.0`.

**When to use it:** When you want onset times anchored to the subject's actual response
rather than the programmed stimulus timing (captures reaction time variability).

---

### Contrasts — Motif4Limbs (both methods)

| Contrast | Formula | What you will see |
|---|---|---|
| `task_gt_baseline` | `0.25 × (all 4 limbs)` | The full motor network active during the task vs rest: M1, SMA, cerebellum, thalamus |
| `hand_vs_foot` | `0.5×(hand_L + hand_R) − 0.5×(foot_L + foot_R)` | Hand area (lateral M1, ~knuckle level) **more** than foot area (medial M1/SMA) |
| `foot_vs_hand` | `0.5×(foot_L + foot_R) − 0.5×(hand_L + hand_R)` | Foot/leg area (medial M1, SMA) **more** than hand area |
| `right_vs_left` | `0.5×(hand_R + foot_R) − 0.5×(hand_L + foot_L)` | **Contralateral** dominance: right movements → left hemisphere activation |
| `right_vs_left_hand` | `main_droite − main_gauche` | Right-hand area (left M1 lateral) vs left-hand area (right M1 lateral) |
| `right_vs_left_foot` | `pied_droit − pied_gauche` | Right-foot area (left medial M1) vs left-foot area (right medial M1) |

**Key anatomical landmarks to check:**
- **M1 hand area:** ~40 mm lateral, ~25 mm posterior, ~55 mm superior (MNI)
- **M1 foot area:** medial wall, ~30 mm posterior, ~70 mm superior (MNI)
- **SMA:** midline, ~5 mm anterior, ~65 mm superior (MNI)

---

## Task 2 — Joystick

### What was the task?
The subject moved a joystick to reach a target on screen.
Three directions: `left`, `right`, `center` (return to center).
The paradigm also records when the target was **reached** (`left_reached`, `right_reached`, `center_reached`).

There are **2 runs** per subject.

---

### Method A — `events`

**How the design matrix is built:**
Events come from the **processed `events.tsv`** file (generated from the `.xpe` log).

There are **6 conditions**, each with `modulation = 1.0`:

| Condition | What it represents |
|---|---|
| `left` | Joystick being pushed toward left target (active effort) |
| `left_reached` | Moment the left target was reached (success feedback) |
| `right` | Joystick being pushed toward right target |
| `right_reached` | Moment the right target was reached |
| `center` | Joystick being returned to center |
| `center_reached` | Moment the center position was reached |

Each condition gets its own HRF-convolved regressor.
All modulations are equal (1.0) — the GLM does **not** distinguish between small
and large movements; it only distinguishes between phases.

**When to use it:** When you want to know **where** in the brain each phase
of the movement is represented, regardless of how hard the subject moved.

---

### Method B — `motion` (parametric)

**How the design matrix is built:**
This is a **parametric GLM** — the same 3 directional conditions (`left`, `right`, `center`),
but now the `modulation` of each trial varies with **how much the subject actually moved the joystick**.

Concretely, for each trial:
1. Find the trial onset and duration (onset → time of `*_reached` event)
2. Extract the joystick X/Y position timeseries during that window from the `motion.tsv`
3. Compute the **Euclidean distance** from centre: `dist = sqrt(x² + y²)` at every timestep
4. Take the **peak distance** during that trial as the modulation value (×100 for numerical scaling)

```
modulation = max( sqrt(gamepad_posx² + gamepad_posy²) ) × 100
             during the window [onset, onset + duration]
```

So a trial where the subject made a large, confident movement gets a **high modulation**,
and a trial with a small or hesitant movement gets a **low modulation**.

The HRF-convolved regressor is then `modulation × HRF` — it has a bigger "bump"
for trials where the subject moved more.

**There are only 3 regressors** (no `*_reached` conditions, because we only
parametrize the movement execution phase, not the target-attainment feedback).

**When to use it:** When you want to know **where BOLD amplitude scales with
movement amplitude** — i.e., which areas are more active the harder the subject pushed.
This is sensitive to motor force/effort encoding rather than simple task engagement.

---

### Contrasts — Joystick / Events method

| Contrast | Formula | What you will see |
|---|---|---|
| `task_gt_baseline` | `left + left_reached + right + right_reached + center + center_reached` | Full joystick motor network: M1, SMA, cerebellum, visual areas (cursor tracking) |
| `push_right_vs_left` | `(right + right_reached) − (left + left_reached)` | Lateralization: right pushes → left hemisphere; left pushes → right hemisphere |
| `active_effort_vs_passive` | `0.5×(left + right) − 0.5×(center + center_reached)` | Directed effort (toward target) vs passive return; isolates goal-directed motor drive |
| `goal_attained_feedback` | `0.5×(left_reached + right_reached) − 0.5×(left + right)` | Brain response at the moment the target is reached; reward/completion signal |

---

### Contrasts — Joystick / Motion method

| Contrast | Formula | What you will see |
|---|---|---|
| `amplitude_modulation` | `left + right + center` | Where BOLD **scales with joystick displacement** across all directions — force/effort areas |
| `amplitude_right_vs_left` | `right − left` | Which areas encode **amplitude asymmetrically** for right vs left pushes |
| `amplitude_active_vs_passive` | `0.5×(left + right) − center` | Areas where BOLD scales with **directed** movement amplitude more than return amplitude |

> **Interpretation tip for motion method:** A significant voxel means "when the subject
> pushed harder, this voxel responded more strongly" — not just "this voxel was active
> during the task." This is closer to an encoding of motor effort or force output.

---

## Statistical Pipeline

For each contrast, the pipeline:

1. **Fits one GLM per run** → per-run z-score, beta, variance maps
2. **Fixed-effects fusion** across runs → combined z-score map
3. **Applies two thresholds:**
   - FDR correction (α = 0.001, cluster ≥ 10 voxels)
   - Bonferroni correction (α = 0.05, cluster ≥ 10 voxels)
4. **Saves PNG brain maps** at pre-defined ROI coordinates for QC

| Task | Method | Recommended threshold |
|---|---|---|
| motif4limbs | sequence or behavioral | FDR α=0.001, cluster≥10 |
| joystick | events | FDR α=0.05, cluster≥10 |
| joystick | motion | Bonferroni α=0.05, cluster=0 (no cluster req.) |

> The cluster threshold is set to 0 for the motion method because parametric effects
> are spatially smaller than activation effects — requiring a 10-voxel cluster would
> erase valid voxels.
