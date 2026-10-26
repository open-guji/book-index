#!/usr/bin/env python3
"""3b 候选普查：以首位撰人 Entity 为键，同一 Entity 名下两两比较 Work。
输出各类计数与候选 jsonl。用法：scan.py <out.jsonl>"""
import collections, importlib.util, json, os, re, sys, itertools
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path[:0] = [os.path.join(ROOT, 'scripts'), os.path.join(ROOT, '.claude', 'qa')]
spec = importlib.util.spec_from_file_location('dc', os.path.join(ROOT, 'scripts', 'dedup-census.py'))
dc = importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)
import backrefs  # noqa
W = {}
for t, p, d in backrefs.iter_records(ROOT):
    if t == 'Work' and not d.get('merged_into'):
        W[d['id']] = d
by = collections.defaultdict(list)
for i, d in W.items():
    a = (d.get('authors') or [None])[0]
    if a and a.get('entity_id'):
        by[a['entity_id']].append(i)
print('Work', len(W), '首位有 entity', sum(map(len, by.values())), 'Entity', len(by), file=sys.stderr)
cnt = collections.Counter(); out = open(sys.argv[1], 'w')
for e, ids in by.items():
    if len(ids) < 2: continue
    keys = collections.defaultdict(list)
    for i in ids:
        keys[dc.norm(W[i].get('title') or '')].append(i)
    for k, g in keys.items():
        if len(g) < 2: continue
        names = {dc.norm_name(W[i]['authors'][0].get('name')) for i in g}
        kind = '同题同名' if len(names) == 1 else '同题异名'
        cnt[kind] += 1
        out.write(json.dumps({'entity': e, 'kind': kind, 'title': k, 'ids': g}, ensure_ascii=False) + '\n')
    # 近题：一方题名为另一方前缀／包含（去坊刻套语后），长度≥2
    ks = [k for k in keys if len(k) >= 2]
    for a, b in itertools.combinations(ks, 2):
        if a in b or b in a:
            cnt['近题(包含)'] += 1
            out.write(json.dumps({'entity': e, 'kind': '近题', 'title': a + '｜' + b, 'ids': keys[a] + keys[b]}, ensure_ascii=False) + '\n')
print(dict(cnt))
