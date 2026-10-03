#!/usr/bin/env python3
"""S5d·「排印本」归属定案（overview#233，据 #230 用户答复：「归鉛印本。将来有现代出版
社的，非铅印，新增印刷本。」）：

S5c 第二轮补漏（overview#217）曾发现全库有 8 条「排印本」归属两可、按下不表，
交由用户裁决。#230 用户答复：排印本一律归鉛印本；并新增「印刷本」词，专收现代出版社、
非鉛印之印本（见 SCHEMA.md、classify() 同步改动）。

本脚本只改这 8 条既有之 `edition_type`（原皆为占位之「刻本」），`ai_note` 记依据；
不涉词表增补（那两处在 backfill_edition_type.py／verify.py／SCHEMA.md 手改，非本脚本之责）。

用法：python3 .claude/qa/s5/s5d_q4_paiyinben_lead_print.py [--dry-run]
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

NOTE_DATE = '2026-09-28'
NOTE = f'{NOTE_DATE} overview#233（据 #230 用户定）：排印本归鉛印本，edition_type 由「刻本」改「鉛印本」'

TARGET_IDS = {
    '988fz20jk9', '988g1d1o29', '988g1cqfif', '988g43df5v',
    '988g4lsf7v', '988g5yhfyo', '988g4m3nrc', '96mn3rv4sg',
}


def find_files_by_id(ids_wanted):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True):
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        if d.get('id') in ids_wanted:
            out[d['id']] = rel
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    paths = find_files_by_id(TARGET_IDS)
    n_ok = n_skip = 0
    rows = []
    for bid in sorted(TARGET_IDS):
        rel = paths.get(bid)
        if not rel:
            print(f'警告：{bid} 掃不到檔案')
            n_skip += 1
            continue
        d, fmt = jio.load(rel)
        old = d.get('edition_type')
        if old != '刻本':
            print(f'跳过 {bid}：edition_type 现值 {old!r} 与预期旧值「刻本」不符')
            n_skip += 1
            continue
        rows.append((bid, d.get('edition'), old, '鉛印本'))
        if a.dry_run:
            n_ok += 1
            continue
        d['edition_type'] = '鉛印本'
        jio.addnote(d, NOTE)
        jio.save(rel, d, fmt)
        n_ok += 1

    for bid, edition, old, new in rows:
        print(f'  {bid}  {old}→{new}  原文「{edition}」')
    print(f'edition_type 改动 {n_ok}')
    print(f'跳过             {n_skip}')
    if a.dry_run:
        print('（--dry-run，未写盘）')


if __name__ == '__main__':
    main()
