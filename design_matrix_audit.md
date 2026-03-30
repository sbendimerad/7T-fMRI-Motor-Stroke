# Design Matrix Audit — Scientific Review
## Sub-07 | Motif4Limbs + Joystick

---

## POINT 1 — Sequence vs Behavioral: why they are the same for sub-07

### What the two methods are supposed to do

| Method | What it uses as "onset" |
|---|---|
| **Sequence** | Reconstructs onsets mathematically from the CSV file using fixed timing rules: `BLANK=1.0s + STIM=2.2s + PAUSE=4.8s between blocks` |
| **Behavioral** | Uses the **actual time** the computer logged each event in the task log file |

The **scientific goal** of the behavioral method is to capture **when the subject actually responded** (reaction time), not just when the stimulus appeared. This is important because brain activation tracks the subject's action, not the screen.

---

### What happens for sub-05 (old log format — key press captured)

The old log records both the stimulus presentation AND the key press separately:

```
event            time
pied_droit       onset = 1.027s   ← stimulus shown on screen
key:49:978       time  = 5.232s   ← subject pressed the pedal (RT=978ms embedded in event name)
```

So for sub-05:
- **Sequence onset** of trial 1 = 1.0s (calculated from fixed timing)
- **Behavioral onset** of trial 1 = 5.232s (= when the pedal was pressed)
- **Difference = 4.2s = the reaction time**

Real RT data from sub-05 run-1:
```
Mean RT = 835 ms  |  Std = 252 ms
```
This is **scientifically meaningful**: the brain activates when the subject moves their limb, not when the cue appears. Using reaction time–anchored onsets makes the model more biologically accurate.

---

### What happens for sub-07 (new log format — stimulus name, no key press)

The new log records the stimulus name at the moment it appears — but does **NOT** record a separate key press event:

```
event                    time
blank                    76768 ms
pied_droit               77778 ms   ← stimulus shown = this is what we use
right_pedal_onset:1048   78827 ms   ← pedal pressed 1048ms later — but our code ignores this!
blank                    79995 ms
```

Because our `_events_motif_behavioral` function looks for `pied_droit`, `main_gauche` etc. directly, it picks up the **stimulus onset**, not the key press. So:

| Trial | Sequence onset (s) | Behavioral onset (s) | Difference (ms) |
|---|---|---|---|
| 1 | 1.00 | 1.025 | 25 |
| 2 | 4.20 | 4.253 | 53 |
| 3 | 7.40 | 7.482 | 82 |
| 4 | 10.60 | 10.712 | 112 |
| 5 | 18.60 | 18.761 | 161 |

The difference grows because the sequence uses perfect fixed timing while the behavioral log has real computer-clock timing. But these are **tiny differences** (25–112 ms in the first 5 trials) relative to the TR of 1600ms. At the HRF resolution (~5s), these differences are completely invisible.

**Conclusion for sub-07:**
> The behavioral method captures the **stimulus onset**, not the **key press**. It is therefore mathematically nearly identical to the sequence method. The two design matrices will produce virtually the same results. You are **not capturing reaction time** for sub-07 with the behavioral method.

---

### What is missing and what you could do

The information needed to capture RT for sub-07 **IS in the log file** — it is encoded in the event names like `right_pedal_onset:1048` (1048ms = RT). The current code ignores these events. If you wanted to use true behavioral onsets for sub-07, you would need to extract the key press time from these events.

**Practical recommendation for sub-07:**
- Use the **sequence** method as your primary analysis (it is honest about what it uses)
- The behavioral method adds nothing new for sub-07
- For future subjects, ask whether the log format has changed again, and update the behavioral loader to extract the `right_pedal_onset:XXX` RT

---

## POINT 2 — Joystick / Motion: why `amplitude_active_vs_passive` may be weak

### What the contrast is supposed to test

```
amplitude_active_vs_passive = 0.5*(left + right) − center
```

The idea: when the subject pushes toward a target (left or right), this is **active goal-directed effort**. When they return to center, this is **passive return**. We expect the brain to work harder during active pushes, so the joystick displacement should be larger → higher modulation → stronger BOLD.

### What the data actually shows

The peak joystick displacement (×100) for sub-07 run-1:

| Condition | N trials | Mean displacement | Std |
|---|---|---|---|
| `left` | 30 | 59.6 | 5.3 |
| `right` | 30 | 55.7 | 8.1 |
| `center` | 61 | 61.5 | 11.4 |

**The center return movement has the same displacement as the directed pushes.**

### Physical explanation

Imagine the joystick target is placed at position X=60 units to the left:
- To push **left**: you move from 0 → 60 = displacement of **60 units**
- To return to **center**: you move from 60 → 0 = displacement of **60 units**

The distance is symmetric. The joystick task was designed to require the same physical effort in both directions, so the parametric modulation cannot separate active effort from passive return.

**This is not a bug in your code — it is a property of the task design.**

The contrast will be estimated with very small beta values (near zero), large uncertainty, and you are unlikely to find significant voxels. Do not over-interpret a null result for this contrast.

The contrasts `amplitude_modulation` (full task > baseline) and `amplitude_right_vs_left` (lateralization) remain **fully valid** because they do not rely on the active/passive distinction.

---

## POINT 3 — Joystick / Events: collinearity between `left` and `left_reached`

### What the HRF does to closely spaced events

The HRF (haemodynamic response function) is the shape of the BOLD signal after a neural event. It:
- **Rises** slowly over ~5 seconds after the event
- **Peaks** at ~5–6 seconds
- **Returns** to baseline over ~15–20 seconds

If two events happen within **~4 seconds of each other**, their HRFs overlap almost completely. The GLM cannot tell which event caused the BOLD signal — this is collinearity.

### What the actual timing looks like

For sub-07, the interval between `left` (push onset) and `left_reached` (target reached) is:

| Trial | left onset (s) | left_reached onset (s) | Interval |
|---|---|---|---|
| 1 | 24.08 | 25.79 | **1.71 s** |
| 2 | 28.89 | 29.96 | **1.07 s** |
| 3 | 33.70 | 35.44 | **1.75 s** |
| 4 | 43.32 | 44.65 | **1.33 s** |
| 5 | 48.13 | 49.19 | **1.06 s** |
| 6 | 52.94 | 53.93 | **0.99 s** |

**The subject reaches the target in ~1–2 seconds.** The HRF for `left` is still rising at the time `left_reached` occurs. After convolution, the two regressors look nearly identical.

This explains the high correlation in the design matrix:
- `left` ↔ `left_reached`: **r = 0.92** (run 1), **r = 0.83** (run 2)
- `right` ↔ `right_reached`: **r = 0.89** (run 1), **r = 0.90** (run 2)
- `center` ↔ `center_reached`: **r = 0.67** (run 1), **r = 0.88** (run 2)

### What this means for each contrast

| Contrast | Formula | Reliability | Why |
|---|---|---|---|
| `task_gt_baseline` | sum of all 6 conditions | ✅ **Reliable** | Sums correlated pairs — collinearity cancels out |
| `push_right_vs_left` | (right+right_reached) − (left+left_reached) | ✅ **Reliable** | Compares two pairs against each other — collinearity within pairs cancels |
| `goal_attained_feedback` | (left_reached+right_reached) − (left+right) | ❌ **Unreliable** | Tries to subtract two nearly identical regressors — beta estimates have huge variance |
| `active_effort_vs_passive` | (left+right) − (center+center_reached) | ⚠️ **Partially affected** | center ↔ center_reached correlation (0.67–0.88) contaminates this contrast |

### Intuitive explanation for `goal_attained_feedback`

Imagine you have two thermometers that always read almost the same temperature. If you subtract one from the other, you get a number near zero — but the tiny measurement errors dominate and the result is meaningless noise. That is exactly what happens to the GLM beta estimates for `left_reached − left`.

---

## Summary of Recommendations

### Motif4Limbs
| Issue | Severity | Action |
|---|---|---|
| Behavioral = Sequence for sub-07 | ⚠️ Medium | Use **sequence** as primary method for sub-07. Flag in your methods section that sub-07 lacks true RT data. |
| `right_pedal_onset:XXX` events ignored | ⚠️ Medium | Future: update behavioral loader to extract RT from these events for sub-06+ |
| Design matrix collinearity | ✅ None | r < 0.26 — excellent design, all contrasts reliable |

### Joystick / Motion method
| Issue | Severity | Action |
|---|---|---|
| `amplitude_active_vs_passive` likely null | ⚠️ Low | Report it, do not over-interpret null result. The task geometry makes it indistinguishable. |
| `amplitude_modulation` and `amplitude_right_vs_left` | ✅ Reliable | Use as main contrasts for this method |

### Joystick / Events method
| Issue | Severity | Action |
|---|---|---|
| `goal_attained_feedback` unreliable | ❌ High | **Do not interpret this contrast** — the collinearity (r=0.92) makes the estimates noise |
| `active_effort_vs_passive` partially affected | ⚠️ Medium | Interpret with caution, especially for center vs center_reached separation |
| `task_gt_baseline` and `push_right_vs_left` | ✅ Reliable | These are your main usable contrasts for the events method |

### Overall recommendation
> For the joystick task, **the motion method is your primary scientific tool** for understanding motor encoding. The events method is valid only for `task_gt_baseline` and lateralization (`push_right_vs_left`). For the motif4limbs task, both methods are well-conditioned — use sequence as primary for sub-07 specifically.
