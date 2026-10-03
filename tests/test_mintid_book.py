"""Regression: mintid.py 生成 Book ID 不得中止（D1 #1）。

坑：Book（type=0）之 Official raw 不受 type/status 位贡献，数值天然较小，
常编出 10 位而非旧断言写死的 12 位，逢 Book 必 SystemExit。
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import mintid


def test_mint_book_100_no_abort():
    ids = mintid.mint("Book", "coordinator", 100, status=0)
    assert len(ids) == 100
    assert len(set(ids)) == 100, "须唯一"
    for i in ids:
        assert all(c in mintid.A for c in i), "须全 base36 小写字符"
        p = mintid.parse(i)
        assert p["type_name"] == "Book"
        assert p["raw"] < 2 ** 63, "sign bit 须为 0"
        assert mintid.dec(i) == p["raw"], "编解码须往返一致"


def test_mint_book_draft_no_abort():
    ids = mintid.mint("Book", "coordinator", 20, status=1)
    assert len(ids) == 20
    for i in ids:
        p = mintid.parse(i)
        assert p["type_name"] == "Book"
        assert p["status"] == 1


if __name__ == "__main__":
    test_mint_book_100_no_abort()
    test_mint_book_draft_no_abort()
    print("PASS")
