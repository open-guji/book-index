#!/usr/bin/env python3
"""本批墓碑链收口：merged_into 指向本批被并者的旧墓碑，改指本批 keeper（只改 merged_into 一值，不碰他线既有链），
并在 keeper 的 merged_in 记一笔（via 原指向），满足 check-duplicate-audit 的并入历史要求。
用法：fix_my_chains.py <batch.json> [--apply]"""
import json, glob, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
b = json.load(open(sys.argv[1])); ap = '--apply' in sys.argv
to = {l: g['keeper'] for g in b['groups'] for l in g['losers']}
import datetime
AT = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
def kpath(i): return glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
add = {}
n = 0
for p in glob.glob(f'{ROOT}/Work/*/*/*/*.json'):
    if os.path.getsize(p) > 900: continue
    raw = open(p, encoding='utf-8').read(); d = json.loads(raw)
    t = d.get('merged_into')
    if t in to and d['id'] not in to:
        n += 1; print(d['id'], t, '->', to[t])
        add.setdefault(to[t], []).append({'id': d['id'], 'title': d.get('title'), 'at': AT, 'by': 'A11-去重方案子目异名',
            'rule': '墓碑鏈收口：原並入 %s（本批被並），改指鏈末' % t, 'via': t})
        if ap:
            d['merged_into'] = to[t]
            open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
if ap:
    for k, items in add.items():
        p = kpath(k); raw = open(p, encoding='utf-8').read(); d = json.loads(raw)
        have = {x.get('id') if isinstance(x, dict) else x for x in d.get('merged_in') or []}
        d['merged_in'] = (d.get('merged_in') or []) + [x for x in items if x['id'] not in have]
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
print('改', n)
