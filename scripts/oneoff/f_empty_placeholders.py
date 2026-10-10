#!/usr/bin/env python3
"""F（overview#508）：删空占位值。

删除（仅这几类，其它一律不动）：
- Work／Book 的 `authors[].dynasty` 为空串 `""` 或 `null`；
- Work 顶层 `dynasty` 为 `null`（或空串）；
- Collection 的 `related_collections: []`。

`dynasty` 有值的一律不动。读写走 build/v2common.py 的保格式函数，不改键序与缩进，
不改 revision／revised_at、文件名、id。

用法（仓根目录）：
    python3 scripts/oneoff/f_empty_placeholders.py --dry-run   # 只统计
    python3 scripts/oneoff/f_empty_placeholders.py             # 真跑
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'build'))
import v2common as V  # noqa: E402


def _empty(v):
    return v is None or v == ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.join(HERE, '..', '..'))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    occ = collections.Counter()
    recs = collections.defaultdict(set)
    bad_fmt = []
    files = 0

    for typ in ('Work', 'Book', 'Collection'):
        for p in sorted(V.iter_json(root, typ)):
            if not V.is_record_path(root, p):
                continue
            raw = open(p, encoding='utf-8').read()
            d = json.loads(raw)
            rid = d.get('id')
            hits = []  # (kind, label)
            if typ in ('Work', 'Book'):
                if 'dynasty' in d and _empty(d['dynasty']):
                    hits.append(('top', repr(d['dynasty'])))
                    del d['dynasty']
                for au in d.get('authors') or []:
                    if isinstance(au, dict) and 'dynasty' in au and _empty(au['dynasty']):
                        hits.append(('authors', repr(au['dynasty'])))
                        del au['dynasty']
            if typ == 'Collection' and d.get('related_collections') == []:
                hits.append(('rc_empty', '[]'))
                del d['related_collections']
            if not hits:
                continue
            fmt = V.detect_format(raw, json.loads(raw))
            if fmt is None:
                bad_fmt.append(os.path.relpath(p, root))
                continue
            files += 1
            for kind, label in hits:
                key = (typ, kind, label)
                occ[key] += 1
                recs[key].add(rid)
            if not a.dry_run:
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(V.dump(d, fmt))

    mode = 'DRY-RUN' if a.dry_run else 'WRITE'
    print(f'[{mode}] 改动文件 {files}')
    for key in sorted(occ):
        print(f'  {key[0]:10s} {key[1]:10s} {key[2]:8s} 处 {occ[key]:6d}  记录 {len(recs[key])}')
    if bad_fmt:
        print('保格式失败（未动）:', *bad_fmt, sep='\n  ')
    return 1 if bad_fmt else 0


if __name__ == '__main__':
    sys.exit(main())
