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


def test_all_records_todo_review_shape_ok():
    rows = _all_works() + _all_collections()
    rows += [(f, json.load(open(f, encoding="utf-8"))) for f in glob.glob(str(ROOT / "Book/*/*/*/*.json"))]
    rows += [(f, json.load(open(f, encoding="utf-8"))) for f in glob.glob(str(ROOT / "Entity/*/*/*/*.json"))]
    bad_todo = [f for f, d in rows if not verify.todo_ok(d.get("todo"))]
    bad_review = [f for f, d in rows if not verify.review_ok(d.get("review"))]
    assert bad_todo == [], f"todo 形狀不合：{bad_todo[:5]}"
    assert bad_review == [], f"review 形狀不合：{bad_review[:5]}"


def test_schema_md_documents_new_common_fields():
    # 2026-10-08 起格式定义在 schema/（overview#496）：共通欄在 common.md，派生欄在 derived.md
    section = "".join((ROOT / "schema" / f).read_text(encoding="utf-8") for f in ("common.md", "derived.md"))
    for token in ("todo", "review", "_edition_count", "_member_count", "unreviewed", "disputed"):
        assert token in section, f"通用欄位一節缺 {token}"
