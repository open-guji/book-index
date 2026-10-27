#!/usr/bin/env python3
"""apply_batch 善后：全库 Work 墓碑里 merged_into 指向本批被并者的，改指本批 keeper（只动与本批相关的链，不碰别处）。用法：fix_chain_mine.py <批次目录>"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
mp = {l: g['keeper'] for g in json.load(open(os.path.join(sys.argv[1], 'merges.json')))['merges'] for l in g['losers']}
n = 0
for p in glob.glob(ROOT + '/Work/*/*/*/*.json'):
    raw = open(p, encoding='utf-8').read()
    if '"merged_into"' not in raw: continue
    d = json.loads(raw)
    if d.get('merged_into') in mp and d['id'] not in mp:
        d['merged_into'] = mp[d['merged_into']]; n += 1
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
print('墓碑改指', n)
