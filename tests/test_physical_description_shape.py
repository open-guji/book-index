"""Regression: verify.py 的 Book.physical_description／edition_type 形状校验（S2b，overview#157）。"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import verify


def test_valid_full_item_passes():
    assert verify.physical_description_ok({
        "leaf_style": "半葉十行行二十字，白口，四周雙邊，單黑魚尾",
        "binding": "線裝", "dimensions": "框高21.5公分，寬15公分",
        "condition": "", "source": "library_data/臺灣故宮博物院善本古籍",
    })


def test_only_leaf_style_passes():
    assert verify.physical_description_ok({
        "leaf_style": "每半葉十行行二十二字", "source": "description 原文抽取",
    })


def test_not_a_dict_fails():
    assert not verify.physical_description_ok(["半葉十行行二十字"])


def test_missing_source_fails():
    assert not verify.physical_description_ok({"leaf_style": "半葉十行行二十字"})


def test_empty_source_fails():
    assert not verify.physical_description_ok({"leaf_style": "半葉十行行二十字", "source": "  "})


def test_all_content_fields_empty_fails():
    assert not verify.physical_description_ok({
        "leaf_style": "", "binding": "", "dimensions": "", "condition": "",
        "source": "metadata.npm_item_id",
    })


def test_non_string_field_fails():
    assert not verify.physical_description_ok({
        "leaf_style": "半葉十行行二十字", "dimensions": 21.5, "source": "x",
    })


def test_valid_edition_type_values_pass():
    for v in ('刻本', '抄本', '稿本', '活字本', '石印本', '鉛印本', '影印本', '套印本', '拓本', '其他'):
        assert verify.edition_type_ok(v)


def test_unknown_edition_type_fails():
    assert not verify.edition_type_ok('鈔本')
    assert not verify.edition_type_ok('')
    assert not verify.edition_type_ok(None)
