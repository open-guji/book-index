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
    'collections', 'aliases', 'ai_note_fix', 'ai_note2', 'ai_note_periodfix', 'book_contained_in',
    'parent_works', 'parent_work', 'promoted_at',
    'has_text', 'has_image', 'related_to',
)
# 仅非 Entity 才算旧键（Entity 地名的 history[] 沿革是正当字段）；volume_count 仅 Book 层合法
NON_ENTITY_LEGACY = ('history', 'volume_count')
# authors[] 里已删的杂键（legacy.md §一）
AUTHOR_LEGACY = ('title_or_office', 'courtesy_name', 'alt_names', 'entity_basis', 'sources', 'birthplace',
                 'alias', 'additional_names', 'official', 'name_note')
AUTHOR_ROLE = 'authors[].role 为英文 author'
AUTHOR_KEYS = 'authors[] 杂键（cbdb_*／title_or_office 等）'
RES_GROUP_LABEL = 'resources[].group_label'
CONTAINED_STR = 'contained_in[] 字符串形'
EMPTY_REL_COLL = 'related_collections 空占位'
WORK_CLASSIF = 'Work classification 对象'
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
                if t != 'Entity':
                    for k in NON_ENTITY_LEGACY:
                        if k == 'volume_count' and t == 'Book':
                            continue            # Book.volume_count 是正当字段（book.md），只在 Work／Collection 算旧键
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
                if isinstance(rs, list) and any(isinstance(r, dict) and 'group_label' in r for r in rs):
                    hit(RES_GROUP_LABEL, p)
                au = j.get('authors')
                if isinstance(au, list):
                    if any(isinstance(a, dict) and a.get('role') == 'author' for a in au):
                        hit(AUTHOR_ROLE, p)
                    if any(isinstance(a, dict) and (any(k in a for k in AUTHOR_LEGACY) or any(k.startswith('cbdb_') for k in a))
                           for a in au):
                        hit(AUTHOR_KEYS, p)
                ci = j.get('contained_in')
                if isinstance(ci, list) and any(isinstance(x, str) for x in ci):
                    hit(CONTAINED_STR, p)
                if j.get('related_collections') == []:
                    hit(EMPTY_REL_COLL, p)
                if t == 'Work' and isinstance(j.get('classification'), dict):
                    hit(WORK_CLASSIF, p)
    return n, bad, cnt, ex


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('roots', nargs='+', help='库根目录（含 Work/Book/Collection/Entity）')
    ap.add_argument('--examples', type=int, default=0, help='每个非 0 项列出前 N 个文件')
    ap.add_argument('--json', action='store_true', help='输出 JSON')
    a = ap.parse_args()

    names = list(LEGACY_KEYS) + list(NON_ENTITY_LEGACY) + [OTHER_UNDERSCORE, UPPER_TYPE, RES_TYPE, RES_GROUP_LABEL, AUTHOR_ROLE, AUTHOR_KEYS,
             CONTAINED_STR, EMPTY_REL_COLL, WORK_CLASSIF]
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
