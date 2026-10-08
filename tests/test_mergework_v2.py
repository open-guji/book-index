"""mergework.py schema-v2 版（F6-3，overview#459）：在臨時目錄造新格式小倉（**樣本，非真數據**），
跑真的 main(--apply)，驗併後只寫新格式。前身 test_mergework_t64.py（T64 三缺口）之意併入：
Book.work_id 改指、keeper 無自指；_edition_count 不再寫（build 生成）。"""
import json, os, sys, pathlib, subprocess

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / '.claude/qa'))
import mergework, backrefs, check_v2  # noqa: E402

K, D, O, Z, A = 'w0000000005', 'w0000000009', 'w0000000002', 'w0000000001', 'w0000000007'
CAT = 'w0000000008'          # 一部志書（id 大於 keeper：驗 related 改指後搬到 keeper 側）
B1, B2 = 'b0000000001', 'b0000000002'
C1 = 'c0000000001'
E1, E2 = 'e0000000001', 'e0000000002'


def p(root, typ, rid):
    return os.path.join(root, typ, rid[-1], rid[-2], rid[-3], f'{rid}-樣本.json')


def put(root, typ, d):
    f = p(root, typ, d['id'])
    os.makedirs(os.path.dirname(f), exist_ok=True)
    d = d if "schema_version" in d else dict(d, schema_version=1)  # V15：記錄必填
    open(f, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def get(root, typ, rid):
    return json.load(open(p(root, typ, rid), encoding='utf-8'))


def members(root, node):
    return json.load(open(os.path.join(root, 'classification/zongmu/members', node + '.json'), encoding='utf-8'))['members']


def make(root):
    put(root, 'Work', {'id': K, 'type': 'work', 'title': '列國志傳', 'revision': '1.0.0',
                       'authors': [{'name': '余邵魚', 'role': '撰', 'entity_id': E1}],
                       'related_works': [{'id': D, 'relation': 'related', 'note': '同書'}],
                       'indexed_by': [{'source': '某志', 'source_bid': CAT, 'title_info': '列國志傳八卷'}],
                       '_has_text': True})
    put(root, 'Work', {'id': D, 'type': 'work', 'title': '新刊列國志傳', 'revision': '1.0.0',
                       'authors': [{'name': '余邵魚', 'role': '撰', 'entity_id': E1},
                                   {'name': '陳繼儒', 'role': '評', 'entity_id': E2}],
                       'related_works': [{'id': A, 'relation': 'studies', 'note': '被併者說'},
                                         {'id': Z, 'relation': 'related', 'note': '與甲相關'},
                                         {'id': O, 'relation': 'related'}],
                       'indexed_by': [{'source': '某志', 'source_bid': CAT, 'title_info': '列國志傳八卷'},
                                      {'source': '孫目', 'source_bid': CAT, 'title_info': '新刊京本列國志傳'}],
                       'contained_in': [{'id': C1, 'volume_index': 2}], 'period': 'ming'})
    put(root, 'Work', {'id': O, 'type': 'work', 'title': '續編', 'revision': '1.0.0',
                       'related_works': [{'id': D, 'relation': 'preceded_by'}]})
    put(root, 'Work', {'id': Z, 'type': 'work', 'title': '甲', 'revision': '1.0.0'})
    put(root, 'Work', {'id': A, 'type': 'work', 'title': '原典', 'revision': '1.0.0'})
    put(root, 'Work', {'id': CAT, 'type': 'work', 'title': '某志', 'revision': '1.0.0',
                       'related_works': [{'id': D, 'relation': 'related'}]})
    put(root, 'Book', {'id': B1, 'type': 'book', 'title': '甲本', 'work_id': K, 'revision': '1.0.0'})
    put(root, 'Book', {'id': B2, 'type': 'book', 'title': '乙本', 'work_id': D, 'revision': '1.0.0',
                       'base_edition': [{'role': '底本', 'work_id': D, 'name': 'x', 'source': 't'}]})
    put(root, 'Collection', {'id': C1, 'type': 'collection', 'subtype': 'book_collection', 'title': '叢',
                             'contains': [{'type': 'subwork', 'title': '列國', 'work_id': D}]})
    put(root, 'Entity', {'id': E1, 'type': 'entity', 'subtype': 'people', 'primary_name': '余邵魚'})
    put(root, 'Entity', {'id': E2, 'type': 'entity', 'subtype': 'people', 'primary_name': '陳繼儒'})
    os.makedirs(os.path.join(root, 'classification/zongmu/members'))
    json.dump([{'id': 'zongmu', 'name': '總目', 'primary': True, 'exclusive': True, 'tree': 'zongmu/tree.json'}],
              open(os.path.join(root, 'classification/schemes.json'), 'w'))
    open(os.path.join(root, 'classification/zongmu/members/zm0002.json'), 'w', encoding='utf-8').write(
        mergework.members_dump('zm0002', [[D, '孫目'], [Z, '某志']]))


def run(root, *extra):
    return mergework.main(['--root', str(root), '--keeper', K, '--drop', D, '--rule', '版本條改建Book',
                           '--why', '樣本', '--at', '2026-10-07T00:00:00Z', *extra])


def test_dry_run_writes_nothing(tmp_path, capsys):
    make(str(tmp_path))
    before = {f: open(f, encoding='utf-8').read() for f in map(str, tmp_path.rglob('*.json'))}
    assert run(tmp_path) == 0
    after = {f: open(f, encoding='utf-8').read() for f in map(str, tmp_path.rglob('*.json'))}
    assert before == after
    out = capsys.readouterr().out
    assert '乾跑' in out and '被併者撰人帶 entity_id 而 keeper 無' in out


def test_apply_new_format_only(tmp_path):
    root = str(tmp_path)
    make(root)
    assert run(tmp_path, '--apply') == 0
    assert not os.path.exists(p(root, 'Work', D))
    k = get(root, 'Work', K)
    rels = {(r['id'], r['relation']): r.get('note') for r in k['related_works']}
    # 被併者出邊搬到 keeper；自指（K↔D 的 related）去掉；related 只在小 id 側
    assert (A, 'studies') in rels and rels[(A, 'studies')] == '被併者說'
    assert (D, 'related') not in rels and (K, 'related') not in rels
    assert (Z, 'related') not in rels                 # Z < K → 落在 Z
    assert get(root, 'Work', Z)['related_works'] == [{'id': K, 'relation': 'related', 'note': '與甲相關'}]
    assert (O, 'related') not in rels                 # O < K → 落在 O，與 O 原有的 preceded_by 並存
    o = {(r['id'], r['relation']) for r in get(root, 'Work', O)['related_works']}
    assert o == {(K, 'preceded_by'), (K, 'related')}
    # 他條（志書 CAT > K）的 related 指 D → 改指後小 id 在 K 側，搬到 K
    assert 'related_works' not in get(root, 'Work', CAT)
    assert (CAT, 'related') in rels
    # 著錄整節去重、欄位搬遷、准留之 _has_text 不丟
    assert len(k['indexed_by']) == 2 and k['contained_in'] == [{'id': C1, 'volume_index': 2}]
    assert k['period'] == 'ming' and k['_has_text'] is True
    assert k['additional_titles'] == ['新刊列國志傳']
    assert k['merged_in'][0]['id'] == D and k['merged_in'][0]['rule'] == '版本條改建Book'
    # 不寫舊格式
    for f in ('books', '_edition_count', 'classification'):
        assert f not in k
    assert k['authors'] == [{'name': '余邵魚', 'role': '撰', 'entity_id': E1}]   # 撰人不動
    # 存儲側引用改指
    assert get(root, 'Book', B2)['work_id'] == K
    assert get(root, 'Book', B2)['base_edition'][0]['work_id'] == K
    assert get(root, 'Collection', C1)['contains'][0]['work_id'] == K
    # 分類行改指並重排
    assert members(root, 'zm0002') == [[Z, '某志'], [K, '孫目']]
    # 全倉新格式、無懸空
    assert check_v2.main(['--root', root, '--summary']) == 0
    back = backrefs.scan(root)
    assert D not in back or all(w.endswith('merged_in') for w, _, _ in back[D])
    assert revisions_unchanged(root)


def revisions_unchanged(root):
    return all(json.load(open(f, encoding='utf-8')).get('revision') in (None, '1.0.0')
               for f in pathlib.Path(root).rglob('*.json') if 'classification' not in str(f))


def test_keeper_already_classified_drop_row_removed(tmp_path):
    root = str(tmp_path)
    make(root)
    open(os.path.join(root, 'classification/zongmu/members/zm0009.json'), 'w', encoding='utf-8').write(
        mergework.members_dump('zm0009', [[K, '某志']]))
    writes, notes = mergework.plan_classification(root, K, [D])
    assert writes['classification/zongmu/members/zm0002.json'] == ('zm0002', [[Z, '某志']])
    assert notes and '類不同須人看' in notes[0]


def test_plan_scalar_merge_skips_derived_and_legacy():
    keeper = {'id': K}
    dps = [(D, None, {'id': D, '_edition_count': 3, 'books': ['b'], 'classification': {}, '_has_collated': True,
                      'loss_status': 'lost'}, None)]
    moved, conflicts, nv = mergework.plan_scalar_merge(keeper, dps)
    assert nv == {'_has_collated': True, 'loss_status': 'lost'} and not conflicts


def test_backrefs_storage_side_places(tmp_path):
    root = str(tmp_path)
    make(root)
    back = backrefs.scan(root)
    places = {w for w, _, _ in back[D]}
    assert places == {'Work.related_works', 'Book.work_id', 'Book.base_edition', 'Collection.contains',
                      'classification.members'}
    assert {w for w, _, _ in back[E2]} == {'Work.authors.entity_id'}
    assert {w for w, _, _ in back[C1]} == {'Work.contained_in'}
    assert backrefs.main(['--root', root, '--audit']) == 0


def test_cli_entrypoint(tmp_path):
    make(str(tmp_path))
    r = subprocess.run([sys.executable, str(ROOT / '.claude/qa/mergework.py'), '--root', str(tmp_path),
                        '--keeper', K, '--drop', D, '--rule', 'r', '--why', 'w'],
                       capture_output=True, text=True)
    assert r.returncode == 0 and '乾跑' in r.stdout
