"""Regression: verify.py 的 classification 词表校验（S1-Work分类吸收）。"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import verify


def _vocab():
    return verify.load_classific_vocab()


def test_full_l1_l2_l3_l4_combo_passes():
    V = _vocab()
    # 真实存在的一条第四级组合（方志类某省）：取词表里任一条校验，不写死具体省名
    import json
    rows = json.load(open(pathlib.Path(__file__).parent.parent / "classific.json", encoding="utf-8"))
    r4 = next(r for r in rows if r.get("cata_l4"))
    c = {"l1": r4["cata_l1"], "l2": r4["cata_l2"], "l3": r4["cata_l3"], "l4": r4["cata_l4"]}
    assert verify.classification_ok(c, V)


def test_l1_only_passes():
    V = _vocab()
    assert verify.classification_ok({"l1": "史部", "l2": "", "l3": "", "l4": ""}, V)


def test_empty_all_passes():
    V = _vocab()
    assert verify.classification_ok({"l1": "", "l2": "", "l3": "", "l4": ""}, V)


def test_unknown_l1_fails():
    V = _vocab()
    assert not verify.classification_ok({"l1": "丙部", "l2": "", "l3": "", "l4": ""}, V)


def test_l2_not_under_l1_fails():
    V = _vocab()
    # 小說類属集部，不属经部
    assert not verify.classification_ok({"l1": "經部", "l2": "小說類", "l3": "", "l4": ""}, V)


def test_l2_without_l1_is_invalid_shape():
    V = _vocab()
    assert not verify.classification_ok({"l1": "", "l2": "易類", "l3": "", "l4": ""}, V)


def test_l3_not_under_l2_fails():
    V = _vocab()
    # 詩評之屬属集評類，不属易類
    assert not verify.classification_ok(
        {"l1": "經部", "l2": "易類", "l3": "詩評之屬", "l4": ""}, V)


def test_valid_l2_only_passes():
    V = _vocab()
    assert verify.classification_ok({"l1": "經部", "l2": "易類", "l3": "", "l4": ""}, V)
