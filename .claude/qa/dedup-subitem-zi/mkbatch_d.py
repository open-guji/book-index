#!/usr/bin/env python3
"""D 档「缺撰人同题同卷」逐对子 agent 核后的并条：dcomps.json（SAME 连通簇，已剔簇内有非 SAME 对者）→ batch.json。
用法：mkbatch_d.py <dcomps.json> <排除簇序号逗号分隔> <输出目录> [--base sha]"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
def live(i):
    d = load(i)
    while d.get('merged_into'): d = load(d['merged_into'])
    return d
comps = json.load(open(sys.argv[1])); excl = {int(x) for x in sys.argv[2].split(',') if x}
out = sys.argv[3]; base = sys.argv[sys.argv.index('--base') + 1] if '--base' in sys.argv else ''
groups = []
for n, c in enumerate(comps):
    if n in excl: continue
    ds = {}
    for i in c:
        d = live(i); ds[d['id']] = d
    if len(ds) < 2: continue
    keeper = max(ds, key=lambda i: (bool(ds[i].get('authors')), len(ds[i].get('indexed_by') or []), len(ds[i].get('resources') or []), -int(i, 36)))
    losers = sorted(set(ds) - {keeper})
    t = ds[keeper]['title']
    ev = '同題《%s》：缺撰人同题同卷，逐對獨立子 agent 核為同一部書（題名專指、部類／叢書／卷數相容）' % t
    notes = {l: {'ai_note': ds[l].get('ai_note'), 'description': (ds[l].get('description') or {}).get('text') if isinstance(ds[l].get('description'), dict) else ds[l].get('description')} for l in losers}
    groups.append({'case_id': keeper, 'cluster_id': 'subzi-d-%s' % keeper, 'type': 'work', 'keeper': keeper, 'losers': losers,
      'keeper_source': '去重方案新-子目异名-子 D 档逐對核（book-index %s，.claude/qa/dedup-subitem-zi/mkbatch_d.py）' % base,
      'evidence': ev, 'rule': '去重方案新-子目异名-子 D 档：缺撰人、同题同卷、無直接互見證據的對，由獨立子 agent 逐對按 4a-B 口徑核（泛稱題名、不同輯者輯本不并），簇內無非同書對，43 簇獨立複核 41 同書 0 異 2 存疑（存疑簇剔出）',
      'why': ev, 'loser_original_notes': notes, 'levels': ['D']})
os.makedirs(out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
