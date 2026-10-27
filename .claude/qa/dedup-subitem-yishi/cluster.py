#!/usr/bin/env python3
"""由 pairs.tsv 的 A／B 边连簇；两簇之间若有 X（已判）、C、或带矛盾的 D（卷數矛盾／撰人異／朝代不合／敦煌）就不连。
输出 clusters.json（每簇成员与所用边）与 rest.tsv（不在同一簇的对 → dedup-judged 候选）。
用法：python3 cluster.py <pairs.tsv> <out目录>"""
import collections, csv, json, os, sys
rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8'), delimiter='\t'))
assert rows
BLOCK = ('卷數矛盾', '撰人異', '朝代不合', '敦煌', '已判')
par = {}
def f(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
members = collections.defaultdict(set)
def mem(x): return members[f(x)] if members[f(x)] else {x}
block = set()
for r in rows:
    if r['判定'] in ('X', 'C') or (r['判定'] == 'D' and any(k in r['依据'] for k in BLOCK)):
        block.add(frozenset((r['Work甲'], r['Work乙'])))
edges = [r for r in rows if r['判定'] in ('A', 'B')]
edges.sort(key=lambda r: (r['判定'], r['Work甲'], r['Work乙']))   # A 先连
used, skipped = [], []
for r in edges:
    a, b = r['Work甲'], r['Work乙']
    ra, rb = f(a), f(b)
    if ra == rb: used.append(r); continue
    ma, mb = mem(a), mem(b)
    if any(frozenset((x, y)) in block for x in ma for y in mb):
        skipped.append(r); continue
    par[ra] = rb; members[rb] = ma | mb; members.pop(ra, None); used.append(r)
comp = collections.defaultdict(set)
for r in used:
    comp[f(r['Work甲'])] |= {r['Work甲'], r['Work乙']}
cl = []
for root, ms in comp.items():
    es = [r for r in used if r['Work甲'] in ms]
    cl.append({'group': es[0]['组'], 'title': es[0]['题名'], 'members': sorted(ms),
               'edges': [[r['Work甲'], r['Work乙'], r['判定'], r['依据']] for r in es]})
cl.sort(key=lambda c: (int(c['group']), c['members'][0]))
os.makedirs(sys.argv[2], exist_ok=True)
json.dump(cl, open(os.path.join(sys.argv[2], 'clusters.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
same = {frozenset((x, y)) for c in cl for x in c['members'] for y in c['members'] if x != y}
with open(os.path.join(sys.argv[2], 'rest.tsv'), 'w', encoding='utf-8', newline='') as fo:
    w = csv.writer(fo, delimiter='\t', lineterminator='\n')
    w.writerow(list(rows[0].keys()))
    for r in rows:
        if r['判定'] != 'X' and frozenset((r['Work甲'], r['Work乙'])) not in same:
            w.writerow(list(r.values()))
print('簇', len(cl), '被并', sum(len(c['members']) - 1 for c in cl), '跳过边（会连上已判分立）', len(skipped), file=sys.stderr)
for r in skipped[:30]: print('  skip', r['组'], r['题名'], r['Work甲'], r['Work乙'], r['判定'], file=sys.stderr)
