#!/usr/bin/env python3
"""去重方案部分 5e（2026-10-25）：全库扫描 live Book 的 contained_in，
把仍写草稿 Collection ID 的项按 promotions 换成正式 ID，换后同 ID 去重。
只改 Book；原值写 原值.json，清单写 清单.tsv。用法：fix_contained_in.py [--apply]"""
import json, sys, os, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = '2026-10-25'
def save(f, j): open(f, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
def bump(j):
    a, b, c = [int(x) for x in j.get('revision', '1.0.0').split('.')]
    j['revision'] = f'{a}.{b}.{c+1}'; j['revised_at'] = TODAY
pm = {}
for f in glob.glob(f'{ROOT}/promotions/*.json'):
    for k, v in json.load(open(f, encoding='utf-8'))['promotions'].items():
        if v.get('type') == 'collection': pm[k] = v['production_id']
coll = {os.path.basename(f).split('-')[0] for f in glob.glob(f'{ROOT}/Collection/*/*/*/*.json')}
print(f'載入 promotions(collection) {len(pm)}、正式 Collection {len(coll)}', file=sys.stderr)
assert pm and coll
orig, out, rows, n = {}, [], [], 0
for f in glob.glob(f'{ROOT}/Book/*/*/*/*.json'):
    n += 1
    s = open(f, encoding='utf-8').read()
    if '"contained_in"' not in s: continue
    j = json.loads(s)
    if j.get('merged_into'): continue
    ci = j.get('contained_in') or []
    if not any(c.get('id') in pm for c in ci): continue
    seen, new = set(), []
    for c in ci:
        c = dict(c); old = c['id']; c['id'] = pm.get(old, old)
        assert c['id'] in coll, (j['id'], old, c['id'])
        if old != c['id']: rows.append((j['id'], j.get('title', ''), old, c['id']))
        if c['id'] in seen: continue
        seen.add(c['id']); new.append(c)
    orig[j['id']] = {'contained_in': ci}
    j['contained_in'] = new; bump(j); out.append((f, j))
print(f'載入 Book {n}，需改 {len(out)}', file=sys.stderr)
assert n > 0
if '--apply' in sys.argv:
    for f, j in out: save(f, j)
    json.dump(orig, open(os.path.join(HERE, '原值.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, '清單.tsv'), 'w', encoding='utf-8') as fo:
        fo.write('book_id\ttitle\t草稿collection_id\t正式collection_id\n')
        for r in sorted(rows): fo.write('\t'.join(r) + '\n')
for f, _ in out: print(('改 ' if '--apply' in sys.argv else '乾跑 ') + os.path.relpath(f, ROOT))
