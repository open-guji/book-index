#!/usr/bin/env python3
"""S5c 第二轮补漏（overview#217，协调者验收反馈 2026-09-28 16:37Z）：

第一轮全量重算只接受了 #214 已确认的 161 条，把重算命中之其余 75 条一律当作与
#214 报告「50 条假阳性」同源而按下不表——协调者指出这个判断不成立，其中至少
7 条原文明写、未含「傳鈔／影鈔／覆刊／重刊」等描述底本的限定语，理应径改：
  - 988fz7bksh／988g7kutjb／988fzsjpqj／988g66adji／988g35z11e／988g2yskjn
    （协调者逐条指出）
  - 988g2got1n（本道自查同源新例：「寫刊」与「本」字间插入紀年语，未被
    backfill_edition_type.classify() 原「寫刻|寫刊」例外之相邻子串匹配覆盖，
    同属「裸寫」pipeline bug 的变体）
其余重算命中之记录（含 8 条「排印本」归属两可、3 条 #214 原存疑、988g481zb6
「景寫…重刻…本」技法叙述两解皆通者）本轮仍不动，详见 issue 评论。

用法：python3 .claude/qa/s5/s5c_q4_book_field_fix_round2.py [--dry-run]
"""
import argparse, csv, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE_DATE = '2026-09-28'


def load_fix():
    out = {}
    with open(os.path.join(HERE, 'q4_edition_type_fix_round2.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[r['id']] = (r['old'], r['new'], r['理由'])
    return out


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

    fix = load_fix()
    paths = find_files_by_id(set(fix))
    n_ok = n_skip = 0
    for bid, (old, new, why) in fix.items():
        rel = paths.get(bid)
        if not rel:
            print(f'警告：{bid} 掃不到檔案')
            n_skip += 1
            continue
        d, fmt = jio.load(rel)
        if d.get('edition_type') != old:
            print(f'跳过 {bid}：edition_type 现值 {d.get("edition_type")!r} 与预期旧值 {old!r} 不符')
            n_skip += 1
            continue
        if a.dry_run:
            n_ok += 1
            continue
        d['edition_type'] = new
        jio.addnote(d, f'{NOTE_DATE} overview#217 第二轮补漏（协调者验收反馈）：edition_type 由「{old}」改「{new}」，'
                        f'原文「{d.get("edition")}」——{why}')
        jio.save(rel, d, fmt)
        n_ok += 1

    print(f'edition_type 改动（第二轮） {n_ok}')
    print(f'跳过                        {n_skip}')
    if a.dry_run:
        print('（--dry-run，未写盘）')


if __name__ == '__main__':
    main()
