#!/usr/bin/env python3
"""Q3：按 A12 处理结果（动作 created／mapped）给 Work.authors 补 entity_id。默认乾跑。
用法：python3 -I attach.py Q3-A12处理结果.tsv [--apply]
只补 name 与 dynasty 都与表一致、且尚无 entity_id 的作者位；核对 Entity 存在且未并条。"""
import argparse, csv, datetime, glob, json, os, collections
ap = argparse.ArgumentParser(); ap.add_argument('tsv'); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
m = {}
for r in csv.reader(open(a.tsv, encoding='utf-8'), delimiter='\t'):
    if len(r) >= 5 and r[3] in ('created', 'mapped'):
        m[(r[0], r[1])] = r[4]
ent = {}
for p in glob.glob(os.path.join(ROOT, 'Entity/*/*/*/*.json')):
    i = os.path.basename(p).split('-')[0]
    if i in m.values():
        d = json.load(open(p, encoding='utf-8')); ent[i] = d
bad = [v for v in m.values() if v not in ent or ent[v].get('merged_into')]
if bad: print('警告：Entity 缺失或已并', bad[:5], len(bad))
today = datetime.date.today().isoformat(); C = collections.Counter()
for p in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
    d = json.load(open(p, encoding='utf-8'))
    if d.get('merged_into'): continue
    hit = False
    for au in d.get('authors') or []:
        if isinstance(au, dict) and not au.get('entity_id'):
            k = (au.get('name'), au.get('dynasty') or '')
            v = m.get(k)
            if v and v in ent and not ent[v].get('merged_into'):
                au['entity_id'] = v; hit = True; C['author_slots'] += 1
    if hit:
        C['works'] += 1
        x = d['revision'].split('.'); d['revision'] = '%s.%d.0' % (x[0], int(x[1]) + 1); d['revised_at'] = today
        if a.apply:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')
print(dict(C), '（乾跑）' if not a.apply else '')
