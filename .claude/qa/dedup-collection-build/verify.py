#!/usr/bin/env python3
"""机器全检：批目录 plan.json 里每个 Collection 档存在且 sources[0].id==head；每个挂接 Book 的源记录确属该丛书头，且无 Book 被挂 >1 个本批 Collection。"""
import json, glob, os, sys, collections
P, plan_path = sys.argv[1], sys.argv[2]
rec = {}
for f in sorted(glob.glob(P + '/*.json')):
    for r in json.load(open(f, encoding='utf-8')):
        rec[r['source_record_id']] = r
plan = json.load(open(plan_path, encoding='utf-8'))['plan']
bp = {os.path.basename(f).split('-')[0]: f for f in glob.glob('Book/*/*/*/*.json')}
bad = n = multi = 0
for p in plan:
    c = json.load(open(p['path'], encoding='utf-8'))
    assert c['sources'][0]['id'] == p['head'] and c['id'] == p['id'], p['id']
    for b in p['books']:
        d = json.load(open(bp[b], encoding='utf-8')); n += 1
        hs = {rec[s['id']]['series']['series_id'] for s in d['sources'] if s['id'] in rec}
        ci = [x['id'] for x in d['contained_in']]
        if p['id'] not in ci or p['head'] not in hs:
            bad += 1
        if len(ci) > 1:
            multi += 1
print('Collection', len(plan), '挂接', n, '错', bad, '挂多个 Collection 的 Book', multi)
