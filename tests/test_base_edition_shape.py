"""Regression: verify.py 的 Book.base_edition 形状校验（S2c，overview#190）。"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import verify

BOOKS = {"b1": {}, "b2": {}}
WORKS = {"w1": {}}


def test_valid_single_item_passes():
    assert verify.base_edition_ok(
        [{"role": "底本", "name": "宋淳熙三年閩山阮氏種德堂巾箱本", "source": "dating.based_on+edition切分"}],
        "b1", BOOKS, WORKS,
    )


def test_empty_list_passes():
    assert verify.base_edition_ok([], "b1", BOOKS, WORKS)


def test_with_book_id_passes():
    assert verify.base_edition_ok(
        [{"role": "配補", "book_id": "b2", "name": "明聞人銓覆宋本", "note": "評注",
          "source": "lineage.derived_from"}],
        "b1", BOOKS, WORKS,
    )


def test_with_work_id_passes():
    assert verify.base_edition_ok(
        [{"role": "參校", "work_id": "w1", "name": "某本", "source": "lineage.derived_from"}],
        "b1", BOOKS, WORKS,
    )


def test_not_a_list_fails():
    assert not verify.base_edition_ok({"role": "底本"}, "b1", BOOKS, WORKS)


def test_item_not_a_dict_fails():
    assert not verify.base_edition_ok(["底本"], "b1", BOOKS, WORKS)


def test_unknown_role_fails():
    assert not verify.base_edition_ok(
        [{"role": "主底本", "name": "某本", "source": "x"}], "b1", BOOKS, WORKS,
    )


def test_missing_name_fails():
    assert not verify.base_edition_ok(
        [{"role": "底本", "source": "x"}], "b1", BOOKS, WORKS,
    )


def test_blank_name_fails():
    assert not verify.base_edition_ok(
        [{"role": "底本", "name": "  ", "source": "x"}], "b1", BOOKS, WORKS,
    )


def test_missing_source_fails():
    assert not verify.base_edition_ok(
        [{"role": "底本", "name": "某本"}], "b1", BOOKS, WORKS,
    )


def test_book_id_not_found_fails():
    assert not verify.base_edition_ok(
        [{"role": "底本", "book_id": "no-such", "name": "某本", "source": "x"}], "b1", BOOKS, WORKS,
    )


def test_book_id_self_reference_fails():
    assert not verify.base_edition_ok(
        [{"role": "底本", "book_id": "b1", "name": "某本", "source": "x"}], "b1", BOOKS, WORKS,
    )


def test_work_id_not_found_fails():
    assert not verify.base_edition_ok(
        [{"role": "底本", "work_id": "no-such", "name": "某本", "source": "x"}], "b1", BOOKS, WORKS,
    )
