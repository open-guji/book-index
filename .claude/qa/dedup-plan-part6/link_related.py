#!/usr/bin/env python3
"""去重方案部分 6：同题同版本名、但总目是不同源记录的 Collection 补 related_collections 互链（不并）。

    python3 .claude/qa/dedup-plan-part6/link_related.py <pairs.tsv> [--apply]

pairs.tsv 每行「a<TAB>b<TAB>理由」。按 V07 只存 id 较小一侧；已有则跳过；revision 升 patch。
"""
import argparse, datetime, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'build')]
import v2common as V  # noqa: E402

TODAY = datetime.date.today().isoformat()


def col_path(i):
    hits = glob.glob(os.path.join(ROOT, 'Collection', *i[-3:], i + '-*.json'))
    assert len(hits) == 1, (i, hits)
    return hits[0]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('pairs'); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    rows = [l.rstrip('\n').split('\t') for l in open(a.pairs, encoding='utf-8') if l.strip() and not l.startswith('#')]
    print('载入 %d 对' % len(rows)); assert rows
    n = 0
    for x, y, *_ in rows:
        lo, hi = sorted((x, y))
        p = col_path(lo); raw = open(p, encoding='utf-8').read(); d = json.loads(raw); fmt = V.detect_format(raw, d)
        for i in (lo, hi):
            assert not json.load(open(col_path(i), encoding='utf-8')).get('merged_into'), ('墓碑', i)
        r = d.setdefault('related_collections', [])
        if hi in r:
            continue
        r.append(hi); n += 1
        a_, b_, c_ = (int(t) for t in (d.get('revision') or '1.0.0').split('.'))
        d['revision'] = '%d.%d.%d' % (a_, b_, c_ + 1); d['revised_at'] = TODAY
        print(lo, '→', hi, d.get('title'))
        if a.apply:
            open(p, 'w', encoding='utf-8', newline='\n').write(V.dump(d, fmt))
    print('新增互链 %d' % n)


if __name__ == '__main__':
    main()
