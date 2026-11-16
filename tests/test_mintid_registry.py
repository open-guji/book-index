"""mintid 车道登记强制（2026-11-16 撞号之后）。"""
import sys, pathlib
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import mintid


def test_no_active_conflicts():
    assert mintid.lane_conflicts() == []


def test_unregistered_lane_rejected():
    mintid.LANE_MACHINE["zz-unregistered"] = 1999
    try:
        with pytest.raises(SystemExit):
            mintid.mint("Work", "zz-unregistered", 1)
    finally:
        del mintid.LANE_MACHINE["zz-unregistered"]


def test_injection_mismatch_rejected():
    old = mintid.LANE_MACHINE["a11-pm-kr"]
    mintid.LANE_MACHINE["a11-pm-kr"] = 1918
    try:
        with pytest.raises(SystemExit):
            mintid.mint("Work", "a11-pm-kr", 1)
    finally:
        mintid.LANE_MACHINE["a11-pm-kr"] = old


def test_retired_rejected():
    with pytest.raises(SystemExit):
        mintid.mint("Work", "a11-pm-sjy", 1)


def test_kind_restricted():
    with pytest.raises(SystemExit):
        mintid.mint("Book", "a11-pm-sjy2", 1)
    assert len(mintid.mint("Work", "a11-pm-sjy2", 2)) == 2


def test_same_value_injection_ok():
    mintid.LANE_MACHINE["a11-pm-kr"] = 1910
    assert len(mintid.mint("Work", "a11-pm-kr", 1)) == 1
