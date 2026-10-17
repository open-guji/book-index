#!/usr/bin/env python3
"""Book.provenance[].seal_marks 引用檢查 B-S01…B-S05 的正反例（GUJI-542 P1 補測）。

用最小假 registry（只需 .sub／.rec），不依賴實庫。直接跑：python3 test_seal_marks.py
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # .claude/qa/

import check_v2 as cv  # noqa: E402


class Reg:
    def __init__(self, recs):
        self.rec = recs
        self.sub = {k: v.get("subtype") for k, v in recs.items()}


SEAL = {"subtype": "seal", "end": 1500}
REG = Reg({
    "S_OK": dict(SEAL),
    "S_NOEND": {"subtype": "seal"},
    "S_TOMB": {"subtype": "seal", "merged_into": "S_OK"},
    "S_OLD": {"subtype": "seal", "end": 1200},
    "P1": {"subtype": "people"},
})


def codes(marks, year=None):
    rec = {"provenance": [{"seal_marks": marks}]}
    if year is not None:
        rec["dating"] = {"year": year}
    return sorted((c, lv) for c, lv, _f, _d in cv.check_seal_marks(rec, REG))


def run() -> None:
    E, W = cv.es.ERROR, cv.es.WARN
    assert codes([{"seal_id": "S_OK"}], 1400) == [], "正例：存在的 seal、年份不早於 end"
    assert codes([{"seal_id": "S_NOEND"}], 1400) == [], "正例：seal 無 end 不報 B-S04"
    assert codes([{"seal_id": "S_OK", "position": "x" * 30}]) == [], "正例：position=30 字不報"
    assert codes([{"seal_id": "NOPE"}]) == [("B-S01", E)], "B-S01 不存在"
    assert codes([{"seal_id": "P1"}]) == [("B-S01", E)], "B-S01 非 seal"
    assert codes([{"seal_id": "S_OK"}, {"seal_id": "S_OK"}]) == [("B-S02", E)], "B-S02 項內重複"
    assert codes([{"seal_id": "S_TOMB"}]) == [("B-S03", W)], "B-S03 墓碑"
    assert codes([{"seal_id": "S_OLD"}], 1300) == [("B-S04", W)], "B-S04 印止於書年份前"
    assert codes([{"seal_id": "S_OLD"}], 1200) == [], "B-S04 邊界：end==year 不報"
    assert codes([{"seal_id": "S_OLD"}]) == [], "B-S04：書無 year 不報"
    assert codes([{"seal_id": "S_OK", "position": "x" * 31}]) == [("B-S05", E)], "B-S05 position>30"
    # 不同 provenance 項各自去重
    rec = {"provenance": [{"seal_marks": [{"seal_id": "S_OK"}]}, {"seal_marks": [{"seal_id": "S_OK"}]}]}
    assert not cv.check_seal_marks(rec, REG), "跨項同 seal 不算重複"
    print("OK：B-S01…B-S05 正反例")


def test_seal_marks_codes():
    run()


if __name__ == "__main__":
    run()
