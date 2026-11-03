#!/usr/bin/env python3
"""版本关系产物等价比对（06 稿步 2／3 验收）。

对「版本关系字段涉及的 Book 及其 Work」，用指定的 build 目录在指定的库根上算出这些产物：
  Book：卡片 from、_derived_by、_lineage_refs、_related、_lineage_graph_ref
  Work：lineage/<wid>.json 的内容（节点＋边）
写成 JSON，再用 --diff 比两份。步 2：旧 build＋旧数据 vs 新 build＋旧数据，应逐字节相同；
步 3：迁移前 vs 迁移后（新 build），差异须落在已知清单内（见 06 稿 §三）。

  python3 .claude/qa/lineage_equiv.py dump --root . [--build build] --out /tmp/a.json
  python3 .claude/qa/lineage_equiv.py diff /tmp/a.json /tmp/b.json
"""
import argparse, importlib.util, json, os, sys


def load_build(build_dir):
    build_dir = os.path.abspath(build_dir)
    sys.path.insert(0, build_dir)
    for m in ('v2common', 'names', 'build_derived'):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location('build_derived', os.path.join(build_dir, 'build_derived.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules['build_derived'] = mod
    spec.loader.exec_module(mod)
    return mod


def involved(R):
    """Book 记录里任一版本关系字段涉及的 id（本身＋对象）。"""
    ids = set()
    for bid, b in R['Book'].items():
        lin = b.get('lineage') if isinstance(b.get('lineage'), dict) else {}
        refs = []
        for x in (lin.get('derived_from') or []) + (lin.get('related_to') or []):
            if isinstance(x, dict):
                refs.append(x.get('ref') or x.get('book_id'))
        for x in b.get('base_edition') or []:
            if isinstance(x, dict):
                refs.append(x.get('book_id'))
        for x in b.get('related_books') or []:
            refs.append(x.get('book_id') if isinstance(x, dict) else x)
        refs = [r for r in refs if isinstance(r, str) and r in R['Book']]
        if refs or lin.get('derived_from') or lin.get('related_to') or b.get('base_edition') or b.get('related_books'):
            ids.add(bid)
            ids.update(refs)
    return ids


def dump(root, build_dir, out):
    bd = load_build(build_dir)
    V = sys.modules['v2common']
    recs, _, _ = V.load_repo(root)
    b = bd.Build(recs, None, None, {}, hub=bd.HUB, text_index=None)
    ids = involved(b.R)
    res = {'books': {}, 'works': {}}
    wids = set()
    for bid in sorted(ids):
        v, _ = b.build_book(bid)
        card = b.book_card(bid)
        res['books'][bid] = {k: v.get(k) for k in ('_derived_by', '_lineage_refs', '_related', '_lineage_graph_ref')}
        res['books'][bid]['card_from'] = card.get('from')
        w = b.R['Book'][bid].get('work_id')
        if w in b.R['Work']:
            wids.add(w)
    for wid in sorted(wids):
        v, extra = b.build_work(wid)
        res['works'][wid] = {'_lineage_graph_ref': v.get('_lineage_graph_ref'), 'lineage': extra.get('lineage')}
    json.dump(res, open(out, 'w', encoding='utf8'), ensure_ascii=False, sort_keys=True, indent=1)
    print('books', len(res['books']), 'works', len(res['works']))


def diff(a, b):
    A, B = json.load(open(a, encoding='utf8')), json.load(open(b, encoding='utf8'))
    n = 0
    for part in ('books', 'works'):
        for k in sorted(set(A[part]) | set(B[part])):
            if A[part].get(k) != B[part].get(k):
                n += 1
                print(f'DIFF {part[:-1]} {k}')
                for f in sorted(set(A[part].get(k) or {}) | set(B[part].get(k) or {})):
                    x, y = (A[part].get(k) or {}).get(f), (B[part].get(k) or {}).get(f)
                    if x != y:
                        print(f'   {f}:\n     -{json.dumps(x, ensure_ascii=False)[:300]}\n     +{json.dumps(y, ensure_ascii=False)[:300]}')
    print('differences', n)
    return n


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('dump'); d.add_argument('--root', default='.'); d.add_argument('--build', default='build'); d.add_argument('--out', required=True)
    f = sub.add_parser('diff'); f.add_argument('a'); f.add_argument('b')
    a = ap.parse_args()
    if a.cmd == 'dump':
        dump(a.root, a.build, a.out)
    else:
        sys.exit(1 if diff(a.a, a.b) else 0)
