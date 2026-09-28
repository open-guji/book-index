"""Regression: verify.py 的 Collection._member_type 校验
（S3b/overview#171 建，S3c/overview#191 补反挂成员）。"""
import collections
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


def test_reverse_book_alone_is_book():
    # S3c/#191：正向清單全空，但有 Book.contained_in 反掛，仍須推出 Book
    # （全庫最大幾部叢編，如「國立故宮博物院善本舊籍」，正向清單本就是空的）
    assert verify.derive_member_type({}, reverse_has_book=True) == "Book"


def test_reverse_work_alone_is_work():
    assert verify.derive_member_type({}, reverse_has_work=True) == "Work"


def test_forward_book_and_reverse_work_is_mixed():
    d = {"books": ["988x"]}
    assert verify.derive_member_type(d, reverse_has_work=True) == "mixed"


def test_forward_and_reverse_both_book_side_stays_book():
    d = {"books": ["988x"]}
    assert verify.derive_member_type(d, reverse_has_book=True) == "Book"


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


def test_member_type_ok_uses_reverse_flags():
    # 正向清單全空，僅靠反掛判定；不傳反掛旗標會誤判成過期
    d = {"_member_type": "Book"}
    assert not verify.member_type_ok(d)  # 不傳旗標＝當作兩側皆空，Book 對不上 None
    assert verify.member_type_ok(d, reverse_has_book=True)


def _all_collections():
    out = []
    for f in glob.glob(str(ROOT / "Collection/*/*/*/*.json")):
        if f.endswith("volume_book_mapping.json"):
            continue
        out.append((f, json.load(open(f, encoding="utf-8"))))
    return out


def _reverse_counters():
    """全庫 Book／Work 之 contained_in[].id -> 反掛計數（同 s3c_member_type_reverse.py 的算法）。"""
    IB, IW = verify.idx("books"), verify.idx("works")
    rev_b, rev_w = collections.Counter(), collections.Counter()
    for _, ie in IB.items():
        p = ROOT / ie["path"]
        if not p.exists():
            continue
        d = json.load(open(p, encoding="utf-8"))
        for ci in d.get("contained_in") or []:
            cid_ = ci.get("id") if isinstance(ci, dict) else ci
            if cid_:
                rev_b[cid_] += 1
    for _, ie in IW.items():
        p = ROOT / ie["path"]
        if not p.exists():
            continue
        d = json.load(open(p, encoding="utf-8"))
        for ci in d.get("contained_in") or []:
            cid_ = ci.get("id") if isinstance(ci, dict) else ci
            if cid_:
                rev_w[cid_] += 1
    return rev_b, rev_w


def test_all_84_collections_have_up_to_date_member_type():
    rows = _all_collections()
    assert len(rows) == 84
    rev_b, rev_w = _reverse_counters()
    bad = [
        f for f, d in rows
        if not verify.member_type_ok(d, bool(rev_b.get(d["id"], 0)), bool(rev_w.get(d["id"], 0)))
    ]
    assert bad == [], f"_member_type 不合或過期：{bad}"


def test_member_type_distribution_matches_current_data():
    """回归：S3c（overview#191）计入反挂成员之后的分布快照——
    Book 39／Work 29／mixed 5／无（不写）11。
    若 Book／Work 的 contained_in 或 Collection 的 books／contained_works 结构改动导致
    此分布变化，需重跑 s3c_member_type_reverse.py 并更新本测试。"""
    rows = _all_collections()
    rev_b, rev_w = _reverse_counters()
    dist = collections.Counter(
        verify.derive_member_type(d, bool(rev_b.get(d["id"], 0)), bool(rev_w.get(d["id"], 0)))
        for _, d in rows
    )
    assert dist == collections.Counter({"Book": 39, "Work": 29, None: 11, "mixed": 5})


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
