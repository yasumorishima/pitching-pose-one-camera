# PLAN v2 — How much of a pitch's mechanics can one camera measure?

Status: draft, not run. Nothing has been compared with a reference yet.
v1 → v2: changes from an independent plan review, each checked against the OBP source files (see "Review log").

## Question
A team or a coach usually films with **one** camera. From one view, how close do standard pitching
measures come to a 3D reference, and which angle should you film from?

OpenBiomechanics (OBP) has published an **eight**-camera triangulation vs Theia3D (`computer_vision/splat`:
median 3.5 cm). OBP has not reported the single-camera case or pitching measures (literature not searched).

## Data (public, CC BY-NC-SA 4.0, Driveline OBP Computer Vision project)
- Trial `OBP_movement_BaseballThrow_001` (62.7 mph — not representative of game pitching): eight genlocked
  OptiTrack Prime Color videos, cameras 15–22, 360 fps, global shutter; Drive IDs from
  `computer_vision/4d_reconstruction/obp4d/fetch.py`; sha256 + bytes recorded.
- Theia3D C3D of the same trial: segment 4x4 transforms, read with ezc3d `data["rotations"]` (4×4×19×T, mm).
- Provisional intrinsics (`computer_vision/calibration/results/`). The Theia→rig alignment
  (`theia_alignment.json`) was fitted on COCO keypoints triangulated from **all 8 cameras**
  (`fit_code_available: false`), so it is used **only** for figures and camera geometry, never for scoring.
- Edgertronic 69.1 mph (4 cams) and iPhone 70.3 mph (240 fps, rolling shutter): no reference known →
  **development data** only. Step 1 lists the Drive `theia3d_output` folder; any other Theia-scored trial
  becomes extra development data, not scoring data.

## References
- **R1 = Theia3D**, measures computed in Theia's **native lab frame** (mm, +Z up), no alignment needed.
  Joints = segment origins: shoulder `*_uarm`, elbow `*_larm`, wrist `*_hand`, hip `*_thigh`, knee `*_shank`,
  ankle `*_foot`; plus `pelvis`, `torso`. Theia is markerless software, not ground truth. Theia's hip/shoulder
  are deep joint centres, COCO's are surface points.
- **R2₋c = our triangulation over the other 7 cameras** (RANSAC-DLT, same detector). "Single view vs R2₋c" =
  what is lost by geometry alone (shared detector bias cancels and is invisible there).
- **Floor** = R2 (all 8) vs R1 on each measure = definition + detector difference; reported first.
- Gate: R2 vs R1 median joint residual after similarity fit ≤ 5 cm (declared now). If it fails, stop; do not
  switch detectors to pass it.

## Arms (single view, camera c)
- **A2D**: angles in the image plane, image y-axis as vertical (the coach's condition). Compared with the
  **3D** R1 angle — the coach's real question ("is my 2D angle the true angle?"). A camera-corrected-vertical
  column is reported separately.
- **A3D**: monocular 2D→3D lifter on the same keypoints; angles from the lifted skeleton (scale-free).
- Optional third arm: MediaPipe BlazePose world landmarks (only if its model-card licence checks out).

## Measures (exact formulas in code + tests before scoring)
- Throw direction = rear-ankle→lead-ankle horizontal at foot contact.
- Stride = ankle–ankle distance ÷ (thigh + shank length).
- Lead-knee flexion, elbow flexion at foot contact; at release.
- Trunk forward tilt at release (in the plane of throw direction and vertical).
- Arm slot at release = shoulder→wrist angle above horizontal in the frontal plane.
- Hip–shoulder separation at foot contact: **A3D only** (transverse rotation is depth; not identifiable in A2D),
  horizontal projection with declared vertical.
- Layback proxy = forearm projected on the plane ⟂ humerus vs the trunk long axis on that plane; undefined when
  the elbow is within 30° of straight; **A3D only**. Theia's segment-based ER is reported alongside, not as target.
- Primary metric: **RMSE over the whole time series (video frames 800–1099)** per measure; event values secondary.

## Events and timing
- Release = video frame 950 (OBP contributor, `release_keypoints.csv`). Foot contact from Theia foot-segment
  height/velocity with thresholds frozen on the development throws' detected ankles.
- C3D offset: 4d pipeline +1, splat 0, offset study minimum +0.5 frame. Primary +1 (declared); report 0, +0.5
  (interpolated), +1, and events ±2 frames as sensitivity.
- One declared low-pass filter applied to every source (Theia smooths internally).

## Models (code licences checked: rtmlib, mmpose, MotionBERT, ViTPose, MediaPipe Apache-2.0; VideoPose3D
CC BY-NC; Ultralytics AGPL → not used)
- 2D: rtmlib + RTMPose-m (ONNX, CPU). 3D: MotionBERT-Lite (input resampled 360→50 fps, frozen) or RTMW3D-L.
- Weights are trained on research-only datasets (e.g. Human3.6M, AIC, Halpe): downloaded at run time, never
  committed, URL + sha256 recorded, README says "research-use weights".

## Freezing (n = 1 throw)
- Development uses only: Edgertronic and iPhone throws (no reference) and **2 dev cameras** (chosen now: 17, 21).
  The 6 others (15, 16, 18, 19, 20, 22) are scored once.
- Frozen as numbers before scoring: frame window, keypoint confidence threshold, filter, lifter fps/window,
  vertical and throw-direction definitions, event thresholds, offset, detector and lifter versions.
- Later changes → AMENDMENTS with reason; both results reported.

## Gates (each must be able to fail; planted defects verified to trip them)
- (a) Known-answer tests: synthetic skeleton with set angles under random rotation/scale → exact values; sign-flip
  and L/R-swap mutations must fail the tests.
- (b) R1 reprojected into the dev cameras (figure-only alignment): median px to detections ≤ declared threshold;
  +5 frames and L/R swap must exceed it.
- (c) Throwing arm (fastest wrist) = right/left as declared; a mirrored video flips it.
- (d) All 8 decoded videos have equal frame counts; a dropped-frame plant fails.
- (e) Lifter bone-length coefficient of variation ≤ threshold.
- Download sha256 match.

## What can be claimed
- One throw, one athlete, this rig (global shutter, calibrated intrinsics). Not "a phone", not population
  estimates; "best angle" is a case study. Frames are not independent.

## Licence and use
- Derived numbers/figures CC BY-NC-SA 4.0 with attribution (also data-derived constants inside code); code MIT.
- OBP defines commercial as including intent to profit "now or in the future", and forbids **any** use by
  employees/contractors of professional sports organizations → owner decides before publishing.

## Compute
- GitHub Actions CPU in a public repo. Raspberry Pi does not run inference.

## Review log
- v2 (2026-11-01): opus plan review. Verified myself: `theia_alignment.json` note + `fit_cameras` 15–22 +
  `fit_code_available: false`; splat `theia.py` segment map and `data["rotations"]`; LICENSE-DATA wording.
