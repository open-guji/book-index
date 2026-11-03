#!/usr/bin/env python3
"""删并条历史字段（用户 11-03 定，可做可不做第 5 组）：先把账写进 ledger，再从记录里删掉。

  python3 .claude/qa/merge-history/strip.py [--root 数据仓根] [--ledger 输出 tsv] [--apply]

删的字段：顶层 merged_in／merged_from／merge_history，indexed_by[].merged_from。
账的格式同 export.py（每行一个「旧号 → 留存号」）。不加 --apply 只出数、不写。
文件按 json.dumps(indent=2, ensure_ascii=False) + 换行写回（全库现行格式；个别缩进不同的文件顺手统一）。
"""
import argparse, collections, glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export import COLS, clean, rows_of, ROOT  # noqa: E402

TOP = ('merged_in', 'merged_from', 'merge_history')


def strip(d):
    hit = False
    for k in TOP:
        if k in d:
            del d[k]; hit = True
    for ib in d.get('indexed_by') or []:
        if isinstance(ib, dict) and 'merged_from' in ib:
            del ib['merged_from']; hit = True
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--ledger', required=True)
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    rows, changed, skipped = [], [], []
    for t in ('Work', 'Book', 'Collection', 'Entity'):
        for p in sorted(glob.glob(os.path.join(a.root, t, '**', '*.json'), recursive=True)):
            with open(p, encoding='utf-8') as f:
                s = f.read()
            d = json.loads(s)
            r = list(rows_of(d, t))
            if not strip(d):
                continue
            if json.dumps(json.loads(s), ensure_ascii=False, indent=2) + '\n' != s:
                skipped.append(p)
            rows.extend(r); changed.append((p, d))
    print('改', len(changed), '其中缩进不规范、顺手统一', len(skipped), '账', len(rows),
          dict(collections.Counter((x[2], x[3]) for x in rows)))
    for p in skipped[:20]:
        print('  统一缩进', p)
    if not a.apply:
        return
    with open(a.ledger, 'w', encoding='utf-8') as f:
        f.write('\t'.join(COLS) + '\n')
        for x in rows:
            f.write('\t'.join(clean(v) for v in x) + '\n')
    for p, d in changed:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
