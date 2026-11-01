"""Draw the detected 2D skeleton and the chosen box on chosen frames (visual check, plan: "look at it").

usage: python tools/overlay.py <camera> <frame,frame,...> [--work work] [--out overlays]
Needs work/videos/cam<camera>.mp4 (src/fetch.py) and results/kp2d/cam<camera>.npz (src/detect2d.py).
Frame numbers are decoder indices (the burned-in counter in the video reads index + 1).
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

EDGES = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (11, 12), (5, 11), (6, 12), (11, 13), (13, 15), (12, 14), (14, 16)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("camera")
    ap.add_argument("frames")
    ap.add_argument("--work", default="work")
    ap.add_argument("--out", default="overlays")
    a = ap.parse_args()
    d = np.load(f"results/kp2d/cam{a.camera}.npz")
    cap = cv2.VideoCapture(str(Path(a.work) / "videos" / f"cam{a.camera}.mp4"))
    Path(a.out).mkdir(parents=True, exist_ok=True)
    for f in map(int, a.frames.split(",")):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, img = cap.read()
        if not ok:
            raise SystemExit(f"frame {f} not readable")
        i = f - int(d["frames"][0])
        k, b = d["keypoints"][i], d["box"][i]
        cv2.rectangle(img, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 255, 255), 2)
        for p, q in EDGES:
            cv2.line(img, tuple(map(int, k[p])), tuple(map(int, k[q])), (0, 255, 0), 2)
        for j in range(17):  # odd COCO index = left side (red), even = right side (blue)
            cv2.circle(img, tuple(map(int, k[j])), 4, (0, 0, 255) if j % 2 else (255, 0, 0), -1)
        cv2.putText(img, f"cam{a.camera} index {f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.imwrite(str(Path(a.out) / f"cam{a.camera}_{f}.jpg"), img)
    print("ok")


if __name__ == "__main__":
    main()
