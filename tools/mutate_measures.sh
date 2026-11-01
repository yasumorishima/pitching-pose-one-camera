#!/bin/bash
# Plant known defects in src/measures.py one at a time; each must make tests/test_measures.py fail.
# usage: bash tools/mutate_measures.sh   (from anywhere; needs python with numpy + pytest)
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
bad=0
run(){ # name, sed expression
  rm -rf "$TMP/r"; cp -r "$REPO" "$TMP/r"; sed -i "$2" "$TMP/r/src/measures.py"
  if cmp -s "$REPO/src/measures.py" "$TMP/r/src/measures.py"; then echo "$1: NOT APPLIED"; bad=1; return; fi
  if (cd "$TMP/r" && python -m pytest -q -x tests/test_measures.py >/dev/null 2>&1); then echo "$1: SURVIVED"; bad=1; else echo "$1: caught"; fi
}
run tilt_sign 's/np.arctan2(axis @ d, axis @ up)/np.arctan2(-(axis @ d), axis @ up)/'
run sep_sign 's/s = np.cross(hip, sho) @ up/s = np.cross(sho, hip) @ up/'
run slot_plane 's/np.abs(u @ lat)/np.abs(u @ d)/'
run layback_gate 's/< min_flexion\] = np.nan/> min_flexion] = np.nan/'
run knee_side 's/return flexion(J\[f"hip_{lead}"\], J\[f"knee_{lead}"\], J\[f"ankle_{lead}"\])/return flexion(J[f"hip_{arm}"], J[f"knee_{arm}"], J[f"ankle_{arm}"])/'
run stride_leg 's/+ np.linalg.norm(J\[f"knee_{lead}"\] - J\[f"ankle_{lead}"\], axis=-1))/)/'
run flexion_def 's/return 180.0 - _angle(p_prox - p_mid, p_dist - p_mid)/return _angle(p_prox - p_mid, p_dist - p_mid)/'
run fc_tol 's/<= planted + tol)/<= planted + 10 * tol)/'
run tilt2d 's/return _angle(axis, np.array(\[0.0, -1.0\]))/return _angle(axis, np.array([1.0, 0.0]))/'
run d_horizontal 's/v = v - np.dot(v, up) \* up/v = v/'
exit $bad
