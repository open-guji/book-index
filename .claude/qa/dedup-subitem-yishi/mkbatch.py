#!/usr/bin/env python3
"""由 clusters.json 生成 batch.json（apply_batch 格式），剔除已成墓碑者与核对否决的簇。
keeper 优先：撰人非丛书编者错位、单书著录（非叢書子目）、有自身撰人（非据丛书补）、indexed_by 多、资源多、id 早。
用法：mkbatch.py <feat.json> <clusters.json> <输出目录> [--skip c号 ...] [--no-keeper id ...] [--part K/N] [--base sha]"""
import argparse, glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
RULE = '去重方案新-子目异名-史：叢書子目與單行本／他叢書子目同題，同撰人（含輯者同）或總目單書著錄版本列該叢書本，卷數不矛盾（判據見子目-乙-跨丛书同题子目判据.md、部分4 4a-α）'
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
ap = argparse.ArgumentParser(); ap.add_argument('feat'); ap.add_argument('clusters'); ap.add_argument('out')
ap.add_argument('--skip', nargs='*', default=[]); ap.add_argument('--no-keeper', nargs='*', default=[])
ap.add_argument('--part', default='1/1'); ap.add_argument('--base', default='')
a = ap.parse_args()
F = json.load(open(a.feat, encoding='utf-8')); FW = {w['id']: w for g in F for w in g['works']}
CL = json.load(open(a.clusters, encoding='utf-8'))
def edrole(i):
    w = FW[i]; cn = {c2[0] for c in w['cols'] for c2 in c['auth'] if c2[0]}
    return bool(cn & {x[0] for x in w['authors']}) and not any('獨撰類' in (x[2] or '') for x in w['ib'])
groups = []
for ci, c in enumerate(CL):
    if 'c%d' % ci in a.skip: continue
    ds = {i: load(i) for i in c['members']}
    live = [i for i in c['members'] if not ds[i].get('merged_into')]
    if len(live) < 2: continue
    key = lambda i: (i not in a.no_keeper, not edrole(i), not FW[i]['congshu'] and not FW[i]['cols'], bool(ds[i].get('authors')) and not FW[i]['butu'],
                     len(ds[i].get('indexed_by') or []), len(ds[i].get('resources') or []), -int(i, 36))
    keeper = max(live, key=key)
    losers = sorted(set(live) - {keeper})
    ev = '跨叢書／單行同題子目（%s）：%s' % ('／'.join(sorted({('《%s》' % x['title']) for i in live for x in FW[i]['cols']}) or ['單行']),
                                       '；'.join(sorted({e[3] for e in c['edges'] if e[0] in live and e[1] in live})))
    notes = {l: {'ai_note': ds[l].get('ai_note'), 'description': (ds[l].get('description') or {}).get('text') if isinstance(ds[l].get('description'), dict) else ds[l].get('description')} for l in losers}
    groups.append({'case_id': keeper, 'cluster_id': 'subyishi-c%d' % ci, 'type': 'work', 'keeper': keeper, 'losers': losers,
                   'keeper_source': '去重方案新-子目异名-史 簇 c%d（book-index %s）' % (ci, a.base), 'evidence': ev[:900], 'rule': RULE, 'why': ev[:900],
                   'loser_original_notes': notes})
k, n = map(int, a.part.split('/'))
sz = -(-len(groups) // n); groups = groups[(k - 1) * sz:k * sz]
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
