"""Regression: verify.py 的 Collection.count 校验（S3-Collection.count 吸收，overview#140）。"""
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude/qa"))
import verify


def test_shape_all_int_or_none_with_source_passes():
    c = {"juan": 100, "ce": None, "zhong": 36, "han": None, "source": "description：「凡一百卷」"}
    assert verify.count_ok(c)


def test_all_four_null_fails():
    # 至少一項非空才寫這個物件；全空即不該寫（該整欄位留 None，不是寫這種形狀）
    c = {"juan": None, "ce": None, "zhong": None, "han": None, "source": "本条未见明文"}
    assert not verify.count_ok(c)


def test_missing_source_fails():
    c = {"juan": 100, "ce": None, "zhong": None, "han": None, "source": ""}
    assert not verify.count_ok(c)


def test_non_string_source_fails():
    c = {"juan": 100, "ce": None, "zhong": None, "han": None, "source": None}
    assert not verify.count_ok(c)


def test_non_int_field_fails():
    c = {"juan": "100", "ce": None, "zhong": None, "han": None, "source": "x"}
    assert not verify.count_ok(c)


def test_bool_is_not_a_valid_int():
    # Python 里 True/False 是 int 的子类，必须显式排除，否则 True 会被当成 1 混过去
    c = {"juan": True, "ce": None, "zhong": None, "han": None, "source": "x"}
    assert not verify.count_ok(c)


def test_not_a_dict_fails():
    assert not verify.count_ok([100, None, None, None])


def _all_collections():
    out = []
    for f in glob.glob(str(ROOT / "Collection/*/*/*/*.json")):
        if f.endswith("volume_book_mapping.json"):
            continue
        out.append((f, json.load(open(f, encoding="utf-8"))))
    return out


def test_all_84_collections_have_valid_count_shape_where_present():
    rows = _all_collections()
    assert len(rows) == 85   # 2026-10-07 #19 补立《四庫全書存目叢書》8rldhjfpv8cg
    bad = [f for f, d in rows if d.get("count") is not None and not verify.count_ok(d["count"])]
    assert bad == [], f"count 形狀不對：{bad}"


def test_bainaben_ershisishi_juan_count_corrected_to_count_ce():
    """回归：百衲本《二十四史》的 juan_count 曾误记册数（820）为卷数，
    S3 道已订正：juan_count 归 None，真实册数移入 count.ce。"""
    f = str(ROOT / "Collection/h/h/c/8rlcsybg2hhc-二十四史百衲本.json")
    d = json.load(open(f, encoding="utf-8"))
    assert d.get("juan_count") is None
    assert d["count"]["ce"] == 820
    assert verify.count_ok(d["count"])


def test_schema_md_documents_count_field():
    section = (ROOT / "schema" / "collection.md").read_text(encoding="utf-8")  # 2026-10-08 起格式定义在 schema/（overview#496）
    assert '"count"' in section or '`count`' in section   # schema-v2 起以字段表記
    assert "juan" in section and "ce" in section and "zhong" in section and "han" in section
