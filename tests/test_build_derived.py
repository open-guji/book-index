"""build/build_derived.py：確定性、樞紐規則、分頁、關係展開、自帶校驗（schema-v2，overview#459）。"""
import json
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
sys.path.insert(0, str(ROOT / 'tests'))
import build_derived as BD  # noqa: E402
import v2sample as S  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return S.make(str(tmp_path / 'repo'))


def run(root, **kw):
    kw.setdefault('quiet', True)
    return BD.run(root, **kw)


def entry(out, i):
    return json.load(open(os.path.join(out, 'entry', f'{i}.json'), encoding='utf-8'))


def tree_bytes(out):
    got = {}
    for dp, _, fns in os.walk(out):
        for fn in fns:
            p = os.path.join(dp, fn)
            got[os.path.relpath(p, out)] = open(p, 'rb').read()
    return got


def test_deterministic_and_rerun_writes_nothing(repo, tmp_path):
    a, b = str(tmp_path / 'a'), str(tmp_path / 'b')
    r1, _ = run(repo, out_dir=a)
    run(repo, out_dir=b)
    assert tree_bytes(a) == tree_bytes(b)
    r3, _ = run(repo, out_dir=a)
    assert r3['write']['written'] == 0 and r3['write']['removed'] == 0
    assert r1['fatal'] == []


def test_stale_products_removed(repo, tmp_path):
    out = str(tmp_path / 'o')
    run(repo, out_dir=out)
    os.remove(S.path(repo, 'Book', S.B3))
    r, _ = run(repo, out_dir=out)
    assert not os.path.exists(os.path.join(out, 'entry', f'{S.B3}.json'))
    assert r['write']['removed'] >= 1


def test_count_conservation_and_sidecar_ignored(repo):
    r, prods = run(repo, check_only=True)
    assert r['entries'] == sum(r['records'].values()) == 10
    assert any(p.endswith('volume_book_mapping.json') for p in r['sidecars_ignored'])


def test_reverse_derived_and_legacy_union(repo):
    _, P = run(repo, check_only=True)
    w1 = P[f'entry/{S.W1}.json']
    assert [b['id'] for b in w1['_books']] == [S.B1, S.B2]          # 按年代
    assert w1['_edition_count'] == 2
    rel = {(x['id'], x['relation'], x['direction']) for x in w1['_related']}
    assert (S.W2, 'has_part', 'in') in rel                          # 兩側都寫 → 去重後一條
    assert (S.W3, 'studied_by', 'in') in rel                        # 只有反向形 → 照樣展開
    assert (S.W4, 'related', 'out') in rel                         # 對稱：小 id 側為 out
    note = [x for x in w1['_related'] if x['id'] == S.W2][0]['note']
    assert note == '乙側說；甲側說'                                    # 規範側 note 在前，簡單拼接
    w2 = P[f'entry/{S.W2}.json']
    assert {(x['id'], x['relation'], x['direction']) for x in w2['_related']} == {(S.W1, 'part_of', 'out')}
    w4 = P[f'entry/{S.W4}.json']
    assert (S.W3, 'studied_by', 'in') in {(x['id'], x['relation'], x['direction']) for x in w4['_related']}   # commentary_on→studies
    assert (S.W1, 'related', 'in') in {(x['id'], x['relation'], x['direction']) for x in w4['_related']}
    c = P[f'entry/{S.C1}.json']
    assert c['_member_count'] == 3 and c['_member_type'] == 'mixed'
    assert {(x['t'], x['id']) for x in P[f'members/{S.C1}/1.json']} == {('book', S.B1), ('book', S.B3), ('work', S.W2)}
    b3 = P[f'entry/{S.B3}.json']
    assert [x['id'] for x in b3['_collections']] == [S.C1]           # 叢編側獨有也反映到成員
    e = P[f'entry/{S.E1}.json']
    assert {(x['work_id'], x['role']) for x in e['_works']} == {(S.W1, '撰'), (S.W2, '注')}
    assert P[f'entry/{S.B1}.json']['_derived_by'][0]['id'] == S.B2
    assert P[f'entry/{S.B2}.json']['_lineage_refs'][S.B1]['title'] == '甲書宋本'
    assert P[f'lineage/{S.W1}.json']['edges'] == [{'from': S.B1, 'to': S.B2, 'rel': '翻刻', 'ref_type': 'book'}]
    w5 = P[f'entry/{S.W5}.json']
    assert w5['_member_catalog'] == {'total': 1, 'pages': 1}
    assert P[f'catalog/{S.W5}/1.json'][0]['id'] == S.W4
    assert P[f'entry/{S.W4}.json']['_catalogs'] == [{'bid': S.W5, 'title': '某志', 'section': '經部'}]


def test_old_underscore_fields_recomputed(repo):
    _, P = run(repo, check_only=True)
    assert P[f'entry/{S.C1}.json']['_member_count'] == 3               # 源裡寫 1，以生成值為準
    assert P[f'entry/{S.W1}.json']['_has_image'] is True


def test_hub_cards_and_rename_spread(repo):
    b = BD.Build(*_load(repo), hub=1)
    P = b.products()
    assert S.W1 in b.hubs and S.C1 in b.hubs
    assert P[f'entry/{S.B1}.json']['_work'] == {'id': S.W1, 'h': 1}
    assert P[f'entry/{S.B1}.json']['_collections'][0] == {'id': S.C1, 'h': 1, 'vol': 3}
    assert P['_hubs.json'][S.W1]['title'] == '甲書'
    res = BD.hub_check(b, P, limit=3)
    # 改樞紐名只牽動 _hubs＋自己＋（Work 時）作者人物頁的作品卡——同 F4-4 實測（國史經籍志 4 檔）
    assert res and all(x['ok'] for x in res), res
    assert {x['type']: x['changed'] for x in res} == {'Collection': 2, 'Work': 3, 'Entity': 2}


def test_pagination(repo, monkeypatch):
    monkeypatch.setattr(BD, 'PAGE', 2)
    monkeypatch.setattr(BD, 'MEMBER_HEAD', 1)
    _, P = run(repo, check_only=True)
    c = P[f'entry/{S.C1}.json']
    assert c['_member_pages'] == 2 and len(c['_members']) == 1
    assert len(P[f'members/{S.C1}/1.json']) == 2 and len(P[f'members/{S.C1}/2.json']) == 1
    w1 = P[f'entry/{S.W1}.json']
    assert w1['_related_total'] == 3 and len(w1['_related']) == 2
    assert len(P[f'related/{S.W1}/2.json']) == 1


def test_validation_unknown_underscore_and_dangling(repo):
    d = S.read(repo, 'Work', S.W2)
    d['_foo'] = 1
    d['related_works'].append({'id': 'w9999999999', 'relation': 'related'})
    S.put(repo, 'Work', d)
    r, _ = run(repo, check_only=True)
    assert any('_foo' in f for f in r['fatal'])
    assert r['dangling']['Work.related_works']['sample'] == [[S.W2, 'w9999999999']]
    assert r['source_fields']['legacy_underscore_fields']['Work._edition_count'] == 1
    assert run(repo, check_only=True, strict=True)[0]['fatal']


def test_ref_root_resolves_external_ids(repo, tmp_path):
    draft = str(tmp_path / 'draft')
    S.put(draft, 'Book', {'id': 'd000000001', 'type': 'book', 'title': '草稿本', 'work_id': S.W1})
    r, P = run(draft, ref_roots=[repo], check_only=True)
    assert r['dangling'] == {} and r['entries'] == 1
    assert P['entry/d000000001.json']['_work']['title'] == '甲書'


def _load(root):
    import v2common as V
    recs, _, _ = V.load_repo(root)
    return recs, None, None, None


def test_index_matches_entry_extractor_rules(repo, tmp_path):
    shards = BD.build_index(*_idx_args(repo))
    w1 = shards[f'index/works/{BD.shard_of(S.W1):x}.json'][S.W1]
    assert w1 == {'id': S.W1, 'title': '甲書', 'type': 'Work', 'path': os.path.relpath(S.path(repo, 'Work', S.W1), repo),
                  'author': '張三'}
    b1 = shards[f'index/books/{BD.shard_of(S.B1):x}.json'][S.B1]
    assert b1['sort_year'] == 1200 and b1['has_image'] is True and b1['work_id'] == S.W1
    e1 = shards[f'index/entities/{BD.shard_of(S.E1):x}.json'][S.E1]
    assert e1['type'] == 'entity' and e1['subtype'] == 'people'
    assert list(shards['index/collections.json']) == [S.C1]
    assert sum(len(v) for v in shards.values()) == 10


def test_write_index_keeps_shard_format(repo):
    shards = BD.build_index(*_idx_args(repo))
    rel = next(k for k in shards if k.startswith('index/works/'))
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(json.dumps({'x': {}}, ensure_ascii=False, indent=1))   # 縮排 1、無尾換行
    assert BD.write_index(repo, shards) == len(shards)
    raw = open(p, encoding='utf-8').read()
    assert raw == json.dumps(shards[rel], ensure_ascii=False, indent=1)
    assert BD.write_index(repo, shards) == 0                                 # 重寫零變動


def _idx_args(root):
    import v2common as V
    recs, _, _ = V.load_repo(root)
    return recs, {}


def test_load_promotions_reads_bim_shape(tmp_path):
    # bim promotion.py 写的是 {production_id, type, promoted_at}；舊式 to／字串也認
    (tmp_path / 'promotions.json').write_text(json.dumps({'version': 1, 'promotions': {
        'd1': {'production_id': 'p1', 'type': 'work', 'promoted_at': '2026-10-07'},
        'd2': {'to': 'p2'}, 'd3': 'p3', 'd4': {'type': 'work'}}}), encoding='utf-8')
    assert BD.load_promotions(str(tmp_path)) == {'d1': 'p1', 'd2': 'p2', 'd3': 'p3'}
