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
