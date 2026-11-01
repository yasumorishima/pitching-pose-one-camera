"""Pitching measures from joint positions. Pure numpy; one definition used for every source.

Joint dict keys (each an array of shape (T, D), D = 3 for 3D or 2 for image coordinates):
  shoulder_l/r, elbow_l/r, wrist_l/r, hip_l/r, knee_l/r, ankle_l/r.
`arm` is "r" or "l" (throwing side); the lead leg is the other side.

3D: `up` is a unit vector (Theia lab frame: +Z). Throw direction d = horizontal part of
(lead ankle - rear ankle) at foot contact. Lateral l = up x d.
2D (image, y down): vertical = image up (0, -1); the coach's condition, no camera correction.

Angles in degrees. Knee/elbow flexion: 0 = straight. Stride: ankle-ankle distance divided by
lead thigh + shank length (scale-free). Layback proxy and hip-shoulder separation are 3D only.
"""
import numpy as np


def _unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        return v / n


def _angle(a, b):
    """Angle between vectors (degrees), row-wise."""
    c = np.sum(_unit(a) * _unit(b), axis=-1)
    return np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))


def flexion(p_prox, p_mid, p_dist):
    """180 - interior angle at p_mid (0 = straight limb)."""
    return 180.0 - _angle(p_prox - p_mid, p_dist - p_mid)


def sides(arm):
    if arm not in ("r", "l"):
        raise ValueError("arm must be 'r' or 'l'")
    return arm, ("l" if arm == "r" else "r")


def stride(J, arm):
    _, lead = sides(arm)
    d = np.linalg.norm(J[f"ankle_{lead}"] - J[f"ankle_{arm}"], axis=-1)
    leg = (np.linalg.norm(J[f"hip_{lead}"] - J[f"knee_{lead}"], axis=-1)
           + np.linalg.norm(J[f"knee_{lead}"] - J[f"ankle_{lead}"], axis=-1))
    return d / leg


def knee_flexion(J, arm):
    _, lead = sides(arm)
    return flexion(J[f"hip_{lead}"], J[f"knee_{lead}"], J[f"ankle_{lead}"])


def elbow_flexion(J, arm):
    return flexion(J[f"shoulder_{arm}"], J[f"elbow_{arm}"], J[f"wrist_{arm}"])


def _mid(J, name):
    return (J[f"{name}_l"] + J[f"{name}_r"]) / 2


def throw_direction(J, arm, up, fc):
    """Horizontal unit vector from rear ankle to lead ankle at frame index fc (3D)."""
    _, lead = sides(arm)
    v = J[f"ankle_{lead}"][fc] - J[f"ankle_{arm}"][fc]
    v = v - np.dot(v, up) * up
    return v / np.linalg.norm(v)


def trunk_tilt(J, arm, up=None, d=None):
    """3D: signed forward tilt toward the target in the (d, up) plane.
    2D: unsigned angle of the trunk axis from image vertical."""
    axis = _mid(J, "shoulder") - _mid(J, "hip")
    if axis.shape[-1] == 2:
        return _angle(axis, np.array([0.0, -1.0]))
    return np.degrees(np.arctan2(axis @ d, axis @ up))


def arm_slot(J, arm, up=None, d=None):
    """Angle of shoulder->wrist above horizontal. 3D: in the frontal plane (perpendicular to d).
    2D: above the image horizontal."""
    u = J[f"wrist_{arm}"] - J[f"shoulder_{arm}"]
    if u.shape[-1] == 2:
        return np.degrees(np.arctan2(-u[..., 1], np.abs(u[..., 0])))
    lat = np.cross(up, d)
    return np.degrees(np.arctan2(u @ up, np.abs(u @ lat)))


def hip_shoulder_separation(J, up):
    """3D only. Signed angle (about up) from the hip line to the shoulder line, horizontal projection."""
    def h(v):
        return v - (v @ up)[..., None] * up
    hip = h(J["hip_r"] - J["hip_l"])
    sho = h(J["shoulder_r"] - J["shoulder_l"])
    s = np.cross(hip, sho) @ up
    c = np.sum(hip * sho, axis=-1)
    return np.degrees(np.arctan2(s, c))


def layback_proxy(J, arm, min_flexion=30.0):
    """3D only. Forearm and trunk axis projected on the plane perpendicular to the humerus; angle
    between them. NaN when the elbow is within `min_flexion` degrees of straight."""
    hum = _unit(J[f"elbow_{arm}"] - J[f"shoulder_{arm}"])
    fore = J[f"wrist_{arm}"] - J[f"elbow_{arm}"]
    trunk = _mid(J, "shoulder") - _mid(J, "hip")

    def p(v):
        return v - np.sum(v * hum, axis=-1, keepdims=True) * hum
    out = _angle(p(fore), p(trunk))
    out[elbow_flexion(J, arm) < min_flexion] = np.nan
    return out


def foot_contact(lead_ankle_height, release, tol=20.0):
    """First frame after the leg-lift peak (max height before release) at which the lead ankle is
    within `tol` (same units as height) of its planted height = min over [peak, release + 30]."""
    h = np.asarray(lead_ankle_height, dtype=float)
    peak = int(np.nanargmax(h[:release]))
    planted = np.nanmin(h[peak:release + 31])
    idx = np.flatnonzero(h[peak:release + 1] <= planted + tol)
    if len(idx) == 0:
        raise ValueError("no foot contact before release")
    return peak + int(idx[0])
