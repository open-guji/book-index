#!/usr/bin/env python3
"""S4 新 schema 吸收④：Entity.dates 迁移（overview#143）。

跑法：
    python3 .claude/qa/s4/migrate_dates.py --dry-run           # 只報數，不寫
    python3 .claude/qa/s4/migrate_dates.py --limit 200         # 只跑前 200 條（試跑）
    python3 .claude/qa/s4/migrate_dates.py --shard-start i --shard-end k  # 只跑指定分片區間（分批提交用）
    python3 .claude/qa/s4/migrate_dates.py                     # 全量

只寫 Entity 活条（按 `index/entities/*.json` 為準——tombstone〔`retired: true`〕
不在此索引之列，故不會被碰到）的 `dates` 欄；`birth_year`／`death_year` 原樣保留，
不刪、不改。已有 `dates` 欄的條目略過（冪等，可重跑）。

兩類寫入，見 overview#143：

  1. 機械遷移：有 `birth_year` 或 `death_year` 者 -> `dates.birth`/`dates.death`，
     `basis` 記 `"現行字段"`。

  2. 補 `floruit`：`cbdb_id` 存在、`birth_year`／`death_year` 全缺、且 `dynasty_basis`
     帶 `cbdb:index_year=NNNN` 者——這是 2026-09-06 CBDB enrich 落盤時已寫入的原文
     （見 `dynasty_basis` 欄，如 `"cbdb:index_year=1019→北宋"`），是庫內既有的 CBDB
     快取，不在線抓 CBDB。取該年當活動年參考點，`dates.floruit=[年,年]`，
     `basis` 記 `"cbdb:index_year"`；取不到旁證的不補、`dates` 缺省。

用 `jio.py` 讀寫，保留原檔縮排／換行風格，不動索引（`dates` 不在 `verify.py`
所比對的索引欄位之列，機械遷移不必回寫索引）。
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # .claude/qa/，jio.py 所在
import jio

INDEX_YEAR_RE = re.compile(r'index_year=(-?\d+)')


def plan_dates(d):
    """給一條 Entity 記錄，回傳該寫入的 `dates` 值；已有 `dates` 或無可迁移之資料則回傳 None。"""
    if 'dates' in d:
        return None
    by, dy = d.get('birth_year'), d.get('death_year')
    if by is not None or dy is not None:
        return {'birth': by, 'death': dy, 'floruit': None, 'basis': '現行字段'}
    cbdb_id = (d.get('external_ids') or {}).get('cbdb_id')
    if cbdb_id:
        m = INDEX_YEAR_RE.search(d.get('dynasty_basis') or '')
        if m:
            y = int(m.group(1))
            return {'birth': None, 'death': None, 'floruit': [y, y], 'basis': 'cbdb:index_year'}
    return None


def iter_entity_rels(shard_start=None, shard_end=None):
    """按 `index/entities/*.json` 枚舉活条的相對路徑（tombstone 不在此索引之列）。
    可選按檔名（分片碼，`index/entities/<碼>.json`）取一段區間，供分批提交用。"""
    for f in sorted(glob.glob(os.path.join(jio.ROOT, 'index', 'entities', '*.json'))):
        shard = os.path.splitext(os.path.basename(f))[0]
        if shard_start and shard < shard_start:
            continue
        if shard_end and shard > shard_end:
            continue
        idx = json.load(open(f, encoding='utf-8'))
        for eid, ie in idx.items():
            yield eid, ie['path']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只統計，不寫檔')
    ap.add_argument('--limit', type=int, default=None, help='只處理前 N 條符合條件者（試跑用）')
    ap.add_argument('--shard-start', default=None, help='只跑 index/entities/ 分片碼 >= 此值')
    ap.add_argument('--shard-end', default=None, help='只跑 index/entities/ 分片碼 <= 此值')
    a = ap.parse_args()

    n_mech, n_floruit, n_skip_has, n_none, n_touched = 0, 0, 0, 0, 0
    touched = []
    for eid, rel in iter_entity_rels(a.shard_start, a.shard_end):
        d, fmt = jio.load(rel)
        if 'dates' in d:
            n_skip_has += 1
            continue
        dates = plan_dates(d)
        if dates is None:
            n_none += 1
            continue
        if a.limit is not None and n_touched >= a.limit:
            break
        if dates['basis'] == '現行字段':
            n_mech += 1
        else:
            n_floruit += 1
        touched.append((eid, dates))
        if not a.dry_run:
            d['dates'] = dates
            jio.save(rel, d, fmt)
        n_touched += 1

    print(f'機械遷移（birth_year/death_year -> dates）  {n_mech}')
    print(f'補 floruit（cbdb:index_year）                {n_floruit}')
    print(f'已有 dates，略過                             {n_skip_has}')
    print(f'無可迁移之資料                               {n_none}')
    print(f'{"（--dry-run 未寫檔）" if a.dry_run else "已寫入"}  共 {n_touched} 條')
    if a.dry_run or a.limit:
        for eid, dates in touched[:30]:
            print('  ', eid, dates)


if __name__ == '__main__':
    main()
