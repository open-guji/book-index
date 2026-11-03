#!/usr/bin/env python3
"""把记录里的并条历史字段导出成一份并条账（删字段之前跑；用户 11-03 定删 merged_in／merged_from／merge_history）。

  python3 .claude/qa/merge-history/export.py            # 写 .claude/qa/purge-tombstones/ledger/history-<日期>.tsv

每行一个「旧号 → 留存号」：
  old_id   被并方 id（merge_history 早期账没有被并方 id 时为空，只留名）
  keeper   写着这条账的记录 id（它自己若已成墓碑，终点由并条账表沿链解）
  type     keeper 的类型
  field    来源字段：merged_in／merged_from／merge_history／indexed_by.merged_from
  title    被并方题名或人名
  at／by／rule／why  merged_in 原有的时间、执行者、规则、理由（merge_history 的 date／reason 也放这两列）
  extra    其余子键原样（JSON）
"""
import datetime, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
COLS = ['old_id', 'keeper', 'type', 'field', 'title', 'at', 'by', 'rule', 'why', 'extra']


def clean(v):
    return '' if v is None else str(v).replace('\t', ' ').replace('\n', ' ')


def rows_of(d, t):
    k = d['id']
    for e in d.get('merged_in') or []:
        if isinstance(e, dict):
            rest = {x: y for x, y in e.items() if x not in ('id', 'title', 'primary_name', 'at', 'by', 'rule', 'why')}
            yield [e.get('id'), k, t, 'merged_in', e.get('title') or e.get('primary_name'), e.get('at'), e.get('by'),
                   e.get('rule'), e.get('why'), json.dumps(rest, ensure_ascii=False) if rest else '']
        else:
            yield [None, k, t, 'merged_in', None, None, None, None, None, json.dumps(e, ensure_ascii=False)]
    for e in d.get('merged_from') or []:
        if isinstance(e, str):
            yield [e, k, t, 'merged_from', None, None, None, None, None, '']
        else:
            yield [None, k, t, 'merged_from', None, None, None, None, None, json.dumps(e, ensure_ascii=False)]
    for e in d.get('merge_history') or []:
        if isinstance(e, dict):
            rest = {x: y for x, y in e.items() if x not in ('merged_from', 'title', 'primary_name', 'date', 'reason')}
            mf = e.get('merged_from')
            yield [mf if isinstance(mf, str) else None, k, t, 'merge_history', e.get('title') or e.get('primary_name'),
                   e.get('date'), None, None, e.get('reason'),
                   json.dumps(dict(rest, **({'merged_from': mf} if mf is not None and not isinstance(mf, str) else {})),
                              ensure_ascii=False) if rest or (mf is not None and not isinstance(mf, str)) else '']
    for i, ib in enumerate(d.get('indexed_by') or []):
        if isinstance(ib, dict) and ib.get('merged_from'):
            mf = ib['merged_from']
            for x in (mf if isinstance(mf, list) else [mf]):
                yield [x if isinstance(x, str) else None, k, t, 'indexed_by.merged_from', ib.get('title_info'),
                       None, None, None, None, json.dumps({'indexed_by_seq': i, 'source_bid': ib.get('source_bid'),
                                                           **({} if isinstance(x, str) else {'value': x})}, ensure_ascii=False)]


def main():
    out = []
    for t in ('Work', 'Book', 'Collection', 'Entity'):
        for p in sorted(glob.glob(os.path.join(ROOT, t, '**', '*.json'), recursive=True)):
            with open(p, encoding='utf-8') as f:
                d = json.load(f)
            out.extend(rows_of(d, t))
    led = os.path.join(ROOT, '.claude/qa/purge-tombstones/ledger')
    fn = os.path.join(led, 'history-%s.tsv' % datetime.date.today().strftime('%Y%m%d'))
    with open(fn, 'w', encoding='utf-8') as f:
        f.write('\t'.join(COLS) + '\n')
        for r in out:
            f.write('\t'.join(clean(x) for x in r) + '\n')
    import collections
    print(fn, len(out), dict(collections.Counter((r[2], r[3]) for r in out)))


if __name__ == '__main__':
    main()
