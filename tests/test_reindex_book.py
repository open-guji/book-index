"""Regression: reindex.py 并入 Book 支持（D1 #2）。

坑：REC_RE 原只认 12-13 位 id，Book（10 位）全落空，scan_files()/fix_membership()
只扫 Work/Entity；expect_book() 照搬先秦道 `附-reindex_books.py` 时，
sort_year 只取 dating.year，庫中多記於 dating.year_range，逢之即誤把既有值清空。
"""
import json, os, sys, pathlib, shutil, tempfile

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
    # 坑：reindex.py 的 fix_membership() 掃檔靠 reindex.ROOT，但實際讀寫索引分片
    # 靠 jio.load/jio.save——jio.py 自己另算一份 ROOT，兩者互不相關。
    # 只 patch reindex.ROOT 而漏了 jio.ROOT，会让 jio 仍讀寫【真倉】的 index/books/*.json
    # ——本測試第一次寫就是這樣把生產庫 index/books/9.json 炸成只剩 8 條，須兩處都 patch。
    tmp = tempfile.mkdtemp()
    try:
        p, sh = _make_repo(tmp)
        monkeypatch.setattr(reindex, "ROOT", tmp)
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


if __name__ == "__main__":
    test_rec_re_accepts_book_10_char_id()
    test_expect_book_sort_year_falls_back_to_year_range()
    test_expect_book_prefers_explicit_year_over_range()
    test_expect_book_omits_empty_edition_and_zero_juan_count()
    print("PASS (monkeypatch 测试需 pytest 运行)")
