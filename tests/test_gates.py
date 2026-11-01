import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from check_inputs import NEEDED_SEGMENTS, gate_equal_counts, gate_segments  # noqa: E402


def test_equal_counts_pass():
    assert gate_equal_counts({f"cam{c}": 1500 for c in range(15, 23)}) == 1500


def test_dropped_frame_fails():
    counts = {f"cam{c}": 1500 for c in range(15, 23)}
    counts["cam19"] = 1499
    with pytest.raises(SystemExit):
        gate_equal_counts(counts)


def test_empty_fails():
    with pytest.raises(SystemExit):
        gate_equal_counts({"cam15": 0, "cam16": 0})


def test_segments_pass_and_missing_fails():
    labels = NEEDED_SEGMENTS + ["head_4X4", "l_toes_4X4", "r_toes_4X4", "worldbody_4X4", "x_4X4"]
    gate_segments(labels, (4, 4, len(labels), 10))
    with pytest.raises(SystemExit):
        gate_segments([s for s in labels if s != "r_hand_4X4"], (4, 4, len(labels) - 1, 10))
    with pytest.raises(SystemExit):
        gate_segments(labels, (4, 4, len(labels) + 1, 10))
