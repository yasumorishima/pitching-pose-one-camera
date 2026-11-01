"""Step-1 checks on the downloaded inputs. Reads only metadata (frame counts, sizes, rates, labels);
no pose or Theia3D values are read here, so nothing is compared with a reference.

Gates (each raises SystemExit when broken):
- every video decodes to the same number of frames (plan gate d);
- the C3D carries rotations of shape (4, 4, n_segments, T) with the 19 Theia segments the plan uses.
"""
import argparse
import json
from pathlib import Path

NEEDED_SEGMENTS = [
    "l_uarm_4X4", "r_uarm_4X4", "l_larm_4X4", "r_larm_4X4", "l_hand_4X4", "r_hand_4X4",
    "l_thigh_4X4", "r_thigh_4X4", "l_shank_4X4", "r_shank_4X4", "l_foot_4X4", "r_foot_4X4",
    "pelvis_4X4", "torso_4X4",
]


def gate_equal_counts(counts):
    """counts: {camera: decoded frame count}. All must be equal and positive."""
    vals = set(counts.values())
    if len(vals) != 1 or min(vals) <= 0:
        raise SystemExit(f"gate d failed: decoded frame counts differ or are empty: {counts}")
    return vals.pop()


def gate_segments(labels, shape):
    missing = [s for s in NEEDED_SEGMENTS if s not in labels]
    if missing:
        raise SystemExit(f"C3D is missing segments: {missing}")
    if len(shape) != 4 or shape[0] != 4 or shape[1] != 4 or shape[2] != len(labels):
        raise SystemExit(f"C3D rotations have an unexpected shape: {shape}")


def decode_count(path):
    import cv2
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"cannot open {path}")
    meta = {
        "fps_header": cap.get(cv2.CAP_PROP_FPS),
        "frames_header": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }
    n = 0
    while cap.grab():
        n += 1
    cap.release()
    meta["frames_decoded"] = n
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="work")
    ap.add_argument("--out", default="inputs/input_check.json")
    a = ap.parse_args()
    work = Path(a.work)
    videos = {}
    for p in sorted((work / "videos").glob("cam*.mp4")):
        videos[p.stem] = decode_count(p)
    if len(videos) != 8:
        raise SystemExit(f"expected 8 videos, found {sorted(videos)}")
    n = gate_equal_counts({k: v["frames_decoded"] for k, v in videos.items()})

    import ezc3d
    c = ezc3d.c3d(str(work / "theia.c3d"))
    rot = c["data"]["rotations"]
    labels = list(c["parameters"]["ROTATION"]["LABELS"]["value"])
    rate = float(c["parameters"]["ROTATION"]["RATE"]["value"][0])
    gate_segments(labels, rot.shape)
    out = {
        "videos": videos,
        "video_frames": n,
        "c3d": {"rotation_shape": list(rot.shape), "rotation_rate": rate, "segments": labels,
                "point_rate": float(c["header"]["points"]["frame_rate"]),
                "first_frame": int(c["header"]["points"]["first_frame"])},
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"video_frames": n, "c3d_shape": list(rot.shape), "rate": rate}))


if __name__ == "__main__":
    main()
