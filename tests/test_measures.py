"""Known-answer tests: a synthetic skeleton with set angles, rotated/scaled/translated at random,
must give the set values (plan gate a)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import measures as M  # noqa: E402

TRUTH = dict(tilt=25.0, sep=-30.0, knee=40.0, stride=0.85, layback=70.0)


def rz(a):
    a = np.radians(a); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def canonical():
    """Right-handed thrower, up = +z, throw direction = +x, lateral = up x d = +y."""
    t = np.radians(TRUTH["tilt"])
    hip_mid = np.array([0.0, 0.0, 1.0])
    e = np.array([0.0, -1.0, 0.0])            # left -> right points to -y
    J = {}
    J["hip_l"] = hip_mid - 0.15 * e
    J["hip_r"] = hip_mid + 0.15 * e
    sho_mid = hip_mid + 0.5 * np.array([np.sin(t), 0, np.cos(t)])
    es = rz(TRUTH["sep"]) @ e
    J["shoulder_l"] = sho_mid - 0.2 * es
    J["shoulder_r"] = sho_mid + 0.2 * es
    # lead (left) leg in the x-z plane with knee flexion TRUTH["knee"]
    u1 = np.array([0.3, 0, -1.0]); u1 /= np.linalg.norm(u1)
    k = np.radians(TRUTH["knee"])
    u2 = np.array([[np.cos(k), 0, -np.sin(k)], [0, 1, 0], [np.sin(k), 0, np.cos(k)]]) @ u1
    J["knee_l"] = J["hip_l"] + 0.45 * u1
    J["ankle_l"] = J["knee_l"] + 0.42 * u2
    J["ankle_r"] = J["ankle_l"] - np.array([TRUTH["stride"] * 0.87, 0, 0]) + np.array([0, 0, 0.03])
    J["knee_r"] = J["ankle_r"] + np.array([0, 0, 0.42])
    # stride uses the horizontal-plus-vertical ankle distance; keep the expected value exact:
    # ankle_r was offset by (0, 0, 0.03) -> expected stride computed below
    # throwing (right) arm: humerus lateral (-y), forearm perpendicular, at TRUTH["layback"] from trunk axis
    hum = np.array([0, -1.0, 0])
    trunk = np.array([np.sin(t), 0, np.cos(t)])
    b = np.radians(TRUTH["layback"])
    fore = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]]) @ trunk
    J["elbow_r"] = J["shoulder_r"] + 0.3 * hum
    J["wrist_r"] = J["elbow_r"] + 0.27 * fore
    J["elbow_l"] = J["shoulder_l"] + np.array([0, 0.3, -0.05])
    J["wrist_l"] = J["elbow_l"] + np.array([0.1, 0, -0.2])
    J["knee_r"] = J["hip_r"] + np.array([0, 0, -0.45]) + 0 * J["knee_r"]
    expect = dict(TRUTH)
    expect["stride"] = np.linalg.norm(J["ankle_l"] - J["ankle_r"]) / (0.45 + 0.42)
    u = J["wrist_r"] - J["shoulder_r"]
    expect["slot"] = np.degrees(np.arctan2(u[2], abs(u[1])))
    expect["elbow"] = 90.0
    return {k: np.repeat(v[None], 3, axis=0) for k, v in J.items()}, expect


def random_pose(seed):
    rng = np.random.default_rng(seed)
    Q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    if np.linalg.det(Q) < 0:
        Q[:, 0] *= -1
    return Q, rng.uniform(0.5, 1500.0), rng.normal(size=3) * 100


@pytest.mark.parametrize("seed", range(20))
def test_known_answers_under_rotation_and_scale(seed):
    J, ex = canonical()
    R, s, tr = random_pose(seed)
    Jw = {k: s * v @ R.T + tr for k, v in J.items()}
    up = R @ np.array([0, 0, 1.0])
    d = M.throw_direction(Jw, "r", up, 0)
    assert np.allclose(d, R @ np.array([1.0, 0, 0]), atol=1e-9)
    assert np.allclose(M.trunk_tilt(Jw, "r", up, d), ex["tilt"], atol=1e-6)
    assert np.allclose(M.hip_shoulder_separation(Jw, up), ex["sep"], atol=1e-6)
    assert np.allclose(M.knee_flexion(Jw, "r"), ex["knee"], atol=1e-6)
    assert np.allclose(M.elbow_flexion(Jw, "r"), ex["elbow"], atol=1e-6)
    assert np.allclose(M.stride(Jw, "r"), ex["stride"], atol=1e-9)
    assert np.allclose(M.arm_slot(Jw, "r", up, d), ex["slot"], atol=1e-6)
    assert np.allclose(M.layback_proxy(Jw, "r"), ex["layback"], atol=1e-6)


def test_wrong_arm_changes_answers():
    J, ex = canonical()
    assert not np.allclose(M.knee_flexion(J, "l"), ex["knee"], atol=1.0)
    assert not np.allclose(M.elbow_flexion(J, "l"), ex["elbow"], atol=1.0)


def test_layback_nan_when_arm_straight():
    J, _ = canonical()
    J["wrist_r"] = J["elbow_r"] + (J["elbow_r"] - J["shoulder_r"])
    assert np.all(np.isnan(M.layback_proxy(J, "r")))


def test_2d_measures():
    J = {"hip_l": [0, 0], "hip_r": [0, 0], "shoulder_l": [10, -100], "shoulder_r": [10, -100],
         "knee_l": [0, 50], "ankle_l": [50, 50], "ankle_r": [-80, 100],
         "elbow_r": [60, -100], "wrist_r": [60, -150]}
    J = {k: np.array([v], float) for k, v in J.items()}
    assert np.allclose(M.knee_flexion(J, "r"), 90.0)
    assert np.allclose(M.trunk_tilt(J, "r"), np.degrees(np.arctan2(10, 100)))
    assert np.allclose(M.arm_slot(J, "r"), np.degrees(np.arctan2(50, 50)))


def test_foot_contact():
    h = np.r_[np.full(10, 50.0), np.linspace(50, 400, 20), np.linspace(400, 30, 30), np.full(40, 30.0)]
    fc = M.foot_contact(h, release=80, tol=20.0)
    assert h[fc] <= 50 and h[fc - 1] > 50
