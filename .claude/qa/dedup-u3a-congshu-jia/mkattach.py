#!/usr/bin/env python3
"""轨 A：两轮 verdict 都判 SAME 且同 eid → attach 清单。python3 mkattach.py <scratch> <out.json>
再剔：候选已挂作品 0 部且说明是据本 Work 建档（循环证据）；人工剔除名单 DROP。"""
import glob, json, sys, collections
S, out = sys.argv[1], sys.argv[2]
DROP = {'俞培元', '李放', '汪琥', '江洪', '王一清', '石頑', '釋懷素', '點石齋', '楊掄', '吳琯', '朱弁'}
def load(pat):
    V = {}
    for f in glob.glob(S + pat):
        for l in open(f, encoding='utf-8'):
            if l.strip():
                d = json.loads(l); V[d['name']] = d
    return V
V1, V2 = load('/verdA/A-*.jsonl'), load('/verdA2/A2-*.jsonl')
rows = [json.loads(l) for l in open(S + '/c/slots.jsonl', encoding='utf-8')]
by = collections.defaultdict(list)
for r in rows: by[r['name']].append(r)
items = []; names = 0
for n, v in V1.items():
    w = V2.get(n)
    if v['verdict'] != 'SAME' or not w or w['verdict'] != 'SAME' or w.get('eid') != v.get('eid') or n in DROP: continue
    ex = set(v.get('exclude') or []) | set(w.get('exclude') or [])
    names += 1
    for r in by[n]:
        if r['id'] in ex: continue
        items.append({'path': r['path'], 'slot': 0, 'name': r['name'], 'entity_id': v['eid'], 'work_id': r['id'], 'title': r['title'], 'reason': v.get('reason')})
json.dump(items, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('名字', names, 'Work', len(items), '一审SAME', sum(1 for v in V1.values() if v['verdict'] == 'SAME'), '二审记录', len(V2))
