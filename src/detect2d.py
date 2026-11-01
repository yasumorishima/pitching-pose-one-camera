"""Step 2: 2D keypoints (COCO-17) on every camera with rtmlib (Apache-2.0 code).

Detector + pose model = rtmlib Body(mode="balanced"): YOLOX-m (Human-Art) + RTMPose-m body7 256x192.
The ONNX weights are downloaded at run time from download.openmmlab.com and never committed; they were
trained on research-only datasets. Their sha256 goes into results/kp2d/meta.json.

Person choice (frozen): in the first frame of the window take the largest box; in each later frame take
the box whose centre is nearest to the previous chosen centre. Number of boxes per frame is recorded.
No Theia3D value is read here.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

FIRST, LAST = 700, 1199  # video frames, inclusive; release is at 950 (OBP contributor)
CAMERAS = list(range(15, 23))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def choose(boxes, prev_centre):
    """boxes: (N, 4) x1 y1 x2 y2. Returns index of the chosen box."""
    boxes = np.asarray(boxes, dtype=float).reshape(-1, 4)
    if prev_centre is None:
        area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        return int(np.argmax(area))
    centre = (boxes[:, :2] + boxes[:, 2:]) / 2
    return int(np.argmin(np.linalg.norm(centre - prev_centre, axis=1)))


def run_camera(body, video, first, last):
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    idx = 0
    kps, scs, nbox, chosen = [], [], [], []
    prev = None
    while idx <= last:
        ok, img = cap.read()
        if not ok:
            raise SystemExit(f"{video}: ran out of frames at {idx}")
        if idx >= first:
            boxes = body.det_model(img)
            boxes = np.asarray(boxes, dtype=float).reshape(-1, 4)
            nbox.append(len(boxes))
            if len(boxes) == 0:
                kps.append(np.full((17, 2), np.nan)); scs.append(np.zeros(17)); chosen.append([np.nan] * 4)
            else:
                i = choose(boxes, prev)
                prev = (boxes[i, :2] + boxes[i, 2:]) / 2
                k, s = body.pose_model(img, bboxes=[boxes[i].tolist()])
                kps.append(np.asarray(k)[0]); scs.append(np.asarray(s)[0]); chosen.append(boxes[i].tolist())
        idx += 1
    cap.release()
    return np.array(kps), np.array(scs), np.array(nbox), np.array(chosen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="work")
    ap.add_argument("--out", default="results/kp2d")
    ap.add_argument("--first", type=int, default=FIRST)
    ap.add_argument("--last", type=int, default=LAST)
    ap.add_argument("--cameras", default=",".join(map(str, CAMERAS)))
    a = ap.parse_args()
    from rtmlib import Body
    body = Body(mode="balanced", backend="onnxruntime", device="cpu")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    meta = {"first_frame": a.first, "last_frame": a.last, "model": "rtmlib Body balanced", "cameras": {}}
    for c in map(int, a.cameras.split(",")):
        k, s, n, b = run_camera(body, Path(a.work) / "videos" / f"cam{c}.mp4", a.first, a.last)
        np.savez_compressed(out / f"cam{c}.npz", keypoints=k.astype(np.float32), scores=s.astype(np.float32),
                            n_boxes=n.astype(np.int16), box=b.astype(np.float32),
                            frames=np.arange(a.first, a.last + 1, dtype=np.int32))
        meta["cameras"][f"cam{c}"] = {"frames": int(len(k)), "no_box": int((n == 0).sum()),
                                      "multi_box": int((n > 1).sum()), "median_score": float(np.nanmedian(s))}
        print(c, meta["cameras"][f"cam{c}"], flush=True)
    onnx = sorted(Path.home().glob(".cache/**/*.onnx"))
    meta["weights"] = {p.name: sha256(p) for p in onnx}
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    main()
