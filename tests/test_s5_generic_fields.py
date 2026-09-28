"""Regression: verify.py 的通用 todo／review／_edition_count／_member_count／
stale_ref 推广校验（S5，overview#189）。"""
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude/qa"))
import verify


# ---- todo ----

def test_todo_ok_accepts_absent():
    assert verify.todo_ok(None)


def test_todo_ok_accepts_minimal_item():
    assert verify.todo_ok([{"what": "待核撰人"}])


def test_todo_ok_accepts_full_item():
    assert verify.todo_ok([{"what": "待核撰人", "by": "目錄總管", "date": "2026-09-28"}])


def test_todo_ok_rejects_non_list():
    assert not verify.todo_ok({"what": "x"})


def test_todo_ok_rejects_missing_what():
    assert not verify.todo_ok([{"by": "目錄總管"}])


def test_todo_ok_rejects_empty_what():
    assert not verify.todo_ok([{"what": "  "}])


def test_todo_ok_rejects_non_string_by():
    assert not verify.todo_ok([{"what": "x", "by": 1}])


# ---- review ----

def test_review_ok_accepts_absent():
    assert verify.review_ok(None)


def test_review_ok_accepts_minimal():
    assert verify.review_ok({"status": "unreviewed"})


def test_review_ok_accepts_full():
    assert verify.review_ok({"status": "disputed", "by": "目錄總管", "date": "2026-09-28"})


def test_review_ok_rejects_out_of_domain_status():
    assert not verify.review_ok({"status": "confirmed"})


def test_review_ok_rejects_non_dict():
    assert not verify.review_ok(["unreviewed"])


def test_review_ok_rejects_non_string_by():
    assert not verify.review_ok({"status": "reviewed", "by": 1})


# ---- _edition_count ----

def test_derive_edition_count_from_book_work_ids():
    counts = {"d59x": 3}
    assert verify.derive_edition_count("d59x", counts) == 3
    assert verify.derive_edition_count("d59y", counts) == 0


def test_edition_count_ok_passes_when_absent():
    assert verify.edition_count_ok({"id": "d59x"}, {})


def test_edition_count_ok_accepts_matching_positive_value():
    d = {"id": "d59x", "_edition_count": 3}
    assert verify.edition_count_ok(d, {"d59x": 3})


def test_edition_count_ok_rejects_stale_value():
    d = {"id": "d59x", "_edition_count": 2}
    assert not verify.edition_count_ok(d, {"d59x": 3})


def test_edition_count_ok_rejects_zero():
    # =0 者不该写本栏（沿用 _has_text 等「只标异常」之例）
    d = {"id": "d59x", "_edition_count": 0}
    assert not verify.edition_count_ok(d, {})


def test_edition_count_ok_rejects_negative():
    d = {"id": "d59x", "_edition_count": -1}
    assert not verify.edition_count_ok(d, {})


# ---- _member_count ----

def test_derive_member_count():
    d = {"books": ["988a", "988b"], "contained_works": [{"id": "d59a"}]}
    assert verify.derive_member_count(d) == 3


def test_derive_member_count_excludes_contains():
    d = {"contains": [{"type": "preface", "title": "聖諭"}]}
    assert verify.derive_member_count(d) == 0


def test_derive_member_count_includes_reverse_members():
    # overview#198 订正：正向清单本就是空、全靠反挂（如「國立故宮博物院善本舊籍」一类）者，
    # S5 首版会漏算为 0；今须并入反挂集合。
    d = {}
    assert verify.derive_member_count(d, reverse_book_ids={"988a", "988b"}) == 2
    assert verify.derive_member_count(d, reverse_work_ids={"d59a"}) == 1


def test_derive_member_count_dedups_forward_and_reverse():
    # 正向亦列、反挂亦掛者只算一次，不重複计数。
    d = {"books": ["988a"], "contained_works": [{"id": "d59a"}]}
    assert verify.derive_member_count(d, reverse_book_ids={"988a"}, reverse_work_ids={"d59a"}) == 2


def test_member_count_ok_accepts_matching_value():
    d = {"books": ["988a"], "_member_count": 1}
    assert verify.member_count_ok(d)


def test_member_count_ok_rejects_stale_value():
    d = {"books": [], "contained_works": [{"id": "d59a"}], "_member_count": 2}
    assert not verify.member_count_ok(d)


def test_member_count_ok_rejects_zero():
    assert not verify.member_count_ok({"_member_count": 0})


# ---- institution 简繁 ----

def test_institution_simplified_detects_simplified():
    assert verify.institution_simplified("中国国家图书馆")


def test_institution_simplified_passes_traditional():
    assert not verify.institution_simplified("中國國家圖書館")


def test_institution_simplified_passes_none():
    assert not verify.institution_simplified(None)


# ---- title_of / stale title 漂移（单元） ----

def test_title_of_looks_up_work_then_collection():
    IW = {"d59x": {"title": "甲"}}
    IC = {"8rlx": {"title": "乙"}}
    assert verify.title_of("d59x", IW, IC) == "甲"
    assert verify.title_of("8rlx", IW, IC) == "乙"
    assert verify.title_of("nope", IW, IC) is None


# ---- 全库回归：新增派生栏已回填且与校验一致 ----

def _all_works():
    return [(f, json.load(open(f, encoding="utf-8"))) for f in glob.glob(str(ROOT / "Work/*/*/*/*.json"))]


def _all_collections():
    return [(f, json.load(open(f, encoding="utf-8")))
            for f in glob.glob(str(ROOT / "Collection/*/*/*/*.json"))
            if not f.endswith("volume_book_mapping.json")]


def test_all_works_edition_count_up_to_date():
    IB = verify.idx("books")
    import collections
    book_work_ids = collections.Counter(ie.get("work_id") for ie in IB.values() if ie.get("work_id"))
    rows = _all_works()
    bad = [f for f, d in rows if not verify.edition_count_ok(d, book_work_ids)]
    assert bad == [], f"_edition_count 不合或過期：{bad[:5]}（共 {len(bad)} 條）"


def test_all_collections_member_count_up_to_date():
    rev_book_members, rev_work_members = verify.build_reverse_members()
    rows = _all_collections()
    bad = [f for f, d in rows
           if not verify.member_count_ok(d, rev_book_members.get(d.get("id"), set()),
                                          rev_work_members.get(d.get("id"), set()))]
    assert bad == [], f"_member_count 不合或過期：{bad[:5]}（共 {len(bad)} 條）"


def test_all_records_todo_review_shape_ok():
    rows = _all_works() + _all_collections()
    rows += [(f, json.load(open(f, encoding="utf-8"))) for f in glob.glob(str(ROOT / "Book/*/*/*/*.json"))]
    rows += [(f, json.load(open(f, encoding="utf-8"))) for f in glob.glob(str(ROOT / "Entity/*/*/*/*.json"))]
    bad_todo = [f for f, d in rows if not verify.todo_ok(d.get("todo"))]
    bad_review = [f for f, d in rows if not verify.review_ok(d.get("review"))]
    assert bad_todo == [], f"todo 形狀不合：{bad_todo[:5]}"
    assert bad_review == [], f"review 形狀不合：{bad_review[:5]}"


def test_schema_md_documents_new_common_fields():
    schema = (ROOT / "SCHEMA.md").read_text(encoding="utf-8")
    idx = schema.index("## 記錄之共通欄位")
    idx_end = schema.index("## 關聯詞表")
    section = schema[idx:idx_end]
    for token in ("todo", "review", "_edition_count", "_member_count", "unreviewed", "disputed"):
        assert token in section, f"通用欄位一節缺 {token}"
