# pitching-pose-one-camera

**How much of a pitch's mechanics can one camera measure, and from which angle should you film?**

Status: **planning — no results yet.** The plan is in [`PLAN.md`](PLAN.md). Nothing has been compared with
the reference; numbers will appear here only after the pipeline is frozen and scored once.

## Idea in one paragraph
Driveline's OpenBiomechanics Computer Vision project filmed one throw with eight synchronized 360 fps
cameras and processed it with Theia3D. OpenBiomechanics already reports the eight-camera case. This repo
asks the question a coach or a team with **one** camera has: measure stride, knee and elbow flexion,
trunk tilt, arm slot (and, with a 3D lift, hip–shoulder separation and a layback proxy) from each camera
alone, and compare with the 3D reference. Six cameras are scored; two cameras and two other throws are
used only for development.

## Limits (read before using any number)
- One throw (62.7 mph) by one athlete on one rig. A case study, not population estimates.
- Theia3D is markerless software, not ground truth.
- Pose-model weights are trained on research-only datasets; they are downloaded at run time and never
  committed.

## Data, licence, attribution
- Data: [The OpenBiomechanics Project](https://www.openbiomechanics.org/) by Driveline Baseball
  ([GitHub](https://github.com/drivelineresearch/openbiomechanics)), licensed
  [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) with an additional exclusion:
  **any employee or contractor of a professional sports organization or financial analysis firm may not
  use the data for any purpose.** Raw videos are not stored here; the workflow downloads them.
- Numbers and figures derived from the data in this repo: CC BY-NC-SA 4.0. Code: MIT (`LICENSE`).
