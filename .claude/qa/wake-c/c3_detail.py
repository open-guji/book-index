# -*- coding: utf-8 -*-
"""wake-c 第三輪：對候選取 NCID .json 詳情，解析並輸出 c3_det.json。先 python3 c3_cand.py。"""
import json, re, sys
from ndl import get
cand = json.load(open('c3_cand.json')); known = json.load(open('c3_known.json'))
from c3_map import classify
sel = []
for n, i in cand.items():
    if n in known: continue
    if i['y'] > 1867: continue
    pub = ' '.join(i['pub'] or [])
    if not pub or re.match(r'^\s*\[[^\]]*\]\s*$', pub) or '不明' in pub: continue
    if not classify(i['t'], i['cr']): continue
    sel.append(n)
print(len(sel), 'to fetch', flush=True)
OUT = 'c3_det.json'
import os
det = json.load(open(OUT)) if os.path.exists(OUT) else {}
for k, n in enumerate(sel):
    if n in det: continue
    t = get('https://ci.nii.ac.jp/ncid/%s.json' % n)
    if not t: det[n] = None; continue
    try: g = json.loads(t)['@graph'][0]
    except Exception: det[n] = None; continue
    def val(x):
        if isinstance(x, list): return [val(i) for i in x]
        if isinstance(x, dict): return x.get('@value', x)
        return x
    det[n] = {'title': val(g.get('dc:title')), 'alt': g.get('dcterms:alternative'), 'cr': g.get('dc:creator'), 'pub': val(g.get('dc:publisher')), 'date': g.get('dc:date'), 'pd': g.get('prism:publicationDate'), 'ext': g.get('dcterms:extent'), 'note': g.get('cinii:note'), 'own': [o['foaf:name'] for o in g.get('bibo:owner', [])], 'size': g.get('cinii:size'), 'part': [p.get('dc:title') for p in g.get('dcterms:hasPart', [])] if g.get('dcterms:hasPart') else None}
    if k % 50 == 0:
        print(k, flush=True); json.dump(det, open(OUT, 'w'), ensure_ascii=False)
json.dump(det, open(OUT, 'w'), ensure_ascii=False)
print('done')
