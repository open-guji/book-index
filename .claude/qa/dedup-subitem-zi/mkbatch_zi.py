#!/usr/bin/env python3
"""由 clusters.json（cluster.py 产出）的无冲突簇生成 batch.json。
keeper：单行本（非叢書子目）优先，再取有撰人、indexed_by 多、资源多、id 早者。
用法：mkbatch_zi.py <clusters.json> <pairs_zi.tsv> <输出目录> [--skip 簇序号...] [--part i/n] [--base sha]"""
import argparse, csv, glob, json, os, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
RULE = ('去重方案新-子目异名-子：含叢書子目的同题组，叢書子目与单行本或他叢書子目为同一作品——同撰人（含獨撰類子目继承叢書撰人，4a-α 口径）、'
        '或总目单书著录列出该叢書本、或单书 Work 已挂该叢書 Book、或两叢書同名／同出一系（子目-乙判据），卷数不矛盾')
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
ap = argparse.ArgumentParser(); ap.add_argument('clusters'); ap.add_argument('pairs'); ap.add_argument('out')
ap.add_argument('--skip', nargs='*', type=int, default=[]); ap.add_argument('--part', default='1/1'); ap.add_argument('--base', default='')
a = ap.parse_args()
C = json.load(open(a.clusters))
P = {}
for r in csv.DictReader(open(a.pairs), delimiter='\t'):
    P[frozenset((r['a'], r['b']))] = r
ks = [k for k, c in enumerate(C) if not c['conflict'] and k not in a.skip]
pi, pn = map(int, a.part.split('/'))
ks = ks[(pi - 1) * len(ks) // pn: pi * len(ks) // pn]
groups = []
for k in ks:
    c = C[k]; ms = c['ids']
    ds = {i: load(i) for i in ms}
    if any(d.get('merged_into') for d in ds.values()): continue
    sub = lambda i: '所屬叢書記錄' in (ds[i].get('ai_note') or '')
    key = lambda i: (not sub(i), bool(ds[i].get('authors')), len(ds[i].get('indexed_by') or []), len(ds[i].get('resources') or []), -int(i, 36))
    keeper = max(ms, key=key); losers = sorted(set(ms) - {keeper})
    ev = sorted({P[frozenset((x, y))]['why'] for x in ms for y in ms if x < y and frozenset((x, y)) in P and P[frozenset((x, y))]['lv'] in ('A', 'B')})
    ev = '同題《%s》（%s）：%s' % (c['key'], '、'.join('單行本' if not sub(i) else re.search(r'所屬叢書記錄 \S+（(.*)）[ \t]*$', ds[i]['ai_note'], re.M).group(1)[:20] for i in ms), '；'.join(ev))
    notes = {l: {'ai_note': ds[l].get('ai_note'), 'description': (ds[l].get('description') or {}).get('text') if isinstance(ds[l].get('description'), dict) else ds[l].get('description')} for l in losers}
    groups.append({'case_id': keeper, 'cluster_id': 'subzi-%s' % keeper, 'type': 'work', 'keeper': keeper, 'losers': losers,
                   'keeper_source': '去重方案新-子目异名-子 判定（book-index %s，.claude/qa/dedup-subitem-zi/）' % a.base, 'evidence': ev, 'rule': RULE, 'why': ev,
                   'loser_original_notes': notes, 'levels': c['levels']})
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
