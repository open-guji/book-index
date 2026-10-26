#!/usr/bin/env python3
"""由 dedup-zimu-ji/final.py 输出的 judged.tsv 的 A／B 对生成 batch.json（改自 dedup-subitem-yi/mkbatch_yi.py）：按对连通成簇，剔除已成墓碑者；
keeper 取有撰人、indexed_by 多、资源多、id 早者；--keeper 可对指定簇强定 keeper（撰人误字时取正字一侧）。
用法：mkbatch_zj.py <judged.tsv> <输出目录> --levels A B [--keeper id ...] [--only 簇内任一id ...] [--first N 只取前 N 簇] [--base sha]"""
import argparse, collections, csv, glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
RULE = '去重方案新-子目异名-集未：集部與未分類同題組中叢書子目（丛书異名或對單行本）互並，子目-乙判據加 4a-α 口徑（獨撰子目繼承叢書撰人），同撰人或同源叢書家族、卷數不矛盾；B? 逐組人讀（ovr.tsv）'
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
ap = argparse.ArgumentParser(); ap.add_argument('judged'); ap.add_argument('out')
ap.add_argument('--levels', nargs='+', default=['A', 'B']); ap.add_argument('--keeper', nargs='*', default=[])
ap.add_argument('--only', nargs='*'); ap.add_argument('--first', type=int, default=0); ap.add_argument('--base', default='')
a = ap.parse_args()
rows = [r for r in csv.DictReader(open(a.judged, encoding='utf-8'), delimiter='\t') if r['判定'] in a.levels]
par = {}
def f(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for r in rows:
    if load(r['Work甲']).get('merged_into') or load(r['Work乙']).get('merged_into'): continue
    par[f(r['Work甲'])] = f(r['Work乙'])
comp = collections.defaultdict(set)
for x in list(par): comp[f(x)].add(x)
groups = []
for ms in sorted(comp.values(), key=lambda s: min(s)):
    if a.only is not None and not ms & set(a.only): continue
    ds = {i: load(i) for i in ms}
    forced = ms & set(a.keeper)
    key = lambda i: (bool(ds[i].get('authors')), len(ds[i].get('indexed_by') or []), len(ds[i].get('resources') or []), -int(i, 36))
    keeper = forced.pop() if forced else max(ms, key=key)
    losers = sorted(ms - {keeper})
    prs = [r for r in rows if r['Work甲'] in ms]
    cols = sorted({r['甲丛书'] for r in prs} | {r['乙丛书'] for r in prs})
    ev = '同題子目（%s）：%s；判定 %s' % ('／'.join(cols), '；'.join(sorted({r['依据'] for r in prs})), '／'.join(sorted({r['判定'] for r in prs})))
    notes = {l: {'ai_note': ds[l].get('ai_note'), 'description': (ds[l].get('description') or {}).get('text') if isinstance(ds[l].get('description'), dict) else ds[l].get('description')} for l in losers}
    groups.append({'case_id': keeper, 'cluster_id': 'zimuji-%s' % keeper, 'type': 'work', 'keeper': keeper, 'losers': losers,
                   'keeper_source': '去重方案新-子目异名-集未 判定表 %s（book-index %s）' % (os.path.basename(a.judged), a.base), 'evidence': ev, 'rule': RULE, 'why': ev,
                   'loser_original_notes': notes})
if a.first: groups = groups[:a.first]
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
