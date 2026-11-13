#!/usr/bin/env python3
"""R1：按 match.py 的台账给 Work 追加 Kanripo 全文资源（types=text）。幂等；默认乾跑。
用法：python3 -I apply.py tier.tsv [--tiers AB] [--apply]"""
import argparse, datetime, glob, json, os
ap = argparse.ArgumentParser()
ap.add_argument('tsv'); ap.add_argument('--tiers', default='AB'); ap.add_argument('--apply', action='store_true')
a = ap.parse_args()
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
rows = [l.rstrip('\n').split('\t') for l in open(a.tsv, encoding='utf-8')]
want = {r[3]: r for r in rows if r[2] in a.tiers and r[3]}
paths = {}
for p in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
    i = os.path.basename(p).split('-')[0]
    if i in want:
        paths[i] = p
today = datetime.date.today().isoformat()
n = skip = 0
for i, r in want.items():
    p = paths.get(i)
    if not p:
        skip += 1; continue
    d = json.load(open(p, encoding='utf-8'))
    if d.get('merged_into') or any(x.get('id') == 'kanripo' for x in d.get('resources') or []):
        skip += 1; continue
    d.setdefault('resources', []).append({'name': 'Kanripo', 'id': 'kanripo', 'url': 'https://www.kanripo.org/text/' + r[0],
                                          'types': ['text']})
    if d.get('revision'):
        x = d['revision'].split('.')
        d['revision'] = '%s.%d.0' % (x[0], int(x[1]) + 1); d['revised_at'] = today
    n += 1
    if a.apply:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')
print('追加', n, '跳过', skip, '（乾跑）' if not a.apply else '')
