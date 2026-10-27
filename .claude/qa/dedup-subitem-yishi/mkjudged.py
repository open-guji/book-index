#!/usr/bin/env python3
"""未并的对写 dedup-judged：pairs.tsv 中非 X、且两端不在同一个已并簇的对；A／B 而未并的（会连上已判分立、核对存疑剔出）记 D。
用法：mkjudged.py <pairs.tsv> <clusters.json> <输出 tsv> [--skip c号 ...] [--base sha]"""
import argparse, csv, json
ap = argparse.ArgumentParser(); ap.add_argument('pairs'); ap.add_argument('clusters'); ap.add_argument('out')
ap.add_argument('--skip', nargs='*', default=[]); ap.add_argument('--base', default='')
a = ap.parse_args()
CL = json.load(open(a.clusters, encoding='utf-8'))
same, skipped = set(), {}
for ci, c in enumerate(CL):
    ms = c['members']
    for x in ms:
        for y in ms:
            if x < y:
                if 'c%d' % ci in a.skip: skipped[frozenset((x, y))] = ci
                else: same.add(frozenset((x, y)))
n = {'C': 0, 'D': 0}
with open(a.out, 'w', encoding='utf-8', newline='') as f:
    f.write('# 新-子目异名-史（叢書子目對單行本／他叢書同題，史部）判為分立 C／存疑 D 的對；基線 main %s；全量逐對判定見 .claude/qa/dedup-subitem-yishi/\n' % a.base)
    f.write('# Work甲\tWork乙\t判定\t理由\n')
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    for r in csv.DictReader(open(a.pairs, encoding='utf-8'), delimiter='\t'):
        k = frozenset((r['Work甲'], r['Work乙']))
        if r['判定'] == 'X' or k in same: continue
        lv, why = r['判定'], r['依据']
        if k in skipped: lv, why = 'D', '核對存疑未并（簇 c%d）：%s' % (skipped[k], why)
        elif lv in ('A', 'B'): lv, why = 'D', '機判可并但會連上已判分立之對，未并：%s' % why
        n[lv] += 1
        w.writerow([r['Work甲'], r['Work乙'], lv, '%s：%s' % (r['题名'], why)])
print(n)
