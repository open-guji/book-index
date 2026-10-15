#!/usr/bin/env python3
"""build-id-table：旧→新 ID 全表（GUJI-355）。

遍历库根下 Work／Book／Collection／Entity 的 detail 文件，收集并条墓碑
（顶层 `merged_into`，字符串或 `{id}` 对象），把 merged_into 链折叠到最终留存 id，
防环、查悬空与跨类型。只读，不改任何库文件；同一份数据产物逐字节相同（键排序）。

用法：
    python3 scripts/build-id-table.py . --out-dir /tmp/idtable
产物（--out-dir）：
    redirects.json   {"version":1,"redirects":{旧id: 终点id}}   ← 与 web#437 读表格式一致
    redirects.csv    旧id,终点id,类型,跳数,旧文件名
    anomalies.json   {"cycle":[…],"dangling":[…],"cross_type":[…],"self":[…],"ends_at_promoted":[…]}
异常条目不进 redirects。有异常时退出码 1（--allow-anomalies 则为 0）。
升格墓碑（promoted_to）不进表：draft→正式的跳转走 promotions.json。
"""
import argparse
import csv
import json
import os
import re
import sys

TYPES = ('Work', 'Book', 'Collection', 'Entity')
_ID_RE = re.compile(r'^([0-9a-z]+)-')


def merged_into(doc):
    m = doc.get('merged_into') if isinstance(doc, dict) else None
    if isinstance(m, str):
        return m
    if isinstance(m, dict) and isinstance(m.get('id'), str):
        return m['id']
    return ''


def promoted_to(doc):
    v = (doc.get('promoted_to') or doc.get('_promoted_to')) if isinstance(doc, dict) else ''
    return v if isinstance(v, str) else ''


def scan(root):
    """→ (ids: {id: 类型}, edges: {旧id: (目标, 类型, 文件名)}, promoted: set(id))"""
    ids, edges, promoted = {}, {}, set()
    for t in TYPES:
        base = os.path.join(root, t)
        for dp, _dn, fns in os.walk(base):
            for fn in fns:
                if not fn.endswith('.json'):
                    continue
                m = _ID_RE.match(fn)
                if not m:
                    continue
                rid = m.group(1)
                ids[rid] = t
                with open(os.path.join(dp, fn), encoding='utf-8') as f:
                    text = f.read()
                if 'merged_into' not in text and 'promoted_to' not in text:
                    continue
                doc = json.loads(text)
                if promoted_to(doc):
                    promoted.add(rid)
                tgt = merged_into(doc)
                if tgt:
                    edges[rid] = (tgt, t, fn)
    return ids, edges, promoted


def fold(ids, edges, promoted):
    """折叠链 → (redirects: {旧: (终点, 跳数)}, anomalies)"""
    anomalies = {k: [] for k in ('cycle', 'dangling', 'cross_type', 'self', 'ends_at_promoted')}
    out = {}
    for old in sorted(edges):
        tgt0 = edges[old][0]
        if tgt0 == old:
            anomalies['self'].append({'id': old})
            continue
        seen, cur, hops, bad = [old], old, 0, None
        while cur in edges:
            nxt = edges[cur][0]
            if nxt in seen:
                bad = ('cycle', {'id': old, 'path': seen + [nxt]})
                break
            seen.append(nxt)
            cur, hops = nxt, hops + 1
        if bad is None:
            if cur not in ids:
                bad = ('dangling', {'id': old, 'path': seen})
            elif ids[cur] != edges[old][1]:
                bad = ('cross_type', {'id': old, 'path': seen, 'from': edges[old][1], 'to': ids[cur]})
            elif cur in promoted:
                bad = ('ends_at_promoted', {'id': old, 'path': seen})
        if bad:
            anomalies[bad[0]].append(bad[1])
        else:
            out[old] = (cur, hops)
    return out, anomalies


def write(out_dir, redirects, edges, anomalies):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'redirects.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'version': 1, 'redirects': {k: v[0] for k, v in sorted(redirects.items())}},
                  f, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        f.write('\n')
    with open(os.path.join(out_dir, 'redirects.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['old_id', 'final_id', 'type', 'hops', 'file'])
        for k, (to, hops) in sorted(redirects.items()):
            w.writerow([k, to, edges[k][1], hops, edges[k][2]])
    with open(os.path.join(out_dir, 'anomalies.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(anomalies, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write('\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('root', help='库根目录（含 Work/Book/Collection/Entity）')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--allow-anomalies', action='store_true')
    a = ap.parse_args(argv)
    ids, edges, promoted = scan(a.root)
    redirects, anomalies = fold(ids, edges, promoted)
    write(a.out_dir, redirects, edges, anomalies)
    n_bad = sum(len(v) for v in anomalies.values())
    multi = sum(1 for _, h in redirects.values() if h > 1)
    print(f'墓碑边 {len(edges)}；入表 {len(redirects)}（其中多跳折叠 {multi}）；异常 {n_bad} '
          + ' '.join(f'{k}={len(v)}' for k, v in anomalies.items()), file=sys.stderr)
    return 1 if (n_bad and not a.allow_anomalies) else 0


if __name__ == '__main__':
    sys.exit(main())
