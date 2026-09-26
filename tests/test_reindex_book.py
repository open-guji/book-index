"""Regression: reindex.py 并入 Book 支持（D1 #2）。

坑：REC_RE 原只认 12-13 位 id，Book（10 位）全落空，scan_files()/fix_membership()
只扫 Work/Entity；expect_book() 照搬先秦道 `附-reindex_books.py` 时，
sort_year 只取 dating.year，庫中多記於 dating.year_range，逢之即誤把既有值清空。
"""
import json, os, subprocess, sys, pathlib, shutil, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import reindex


BID = "988g9uus2c"  # 10 位，仿真實 Book id 長度


def _make_repo(tmp):
    d0 = os.path.join(tmp, "Book", BID[-3], BID[-2], BID[-1])
    os.makedirs(d0)
    os.makedirs(os.path.join(tmp, "index", "books"))
    record = {
        "id": BID, "type": "book", "title": "測試本",
        "work_id": "d59f2test0000", "edition": "",
        "authors": [{"name": "甲", "role": "撰", "dynasty": "清"}],
        "dating": {"era": "清", "year_range": [1736, 1795]},
        "current_location": {"name": "測試館"},
        "juan_count": {"number": 0, "description": "待考"},
        "resources": [{"types": ["image"]}],
    }
    p = os.path.join(d0, f"{BID}-測試本.json")
    json.dump(record, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    # 分片鍵按 reindex.shard() 算，空索引起手
    sh = reindex.shard(BID)
    open(os.path.join(tmp, "index", "books", f"{sh}.json"), "w", encoding="utf-8").write("{}")
    return p, sh


def test_rec_re_accepts_book_10_char_id():
    assert reindex.REC_RE.match("988g7qh3bb-x")
    assert reindex.REC_RE.match("d59dh4069gcg-x")  # 12 位 Work 仍認得


def test_expect_book_sort_year_falls_back_to_year_range():
    d = {"dating": {"year_range": [1522, 1572]}}
    out = reindex.expect_book(d)
    assert out["sort_year"] == 1522, "無 dating.year 時須退而取 year_range[0]"


def test_expect_book_prefers_explicit_year_over_range():
    d = {"dating": {"year": 1800, "year_range": [1522, 1572]}}
    assert reindex.expect_book(d)["sort_year"] == 1800


def test_expect_book_omits_empty_edition_and_zero_juan_count():
    d = {"edition": "", "juan_count": {"number": 0}}
    out = reindex.expect_book(d)
    assert "edition" not in {k for k, v in out.items() if v is not None} or out.get("edition") is None
    assert out["juan_count"] is None, "juan_count=0 既有庫中慣例一律不寫，須與之一致"


def test_fix_membership_adds_book_entry_idempotently(monkeypatch):
    # 協調者裁（回 pit-jio與reindex的ROOT不同源）：ROOT 已收單一來源
    # （reindex.py 全改經 jio.ROOT 直查，不再自存副本），只 patch jio.ROOT 一處
    # 即可把 scan_files／fix_membership 一併關進沙盒，不會碰到真倉的 index/。
    tmp = tempfile.mkdtemp()
    try:
        p, sh = _make_repo(tmp)
        monkeypatch.setattr(reindex.jio, "ROOT", tmp)
        add, drop, repath = reindex.fix_membership(run=True)
        assert add == 1 and drop == 0 and repath == 0
        idx = json.load(open(os.path.join(tmp, "index", "books", f"{sh}.json"), encoding="utf-8"))
        e = idx[BID]
        assert e["type"] == "Book"
        assert e["title"] == "測試本"
        assert e["work_id"] == "d59f2test0000"
        assert e["sort_year"] == 1736
        assert e["has_image"] is True
        assert "edition" not in e
        assert "juan_count" not in e
        # 冪等：再跑一次不應再增鍵
        add2, drop2, repath2 = reindex.fix_membership(run=True)
        assert (add2, drop2, repath2) == (0, 0, 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_patch_jio_root_alone_leaves_real_repo_index_untouched(monkeypatch):
    """协调者裁（回 pit-jio与reindex的ROOT不同源）之验收测：只 patch jio.ROOT
    一处到临时目录，真仓库的 index/ 应一个字节都不受影响——用真 git 仓的
    `git status --porcelain index/` 核验，不能只信任内存里的推断。"""
    real_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.isdir(os.path.join(real_root, ".git")), "须在真 book-index 仓下跑"

    tmp = tempfile.mkdtemp()
    try:
        d0 = os.path.join(tmp, "Book", "z", "z", "z")
        os.makedirs(d0)
        os.makedirs(os.path.join(tmp, "index", "books"))
        json.dump({"id": "zzzzzzzzzz", "type": "book", "title": "占位"},
                  open(os.path.join(d0, "zzzzzzzzzz-占位.json"), "w", encoding="utf-8"),
                  ensure_ascii=False)
        open(os.path.join(tmp, "index", "books", reindex.shard("zzzzzzzzzz") + ".json"),
             "w", encoding="utf-8").write("{}")

        monkeypatch.setattr(reindex.jio, "ROOT", tmp)
        reindex.fix_membership(run=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    out = subprocess.run(["git", "status", "--porcelain", "index/"],
                          cwd=real_root, capture_output=True, text=True, check=True)
    assert out.stdout == "", f"真倉 index/ 被動了：\n{out.stdout}"


if __name__ == "__main__":
    test_rec_re_accepts_book_10_char_id()
    test_expect_book_sort_year_falls_back_to_year_range()
    test_expect_book_prefers_explicit_year_over_range()
    test_expect_book_omits_empty_edition_and_zero_juan_count()
    print("PASS (monkeypatch 测试需 pytest 运行)")
