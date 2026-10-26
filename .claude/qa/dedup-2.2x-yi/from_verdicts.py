#!/usr/bin/env python3
"""把逐名复核结论（verdicts/*.jsonl）落成挂接清单。
  SAME＋eid：该名在 rest.jsonl 的全部作者位挂 eid，剔除 exclude 列出者；对该 eid 朝代 incompat 的一律不挂；
  复核包未列出的作者位（more）只挂朝代 same 者，多候选（R3）一律不挂。DIFF／UNSURE 整名不挂，登记。
    python3 from_verdicts.py <baseline 输出目录> <verdicts 目录> <输出前缀>"""
import collections, glob, json, os, sys
d0, vd, outp = sys.argv[1:4]
rows = collections.defaultdict(list)
for l in open(os.path.join(d0, 'rest.jsonl'), encoding='utf-8'):
    r = json.loads(l); rows[r['norm']].append(r)
listed = collections.defaultdict(set)
for f in glob.glob(os.path.join(d0, 'pack', '*.jsonl')):
    for l in open(f, encoding='utf-8'):
        x = json.loads(l); listed[x['name']] |= {s['k'] for s in x['slots']}
V = {}
for f in sorted(glob.glob(os.path.join(vd, '*.jsonl'))):
    for l in open(f, encoding='utf-8'):
        if l.strip():
            v = json.loads(l); V[v['name']] = dict(v, file=os.path.basename(f))
print('载入结论', len(V)); assert V
attach, reg, c = [], [], collections.Counter()
for n, v in V.items():
    if n not in rows: c['名不在rest'] += 1; continue
    if v['verdict'] != 'SAME':
        c[v['verdict']] += 1
        for r in rows[n]: reg.append({'path': r['path'], 'slot': r['slot'], 'name': r['name'], 'verdict': v['verdict'], 'reason': v.get('reason'), 'cands': [x['eid'] for x in r['cands']]})
        continue
    ex = set(v.get('exclude') or [])
    for r in rows[n]:
        k = '%s:%s#%d' % (r['type'][0], r['id'], r['slot'])
        cand = {x['eid']: x for x in r['cands']}
        if v.get('eid') not in cand: c['eid不在候选'] += 1; continue
        rel = cand[v['eid']]['rel']
        if k in ex: why = '复核剔除'
        elif rel == 'incompat': why = '朝代冲突'
        elif k not in listed[n] and (rel != 'same' or v['file'].startswith('R3')): why = '未列出且朝代非同或多候选'
        else:
            attach.append({'path': r['path'], 'slot': r['slot'], 'name': r['name'], 'entity_id': v['eid'], 'tier': 'R-逐名复核:' + v['file'][:-6], 'why': v.get('reason')}); c['挂'] += 1; continue
        c[why] += 1; reg.append({'path': r['path'], 'slot': r['slot'], 'name': r['name'], 'verdict': why, 'reason': v.get('reason'), 'cands': list(cand)})
json.dump(attach, open(outp + '-attach.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
with open(outp + '-不挂.jsonl', 'w', encoding='utf-8') as f:
    for x in reg: f.write(json.dumps(x, ensure_ascii=False) + '\n')
print(dict(c))
