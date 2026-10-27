#!/usr/bin/env python3
"""新-待並條：由逐条判定表连簇出 remaining.json（全部待并组）。用法：build_batch.py <判定.tsv> <out.json> [hold.tsv]
簇内若另有判 C／D 的对则整簇留人工；keeper 取判定表多数票，平票取首个。"""
import collections, csv, glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
rows = list(csv.DictReader((l for l in open(sys.argv[1], encoding='utf-8') if not l.startswith('#')), delimiter='\t'))
p = {}
def f(x):
    p.setdefault(x, x)
    while p[x] != x: p[x] = p[p[x]]; x = p[x]
    return x
B = [r for r in rows if r['判定'] == '并']
for r in B: p[f(r['A'])] = f(r['B'])
cl = collections.defaultdict(set)
for r in B: cl[f(r['A'])].update([r['A'], r['B']])
def path(i):
    h = glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json')); return h[0] if h else None
out, held = [], []
for mem in cl.values():
    bad = [r for r in rows if r['判定'] != '并' and r['A'] in mem and r['B'] in mem]
    if bad: held.append((mem, '簇内有分立／存疑对')); continue
    es = [r for r in B if r['A'] in mem]
    votes = collections.Counter(r['keeper'] for r in es)
    keeper = votes.most_common(1)[0][0]
    losers = sorted(mem - {keeper})
    recs = {i: json.load(open(path(i), encoding='utf-8')) for i in mem}
    lab = lambda i: '《%s》%s' % (recs[i].get('title'), '/'.join(str(a.get('name')) for a in (recs[i].get('authors') or [])[:1]))
    why = '待並條逐条定论同书：%s／%s；%s' % (lab(keeper), '、'.join(lab(l) for l in losers), '；'.join(r['理由'] for r in es))
    notes = {l: {k: recs[l].get(k) for k in ('ai_note', 'description') if recs[l].get(k)} for l in losers}
    out.append({'case_id': 'DBT-%s' % keeper, 'cluster_id': 'dbt-%s' % keeper, 'type': 'work', 'keeper': keeper, 'losers': losers,
                'keeper_source': '新-待並條：related 注「待並條」之链接（scripts/dedup-census.py R 段）逐条定论',
                'evidence': why, 'why': why,
                'rule': '去重新-待並條：史部E存疑另立留下的待並條链接逐条复核，同一责任者＋题名异写／省称＋卷数相合者并（B 档，子 agent 初判＋本串复核＋独立抽检）',
                'loser_original_notes': {k: v for k, v in notes.items() if v}})
out.sort(key=lambda g: g['keeper'])
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('簇', len(out), '被并', sum(len(g['losers']) for g in out), '留人工', len(held), file=sys.stderr)
if len(sys.argv) > 3:
    with open(sys.argv[3], 'w', encoding='utf-8') as fh:
        for mem, w in held: fh.write('%s\t%s\n' % (w, ','.join(sorted(mem))))
