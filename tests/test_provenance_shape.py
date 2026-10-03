"""Regression: verify.py 的 Book.provenance 形状校验（S2-Book provenance 吸收）。"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import verify


def test_valid_single_item_passes():
    assert verify.provenance_ok([
        {"institution": "國立故宮博物院", "call_number": "故善012603",
         "seals": [], "notes": "", "source": "metadata.npm_item_id"}
    ])


def test_empty_list_passes():
    assert verify.provenance_ok([])


def test_multiple_items_passes():
    assert verify.provenance_ok([
        {"institution": "國立故宮博物院", "call_number": "故善012603"},
        {"institution": "中國國家圖書館", "call_number": "12433/1148"},
    ])


def test_not_a_list_fails():
    assert not verify.provenance_ok({"institution": "國立故宮博物院"})


def test_item_not_a_dict_fails():
    assert not verify.provenance_ok(["國立故宮博物院"])


def test_missing_institution_fails():
    assert not verify.provenance_ok([{"call_number": "故善012603"}])


def test_empty_institution_fails():
    assert not verify.provenance_ok([{"institution": "", "call_number": "故善012603"}])


def test_blank_institution_fails():
    assert not verify.provenance_ok([{"institution": "   ", "call_number": "故善012603"}])


def test_call_number_non_string_fails():
    assert not verify.provenance_ok([{"institution": "國立故宮博物院", "call_number": 12603}])


def test_call_number_missing_defaults_to_empty_string_and_passes():
    assert verify.provenance_ok([{"institution": "國立故宮博物院"}])
