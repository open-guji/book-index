"""Regression: reindex.py 并入 Collection 支持（Q2 任务书）。

坑：scan_files()/fix_membership()/main() field-drift 循环原只列 works/entities/books
三族，Collection 全落空——`index/collections.json` 是单一档，不比照其余三族分 16 片，
若照搬 sharded glob 会直接扫空。expect_collection() 字段口径逆推自既有 84 条索引
核对到 0 误差（title/subtype 恒有；work_id/edition/additional_titles/measure_info
走 nz() 过滤；sort_year／juan_count／has_image 逻辑同 expect_book；has_text 同
has_image 改认 'text'）。
"""
import json, os, subprocess, sys, pathlib, shutil, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import reindex


CID = "8rlztestcoll"  # 12 位，仿真實 Collection id 長度


def _make_repo(tmp):
    d0 = os.path.join(tmp, "Collection", CID[-3], CID[-2], CID[-1])
    os.makedirs(d0)
    os.makedirs(os.path.join(tmp, "index"))
    record = {
        "id": CID, "type": "collection", "subtype": "book_collection", "title": "測試叢書",
        "additional_titles": ["測試叢書別名"],
        "authors": [{"name": "甲編", "role": "author", "dynasty": "清"}],
        "dating": {"era": "清", "year_range": [1736, 1795]},
        "current_location": {"name": "測試館"},
        "juan_count": {"number": 0, "description": "待考"},
        "resources": [{"types": ["image", "text"]}],
    }
    p = os.path.join(d0, f"{CID}-測試叢書.json")
    json.dump(record, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    # collections 是單一檔，非分片目錄，起手一個空 dict
    open(os.path.join(tmp, "index", "collections.json"), "w", encoding="utf-8").write("{}")
    return p


def test_expect_collection_sort_year_falls_back_to_year_range():
    d = {"dating": {"year_range": [1522, 1572]}}
    out = reindex.expect_collection(d)
    assert out["sort_year"] == 1522, "無 dating.year 時須退而取 year_range[0]"


def test_expect_collection_has_image_and_has_text_from_resources():
    d = {"resources": [{"types": ["image"]}, {"types": ["text"]}]}
    out = reindex.expect_collection(d)
    assert out["has_image"] is True and out["has_text"] is True


def test_expect_collection_omits_empty_edition_and_zero_juan_count():
    d = {"edition": "", "juan_count": {"number": 0}}
    out = reindex.expect_collection(d)
    assert out["edition"] is None
    assert out["juan_count"] is None, "juan_count=0 既有庫中慣例一律不寫，須與 books 一致"


def test_expect_collection_matches_existing_index_with_zero_diff():
    """核心验收：对全库既有 84 条 Collection 记录逐条核对，expect_collection()
    产出须与 index/collections.json 现存值逐字段相符（0 误差），
    证明字段口径与既有索引（即 entry_extractor.py 的口径）一致。"""
    real_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    idx = json.load(open(os.path.join(real_root, "index", "collections.json"), encoding="utf-8"))
    checked = 0
    for cid, ie in idx.items():
        p = os.path.join(real_root, ie["path"])
        if not os.path.exists(p): continue
        d = json.load(open(p, encoding="utf-8"))
        want = reindex.expect_collection(d)
        for fld, v in want.items():
            assert reindex.nz(ie.get(fld)) == v, f"{cid} 字段 {fld}: 索引={ie.get(fld)!r} 記錄推得={v!r}"
        checked += 1
    assert checked == len(idx)


def test_collection_index_matches_disk_active_count():
    """完成判据：磁盘活条数＝索引条数。"""
    real_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    import glob as _glob
    disk_ids = set()
    for f in _glob.glob(os.path.join(real_root, "Collection", "**", "*.json"), recursive=True):
        b = os.path.basename(f)
        if reindex.REC_RE.match(b): disk_ids.add(b.split("-", 1)[0])
    idx = json.load(open(os.path.join(real_root, "index", "collections.json"), encoding="utf-8"))
    assert disk_ids == set(idx), "磁盘活条（Collection 记录档）须与索引键集合一致"


def test_fix_membership_adds_collection_entry_idempotently(monkeypatch):
    tmp = tempfile.mkdtemp()
    try:
        _make_repo(tmp)
        monkeypatch.setattr(reindex.jio, "ROOT", tmp)
        add, drop, repath = reindex.fix_membership(run=True)
        assert add == 1 and drop == 0 and repath == 0
        idx = json.load(open(os.path.join(tmp, "index", "collections.json"), encoding="utf-8"))
        e = idx[CID]
        assert e["type"] == "Collection"
        assert e["title"] == "測試叢書"
        assert e["subtype"] == "book_collection"
        assert e["sort_year"] == 1736
        assert e["dynasty"] == "清"
        assert e["has_image"] is True and e["has_text"] is True
        assert e["additional_titles"] == ["測試叢書別名"]
        assert "juan_count" not in e
        # 冪等：再跑一次不應再增鍵
        add2, drop2, repath2 = reindex.fix_membership(run=True)
        assert (add2, drop2, repath2) == (0, 0, 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_patch_jio_root_alone_leaves_real_collections_index_untouched(monkeypatch):
    real_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.isdir(os.path.join(real_root, ".git")), "须在真 book-index 仓下跑"

    tmp = tempfile.mkdtemp()
    try:
        _make_repo(tmp)
        monkeypatch.setattr(reindex.jio, "ROOT", tmp)
        reindex.fix_membership(run=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    out = subprocess.run(["git", "status", "--porcelain", "index/collections.json"],
                          cwd=real_root, capture_output=True, text=True, check=True)
    assert out.stdout == "", f"真倉 index/collections.json 被動了：\n{out.stdout}"


if __name__ == "__main__":
    test_expect_collection_sort_year_falls_back_to_year_range()
    test_expect_collection_has_image_and_has_text_from_resources()
    test_expect_collection_omits_empty_edition_and_zero_juan_count()
    test_collection_index_matches_disk_active_count()
    print("PASS (monkeypatch/核对测试需 pytest 运行)")
