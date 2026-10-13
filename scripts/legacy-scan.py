#!/usr/bin/env python3
"""legacy-scan：数据旧键计数（Schema落地 V3 / S2 闸，overview#568 B6）。

遍历给定库根目录下 Work／Book／Collection／Entity 的全部源 JSON，统计已退役的旧键。
全表为 0 才算过 S2 闸；有任一非 0 退出码为 1。只读，不改任何文件。

用法：
    python3 scripts/legacy-scan.py . ../book-index-draft
    python3 scripts/legacy-scan.py ../book-index-draft --examples 3   # 每项列前 3 个文件
    python3 scripts/legacy-scan.py . --json
"""
import argparse
import collections
import json
import os
import sys

TYPES = ('Work', 'Book', 'Collection', 'Entity')
# 已退役的顶层键（出处：schema/legacy.md、entity.md、CHANGELOG）
LEGACY_KEYS = (
    'birth_year', 'death_year', 'cbdb_aliases', 'cbdb_aliases_note',
    '_has_text', '_has_collated', '_has_full_text',
    'books', 'works', 'contained_works', '_promoted_to', 'promoted_to',
)
OTHER_UNDERSCORE = '_* 其他下划线键'
UPPER_TYPE = '顶层 type 非小写'
RES_TYPE = 'resources[].type'


def scan(root, examples):
    cnt = collections.Counter()
    ex = collections.defaultdict(list)
    n = bad = 0

    def hit(name, path):
        cnt[name] += 1
        if len(ex[name]) < examples:
            ex[name].append(os.path.relpath(path, root))

    for t in TYPES:
        for d, _, fs in os.walk(os.path.join(root, t)):
            for f in fs:
                if not f.endswith('.json'):
                    continue
                p = os.path.join(d, f)
                try:
                    with open(p, encoding='utf-8') as fh:
                        j = json.load(fh)
                except Exception:
                    bad += 1
                    continue
                if not isinstance(j, dict):
                    continue
                n += 1
                for k in LEGACY_KEYS:
                    if k in j:
                        hit(k, p)
                if any(k.startswith('_') and k not in LEGACY_KEYS for k in j):
                    hit(OTHER_UNDERSCORE, p)
                ty = j.get('type')
                if isinstance(ty, str) and ty != ty.lower():
                    hit(UPPER_TYPE, p)
                rs = j.get('resources')
                if isinstance(rs, list) and any(isinstance(r, dict) and 'type' in r for r in rs):
                    hit(RES_TYPE, p)
    return n, bad, cnt, ex


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('roots', nargs='+', help='库根目录（含 Work/Book/Collection/Entity）')
    ap.add_argument('--examples', type=int, default=0, help='每个非 0 项列出前 N 个文件')
    ap.add_argument('--json', action='store_true', help='输出 JSON')
    a = ap.parse_args()

    names = list(LEGACY_KEYS) + [OTHER_UNDERSCORE, UPPER_TYPE, RES_TYPE]
    results = {}
    for r in a.roots:
        if not os.path.isdir(r):
            print(f'不是目录：{r}', file=sys.stderr)
            return 2
        results[r] = scan(r, a.examples)
    total = sum(sum(c.values()) for _, _, c, _ in results.values())
    bad_total = sum(b for _, b, _, _ in results.values())
    if a.json:
        print(json.dumps({r: {'files': n, 'unreadable': bad, 'counts': dict(c)} for r, (n, bad, c, _) in results.items()},
                         ensure_ascii=False, indent=2))
    else:
        labels = {r: os.path.basename(os.path.abspath(r)) for r in results}
        w = max(len(x) for x in names)
        print(f'{"旧键".ljust(w)}  ' + '  '.join(f'{labels[r]:>18}' for r in results))
        for nm in names:
            print(f'{nm.ljust(w)}  ' + '  '.join(f'{results[r][2][nm]:>18}' for r in results))
        print(f'{"（扫描文件数）".ljust(w)}  ' + '  '.join(f'{results[r][0]:>18}' for r in results))
        for r, (n, bad, c, ex) in results.items():
            if bad:
                print(f'注意：{r} 有 {bad} 个文件读不出 JSON（未计入）', file=sys.stderr)
            for nm, fl in ex.items():
                for f in fl:
                    print(f'  [{labels[r]}] {nm}: {f}')
    print('结果：' + ('全 0，S2 闸通过' if total == 0 and not bad_total else f'旧键共 {total} 处／不可读 {bad_total}，未过'))
    return 0 if total == 0 and not bad_total else 1


if __name__ == '__main__':
    sys.exit(main())
