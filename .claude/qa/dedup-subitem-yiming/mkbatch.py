#!/usr/bin/env python3
"""由 combine.py 的 clusters.json 生成 apply_batch 用的 batch.json；剔除已成墓碑者。
用法：mkbatch.py <clusters.json> <输出目录> --unit 經 [--skip id ...] [--keeper id ...] [--base sha]"""
import argparse, glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
ap = argparse.ArgumentParser(); ap.add_argument('clusters'); ap.add_argument('out'); ap.add_argument('--unit', default='經')
ap.add_argument('--skip', nargs='*', default=[]); ap.add_argument('--keeper', nargs='*', default=[]); ap.add_argument('--base', default='')
a = ap.parse_args()
RULE = '去重方案新-子目异名-%s：含叢書子目、叢書異名或對單行本的同題 Work，同撰人（含獨撰類子目繼承叢書撰人）或同源證據、卷數不矛盾即並（子目-乙判據＋4a-α 口徑）' % a.unit
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
groups = []
for c in json.load(open(a.clusters)):
    ms = [c['keeper']] + c['losers']
    if set(ms) & set(a.skip): continue
    ds = {i: load(i) for i in ms}
    if any(d.get('merged_into') for d in ds.values()): continue
    forced = set(ms) & set(a.keeper)
    k = forced.pop() if forced else c['keeper']
    losers = sorted(set(ms) - {k})
    ev = '同題《%s》：%s（%s 檔）' % (c['key'], c['why'], c['level'])
    notes = {l: {'ai_note': ds[l].get('ai_note'), 'description': (ds[l].get('description') or {}).get('text') if isinstance(ds[l].get('description'), dict) else ds[l].get('description')} for l in losers}
    groups.append({'case_id': k, 'cluster_id': 'yiming-%s' % k, 'type': 'work', 'keeper': k, 'losers': losers,
                   'keeper_source': '去重方案新-子目异名-%s 判定（book-index %s）' % (a.unit, a.base), 'evidence': ev, 'rule': RULE, 'why': ev,
                   'loser_original_notes': notes})
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
