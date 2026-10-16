"""build/sealindex.py：印章反查表 index/seals.json 与分页（GUJI-542 P2）。"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
sys.path.insert(0, str(ROOT / 'tests'))
import build_derived as BD  # noqa: E402
import sealindex as SI  # noqa: E402
import v2sample as S  # noqa: E402

ENTS = {
    's1': {'subtype': 'seal'},
    's2': {'subtype': 'seal', 'merged_into': 's1'},        # 墓碑 → s1
    's3': {'subtype': 'seal', 'appears_in': [{'ref_type': 'Book', 'id': 'b1'}, {'ref_type': 'Book', 'id': 'b9'},
                                             {'ref_type': 'Work', 'id': 'w1'}]},
    'p1': {'subtype': 'people'},
}


def book(*marks_per_prov, **kw):
    d = {'provenance': [{'seal_marks': [{'seal_id': s} for s in ms]} for ms in marks_per_prov]}
    d.update(kw)
    return d


def test_count_is_distinct_books_and_follows_tombstone():
    books = [('b1', book(['s1'], ['s1', 's2'])),          # 同一 Book 两个馆藏本、s2 归 s1：只算 1
             ('b2', book(['s2'])),
             ('b3', book(['s3']))]
    m, p, st = SI.derive(books, ENTS)
    assert m == {'s1': {'count': 2, 'pages': 1}, 's3': {'count': 1, 'pages': 1}}   # 墓碑 s2 不单列
    assert p['index/seals/s1/1.json'] == {'seal_id': 's1', 'page': 1, 'books': ['b1', 'b2']}
    assert st['ignored_marks'] == 0


def test_ignores_bad_refs_and_book_tombstones():
    books = [('b1', book(['nope', 'p1'])), ('b2', book(['s1'], merged_into='b1')), ('b3', {'provenance': [{}]})]
    m, p, st = SI.derive(books, ENTS)
    assert m['s1'] == {'count': 0, 'pages': 0} and not p
    assert st['ignored_marks'] == 2


def test_pagination_and_sorted():
    books = [('b%d' % i, book(['s1'])) for i in (5, 3, 1, 4, 2)]
    m, p, _ = SI.derive(books, ENTS, page=2)
    assert m['s1'] == {'count': 5, 'pages': 3}
    assert [p['index/seals/s1/%d.json' % k]['books'] for k in (1, 2, 3)] == [['b1', 'b2'], ['b3', 'b4'], ['b5']]


def test_tombstone_cycle_is_ignored():
    ents = {'s1': {'subtype': 'seal', 'merged_into': 's2'}, 's2': {'subtype': 'seal', 'merged_into': 's1'}}
    m, p, st = SI.derive([('b1', book(['s1']))], ents)
    assert m == {} and st['ignored_marks'] == 1


def test_reconcile_reports_handwritten_not_in_derived():
    m, p, _ = SI.derive([('b1', book(['s3']))], ENTS)
    r = SI.reconcile(ENTS, m, p)
    assert r == {'s3': {'handwritten': 2, 'derived': 1, 'not_in_derived': ['b9']}}


def test_write_drift_prune(tmp_path):
    root = str(tmp_path)
    m, p, _ = SI.derive([('b1', book(['s1'])), ('b2', book(['s1']))], ENTS, page=1)
    f = SI.files(m, p)
    assert SI.drift(root, f) and all(k == 'missing' for _, k in SI.drift(root, f))
    assert SI.write(root, f) == (3, 0)
    assert SI.drift(root, f) == [] and SI.write(root, f) == (0, 0)
    m2, p2, _ = SI.derive([('b1', book(['s1']))], ENTS, page=1)    # 缩成一页
    f2 = SI.files(m2, p2)
    assert SI.drift(root, f2) == [('index/seals.json', 'differs'), ('index/seals/s1/2.json', 'stale')]
    assert SI.write(root, f2) == (1, 1)
    assert SI.drift(root, f2) == []
    assert not os.path.exists(os.path.join(root, 'index/seals/s1/2.json'))


def test_build_writes_seal_files_and_reports(tmp_path):
    repo = S.make(str(tmp_path / 'repo'))
    out = str(tmp_path / 'o')
    r, _ = BD.run(repo, out_dir=out, quiet=True, write_repo_index=True)
    assert r['fatal'] == []
    assert r['index']['seals']['seals'] == 0
    assert json.load(open(os.path.join(out, 'index', 'seals.json'))) == {}
    assert json.load(open(os.path.join(repo, 'index', 'seals.json'))) == {}
    r2, _ = BD.run(repo, out_dir=out, quiet=True)
    assert r2['write']['seal_files_written'] == 0
