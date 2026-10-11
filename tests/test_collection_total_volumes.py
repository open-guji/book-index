"""Regression: 《二十五史藝文經籍志考補萃編》total_volumes／count（S3b/overview#171）。"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude/qa"))
import verify


def test_ershiwushi_yiwen_jingjizhi_kaobu_cuibian_total_volumes_corrected():
    """回归：《二十五史藝文經籍志考補萃編》total_volumes 曾填反（27 实为卷数），
    S3（overview#140）已在 count 填对 juan/ce 但未订正 total_volumes 本身；
    S3b（overview#171）订正 total_volumes 为 31（册数），count 保持不变。"""
    f = str(ROOT / "Collection/h/h/h/8rlcsybg2hhh-二十五史藝文經籍志考補萃編.json")
    d = json.load(open(f, encoding="utf-8"))
    assert d["total_volumes"] == 31
    assert d["count"]["juan"] == 27
    assert d["count"]["ce"] == 31
    assert verify.count_ok(d["count"])
