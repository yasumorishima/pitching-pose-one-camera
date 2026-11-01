# CLAUDE.md — pitching-pose-one-camera

Working rules for Claude Code (cloud or local). This file is the source of truth for this project; the owner's
local notes are not visible to cloud sessions.

## Session protocol (cloud)
The owner starts a cloud session (environment 「クラウド許可1」, full network) with just 「続き」.
1. Read this file and `PLAN.md`, then continue from the first unfinished item in **Next tasks**.
2. Before ending, update **Next tasks** and add a dated line to **Progress log** in this file.
3. Cloud can push only its session branch: open a PR to `main` and merge it yourself (own repo). Use a merge
   commit (not squash) when the PR contains the freeze commit, so its hash stays in `main`'s history.
4. Write replies to the owner in Japanese (です/ます). Do not claim anything you did not run in this session;
   say where each number was measured (cloud / GitHub Actions).
5. No `gh` CLI in cloud (use the GitHub MCP tools); `workflow_dispatch` returns 403 from cloud, so the workflows
   here run on **push to main** of the files they watch (see `.github/workflows/`).

## Progress log
- 2026-11-01 (local + Raspberry Pi + GitHub Actions): repo created; PLAN v2 after an independent plan review
  (blocking point: `theia_alignment.json` was fitted on keypoints triangulated from all 8 cameras, so R1 is
  scored in Theia's own lab frame). Step 1 (`inputs.yml`): 8 videos × 1,406 frames, 1280×720, 360 fps; Theia3D
  C3D 19 segments × 1,406 frames at 360 Hz; sha256 in `inputs/download_manifest.json`. Step 2 (`detect2d.yml`,
  run 41281835535): rtmlib keypoints for frames 700–1199 on all 8 cameras, a person in every frame; camera 19
  also sees a seated person in the background in every frame and the rule picked the pitcher (looked at
  overlays of camera 19 index 700 and 950 and camera 17 index 950). `src/measures.py` + 24 known-answer tests;
  `tools/mutate_measures.sh` plants 10 formula defects, all caught.

## What this is
How much of a pitch's mechanics can **one** camera measure, and from which angle? Each of eight synchronized
360 fps cameras (Driveline OpenBiomechanics Computer Vision project, one 62.7 mph throw) is used alone and
compared with a 3D reference. Details, references (R1 = Theia3D, R2₋c = 7-camera triangulation), arms (A2D,
A3D) and measures are in `PLAN.md`.

## Non-negotiable discipline
1. **No comparison with R1 or R2 before the freeze.** Development uses only cameras 17 and 21 and, if found,
   the reference-free throws. Cameras 15, 16, 18, 19, 20, 22 are scored once, after the freeze.
2. **Freeze = a commit** that pins every number (frame window, keypoint confidence threshold, filter, lifter
   and its input fps/window, vertical and throw-direction definitions, event thresholds, C3D offset, model
   versions + weight sha256). Changes after it go to `AMENDMENTS.md` with the reason; report both results.
3. **Gates must be able to fail**: verify each new gate with a planted defect (see `tools/mutate_measures.sh`).
4. **Look at images before handing anything over** (`tools/overlay.py`); give numbers with every figure.
5. Licence: data CC BY-NC-SA 4.0 + **no use at all by employees/contractors of professional sports
   organizations**. Never commit videos, the C3D or model weights (weights come from research-only datasets).
   Numbers and figures derived from the data are CC BY-NC-SA 4.0; code MIT. Never write a team's or company's
   name in this repo.
6. One throw, one athlete: never write population claims or "phone" claims.

## Next tasks (in order)
1. **Open checks from step 2** (no reference needed):
   - The burned-in counter reads decoder index + 1 (shows 951 at index 950). Decide and write down which
     index the C3D offset (+1 in OBP `4d_reconstruction`, 0 in `splat`) refers to.
   - Cameras 17 and 19 look out of step at index 950 by eye (ball at knee height vs shoulder height). Measure
     sync with the 8-camera triangulation reprojection error per camera and per frame shift (R2 is our own
     detector, not the reference, so this is allowed).
   - Throwing arm: decide by the fastest wrist (plan gate c). Near index 935 the left hand is farthest from the
     body in OBP `release_keypoints.csv` → possibly left-handed; do not assume.
2. **R2 / R2₋c**: RANSAC-DLT over the cameras with `computer_vision/calibration/results/intrinsics_summary.csv`
   (rows `optitrack_15..22`, zero distortion) and `optitrack_rig_provisional.json` (`camera_poses`, camera-19
   frame, X_i = R_i19 X_19 + t_i19, millimetres). Gate: R2 vs R1 median joint residual ≤ 5 cm — this compares
   with R1, so run it only as part of the frozen scoring.
3. **R1**: Theia joint centres from `data["rotations"]` (ezc3d, 4×4×19×T, mm): shoulder `*_uarm`, elbow
   `*_larm`, wrist `*_hand`, hip `*_thigh`, knee `*_shank`, ankle `*_foot`. Check +Z is up from the data
   (without reading any measure). Events: release = video index 950 (OBP contributor's statement only);
   foot contact = `measures.foot_contact` on the lead foot height.
4. **A3D lifter**: choose (MotionBERT-Lite or RTMW3D-L; check code + weight licences from primary sources;
   360 → ~50 fps input, frozen).
5. **Freeze**, then score once (all six cameras, both arms, offsets 0 / +0.5 / +1, events ±2 frames).
6. README results + a GIF; then update the owner's profile line (section 5) — the owner does that from local.

## How to run
- In cloud: `pip install gdown==5.2.0 opencv-python-headless==4.10.0.84 ezc3d==1.7.2 rtmlib==0.0.16
  onnxruntime==1.20.1 numpy pytest`, then `python src/fetch.py` (videos into `work/`, sha256 must match the
  manifest), `python -m pytest -q tests`, `bash tools/mutate_measures.sh`, `python src/detect2d.py --cameras 17`.
- On GitHub Actions: `inputs.yml` and `detect2d.yml` run on push to `main` of their own files; results are
  committed back by the bot (pull before pushing).
- Not available: the OBP-CV MEGA backup listing (`megatools ls` asks for a login), so other Theia-scored
  throws are still unknown.

## Data access and credits
Drive IDs: `src/fetch.py` (copied from OBP `computer_vision/4d_reconstruction/obp4d/fetch.py` at commit
21d089e3). Calibration: https://github.com/drivelineresearch/openbiomechanics (computer_vision/calibration).
Credit: The OpenBiomechanics Project, Driveline Baseball — CC BY-NC-SA 4.0 (see README).
