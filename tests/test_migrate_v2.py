"""build/migrate_v2.py：M0 盤點、M1 只增不刪、M2 規範化、冪等、不動 revision、保格式（schema-v2，overview#459）。"""
import json
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
sys.path.insert(0, str(ROOT / 'tests'))
import migrate_v2 as M  # noqa: E402
import v2sample as S  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return S.make(str(tmp_path / 'repo'))


def mig(root, steps, *extra):
    rd = os.path.join(root, '..', 'rep')
    rc = M.main(['--root', root, '--steps', steps, '--report-dir', rd, *extra])
    reps = {}
    for st in steps.split(','):
        p = os.path.join(rd, f'{st}.json')
        if os.path.exists(p):
            reps[st] = json.load(open(p, encoding='utf-8'))
    return rc, reps


def snapshot(root):
    out = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            out[os.path.relpath(p, root)] = open(p, encoding='utf-8').read()
    return out


def test_m0_inventory_ok_and_prints_tag(repo):
    rc, R = mig(repo, 'M0')
    assert rc == 0 and R['M0']['unknown_shapes'] == []
    assert R['M0']['records']['Work'] == 5 and len(R['M0']['sidecars']) == 1


def test_m0_unknown_shape_blocks(repo):
    d = S.read(repo, 'Work', S.W2)
    d['related_works'].append({'id': S.W5, 'relation': 'invented_word'})
    S.put(repo, 'Work', d)
    before = snapshot(repo)
    rc, R = mig(repo, 'M0,M1')
    assert rc == 1 and 'M1' not in R
    assert R['M0']['unknown_shapes'][0]['id'] == S.W2
    assert snapshot(repo) == before


def test_m0_duplicate_key_blocks(repo):
    p = S.path(repo, 'Work', S.W5)
    raw = open(p, encoding='utf-8').read().replace('"title": "某志"', '"ai_note": "一", "ai_note": "二", "title": "某志"')
    open(p, 'w', encoding='utf-8').write(raw)
    rc, R = mig(repo, 'M0')
    assert rc == 1 and 'duplicate keys' in R['M0']['unknown_shapes'][0]['shape']


def test_m1_additive(repo):
    rc, R = mig(repo, 'M1')
    assert rc == 0, R
    w1 = S.read(repo, 'Work', S.W1)
    assert w1['authors'][0]['role'] == '撰'                                  # ② 由 Entity 回填
    assert w1['revision'] == '1.0.3' and w1['revised_at'] == '2026-01-01'    # 不動 revision
    w2 = S.read(repo, 'Work', S.W2)
    assert w2['contained_in'] == [{'id': S.C1, 'group': '甲編'}]               # ① 叢編側獨有 → 成員側
    assert w2['related_works'][0]['note'] == '乙側說；甲側說'                   # ④ 規範側拼接
    b3 = S.read(repo, 'Book', S.B3)
    assert b3['contained_in'] == [{'id': S.C1, 'volume_index': 4}]                # sidecar 成員帶冊號補入
    b1 = S.read(repo, 'Book', S.B1)
    assert b1['contained_in'][0]['sub_items'] == ['附錄一', '考證']           # ⓪ sub_items
    ws = [r for r in b1['resources'] if r.get('id') == 'wikisource'][0]
    assert ws['url'] == 'https://zh.wikisource.org/wiki/甲書_(宋本)' and ws['types'] == ['text']
    w4 = S.read(repo, 'Work', S.W4)                                          # related 只在大 id 側：note 附在現有項
    assert '列本書於《丁書》之下' in w4['related_works'][0]['note'] or '列本書於' in w4['related_works'][0]['note']
    assert R['M1']['added']['⓪ Book.resources 維基文庫項（自 wiki_title）'] == 1
    assert R['M1']['protected_violations'] == []


def test_m2_normalise_and_conserve(repo):
    rc, R = mig(repo, 'M1,M2')
    assert rc == 0, R
    w3 = S.read(repo, 'Work', S.W3)
    rels = {(r['id'], r['relation']) for r in w3['related_works']}
    assert (S.W4, 'studies') in rels                                         # commentary_on → studies
    assert (S.W1, 'studies') in rels                                         # 只有反向形 → 規範側落筆
    w1 = S.read(repo, 'Work', S.W1)
    assert (S.W4, 'related') in {(r['id'], r['relation']) for r in w1['related_works']}   # related → 小 id 側
    assert all('title' not in r for r in w1['related_works'])
    assert 'title' not in S.read(repo, 'Collection', S.C1)['contained_works'][0]
    assert all('title' not in x for x in S.read(repo, 'Entity', S.E1)['works'])
    ec = R['M2']['edge_conservation']
    assert ec['old_not_rebuilt_vs_M2_input'] == 0 and ec['old_not_rebuilt_vs_M0'] == 0
    assert any(r.get('relation') == 'has_part' for r in w1['related_works'])   # 反向項留到 M3 才刪


def test_idempotent(repo):
    mig(repo, 'M0,M1,M2')
    once = snapshot(repo)
    rc, R = mig(repo, 'M1,M2')
    assert rc == 0 and R['M1']['records_changed'] == 0 and R['M2']['records_changed'] == 0
    assert {k: v for k, v in snapshot(repo).items() if not k.startswith('..')} == once


def test_format_preserved(repo):
    mig(repo, 'M1,M2')
    raw = open(S.path(repo, 'Work', S.W4), encoding='utf-8').read()
    assert raw == json.dumps(json.loads(raw), ensure_ascii=False, indent=1) + '\n'


def test_dry_run_writes_nothing(repo):
    before = snapshot(repo)
    rc, R = mig(repo, 'M1,M2', '--dry-run')
    assert rc == 0 and R['M1']['records_changed'] > 0
    assert snapshot(repo) == before


# ---------- 第二批：②b role 補「撰」、related_collections、M3、人工核清單 ----------
def _extra(repo):
    d = S.read(repo, 'Work', S.W5)
    d['authors'] = [{'name': '無名氏'}]                                    # 無 entity_id、缺 role
    S.put(repo, 'Work', d)
    S.put(repo, 'Collection', {'id': 'c0000000002', 'type': 'collection', 'title': '續編', 'revision': '1.0.0',
                               'related_collections': [{'collection_id': S.C1, 'type': 'continues', 'note': '續某叢書',
                                                        'title': '某叢書'}, {'work_id': S.W5, 'note': '指向作品'}]})
    b = S.read(repo, 'Book', S.B3)
    b['related_books'] = [S.B1]                                            # 對稱、只在大 id 側
    b['has_full_text'] = True
    S.put(repo, 'Book', b)


def test_m1_role_default(repo):
    _extra(repo)
    rc, R = mig(repo, 'M1')
    assert rc == 0
    assert S.read(repo, 'Work', S.W5)['authors'][0]['role'] == '撰'
    assert R['M1']['added']['②b Work.authors[].role 機械補「撰」（無 entity_id）'] == 1


def test_m2_symmetric_lists(repo):
    _extra(repo)
    rc, R = mig(repo, 'M1,M2')
    assert rc == 0, R
    c2 = S.read(repo, 'Collection', 'c0000000002')
    assert c2['related_collections'][0] == S.C1                             # 對象 → id 字串
    assert isinstance(c2['related_collections'][1], dict)                   # 指向非叢編者原樣保留
    assert R['M2']['symmetric_object_info'][0]['dropped'] == {'type': 'continues', 'note': '續某叢書'}
    assert len(R['M2']['symmetric_unconvertible']) == 1
    assert S.read(repo, 'Book', S.B1)['related_books'] == [S.B3]             # 小 id 側補寫
    assert S.read(repo, 'Collection', S.C1)['related_collections'] == ['c0000000002']


def test_m3_drops_reverse_and_derived(repo):
    _extra(repo)
    rc, R = mig(repo, 'M1,M2,M3')
    assert rc == 0, R
    w1 = S.read(repo, 'Work', S.W1)
    assert 'books' not in w1 and '_edition_count' not in w1
    assert {(r['id'], r['relation']) for r in w1['related_works']} == {(S.W4, 'related')}   # 反向詞項已刪
    assert w1['revision'] == '1.0.3' and w1['revised_at'] == '2026-01-01'
    assert 'works' not in S.read(repo, 'Entity', S.E1)
    c1 = S.read(repo, 'Collection', S.C1)
    assert not {'books', 'contained_works', '_member_count'} & set(c1)
    assert 'related_collections' in c1
    assert S.read(repo, 'Collection', 'c0000000002')['related_collections'] == [{'work_id': S.W5, 'note': '指向作品'}]
    b3 = S.read(repo, 'Book', S.B3)
    assert b3['related_books'] == [] and b3['_has_text'] is True and 'has_full_text' not in b3
    assert R['M3']['edge_conservation']['old_not_rebuilt'] == 0
    # W2 作者為空 → M1③ 按 Entity.works 補入作者（目錄總管 10-07），M3 刪 Entity.works 不丟
    assert S.read(repo, 'Work', S.W2)['authors'][0] == {
        'name': '張三', 'role': '注', 'entity_id': S.E1, 'note': '據 Entity.works 補入（schema-v2 遷移 M1）'}
    assert not R['M3']['lost']
    md = open(os.path.join(repo, '..', 'rep', '人工核清單.md'), encoding='utf-8').read()
    assert 'related_collections' in md
    desc = S.read(repo, 'Collection', 'c0000000002')['description']['text']
    assert desc == '與《某叢書》（c0000000001）關係：continues；續某叢書'                # 併進 description，不增欄位


def test_m3_then_strict_build_clean(repo):
    import build_derived as BD
    _extra(repo)
    mig(repo, 'M1,M2,M3')
    r, P = BD.run(repo, check_only=True, strict=True, quiet=True)
    assert r['fatal'] == [], r['fatal']
    assert {(x['id'], x['relation'], x['direction']) for x in P[f'entry/{S.W1}.json']['_related']} >= {
        (S.W2, 'has_part', 'in'), (S.W3, 'studied_by', 'in'), (S.W4, 'related', 'out')}


def test_m3_idempotent(repo):
    _extra(repo)
    mig(repo, 'M1,M2,M3')
    rc, R = mig(repo, 'M1,M2,M3')
    assert rc == 0 and all(R[s]['records_changed'] == 0 for s in ('M1', 'M2', 'M3'))


# ---------- M4：分類抽出 ----------
VOCAB = [{'cata_l1': '經部', 'cata_l2': '未分類'}, {'cata_l1': '經部', 'cata_l2': '易類'},
         {'cata_l1': '史部', 'cata_l2': '目錄類'}]


def _with_vocab(repo):
    with open(os.path.join(repo, 'classific.json'), 'w', encoding='utf-8') as f:
        json.dump(VOCAB, f, ensure_ascii=False)
    d = S.read(repo, 'Work', S.W5)
    d['classification'] = {'l1': '經部', 'l2': '未分類', 'l3': '', 'l4': '', 'basis': 'Q3 訂正', 'source': '某目'}
    S.put(repo, 'Work', d)


def test_m4_extract_and_strip(repo):
    import build_derived as BD
    _with_vocab(repo)
    rc, R = mig(repo, 'M4A,M4B')
    assert rc == 0, R
    tree = json.load(open(os.path.join(repo, 'classification', 'zongmu', 'tree.json'), encoding='utf-8'))
    assert [(n['id'], n['label'], n['parent']) for n in tree['nodes']] == [
        ('zm0001', '經部', None), ('zm0002', '易類', 'zm0001'), ('zm0003', '史部', None), ('zm0004', '目錄類', 'zm0003')]
    m = json.load(open(os.path.join(repo, 'classification', 'zongmu', 'members', 'zm0001.json'), encoding='utf-8'))
    assert m == {'node': 'zm0001', 'members': [[S.W5, '某目']]}                    # 未分類 → 父節點
    assert R['M4A']['basis_ledger'] == [{'id': S.W5, 'basis': 'Q3 訂正'}]
    w1 = S.read(repo, 'Work', S.W1)
    assert 'classification' not in w1 and w1['revision'] == '1.0.3' and w1['revised_at'] == '2026-01-01'
    r, P = BD.run(repo, check_only=True, quiet=True)                           # 樣本未跑 M1–M3，不用 --strict
    assert r['fatal'] == [] and r['classification']['problem_count'] == 0
    c = P[f'entry/{S.W1}.json']['_classifications'][0]
    assert (c['node'], c['l1'], c['l2'], c['source']) == ('zm0002', '經部', '易類', '樣本')
    assert 'classification' not in P[f'entry/{S.W1}.json']
    assert P[f'entry/{S.B1}.json']['_work']['cls'] == 'zm0002'                    # 卡片只寫節點 id
    assert {'cata_l1': '經部', 'cata_l2': '易類'} in P['classific.json']


def test_m4_idempotent_and_upsert(repo):
    _with_vocab(repo)
    mig(repo, 'M4')
    rc, R = mig(repo, 'M4A,M4B')
    assert rc == 0 and R['M4A']['records_changed'] == 0 and R['M4B']['records_changed'] == 0
    d = S.read(repo, 'Work', S.W2)                                              # 遷移後又進來一筆舊格式
    d['classification'] = {'l1': '史部', 'l2': '目錄類', 'l3': '', 'l4': '', 'basis': 'S', 'source': '新批'}
    S.put(repo, 'Work', d)
    rc, R = mig(repo, 'M4A,M4B')
    assert rc == 0 and R['M4A']['added']['成員行新增'] == 1
    assert 'classification' not in S.read(repo, 'Work', S.W2)


def test_m4_rejects_path_not_in_tree(repo):
    _with_vocab(repo)
    d = S.read(repo, 'Work', S.W2)
    d['classification'] = {'l1': '子部', 'l2': '無此類', 'source': 'x'}
    S.put(repo, 'Work', d)
    before = snapshot(repo)
    rc, R = mig(repo, 'M4A,M4B')
    assert rc == 1 and R['M4A']['unknown'][0]['id'] == S.W2 and 'M4B' not in R
    assert snapshot(repo) == before


def test_build_rejects_bad_classification(repo):
    import build_derived as BD
    _with_vocab(repo)
    mig(repo, 'M4')
    p = os.path.join(repo, 'classification', 'zongmu', 'members', 'zm0004.json')
    json.dump({'node': 'zm0004', 'members': [[S.W1, 'dup']]}, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    r, _ = BD.run(repo, check_only=True, quiet=True)
    assert any('分類檔' in f for f in r['fatal'])                                 # W1 同在 zm0002 與 zm0004


def test_m1_sidecar_dispositions(repo):
    """目錄總管 10-07 的人工核處置：冊號取並集、zhsy_id 補、舊 book_id 按 zhsy_id 改指、叢編側序號記 details。"""
    import build_derived as BD
    b1 = S.read(repo, 'Book', S.B1)
    b1['zhsy_id'] = 'ZHSY000001'
    S.put(repo, 'Book', b1)
    sc = os.path.join(os.path.dirname(S.path(repo, 'Collection', S.C1)), S.C1, 'zhsy', 'zhsy_book_mappings.json')
    os.makedirs(os.path.dirname(sc))
    json.dump({'collection_id': S.C1, 'mappings': [
        {'zhsy_id': 'ZHSY000001', 'book_id': 'b999999999', 'work_id': S.W1, 'title': '甲書宋本', 'section': '經'},
        {'zhsy_id': 'ZHSY000002', 'book_id': S.B3, 'work_id': S.W2, 'title': '乙書刊本', 'section': '經'}]},
        open(sc, 'w', encoding='utf-8'), ensure_ascii=False)
    vb = os.path.join(os.path.dirname(S.path(repo, 'Collection', S.C1)), S.C1, 'src', 'volume_book_mapping.json')
    d = json.load(open(vb, encoding='utf-8'))
    d['books'][0]['volumes'] = [3, 5]                                       # 記錄 3 → 並集 [3, 5]
    json.dump(d, open(vb, 'w', encoding='utf-8'), ensure_ascii=False)
    c = S.read(repo, 'Collection', S.C1)
    c['contained_works'][0]['volume_index'] = 7                              # 成員側無 → 直接補 7
    S.put(repo, 'Collection', c)
    w2 = S.read(repo, 'Work', S.W2)
    w2['contained_in'] = [{'id': S.C1, 'volume_index': '第2卷'}]              # 與叢編側 7 不一 → 7 記 details
    S.put(repo, 'Work', w2)
    rc, R = mig(repo, 'M1')
    assert rc == 0, R
    b1 = S.read(repo, 'Book', S.B1)
    assert b1['contained_in'][0]['volume_index'] == [3, 5]
    assert S.read(repo, 'Book', S.B3)['zhsy_id'] == 'ZHSY000002'
    assert R['M1']['items']['⓪ 改號'][0]['new'] == S.B1 and 'sidecar 列了不存在的 Book' not in R['M1']['data_errors']
    assert S.read(repo, 'Work', S.W2)['contained_in'][0] == {'id': S.C1, 'volume_index': '第2卷', 'group': '甲編',
                                                             'details': '叢編原序 7'}
    _, P = BD.run(repo, check_only=True, quiet=True)
    assert [m['id'] for m in P[f'members/{S.C1}/1.json'] if m['t'] == 'work'] == [S.W2]
    rc, R = mig(repo, 'M1')
    assert R['M1']['records_changed'] == 0
