# 🧠 7T fMRI Motor Stroke – Design Matrix & GLM Comparison

## Project overview

This project aims to analyse the **7T motor task** performed by stroke patients and controls.

---

## Data organization

### Inputs

Three complementary sources of timing information are available in a the data folder:

1. **Experimental protocol**
   `data/seq/stim_sequence_run-*.csv`

   * Planned order of stimuli per run
   * Same for all subjects
   * No subject-specific timing

2. **Event files (BIDS-like)**
   `data/events/motif-stroke_sub-*_run-*_events.tsv`

   * Generated from log files
   * Contain block-level timing (stimulus + fixation)
   * Onsets are relative to scanner time (TTL)

3. **Behavioral logs**
   `data/log/motif-stroke_sub-*_run-*_*.csv`

   * Raw PsychoPy logs
   * Include actual key presses
   * Allow response-locked modeling

4. **Preprocessed fMRI data**
   `derivatives/fmriprep/`

   * 7T fMRI data processed with **fMRIPrep**
   * MNI space
   * Includes confounds and brain masks

---

## The three GLM models compared

### Method 1 — Event-based (block model)

**Source:** `events.tsv`

* Each motor condition is modeled as a **block** (~14.7 s)
* Fixation periods are implicit baseline
* Captures **sustained motor state**

📌 Best suited for:

* Motor localizers
* Robust M1/SMA activation
* Low sensitivity to reaction-time variability

---

### Method 2 — Response-locked (event model)

**Source:** behavioral log files

* Each event corresponds to the **actual key press**
* Fixed short duration (e.g. 0.2 s)
* Captures **motor execution timing**

📌 Best suited for:

* Studying execution vs intention
* Patient variability
* Timing-sensitive effects

⚠️ More sensitive to noise and missing responses

---

### Method 3 — Protocol-based (stimulus model)

**Source:** `stim_sequence_run-*.csv` + protocol constants

* Timing reconstructed from:

  * known block duration
  * number of stimuli per block
  * inter-stimulus intervals
* Same structure for all subjects
* No behavioral variability

📌 Best suited for:

* Clean experimental control
* Model comparison
* Debugging / sanity checks

---

## Design matrix construction

All models use **Nilearn’s `make_first_level_design_matrix`** with:

* HRF: `glover`
* Drift: cosine basis (high-pass = 0.01 Hz)
* Motion regressors (optional)
* No physiological regressors (CSF / WM / GS excluded)

Each design matrix is saved per run for inspection:

```
results_glm_3methods/
└── sub-XX/run-YY/dir-*/method_*/
    ├── design_matrix.csv
    └── design_top_correlations.csv
```

---

## GLM outputs (per run)

For each contrast, the following maps are saved:

* **Effect size** (`*_effect.nii.gz`)
  → magnitude of activation

* **Effect variance** (`*_variance.nii.gz`)
  → uncertainty of the estimate

* **Z-map** (`*_z.nii.gz`)
  → effect / uncertainty

This allows disentangling:

> *large effects vs significant effects*

---

## Contrasts of interest

```python
task_gt_baseline
hand_gt_foot
foot_gt_hand
left_gt_right
right_gt_left
```

These contrasts probe:

* motor vs baseline activation
* hand vs foot somatotopy
* lateralization

---

## Subject-level fixed effects

For each subject and each method:

* Run-level maps are combined using **fixed effects**
* Effect and variance maps are aggregated across runs
* A subject-level *t-like* map is computed for visualization

Outputs:

```
sub-XX/subject_fixed_effects/method_*/
├── <contrast>_effect_fixed.nii.gz
├── <contrast>_variance_fixed.nii.gz
├── <contrast>_t_fixed.nii.gz
└── plots/
```

---

## Visualization strategy

For each subject × contrast:

1. **Run-level z-maps**
   → QC: consistency across runs

2. **Subject-level effect map**
   → “Where is the motor effect strong?”

3. **Subject-level t-map (viz only)**
   → “Where is the effect reliable?”

Thresholds are used **only for visualization**, not inference.

---

## ROI sanity checks

To validate somatotopy, two canonical ROIs are used:

* **Left hand M1 (hand knob)**
* **Medial M1 (foot area)**

Mean values are extracted per ROI to check:

* sign consistency
* hand/foot dissociation
* run-to-run stability

This produces concise tables for discussion.

---

## Interpretation logic

* **R²** → model fit quality (how much variance is explained)
* **Effect maps** → magnitude of motor activation
* **Variance maps** → stability / noise
* **Z or t maps** → reliability of effects
* **ROI summaries** → neuroanatomical sanity check

No group-level inference is performed yet.

