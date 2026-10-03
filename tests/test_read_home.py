"""curation/read-home.json 的结构与引用校验（overview#321）。

只靠本仓即可跑；设 BOOK_TEXT_DIR 指向 book-text 时，再核「可读」与 text_count。
"""
import glob, json, os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = json.load(open(os.path.join(ROOT, 'curation', 'read-home.json'), encoding='utf-8'))


def _records():
    out = {}
    for t in ('Work', 'Book'):
        for p in glob.glob(os.path.join(ROOT, t, '*', '*', '*', '*.json')):
            d = json.load(open(p, encoding='utf-8'))
            out[d['id']] = d
    return out


REC = _records()


def _items():
    return [it for t in DATA['topics'] for it in t['items']]


def test_top_level_shape():
    assert DATA['schema'] == 'read-home/1'
    assert set(DATA) == {'schema', 'readable', 'picks', 'topics', 'famous', 'not_readable_dropped'}
    assert [t['key'] for t in DATA['topics']] == ['shizhi', 'shumu', 'congshu', 'dangan', 'shishu', 'shiwenji', 'zishu']


def test_picks():
    assert [p['order'] for p in DATA['picks']] == [1, 2, 3, 4, 5, 6]
    for p in DATA['picks']:
        assert p['id'] in REC and REC[p['id']]['title'] == p['title']
        assert p['blurb'] and p['slip'] and p['type_label']
        if p['kind'] == 'Book':
            assert REC[p['id']]['work_id'] == p['work_id']


def test_topic_items_exist_and_unique():
    ids = [i['id'] for i in _items()]
    assert len(ids) == len(set(ids))
    for it in _items():
        r = REC[it['id']]
        assert r['title'] == it['title']
        assert it['kind'] == ('Work' if r['type'] == 'work' else 'Book')
        assert it['text_count'] >= 1
        if 'via_book' in it:
            assert REC[it['via_book']]['work_id'] == it['id']


def test_shizhi_shelf():
    shelf = DATA['topics'][0]
    assert shelf['layout'] == 'shelf' and len(shelf['items']) == 28
    for it in shelf['items']:
        assert it['period_of'] and isinstance(it['orig'], bool)
    assert sum(it['orig'] for it in shelf['items']) == 7
    for t in DATA['topics'][1:]:
        assert all('period_of' not in it and 'orig' not in it for it in t['items'])


def test_famous_books_belong_to_work():
    assert len(DATA['famous']) == 6
    for f in DATA['famous']:
        assert f['work_id'] in REC
        for s in f['systems']:
            for e in s['editions']:
                assert REC[e['book_id']]['work_id'] == f['work_id']


@pytest.mark.skipif(not os.environ.get('BOOK_TEXT_DIR'), reason='未设 BOOK_TEXT_DIR（book-text 路径），跳过可读性核对')
def test_readable_against_book_text():
    root = os.environ['BOOK_TEXT_DIR']
    man = {}
    for p in glob.glob(os.path.join(root, '*', '*', '*', '*', '*', 'manifest.json')):
        parts = p.split(os.sep)
        if parts[-6] in ('Work', 'Book'):
            man[parts[-2]] = json.load(open(p, encoding='utf-8'))
    assert man, 'BOOK_TEXT_DIR 下一个 manifest 也没扫到'
    for p in DATA['picks']:
        assert p['id'] in man, f"推荐 {p['id']} 不可读"
    for it in _items():
        assert it['id'] in man, f"{it['id']} {it['title']} 不可读"
        n = len(man[it['id']]['versions'])
        if it['kind'] == 'Work':
            n += sum(len(man[b]['versions']) for b, r in REC.items() if r['type'] == 'book' and r.get('work_id') == it['id'] and b in man)
        assert it['text_count'] == n, f"{it['id']} text_count {it['text_count']} != {n}"
    for f in DATA['famous']:
        for s in f['systems']:
            for e in s['editions']:
                assert e['readable'] == (e['book_id'] in man)
