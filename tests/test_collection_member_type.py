"""Regression: verify.py 的 Collection._member_type 校验（S3b，overview#171）。"""
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude/qa"))
import verify


def test_only_books_is_book():
    assert verify.derive_member_type({"books": ["988x"], "contained_works": []}) == "Book"


def test_only_contained_works_is_work():
    assert verify.derive_member_type({"books": [], "contained_works": [{"id": "d59x"}]}) == "Work"


def test_both_is_mixed():
    d = {"books": ["988x"], "contained_works": [{"id": "d59x"}]}
    assert verify.derive_member_type(d) == "mixed"


def test_neither_is_none():
    assert verify.derive_member_type({"books": [], "contained_works": []}) is None
    assert verify.derive_member_type({}) is None


def test_contains_is_not_a_member_list():
    # `contains`（結構組成部分）不是平列成員，不可拿來推 member_type
    d = {"contains": [{"type": "preface", "title": "聖諭", "book_id": "96x"}]}
    assert verify.derive_member_type(d) is None


def test_member_type_ok_accepts_matching_value():
    d = {"books": ["988x"], "contained_works": []}
    d["_member_type"] = "Book"
    assert verify.member_type_ok(d)


def test_member_type_ok_rejects_stale_value():
    # 派生欄位：手寫或改了成員清單後未重算，都算不合
    d = {"books": [], "contained_works": [{"id": "d59x"}], "_member_type": "Book"}
    assert not verify.member_type_ok(d)


def test_member_type_ok_rejects_out_of_domain_value():
    d = {"books": ["988x"], "_member_type": "Entity"}
    assert not verify.member_type_ok(d)


def test_member_type_ok_passes_when_absent():
    assert verify.member_type_ok({"books": ["988x"]})


def _all_collections():
    out = []
    for f in glob.glob(str(ROOT / "Collection/*/*/*/*.json")):
        if f.endswith("volume_book_mapping.json"):
            continue
        out.append((f, json.load(open(f, encoding="utf-8"))))
    return out


def test_all_84_collections_have_up_to_date_member_type():
    rows = _all_collections()
    assert len(rows) == 84
    bad = [f for f, d in rows if not verify.member_type_ok(d)]
    assert bad == [], f"_member_type 不合或過期：{bad}"


def test_member_type_distribution_matches_current_data():
    """回归：本轮（overview#171）机械推导之后的分布快照——27 Book／27 Work／3 mixed／27 无（不写）。
    若member 清单结构改动导致此分布变化，需重跑 s3b_collection_finish.py 并更新本测试。"""
    from collections import Counter

    rows = _all_collections()
    dist = Counter(verify.derive_member_type(d) for _, d in rows)
    assert dist == Counter({"Book": 27, "Work": 27, None: 27, "mixed": 3})


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


def test_schema_md_documents_member_type_field():
    schema = (ROOT / "SCHEMA.md").read_text(encoding="utf-8")
    idx = schema.index("### 2. Collection Schema")
    idx_book = schema.index("### 3. Book Schema")
    section = schema[idx:idx_book]
    assert "_member_type" in section
