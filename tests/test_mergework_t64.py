"""T64（overview#367）：mergework.py 補三處缺口的回歸——
  1 併後 Book.work_id 指向 keeper（記錄與 index/books）
  2 keeper 之 related_works 無自指項
  3 keeper 之 _edition_count 重算
搭一個假倉（兩條 Work、兩本 Book 各掛一條、keeper 的 related_works 指著被併者），
patch 三處各自獨立之 ROOT（mergework／jio／backrefs，見 test_mergework_fields.py 之註），
跑真的 main(--apply)。
"""
import json, os, sys, shutil, tempfile, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import mergework, jio, backrefs


def _w(root, rel, d):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def _r(root, rel):
    return json.load(open(os.path.join(root, rel), encoding='utf-8'))


def _sandbox():
    tmp = tempfile.mkdtemp(prefix='mergework_t64_')
    _w(tmp, 'Work/a/a/a/zzzkeeper0aaa-甲書.json', {
        'id': 'zzzkeeper0aaa', 'type': 'work', 'title': '甲書', '_edition_count': 1,
        'related_works': [{'id': 'zzzdrop00bbb', 'relation': '別名'},
                          {'id': 'zzzother0ccc', 'relation': '注'}],
    })
    _w(tmp, 'Work/b/b/b/zzzdrop00bbb-甲書.json', {
        'id': 'zzzdrop00bbb', 'type': 'work', 'title': '甲書',
        'related_works': [{'id': 'zzzkeeper0aaa', 'relation': '別名'}],
    })
    _w(tmp, 'Work/c/c/c/zzzother0ccc-乙書.json', {
        'id': 'zzzother0ccc', 'type': 'work', 'title': '乙書',
        'related_works': [{'id': 'zzzdrop00bbb', 'title': '舊題', 'relation': '被注'}],
    })
    _w(tmp, 'Book/1/1/1/bk00000001-甲書甲本.json',
       {'id': 'bk00000001', 'type': 'book', 'title': '甲書', 'work_id': 'zzzkeeper0aaa'})
    _w(tmp, 'Book/2/2/2/bk00000002-甲書乙本.json',
       {'id': 'bk00000002', 'type': 'book', 'title': '甲書', 'work_id': 'zzzdrop00bbb'})
    _w(tmp, 'index/works/0.json', {
        'zzzkeeper0aaa': {'title': '甲書', 'path': 'x'}, 'zzzdrop00bbb': {'title': '甲書', 'path': 'y'},
        'zzzother0ccc': {'title': '乙書', 'path': 'z'}})
    _w(tmp, 'index/books/0.json', {
        'bk00000001': {'id': 'bk00000001', 'work_id': 'zzzkeeper0aaa'},
        'bk00000002': {'id': 'bk00000002', 'work_id': 'zzzdrop00bbb'}})
    _w(tmp, 'index/entities/0.json', {})
    _w(tmp, 'index/collections.json', {})
    return tmp


def _run(tmp):
    olds = (mergework.ROOT, jio.ROOT, backrefs.ROOT, sys.argv)
    mergework.ROOT = jio.ROOT = backrefs.ROOT = tmp
    sys.argv = ['mergework.py', '--keeper', 'zzzkeeper0aaa', '--drop', 'zzzdrop00bbb',
                '--rule', 'test', '--why', 'test', '--apply']
    try:
        mergework.main()
    finally:
        mergework.ROOT, jio.ROOT, backrefs.ROOT, sys.argv = olds


def test_book_work_id_selfref_edition_count():
    tmp = _sandbox()
    try:
        _run(tmp)
        # 1 Book.work_id 改指（記錄＋索引）
        assert _r(tmp, 'Book/2/2/2/bk00000002-甲書乙本.json')['work_id'] == 'zzzkeeper0aaa'
        ib = _r(tmp, 'index/books/0.json')
        assert ib['bk00000002']['work_id'] == 'zzzkeeper0aaa'
        # 2 keeper 無自指，別條 related_works 照舊改指
        k = _r(tmp, 'Work/a/a/a/zzzkeeper0aaa-甲書.json')
        assert [r['id'] for r in k['related_works']] == ['zzzother0ccc']
        o = _r(tmp, 'Work/c/c/c/zzzother0ccc-乙書.json')
        assert o['related_works'][0]['id'] == 'zzzkeeper0aaa'
        assert o['related_works'][0]['title'] == '甲書'   # 題名隨 keeper
        # 3 _edition_count 重算：1 → 2
        assert k['_edition_count'] == 2
        # 被併者已刪、索引已清
        assert not os.path.exists(os.path.join(tmp, 'Work/b/b/b/zzzdrop00bbb-甲書.json'))
        assert 'zzzdrop00bbb' not in _r(tmp, 'index/works/0.json')
    finally:
        shutil.rmtree(tmp)


def test_clean_self_related_pure():
    rel = [{'id': 'K'}, {'work_id': 'D'}, {'id': 'X', 'relation': 'r'}]
    out, gone = mergework.clean_self_related(rel, 'K', ['D'])
    assert out == [{'id': 'X', 'relation': 'r'}] and len(gone) == 2


def test_no_books_drops_edition_count():
    tmp = _sandbox()
    try:
        os.remove(os.path.join(tmp, 'Book/1/1/1/bk00000001-甲書甲本.json'))
        os.remove(os.path.join(tmp, 'Book/2/2/2/bk00000002-甲書乙本.json'))
        _run(tmp)
        assert '_edition_count' not in _r(tmp, 'Work/a/a/a/zzzkeeper0aaa-甲書.json')
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_book_work_id_selfref_edition_count()
    test_clean_self_related_pure()
    test_no_books_drops_edition_count()
    print("PASS")
