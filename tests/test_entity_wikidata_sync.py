"""S4b：Entity external_ids 补 wikidata_id/viaf_id 的回归（overview#159）。

覆盖：
  1. sync_wikidata_ids.cbdb_variants() 按 cbdb_id 生成原值＋补零 7 位两种查询字面量。
  2. sync_wikidata_ids.parse_bindings() 把 SPARQL JSON 结果按规范化后的 cbdb 值分组。
  3. sync_wikidata_ids.plan_write() 的判断逻辑（写入／一对多／标签不符／既有值冲突／无匹配）。
  4. sync_wikidata_ids.run() 对临时假仓的真实读写（jio.ROOT monkeypatch，仿 test_entity_dates.py）。
  5. 分页／分批抓取、限流重试、429 停手。
  6. verify.py 的 external_ids_ok() 校验（wikidata_id 形状、viaf_id 纯数字）。

2026-09-28 协调者验收 overview#159 不通过后订正：Wikidata 侧 P497 原值／补零 7 位
两种写法并存（苏轼 Q36020 记 "0003767"），原按 str(cbdb_id) 直接比对系统性漏配；
另发现按 cbdb_id 匹配可能撞见 Wikidata／CBDB 一侧既存错配（cbdb_id=126598 王恂
被同时挂着两个 cbdb_id 的 Q18654598／王振 认领），故加标签核验闸。
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


# ---------- cbdb_variants() ----------

def test_cbdb_variants_adds_zero_padded_form():
    assert sw.cbdb_variants([3767]) == ['0003767', '3767']


def test_cbdb_variants_no_change_when_already_seven_digits_or_longer():
    """7 位及以上的数字补零后与原值相同，去重后只剩一个。"""
    assert sw.cbdb_variants([1234567]) == ['1234567']
    assert sw.cbdb_variants([12345678]) == ['12345678']


def test_cbdb_variants_dedupes_across_inputs():
    assert sw.cbdb_variants([3767, '3767', 3767]) == ['0003767', '3767']


# ---------- build_values_query() ----------

def test_build_values_query_includes_both_padded_and_raw_forms():
    q = sw.build_values_query([3767])
    assert '"3767"' in q and '"0003767"' in q


def test_build_values_query_has_label_service_and_viaf_rank():
    q = sw.build_values_query([1])
    assert 'wdt:P497' in q
    assert 'SERVICE wikibase:label' in q
    assert 'p:P214' in q and 'ps:P214' in q and 'wikibase:rank' in q


# ---------- parse_bindings() ----------

def _binding(qid, cbdb, viaf=None, viaf_rank=None, label=None):
    b = {'item': {'value': f'http://www.wikidata.org/entity/{qid}'},
         'cbdb': {'value': cbdb}}
    if label is not None:
        b['itemLabel'] = {'value': label}
    if viaf is not None:
        b['viaf'] = {'value': viaf}
    if viaf_rank is not None:
        b['viafRank'] = {'value': viaf_rank}
    return b


def test_parse_bindings_groups_by_cbdb():
    raw = {'results': {'bindings': [
        _binding('Q123', '456', viaf='1234567', viaf_rank=sw.PREFERRED_RANK, label='张三'),
        _binding('Q999', '789', label='李四'),
    ]}}
    by_cbdb = sw.parse_bindings(raw)
    assert by_cbdb['456'] == {
        'qids': {'Q123'}, 'labels': {'Q123': {'张三'}}, 'viafs': {'Q123': {('1234567', sw.PREFERRED_RANK)}},
    }
    assert by_cbdb['789'] == {'qids': {'Q999'}, 'labels': {'Q999': {'李四'}}, 'viafs': {}}


def test_parse_bindings_normalizes_zero_padded_cbdb():
    """回归：苏轼 Q36020 的 P497 是 "0003767"，须与本库无前导零的 3767 归并同一组。"""
    raw = {'results': {'bindings': [_binding('Q36020', '0003767', label='蘇軾')]}}
    by_cbdb = sw.parse_bindings(raw)
    assert '3767' in by_cbdb and '0003767' not in by_cbdb
    assert by_cbdb['3767']['qids'] == {'Q36020'}


def test_parse_bindings_multi_qid_for_same_cbdb():
    raw = {'results': {'bindings': [
        _binding('Q1', '111'),
        _binding('Q2', '111'),
    ]}}
    by_cbdb = sw.parse_bindings(raw)
    assert by_cbdb['111']['qids'] == {'Q1', 'Q2'}


# ---------- _pick_viaf() ----------

def test_pick_viaf_empty():
    assert sw._pick_viaf(set()) is None


def test_pick_viaf_single_value_no_rank_info():
    assert sw._pick_viaf({('12345', None)}) == '12345'


def test_pick_viaf_prefers_preferred_rank():
    entries = {('11111111', 'http://wikiba.se/ontology#NormalRank'),
               ('22222222', sw.PREFERRED_RANK)}
    assert sw._pick_viaf(entries) == '22222222'


def test_pick_viaf_ambiguous_without_preferred_not_picked():
    """回归：Q465282 两条 P214，wdt: 只吐出畸形值那条；本函数在拿到两条 normal-rank
    分歧值时也不该瞎猜，宁可不补。"""
    entries = {('11111111', 'http://wikiba.se/ontology#NormalRank'),
               ('22222222', 'http://wikiba.se/ontology#NormalRank')}
    assert sw._pick_viaf(entries) is None


def test_pick_viaf_rejects_implausibly_long_value():
    """回归：Q465282（劉向，cbdb_id=450753）实测畸形值 22 位，现行 VIAF 至多 9～10 位。"""
    assert sw._pick_viaf({('7682148997701659870000', sw.PREFERRED_RANK)}) is None


# ---------- plan_write() ----------

def test_plan_write_no_cbdb_id():
    assert sw.plan_write({}, {}) == ('skip_no_cbdb', None)


def test_plan_write_no_match():
    d = {'external_ids': {'cbdb_id': 42}}
    assert sw.plan_write(d, {}) == ('skip_no_match', None)


def test_plan_write_writes_unique_match_with_matching_label():
    d = {'primary_name': '張三', 'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {'Q7': {'張三'}}, 'viafs': {}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'
    assert detail == {'wikidata_id': 'Q7', 'viaf_id': None}


def test_plan_write_matches_via_legacy_string_alt_name():
    """回归：库中有遗留的 alt_names 纯字符串写法（如 hixhd2h9bixi-僧肇.json 的
    "僧"），非 {"name":...} 字典形，_label_matches 须两者都认，不得因此崩掉。"""
    d = {'primary_name': '僧肇', 'alt_names': ['僧'], 'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {'Q7': {'僧'}}, 'viafs': {}}}
    action, _detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'


def test_plan_write_matches_via_alt_name():
    d = {'primary_name': '張三', 'alt_names': [{'name': '子明'}], 'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {'Q7': {'子明'}}, 'viafs': {}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'


def test_plan_write_writes_with_unique_viaf():
    d = {'primary_name': '張三', 'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {'Q7': {'張三'}}, 'viafs': {'Q7': {('99887766', None)}}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'
    assert detail == {'wikidata_id': 'Q7', 'viaf_id': '99887766'}


def test_plan_write_label_mismatch_not_written():
    """回归：cbdb_id=126598 王恂被系统性漏配到标签「王振」的 Q18654598
    （该条目同时挂了两个 cbdb_id，overview#159 协调者验收所报）。"""
    d = {'primary_name': '王恂', 'alt_names': [{'name': '振'}], 'external_ids': {'cbdb_id': 126598}}
    by_cbdb = {'126598': {'qids': {'Q18654598'}, 'labels': {'Q18654598': {'王振'}}, 'viafs': {}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'label_mismatch'
    assert detail == (['王振'], '王恂')


def test_plan_write_label_missing_treated_as_mismatch():
    """取不到标签时也不写（拿不准不写，不因为"没有反证"就当作过）。"""
    d = {'primary_name': '張三', 'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {}, 'viafs': {}}}
    action, _detail = sw.plan_write(d, by_cbdb)
    assert action == 'label_mismatch'


def test_plan_write_multi_qid_not_written():
    d = {'primary_name': '張三', 'external_ids': {'cbdb_id': 42}}
    by_cbdb = {'42': {'qids': {'Q1', 'Q2'}, 'labels': {}, 'viafs': {}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'conflict_multi_qid'
    assert detail == ['Q1', 'Q2']


def test_plan_write_existing_matches_new_skips():
    d = {'primary_name': '張三', 'external_ids': {'cbdb_id': 42, 'wikidata_id': 'Q7'}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {'Q7': {'張三'}}, 'viafs': {}}}
    assert sw.plan_write(d, by_cbdb) == ('skip_has_wikidata_id', None)


def test_plan_write_existing_mismatch_not_overwritten():
    """已有 wikidata_id 且与新取值不同：不覆盖，归入冲突清单。"""
    d = {'primary_name': '張三', 'external_ids': {'cbdb_id': 42, 'wikidata_id': 'Q999'}}
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {'Q7': {'張三'}}, 'viafs': {}}}
    action, detail = sw.plan_write(d, by_cbdb)
    assert action == 'conflict_existing_mismatch'
    assert detail == ('Q999', 'Q7')


def test_plan_write_normalizes_zero_padded_lookup_key():
    """本库 cbdb_id 本就不带前导零；by_cbdb 的键（parse_bindings 输出）同样规范化过，
    plan_write 须用同一把钥匙查——这里直接构造已规范化的 by_cbdb 验证查找不出错。"""
    d = {'primary_name': '張三', 'external_ids': {'cbdb_id': '0042'}}  # 极端情况：cbdb_id 本身含前导零
    by_cbdb = {'42': {'qids': {'Q7'}, 'labels': {'Q7': {'張三'}}, 'viafs': {}}}
    action, _detail = sw.plan_write(d, by_cbdb)
    assert action == 'write'


# ---------- run() on a temp fake repo ----------

def _write(root, rel, data):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def _fake_repo():
    tmp = tempfile.mkdtemp(prefix='sync_wikidata_test_')
    entities = {
        'zzzwd0001aaa': {'primary_name': '甲', 'external_ids': {'cbdb_id': 1}},       # 唯一匹配、标签对上 -> 写
        'zzzwd0002bbb': {'primary_name': '乙', 'external_ids': {'cbdb_id': 2}},       # 一对多 -> 不写
        'zzzwd0003ccc': {'primary_name': '丙', 'external_ids': {'cbdb_id': 3, 'wikidata_id': 'Q3'}},  # 已有且一致 -> 跳过
        'zzzwd0004ddd': {'primary_name': '丁', 'external_ids': {'cbdb_id': 4, 'wikidata_id': 'Q999'}},  # 已有但冲突 -> 不写
        'zzzwd0005eee': {'primary_name': '戊'},                                        # 无 cbdb_id -> 跳过
        'zzzwd0006fff': {'primary_name': '己', 'external_ids': {'cbdb_id': 99}},      # 无匹配 -> 跳过
        'zzzwd0007ggg': {'primary_name': '庚', 'external_ids': {'cbdb_id': 7}},       # 唯一匹配但标签不符 -> 不写
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
        '1': {'qids': {'Q1'}, 'labels': {'Q1': {'甲'}}, 'viafs': {'Q1': {('10001', None)}}},
        '2': {'qids': {'Q2a', 'Q2b'}, 'labels': {}, 'viafs': {}},
        '3': {'qids': {'Q3'}, 'labels': {'Q3': {'丙'}}, 'viafs': {}},
        '4': {'qids': {'Q4'}, 'labels': {'Q4': {'丁'}}, 'viafs': {}},
        '7': {'qids': {'Q7'}, 'labels': {'Q7': {'不是庚'}}, 'viafs': {}},
    }


def test_run_writes_only_unique_unconflicted_and_label_matched(monkeypatch):
    tmp = _fake_repo()
    monkeypatch.setattr(jio, 'ROOT', tmp)

    counts, conflicts_multi, label_mismatches, conflicts_mismatch, written = sw.run(_by_cbdb())

    assert counts['write'] == 1
    assert counts['write_with_viaf'] == 1
    assert counts['conflict_multi_qid'] == 1
    assert counts['label_mismatch'] == 1
    assert counts['conflict_existing_mismatch'] == 1
    assert counts['skip_has_wikidata_id'] == 1
    assert counts['skip_no_cbdb'] == 1
    assert counts['skip_no_match'] == 1
    assert [w[0] for w in written] == ['zzzwd0001aaa']
    assert [c[0] for c in conflicts_multi] == ['zzzwd0002bbb']
    assert [c[0] for c in label_mismatches] == ['zzzwd0007ggg']
    assert [c[0] for c in conflicts_mismatch] == ['zzzwd0004ddd']

    d = json.load(open(os.path.join(
        tmp, 'Entity/a/a/a/zzzwd0001aaa-測試.json'), encoding='utf-8'))
    assert d['external_ids']['wikidata_id'] == 'Q1'
    assert d['external_ids']['viaf_id'] == '10001'

    # 标签不符者原样不动
    d7 = json.load(open(os.path.join(
        tmp, 'Entity/g/g/g/zzzwd0007ggg-測試.json'), encoding='utf-8'))
    assert 'wikidata_id' not in d7.get('external_ids', {})

    # 未写入者原样不动
    d4 = json.load(open(os.path.join(
        tmp, 'Entity/d/d/d/zzzwd0004ddd-測試.json'), encoding='utf-8'))
    assert d4['external_ids']['wikidata_id'] == 'Q999'


def test_run_dry_run_does_not_write(monkeypatch):
    tmp = _fake_repo()
    monkeypatch.setattr(jio, 'ROOT', tmp)

    counts, _, _, _, written = sw.run(_by_cbdb(), dry_run=True)
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
    counts, _, _, _, written = sw.run(_by_cbdb())
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


# ---------- FetchBlocked / 分页 / 分批 ----------

def test_fetch_wikidata_retries_then_raises_after_exhausted(monkeypatch):
    """协调者 2026-09-28 答复 overview#159：429 时重试（间隔 ≥60s），重试用尽仍不通才停手。"""
    import io
    import urllib.error

    calls = {'n': 0}

    def _boom(*a, **k):
        calls['n'] += 1
        raise urllib.error.HTTPError(
            sw.SPARQL_ENDPOINT, 429, 'Too Many Requests', {}, io.BytesIO(b'rate limited'))

    sleeps = []
    monkeypatch.setattr(sw.urllib.request, 'urlopen', _boom)
    monkeypatch.setattr(sw.time, 'sleep', lambda s: sleeps.append(s))
    try:
        sw.fetch_wikidata(max_retries=3, retry_wait=65)
        assert False, '重试用尽仍应抛出 FetchBlocked'
    except sw.FetchBlocked as e:
        assert e.code == 429
    assert calls['n'] == 3, '应恰好试满 max_retries 次'
    assert sleeps == [65, 65], '两次重试之间各等待一次，共 max_retries-1 次'


def test_fetch_wikidata_succeeds_after_one_retry(monkeypatch):
    """第一次 429、第二次成功：不应把中途的失败误判为最终停手。"""
    import io
    import urllib.error

    calls = {'n': 0}
    ok_body = json.dumps({'results': {'bindings': []}}).encode('utf-8')

    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _flaky(*a, **k):
        calls['n'] += 1
        if calls['n'] == 1:
            raise urllib.error.HTTPError(
                sw.SPARQL_ENDPOINT, 429, 'Too Many Requests', {}, io.BytesIO(b'rate limited'))
        return _Resp(ok_body)

    monkeypatch.setattr(sw.urllib.request, 'urlopen', _flaky)
    monkeypatch.setattr(sw.time, 'sleep', lambda s: None)
    raw = sw.fetch_wikidata(max_retries=3, retry_wait=65)
    assert raw == {'head': {'vars': ['item', 'cbdb', 'viaf']}, 'results': {'bindings': []}}
    assert calls['n'] == 2


def test_fetch_wikidata_paginates_until_short_page(monkeypatch):
    """每页 page_size 条，取到不足一页即停止翻页。"""
    import io

    pages = [
        {'results': {'bindings': [_binding('Q1', '1'), _binding('Q2', '2')]}},
        {'results': {'bindings': [_binding('Q3', '3')]}},  # 不足 page_size，最后一页
    ]
    calls = {'n': 0}

    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _paged(*a, **k):
        body = json.dumps(pages[calls['n']]).encode('utf-8')
        calls['n'] += 1
        return _Resp(body)

    monkeypatch.setattr(sw.urllib.request, 'urlopen', _paged)
    raw = sw.fetch_wikidata(page_size=2)
    assert calls['n'] == 2
    assert len(raw['results']['bindings']) == 3


def test_fetch_wikidata_by_cbdb_ids_paces_between_batches_not_before_first(monkeypatch):
    """批间主动等待 pace_seconds，且第一批前不等待（2026-09-28 实测：故障期强制 1 req/min）。
    分批以本库 cbdb_id（原值，未展开变体）为单位——5 个 id、批大小 4 -> 2 批（4+1）；
    补零变体的展开在 build_values_query() 内，不影响分批数。"""
    import io

    calls = {'n': 0}
    sleeps = []

    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _ok(*a, **k):
        calls['n'] += 1
        return _Resp(json.dumps({'results': {'bindings': []}}).encode('utf-8'))

    monkeypatch.setattr(sw.urllib.request, 'urlopen', _ok)
    monkeypatch.setattr(sw.time, 'sleep', lambda s: sleeps.append(s))

    sw.fetch_wikidata_by_cbdb_ids([str(i) for i in range(1, 6)], batch_size=4, pace_seconds=61)

    assert calls['n'] == 2  # 5 个 id，批大小 4 -> 2 批（4+1）
    assert sleeps == [61]  # 批间等待一次，第一批前不等


def test_fetch_wikidata_by_cbdb_ids_dedupes_ids(monkeypatch):
    import io

    seen_queries = []

    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _ok(req, *a, **k):
        seen_queries.append(req.data.decode('utf-8'))
        return _Resp(json.dumps({'results': {'bindings': []}}).encode('utf-8'))

    monkeypatch.setattr(sw.urllib.request, 'urlopen', _ok)
    sw.fetch_wikidata_by_cbdb_ids([1, 1, 2, '2'], batch_size=10, pace_seconds=61)

    assert len(seen_queries) == 1
    assert seen_queries[0].count('%221%22') == 1  # urlencode 后的 "1"，去重只出现一次


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
