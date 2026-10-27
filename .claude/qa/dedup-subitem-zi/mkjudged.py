#!/usr/bin/env python3
"""把本单元不并的对写成 dedup-judged 登记：每组把「并后各簇」用最少的对连通（Kruskal，先 C 后 D），
冲突簇里的 A／B 边改记 D。子目-乙判定表已有的对（YI）不登。用法：mkjudged.py <pairs_zi.tsv> <clusters.json> <输出.tsv> [--skip 簇序号...]"""
import argparse, csv, json, collections
ap = argparse.ArgumentParser(); ap.add_argument('pairs'); ap.add_argument('clusters'); ap.add_argument('out'); ap.add_argument('--skip', nargs='*', type=int, default=[])
a = ap.parse_args()
R = list(csv.DictReader(open(a.pairs), delimiter='\t'))
C = json.load(open(a.clusters))
merged = {}
for k, c in enumerate(C):
    if c['conflict'] or k in a.skip:
        for x, y, *_ in c['conflict']: pass
        continue
    for i in c['ids']: merged[i] = 'K%d' % k
conflict_ids = {i for k, c in enumerate(C) if c['conflict'] or k in a.skip for i in c['ids']}
node = lambda i: merged.get(i, i)
par = {}
def f(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
out = []
for r in R:
    if r['lv'] in ('A', 'B') and r['a'] in conflict_ids:
        r['lv'], r['why'] = 'D', '所在簇含相互矛盾的对（辑者／注者层次或卷数不合），整簇暂不并：' + r['why']
rank = {'C': 0, 'D': 1}
for r in sorted((r for r in R if r['lv'] in rank), key=lambda r: (rank[r['lv']], r['why'].startswith(('缺撰人', '泛称')))):
    x, y = f(node(r['a'])), f(node(r['b']))
    if x == y: continue
    par[x] = y; out.append(r)
with open(a.out, 'w', encoding='utf-8') as fo:
    fo.write('# 新-子目异名-子（含叢書子目、丛书异名或对单行本的同题组·子部）判为分立 C／存疑 D 的对；每组只登连通各簇所需的最少对。全量逐对初判与工具见 .claude/qa/dedup-subitem-zi/\n')
    fo.write('# Work甲\tWork乙\t判定\t理由\n')
    for r in out: fo.write('%s\t%s\t%s\t%s：%s\n' % (r['a'], r['b'], r['lv'], r['key'], r['why']))
print(len(out), collections.Counter(r['lv'] for r in out))
