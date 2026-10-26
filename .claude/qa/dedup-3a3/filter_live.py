#!/usr/bin/env python3
"""从待并组清单取前 N 个仍全活的组写成 batch.json。用法：filter_live.py <remaining.json> <批次目录> <N>"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
G = json.load(open(sys.argv[1], encoding='utf-8')); n = int(sys.argv[3])
def live(i):
    h = glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json'))
    return len(h) == 1 and not json.load(open(h[0], encoding='utf-8')).get('merged_into')
out, dead = [], 0
for g in G:
    if len(out) >= n: break
    if all(live(i) for i in [g['keeper']] + g['losers']): out.append(g)
    else: dead += 1
os.makedirs(sys.argv[2], exist_ok=True)
json.dump({'groups': out}, open(os.path.join(sys.argv[2], 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('取', len(out), '组；跳过已被并', dead, file=sys.stderr)
