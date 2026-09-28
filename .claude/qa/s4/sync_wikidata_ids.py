#!/usr/bin/env python3
"""S4b：Entity external_ids 补 wikidata_id/viaf_id（经 CBDB ID 对 Wikidata，overview#159）。

跑法：
    # 1. 批量抓取 Wikidata（官方 SPARQL 端点，按本库已知 cbdb_id 分批 VALUES 查询＋
    #    限流重试；2026-09-28 协调者答复 overview#159：429 时等 ≥60 秒重试、最多 3 次，
    #    仍不通才停手——不是遇 429 立即停手，是重试用尽才停手。
    #    2026-09-28 实测两坑：① 全量 dump（`?item wdt:P497 ?cbdb` 不加 VALUES 过滤）
    #    ORDER BY 排序 41.8 万行撞 504 Gateway Timeout，非 429/403，重试逻辑接不住；
    #    ② 当前 WDQS 处于故障期，强制 1 请求/分钟，两次请求间隔不足一分钟即 429——
    #    故改按本库已知 cbdb_id 分批（VALUES 子句，命中式查询，无需排序全库），
    #    且批间主动等待 ≥61 秒，不能只在撞 429 后才补等待。）
    python3 .claude/qa/s4/sync_wikidata_ids.py --fetch --out /tmp/wd_p497.json

    # 2. 用抓到的缓存比对本库 cbdb_id，只出报告，不写档
    python3 .claude/qa/s4/sync_wikidata_ids.py --cache /tmp/wd_p497.json --dry-run

    # 3. 真写（可分片，分批提交用）
    python3 .claude/qa/s4/sync_wikidata_ids.py --cache /tmp/wd_p497.json --shard-start i --shard-end k

只写 Entity 活条（按 `index/entities/*.json` 为准——tombstone〔`retired: true`〕不在此索引
之列，故不会被碰到）的 `external_ids.wikidata_id` / `external_ids.viaf_id` 两个子键。
不动 Entity 其他字段（含 S4 刚加的 `dates`），不碰 Work／Book／Collection。

匹配规则（overview#159 §方法）：
  - 按 `cbdb_id` 精确对 Wikidata P497（CBDB ID）；
  - 一个 cbdb_id 对应多个 Wikidata Q 的**不写**，归入 conflict_multi_qid，列清单；
  - Entity 已有 `external_ids.wikidata_id` 的**不覆盖**；与新取值不一致者归入
    conflict_existing_mismatch，列清单；
  - 能同时取到唯一 VIAF（P214）值、且为纯数字者顺带补 `viaf_id`；VIAF 不唯一或非纯数字则不补。

用 `jio.py` 读写，保留原档缩进／换行风格，不动索引（external_ids 不在 verify.py 所比对的
索引栏位之列，机械写入不必回写索引）。
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # .claude/qa/，jio.py 所在
import jio

SPARQL_ENDPOINT = 'https://query.wikidata.org/sparql'
USER_AGENT = 'book-index-sync/1.0 (open-guji project; contact: sheldonli.dev@gmail.com)'
QID_RE = re.compile(r'Q(\d+)$')

DEFAULT_PAGE_SIZE = 5000
DEFAULT_BATCH_SIZE = 2000  # 按 cbdb_id 分批之批大小（VALUES 子句，POST，无 URL 长度顾虑）
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_WAIT = 65  # 秒，≥60（协调者 2026-09-28 答复 overview#159 之令）
DEFAULT_PACE_SECONDS = 61  # 批间主动等待，≥60（2026-09-28 实测：故障期强制 1 请求/分钟）


class FetchBlocked(Exception):
    """403／429 且重试用尽：调用方须停手，不再重试或改走镜像／第三方端点。"""

    def __init__(self, code, body):
        super().__init__(f'HTTP {code}')
        self.code = code
        self.body = body


def _page_query(page_size, offset):
    return f'''SELECT ?item ?cbdb ?viaf WHERE {{
  ?item wdt:P497 ?cbdb .
  OPTIONAL {{ ?item wdt:P214 ?viaf }}
}} ORDER BY ?item LIMIT {page_size} OFFSET {offset}'''


def build_values_query(cbdb_ids):
    """按一批 cbdb_id 构造 VALUES 命中式查询——只查这些值，不必排序／扫描全库 P497。"""
    vals = ' '.join(json.dumps(str(c)) for c in cbdb_ids)
    return f'''SELECT ?item ?cbdb ?viaf WHERE {{
  VALUES ?cbdb {{ {vals} }}
  ?item wdt:P497 ?cbdb .
  OPTIONAL {{ ?item wdt:P214 ?viaf }}
}}'''


def _run_query(query, max_retries, retry_wait, timeout):
    """POST 一次查询（避免大 VALUES 子句撑爆 GET 之 URL 长度上限），429/403 时等
    retry_wait 秒重试，最多 max_retries 次仍失败才抛 FetchBlocked。"""
    data = urllib.parse.urlencode({'query': query}).encode('utf-8')
    headers = {'Accept': 'application/sparql-results+json', 'User-Agent': USER_AGENT,
               'Content-Type': 'application/x-www-form-urlencoded'}
    last_blocked = None
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(SPARQL_ENDPOINT, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429):
                raise
            last_blocked = FetchBlocked(e.code, e.read().decode('utf-8', 'replace')[:2000])
            if attempt < max_retries:
                time.sleep(retry_wait)
    raise last_blocked


def fetch_wikidata(page_size=DEFAULT_PAGE_SIZE, max_retries=DEFAULT_MAX_RETRIES,
                    retry_wait=DEFAULT_RETRY_WAIT, timeout=300):
    """分页批量取 Wikidata 全部 P497（CBDB ID，可选 P214 VIAF），不逐条请求。

    按 `?item` 排序保证跨页稳定；每页 ≤`page_size` 行，单页 429/403 重试
    `max_retries` 次（间隔 `retry_wait` 秒）仍失败才抛 FetchBlocked——由调用方
    决定是否就此停手（overview#159 之令：重试用尽仍不通即停，不改走镜像／第三方端点）。

    2026-09-28 实测：全库 41.8 万行排序在当前端点撞 504 Gateway Timeout（非
    403/429，本函数不接此错），故 `--fetch` 默认改用 `fetch_wikidata_by_cbdb_ids()`；
    本函数留作全量场景可用的备选。
    """
    all_bindings = []
    offset = 0
    while True:
        page = _run_query(_page_query(page_size, offset), max_retries, retry_wait, timeout)
        bindings = page['results']['bindings']
        all_bindings.extend(bindings)
        if len(bindings) < page_size:
            break
        offset += page_size
    return {'head': {'vars': ['item', 'cbdb', 'viaf']}, 'results': {'bindings': all_bindings}}


def fetch_wikidata_by_cbdb_ids(cbdb_ids, batch_size=DEFAULT_BATCH_SIZE, pace_seconds=DEFAULT_PACE_SECONDS,
                                max_retries=DEFAULT_MAX_RETRIES, retry_wait=DEFAULT_RETRY_WAIT, timeout=120):
    """按本库已知 cbdb_id 分批查（VALUES 子句命中式查询），不逐条请求、不扫描全库 P497。

    批间主动等待 `pace_seconds` 秒（非撞 429 才等）——2026-09-28 实测：当前 WDQS
    处于故障期，强制 1 请求/分钟，间隔不足一分钟的下一请求必 429；单批 429/403
    另按 `max_retries`／`retry_wait` 重试，重试用尽才抛 FetchBlocked。
    """
    ids = sorted({str(c) for c in cbdb_ids})
    all_bindings = []
    for i in range(0, len(ids), batch_size):
        if i > 0:
            time.sleep(pace_seconds)
        batch = ids[i:i + batch_size]
        page = _run_query(build_values_query(batch), max_retries, retry_wait, timeout)
        all_bindings.extend(page['results']['bindings'])
    return {'head': {'vars': ['item', 'cbdb', 'viaf']}, 'results': {'bindings': all_bindings}}


def local_cbdb_ids():
    """从本库 Entity 活条读取全部 cbdb_id（`--fetch` 之输入，只用来分批查，不逐条请求）。"""
    ids = set()
    for _eid, rel in iter_entity_rels():
        d, _fmt = jio.load(rel)
        cb = (d.get('external_ids') or {}).get('cbdb_id')
        if cb is not None:
            ids.add(cb)
    return ids


def parse_bindings(raw):
    """把 SPARQL JSON 结果按 cbdb 值分组：{cbdb_str: {'qids': set(), 'viafs': set()}}。"""
    by_cbdb = {}
    for b in raw['results']['bindings']:
        cbdb = b['cbdb']['value'].strip()
        m = QID_RE.search(b['item']['value'])
        if not m:
            continue
        qid = 'Q' + m.group(1)
        viaf = (b.get('viaf') or {}).get('value')
        slot = by_cbdb.setdefault(cbdb, {'qids': set(), 'viafs': set()})
        slot['qids'].add(qid)
        if viaf:
            slot['viafs'].add(viaf)
    return by_cbdb


def plan_write(d, by_cbdb):
    """给一条 Entity 记录，回传 (action, detail)。

    action ∈ {'skip_no_cbdb', 'skip_no_match', 'skip_has_wikidata_id',
               'conflict_multi_qid', 'conflict_existing_mismatch', 'write'}
    """
    ext = d.get('external_ids') or {}
    cbdb_id = ext.get('cbdb_id')
    if cbdb_id is None:
        return 'skip_no_cbdb', None
    slot = by_cbdb.get(str(cbdb_id))
    if slot is None:
        return 'skip_no_match', None
    qids = slot['qids']
    if len(qids) > 1:
        return 'conflict_multi_qid', sorted(qids)
    qid = next(iter(qids))
    existing = ext.get('wikidata_id')
    if existing is not None:
        if existing != qid:
            return 'conflict_existing_mismatch', (existing, qid)
        return 'skip_has_wikidata_id', None
    viaf = None
    viafs = slot['viafs']
    if len(viafs) == 1:
        v = next(iter(viafs))
        if v.isdigit():
            viaf = v
    return 'write', {'wikidata_id': qid, 'viaf_id': viaf}


def iter_entity_rels(shard_start=None, shard_end=None):
    """按 `index/entities/*.json` 枚举活条的相对路径，可选按分片碼取一段区间。"""
    for f in sorted(glob.glob(os.path.join(jio.ROOT, 'index', 'entities', '*.json'))):
        shard = os.path.splitext(os.path.basename(f))[0]
        if shard_start and shard < shard_start:
            continue
        if shard_end and shard > shard_end:
            continue
        idx = json.load(open(f, encoding='utf-8'))
        for eid, ie in idx.items():
            yield eid, ie['path']


def run(by_cbdb, shard_start=None, shard_end=None, limit=None, dry_run=False):
    counts = {
        'skip_no_cbdb': 0, 'skip_no_match': 0, 'skip_has_wikidata_id': 0,
        'conflict_multi_qid': 0, 'conflict_existing_mismatch': 0, 'write': 0, 'write_with_viaf': 0,
    }
    conflicts_multi, conflicts_mismatch, written = [], [], []
    n_touched = 0
    for eid, rel in iter_entity_rels(shard_start, shard_end):
        d, fmt = jio.load(rel)
        action, detail = plan_write(d, by_cbdb)
        if action == 'conflict_multi_qid':
            counts[action] += 1
            conflicts_multi.append((eid, d.get('external_ids', {}).get('cbdb_id'), detail))
            continue
        if action == 'conflict_existing_mismatch':
            counts[action] += 1
            conflicts_mismatch.append((eid, detail[0], detail[1]))
            continue
        if action != 'write':
            counts[action] += 1
            continue
        if limit is not None and n_touched >= limit:
            continue
        counts['write'] += 1
        if detail.get('viaf_id'):
            counts['write_with_viaf'] += 1
        written.append((eid, detail['wikidata_id'], detail.get('viaf_id')))
        if not dry_run:
            d.setdefault('external_ids', {})['wikidata_id'] = detail['wikidata_id']
            if detail.get('viaf_id'):
                d['external_ids']['viaf_id'] = detail['viaf_id']
            jio.save(rel, d, fmt)
        n_touched += 1
    return counts, conflicts_multi, conflicts_mismatch, written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true', help='按本库已知 cbdb_id 分批抓取并落盘缓存，不比对不写档')
    ap.add_argument('--fetch-full-dump', action='store_true', help='改用全量分页 dump（fetch_wikidata()，慢且已知会 504，非默认）')
    ap.add_argument('--out', default=None, help='--fetch 时缓存写入路径')
    ap.add_argument('--page-size', type=int, default=DEFAULT_PAGE_SIZE, help='--fetch-full-dump 分页大小')
    ap.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='--fetch 按 cbdb_id 分批之批大小')
    ap.add_argument('--pace-seconds', type=float, default=DEFAULT_PACE_SECONDS, help='--fetch 批间主动等待秒数（≥60）')
    ap.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES, help='单批 429/403 重试次数上限')
    ap.add_argument('--retry-wait', type=float, default=DEFAULT_RETRY_WAIT, help='--fetch 重试前等待秒数（≥60）')
    ap.add_argument('--cache', default=None, help='已抓到的 SPARQL 结果 JSON 路径')
    ap.add_argument('--dry-run', action='store_true', help='只统计，不写档')
    ap.add_argument('--limit', type=int, default=None, help='只处理前 N 条待写者（试跑用）')
    ap.add_argument('--shard-start', default=None, help='只跑 index/entities/ 分片码 >= 此值')
    ap.add_argument('--shard-end', default=None, help='只跑 index/entities/ 分片码 <= 此值')
    a = ap.parse_args()

    if a.fetch:
        try:
            if a.fetch_full_dump:
                raw = fetch_wikidata(page_size=a.page_size, max_retries=a.max_retries, retry_wait=a.retry_wait)
            else:
                ids = local_cbdb_ids()
                print(f'本库已知 cbdb_id 共 {len(ids)} 条，分批（{a.batch_size}/批）查询…', file=sys.stderr)
                raw = fetch_wikidata_by_cbdb_ids(ids, batch_size=a.batch_size, pace_seconds=a.pace_seconds,
                                                  max_retries=a.max_retries, retry_wait=a.retry_wait)
        except FetchBlocked as e:
            print(f'FETCH BLOCKED：HTTP {e.code}——重试 {a.max_retries} 次（间隔 {a.retry_wait}s）仍不通，按令停手。响应节选：', file=sys.stderr)
            print(e.body, file=sys.stderr)
            sys.exit(2)
        if a.out:
            json.dump(raw, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f'已存至 {a.out}，共 {len(raw["results"]["bindings"])} 条 binding')
        else:
            json.dump(raw, sys.stdout, ensure_ascii=False)
        return

    if not a.cache:
        ap.error('须给 --fetch 或 --cache 之一')
    raw = json.load(open(a.cache, encoding='utf-8'))
    by_cbdb = parse_bindings(raw)

    counts, conflicts_multi, conflicts_mismatch, written = run(
        by_cbdb, a.shard_start, a.shard_end, a.limit, a.dry_run)

    print(f'无 cbdb_id，跳过                     {counts["skip_no_cbdb"]}')
    print(f'cbdb_id 无 Wikidata 匹配              {counts["skip_no_match"]}')
    print(f'已有 wikidata_id 且一致，跳过         {counts["skip_has_wikidata_id"]}')
    print(f'一对多（cbdb_id 对多个 Q），不写      {counts["conflict_multi_qid"]}')
    print(f'既有值与新取值冲突，不写              {counts["conflict_existing_mismatch"]}')
    print(f'写入 wikidata_id                      {counts["write"]}')
    print(f'其中顺带补 viaf_id                    {counts["write_with_viaf"]}')
    print(f'{"（--dry-run 未写档）" if a.dry_run else "已写入"}  共 {len(written)} 条')
    if conflicts_multi:
        print('\n一对多清单（前 20）：')
        for eid, cbdb_id, qids in conflicts_multi[:20]:
            print(f'  {eid}  cbdb_id={cbdb_id}  ->  {qids}')
    if conflicts_mismatch:
        print('\n既有值冲突清单（前 20）：')
        for eid, old, new in conflicts_mismatch[:20]:
            print(f'  {eid}  现有={old}  新取={new}')


if __name__ == '__main__':
    main()
