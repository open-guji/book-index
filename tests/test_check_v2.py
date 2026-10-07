"""check_v2.py：新格式殘留檢查（F6-2，overview#459）。以最小樣例逐項驗。"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude/qa"))
import check_v2  # noqa: E402


def codes(kind, rec):
    return sorted(c for c, _, _ in check_v2.check_record(kind, rec))


NEW_WORK = {
    "id": "1evaaaaaaaaab", "type": "work", "title": "甲",
    "authors": [{"name": "某", "role": "撰", "dynasty": "唐", "entity_id": "x"}],
    "related_works": [
        {"id": "1evaaaaaaaaaz", "relation": "related", "note": "同題"},
        {"id": "1ev0000000000", "relation": "part_of"},
        {"id": "1ev0000000001", "relation": "studies"},
        {"id": "1ev0000000002", "relation": "contains_text_of"},
        {"id": "1ev0000000003", "relation": "preceded_by"},
        {"id": "1ev0000000004", "relation": "collected_in"},
        {"id": "1ev0000000005", "relation": "pseudepigraph_of"},
    ],
    "contained_in": [{"id": "c1", "volume_index": 3}],
    "indexed_by": [{"source": "隋書經籍志", "source_bid": "s1", "title_info": "甲一卷"}],
}


def test_new_format_work_is_clean():
    assert codes("Work", NEW_WORK) == []


def test_underscore_and_old_derived_fields():
    rec = dict(NEW_WORK, _edition_count=3, _has_image=True, has_image=True, promoted_to="abc")
    assert codes("Work", rec) == ["V01", "V01", "V02", "V02"]


def test_has_text_and_has_collated_exempt():
    # 目錄總管 10-07：_has_text／_has_collated 暫留源欄，不報
    rec = dict(NEW_WORK, _has_text=True, _has_collated=True)
    assert codes("Work", rec) == []
    assert codes("Book", {"id": "11b", "type": "book", "work_id": "w", "_has_text": True}) == []


def test_work_books():
    assert codes("Work", dict(NEW_WORK, books=["b1", "b2"])) == ["V03"]


def test_reverse_relation_words():
    for rel in ("has_part", "studied_by", "text_carried_by", "followed_by",
                "has_pseudepigraph", "has_adaptation"):
        rec = dict(NEW_WORK, related_works=[{"id": "1ev0000000009", "relation": rel}])
        assert codes("Work", rec) == ["V04"], rel


def test_deprecated_and_unknown_relation():
    rec = dict(NEW_WORK, related_works=[{"id": "1ev0000000009", "relation": "commentary_on"}])
    assert codes("Work", rec) == ["V05"]
    rec = dict(NEW_WORK, related_works=[{"id": "1ev0000000009", "relation": "inspired"}])
    assert codes("Work", rec) == ["V13"]


def test_related_title_copy():
    rec = dict(NEW_WORK, related_works=[{"id": "1ev0000000009", "title": "乙", "relation": "studies"}])
    assert codes("Work", rec) == ["V06"]


def test_related_on_larger_id_side():
    # 本記錄 id 大於對方 → 該存在對方
    rec = dict(NEW_WORK, related_works=[{"id": "1evaaaaaaaaaa", "relation": "related"}])
    assert codes("Work", rec) == ["V07"]
    # 舊形 work_id 亦認
    rec = dict(NEW_WORK, related_works=[{"work_id": "1evaaaaaaaaaa", "relation": "related"}])
    assert codes("Work", rec) == ["V07"]
    # 非 related 不比大小
    rec = dict(NEW_WORK, related_works=[{"id": "1evaaaaaaaaaa", "relation": "studies"}])
    assert codes("Work", rec) == []


def test_symmetric_id_lists_on_book_and_collection():
    book = {"id": "11b", "type": "book", "title": "x", "work_id": "w",
            "related_books": ["11a", "11c"]}
    assert codes("Book", book) == ["V07"]
    coll = {"id": "2b", "type": "collection", "title": "x", "related_collections": ["2a"]}
    assert codes("Collection", coll) == ["V07"]
    # 對象形（舊）：M2 轉成 id 字符串
    coll = {"id": "2a", "type": "collection", "title": "x",
            "related_collections": [{"id": "2b", "title": "乙", "type": "sibling"}]}
    assert codes("Collection", coll) == ["V14"]


def test_missing_role():
    rec = dict(NEW_WORK, authors=[{"name": "某"}, {"name": "乙", "role": ""}, {"name": "丙", "role": "注"}])
    assert codes("Work", rec) == ["V08", "V08"]


def test_role_not_required_outside_work():
    book = {"id": "11b", "type": "book", "title": "x", "work_id": "w", "authors": [{"name": "某"}]}
    assert codes("Book", book) == []


def test_old_classification():
    rec = dict(NEW_WORK, classification={"l1": "集部", "l2": "", "l3": "", "l4": "", "source": "x"})
    assert codes("Work", rec) == ["V09"]


def test_collection_member_lists_and_entity_works():
    coll = {"id": "2a", "type": "collection", "title": "x",
            "books": ["b"], "contained_works": [{"id": "w", "title": "甲"}],
            "contains": [{"type": "preface", "title": "聖諭"}], "contained_in": ["2z"]}
    assert codes("Collection", coll) == ["V10", "V10"]
    ent = {"id": "4a", "type": "entity", "primary_name": "某", "works": [{"work_id": "w", "role": "撰"}]}
    assert codes("Entity", ent) == ["V11"]


def _write(root, rel, obj):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_file_walk_sidecar_skips_and_exit_code(tmp_path, capsys):
    _write(tmp_path, "Work/1/e/v/1evaaaaaaaaab-甲.json", NEW_WORK)
    _write(tmp_path, "Work/1/e/v/1evaaaaaaaaab/collated_edition/卷一.json", {"sections": [], "_x": 1})
    _write(tmp_path, "Collection/2/a/2a-叢/volume_book_mapping.json", {"items": []})
    _write(tmp_path, "index/works/0.json", [{"id": "x", "_y": 1}])
    out = tmp_path / "o.csv"
    rc = check_v2.main(["--root", str(tmp_path), "--csv", str(out)])
    assert rc == 1
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "path,id,kind,code,field,detail"
    assert len(lines) == 2 and ",V12," in lines[1]


def test_paths_mode_only_checks_given_files(tmp_path):
    _write(tmp_path, "Work/a/1evaaaaaaaaab-甲.json", NEW_WORK)
    _write(tmp_path, "Work/b/1evaaaaaaaaac-乙.json", dict(NEW_WORK, id="1evaaaaaaaaac", books=["b"]))
    assert check_v2.main(["--root", str(tmp_path), "--summary",
                          "--paths", "Work/a/1evaaaaaaaaab-甲.json", "Work/gone.json", "README.md"]) == 0
    assert check_v2.main(["--root", str(tmp_path), "--summary",
                          "--paths", "Work/b/1evaaaaaaaaac-乙.json"]) == 1


def test_codes_filter_and_bad_args(tmp_path):
    _write(tmp_path, "Work/b/w.json", dict(NEW_WORK, books=["b"]))
    assert check_v2.main(["--root", str(tmp_path), "--summary", "--codes", "V08"]) == 0
    assert check_v2.main(["--root", str(tmp_path), "--summary", "--codes", "V99"]) == 2
    assert check_v2.main(["--root", str(tmp_path / "nope"), "--summary"]) == 2
