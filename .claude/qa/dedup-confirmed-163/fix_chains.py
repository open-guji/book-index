#!/usr/bin/env python3
"""墓碑二跳链收口：merged_into 指向另一座墓碑的，改指链末（规则 3：引用全改写）。只改 merged_into 一个值。"""
import json, glob, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
tomb, path = {}, {}
for t in ('Work', 'Book', 'Entity', 'Collection'):
    for p in glob.glob(f'{ROOT}/{t}/*/*/*/*.json'):
        if os.path.getsize(p) < 900:
            d = json.load(open(p, encoding='utf-8'))
            if d.get('merged_into'):
                tomb[d['id']] = d['merged_into']; path[d['id']] = p
n = 0
for i, tgt in tomb.items():
    end = tgt; seen = {i}
    while end in tomb and end not in seen:
        seen.add(end); end = tomb[end]
    if end != tgt:
        raw = open(path[i], encoding='utf-8').read(); d = json.loads(raw); d['merged_into'] = end
        open(path[i], 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
        n += 1; print(i, tgt, '->', end)
print('改指', n)
