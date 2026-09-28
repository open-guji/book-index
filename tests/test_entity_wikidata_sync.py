"""S4b：Entity external_ids 补 wikidata_id/viaf_id 的回归（overview#159）。

覆盖三件：
  1. sync_wikidata_ids.parse_bindings() 把 SPARQL JSON 结果按 cbdb 值分组。
  2. sync_wikidata_ids.plan_write() 的判断逻辑（写入／一对多不写／既有值冲突不写／无匹配跳过）。
  3. sync_wikidata_ids.run() 对临时假仓的真实读写（jio.ROOT monkeypatch，仿 test_entity_dates.py）。
  4. verify.py 的 external_ids_ok() 校验（wikidata_id 形状、viaf_id 纯数字）。
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '.claude', 'qa'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '.claude', 'qa', 's4'))

import jio
import sync_wikidata_ids as sw
import verify


# ---------- parse_bindings() ----------

def _binding(qid, cbdb, viaf=None):
    b = {'item': {'value': f'http://www.wikidata.org/entity/{qid}'},
         'cbdb': {'value': cbdb}}
    if viaf is not None:
        b['viaf'] = {'value': viaf}
    return b


def test_parse_bindings_groups_by_cbdb():
    raw = {'results': {'bindings': [
        _binding('Q123', '456', '1234567'),
        _binding('Q999', '789'),
    ]}}
    by_cbdb = sw.parse_bindings(raw)
    assert by_cbdb['456'] == {'qids': {'Q123'}, 'viafs': {'1234567'}}
    assert by_cbdb['789'] == {'qids': {'Q999'}, 'viafs': set()}


def test_parse_bindings_multi_qid_for_same_cbdb():
    raw = {'results': {'bindings': [
        _binding('Q1', '111'),
        _binding('Q2', '111'),
    ]}}
    by_cbdb = sw.parse_bindings(raw)
    assert by_cbdb['111']['qids'] == {'Q1', 'Q2'}


# ---------- plan_write() ----------

def test_plan_write_no_cbdb_id():
    assert sw.plan_write({}, {}) == ('skip_no_cbdb', None)


def test_plan_write_no_match():
    d = {'external_ids': {'cbdb_id': 42}}
    assert sw.plan_write(d, {}) == ('skip_no_match', None)


def test_plan_write_writes_unique_match():
    d = {'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'viafs': set()}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'
    assert detail == {'wikidata_id': 'Q7', 'viaf_id': None}


def test_plan_write_writes_with_unique_viaf():
    d = {'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'viafs': {'99887766'}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'
    assert detail == {'wikidata_id': 'Q7', 'viaf_id': '99887766'}


def test_plan_write_skips_non_numeric_viaf():
    """VIAF 取到非纯数字值（脏数据）时不补，仍写 wikidata_id。"""
    d = {'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'viafs': {'abc123'}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'
    assert detail['viaf_id'] is None


def test_plan_write_ambiguous_viaf_not_written():
    """VIAF 不唯一时不补（宁缺不错）。"""
    d = {'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'viafs': {'111', '222'}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'
    assert detail['viaf_id'] is None


def test_plan_write_multi_qid_not_written():
    d = {'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q1', 'Q2'}, 'viafs': set()}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'conflict_multi_qid'
    assert detail == ['Q1', 'Q2']


def test_plan_write_existing_matches_new_skips():
    d = {'external_ids': {'cbdb_id': 42, 'wikidata_id': 'Q7'}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'viafs': set()}}
    assert sw.plan_write(d, by_cbdb) == ('skip_has_wikidata_id', None)


def test_plan_write_existing_mismatch_not_overwritten():
    """已有 wikidata_id 且与新取值不同：不覆盖，归入冲突清单。"""
    d = {'external_ids': {'cbdb_id': 42, 'wikidata_id': 'Q999'}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'viafs': set()}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'conflict_existing_mismatch'
    assert detail == ('Q999', 'Q7')


# ---------- run() on a temp fake repo ----------

def _write(root, rel, data):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def _fake_repo():
    tmp = tempfile.mkdtemp(prefix='sync_wikidata_test_')
    entities = {
        'zzzwd0001aaa': {'external_ids': {'cbdb_id': 1}},                       # 唯一匹配 -> 写
        'zzzwd0002bbb': {'external_ids': {'cbdb_id': 2}},                       # 一对多 -> 不写
        'zzzwd0003ccc': {'external_ids': {'cbdb_id': 3, 'wikidata_id': 'Q3'}},  # 已有且一致 -> 跳过
        'zzzwd0004ddd': {'external_ids': {'cbdb_id': 4, 'wikidata_id': 'Q999'}},  # 已有但冲突 -> 不写
        'zzzwd0005eee': {},                                                      # 无 cbdb_id -> 跳过
        'zzzwd0006fff': {'external_ids': {'cbdb_id': 99}},                      # 无匹配 -> 跳过
    }
    idx = {}
    for eid, base in entities.items():
        rel = f'Entity/{eid[-3]}/{eid[-2]}/{eid[-1]}/{eid}-測試.json'
        _write(tmp, rel, {'id': eid, 'type': 'entity', **base})
        idx[eid] = {'path': rel}
    os.makedirs(os.path.join(tmp, 'index', 'entities'))
    _write(tmp, 'index/entities/z.json', idx)
    return tmp


def _by_cbdb():
    return {
        '1': {'qids': {'Q1'}, 'viafs': {'10001'}},
        '2': {'qids': {'Q2a', 'Q2b'}, 'viafs': set()},
        '3': {'qids': {'Q3'}, 'viafs': set()},
        '4': {'qids': {'Q4'}, 'viafs': set()},
    }


def test_run_writes_only_unique_unconflicted(monkeypatch):
    tmp = _fake_repo()
    monkeypatch.setattr(jio, 'ROOT', tmp)

    counts, conflicts_multi, conflicts_mismatch, written = sw.run(_by_cbdb())

    assert counts['write'] == 1
    assert counts['write_with_viaf'] == 1
    assert counts['conflict_multi_qid'] == 1
    assert counts['conflict_existing_mismatch'] == 1
    assert counts['skip_has_wikidata_id'] == 1
    assert counts['skip_no_cbdb'] == 1
    assert counts['skip_no_match'] == 1
    assert [w[0] for w in written] == ['zzzwd0001aaa']
    assert [c[0] for c in conflicts_multi] == ['zzzwd0002bbb']
    assert [c[0] for c in conflicts_mismatch] == ['zzzwd0004ddd']

    d = json.load(open(os.path.join(
        tmp, 'Entity/a/a/a/zzzwd0001aaa-測試.json'), encoding='utf-8'))
    assert d['external_ids']['wikidata_id'] == 'Q1'
    assert d['external_ids']['viaf_id'] == '10001'

    # 未写入者原样不动
    d4 = json.load(open(os.path.join(
        tmp, 'Entity/d/d/d/zzzwd0004ddd-測試.json'), encoding='utf-8'))
    assert d4['external_ids']['wikidata_id'] == 'Q999'


def test_run_dry_run_does_not_write(monkeypatch):
    tmp = _fake_repo()
    monkeypatch.setattr(jio, 'ROOT', tmp)

    counts, _, _, written = sw.run(_by_cbdb(), dry_run=True)
    assert counts['write'] == 1

    d = json.load(open(os.path.join(
        tmp, 'Entity/a/a/a/zzzwd0001aaa-測試.json'), encoding='utf-8'))
    assert 'wikidata_id' not in d.get('external_ids', {})


def test_run_is_idempotent(monkeypatch):
    """已写入 wikidata_id 的条目重跑应保持不变（skip_has_wikidata_id）。"""
    tmp = _fake_repo()
    monkeypatch.setattr(jio, 'ROOT', tmp)

    sw.run(_by_cbdb())
    before = open(os.path.join(
        tmp, 'Entity/a/a/a/zzzwd0001aaa-測試.json'), encoding='utf-8').read()
    counts, _, _, written = sw.run(_by_cbdb())
    after = open(os.path.join(
        tmp, 'Entity/a/a/a/zzzwd0001aaa-測試.json'), encoding='utf-8').read()

    assert before == after
    assert counts['write'] == 0
    # 重跑后 zzzwd0001aaa（首轮新写）与 zzzwd0003ccc（本就已有且一致）皆归入此类
    assert counts['skip_has_wikidata_id'] == 2


def test_run_leaves_real_repo_untouched(monkeypatch):
    """monkeypatch jio.ROOT 后跑同步，不应碰到真仓（回归：migrate_dates 同款隔离测试）。"""
    real_root = os.path.dirname(HERE)
    assert os.path.isdir(os.path.join(real_root, '.git')), '须在真 book-index 仓下跑'

    tmp = _fake_repo()
    monkeypatch.setattr(jio, 'ROOT', tmp)
    sw.run(_by_cbdb())

    import subprocess
    out = subprocess.run(['git', 'status', '--porcelain'], cwd=real_root,
                          capture_output=True, text=True, check=True)
    assert 'zzzwd0001aaa' not in out.stdout


# ---------- FetchBlocked ----------

def test_fetch_wikidata_raises_on_429(monkeypatch):
    import urllib.error

    def _boom(*a, **k):
        raise urllib.error.HTTPError(
            sw.SPARQL_ENDPOINT, 429, 'Too Many Requests', {}, None)

    monkeypatch.setattr(sw.urllib.request, 'urlopen', _boom)
    try:
        sw.fetch_wikidata()
        assert False, '应抛出 FetchBlocked'
    except sw.FetchBlocked as e:
        assert e.code == 429


def test_fetch_wikidata_reraises_other_http_errors(monkeypatch):
    import urllib.error
    import io

    def _boom(*a, **k):
        raise urllib.error.HTTPError(
            sw.SPARQL_ENDPOINT, 500, 'Internal Server Error', {}, io.BytesIO(b''))

    monkeypatch.setattr(sw.urllib.request, 'urlopen', _boom)
    try:
        sw.fetch_wikidata()
        assert False, '非 403/429 不应被 FetchBlocked 吞掉'
    except sw.FetchBlocked:
        assert False, '500 不该算 FetchBlocked'
    except urllib.error.HTTPError:
        pass


# ---------- verify.py external_ids_ok() ----------

def test_external_ids_ok_none_when_absent():
    assert verify.external_ids_ok({}) is None


def test_external_ids_ok_accepts_valid():
    assert verify.external_ids_ok(
        {'external_ids': {'wikidata_id': 'Q123456', 'viaf_id': '1234567'}}) is None


def test_external_ids_ok_rejects_bad_qid():
    err = verify.external_ids_ok({'external_ids': {'wikidata_id': '123456'}})
    assert err is not None and 'wikidata_id' in err


def test_external_ids_ok_rejects_lowercase_q():
    err = verify.external_ids_ok({'external_ids': {'wikidata_id': 'q123'}})
    assert err is not None


def test_external_ids_ok_rejects_non_numeric_viaf():
    err = verify.external_ids_ok({'external_ids': {'viaf_id': 'VIAF123'}})
    assert err is not None and 'viaf_id' in err


def test_external_ids_ok_accepts_missing_subfields():
    assert verify.external_ids_ok({'external_ids': {'cbdb_id': 1}}) is None
