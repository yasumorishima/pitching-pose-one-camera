"""Download the eight Prime Color videos of OBP_movement_BaseballThrow_001 (62.7 mph, 360 fps) and the
Theia3D C3D of the same trial, and record sha256 + bytes.

Drive IDs are copied from drivelineresearch/openbiomechanics
computer_vision/4d_reconstruction/obp4d/fetch.py at commit 21d089e38c9c9a7bd6dc7b29aecefcad63180bdd.
Data: The OpenBiomechanics Project (Driveline Baseball), CC BY-NC-SA 4.0 with an extra exclusion for
professional sports organizations (see README). Files are downloaded into work/ and never committed.
"""
import argparse
import hashlib
import json
from pathlib import Path

import gdown

OBP_COMMIT = "21d089e38c9c9a7bd6dc7b29aecefcad63180bdd"
VIDEOS = {
    15: "1u4-xPnQ3DCG_ocUZn-bTeieqCGm_W4Ka",
    16: "1WHEr9MXDQBv0nrEB1ahEfK6Dd-ObP2JL",
    17: "1b37Da2tNjqytG3-rRqkgawoeQJktXVsS",
    18: "1Err5ZMBa_M5npiO437LuLV4HFjE3b-_U",
    19: "1sa2wrKhEHXsEvM59PQdixIDVa_e5QEDI",
    20: "1xJDj0xlDX7FHfqPYkfBK3hiJnWhPWsLO",
    21: "1vwbuVrvkbo_wFLTEEYFm2mWRH3RshiWV",
    22: "1nE1uRyTCxTriwIQMYXC9DjXI5xKRpOuZ",
}
C3D = "1EgP-OVVpp5wv2pgorCV8Qs4-vcXZ_NjX"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(file_id, out, min_bytes):
    if not (out.exists() and out.stat().st_size > min_bytes):
        gdown.download(id=file_id, output=str(out), quiet=True, resume=True)
    if not (out.exists() and out.stat().st_size > min_bytes):
        raise SystemExit(f"download failed or too small: {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="work")
    ap.add_argument("--manifest", default="inputs/download_manifest.json")
    a = ap.parse_args()
    work = Path(a.work)
    (work / "videos").mkdir(parents=True, exist_ok=True)
    items = [(f"cam{c}.mp4", work / "videos" / f"cam{c}.mp4", fid, 10**6) for c, fid in VIDEOS.items()]
    items.append(("theia.c3d", work / "theia.c3d", C3D, 10**5))
    manifest = {"obp_commit": OBP_COMMIT, "files": {}}
    for name, path, fid, min_bytes in items:
        fetch(fid, path, min_bytes)
        manifest["files"][name] = {"drive_id": fid, "bytes": path.stat().st_size, "sha256": sha256(path)}
    old = Path(a.manifest)
    if old.exists():
        prev = json.loads(old.read_text())["files"]
        changed = [k for k in prev if k in manifest["files"] and prev[k]["sha256"] != manifest["files"][k]["sha256"]]
        if changed:
            raise SystemExit(f"source files changed since the recorded manifest: {changed}")
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v["bytes"] for k, v in manifest["files"].items()}))


if __name__ == "__main__":
    main()
