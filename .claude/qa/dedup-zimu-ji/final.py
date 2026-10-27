#!/usr/bin/env python3
"""新-子目异名-集未：机判 zj-pairs.tsv ＋ 人判 ovr.tsv → 终判 judged.tsv（列兼容 dedup-subitem-yi/mkbatch_yi.py）。
未被人判覆盖的对：A／B 照机判；B? 降 D（未核不并）；C? 作 C；D 留 D。
ovr.tsv 每行：组题名 \t id 末四位逗号串或 * \t 判 \t 依据；组内这些 id 两两取该判（只列一个 id 时指它与组内其余各条），后行覆盖前行。
用法：P4WORK=<工作目录> final.py [--hold 子目-乙-并判定表 ...]  输出 $P4WORK/judged.tsv，并报告未命中的 ovr 行。"""
import argparse, csv, os, sys
WK = os.environ.get('P4WORK', '/tmp/p4'); HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('--hold', nargs='*', default=[]); a = ap.parse_args()
DEF = {'A': 'A', 'B': 'B', 'B?': 'D', 'C?': 'C', 'D': 'D'}
ovr = []
for ln in open(HERE + '/ovr.tsv', encoding='utf-8'):
    p = ln.rstrip('\n').split('\t')
    if len(p) < 4 or not p[0]: continue
    ovr.append([p[0], None if p[1] == '*' else set(p[1].split(',')), p[2], p[3], 0])
# 在跑「子目-乙-并」已领的对涉及的 Work：先让出
hold = set()
for f in a.hold:
    for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
        if r.get('判定') in ('A', 'B', 'B?'): hold |= {r['Work甲'], r['Work乙']}
rows = list(csv.DictReader(open(WK + '/zj-pairs.tsv', encoding='utf-8'), delimiter='\t'))
out = []
for r in rows:
    j, why = DEF[r['机判']], '机判%s：撰人%s、卷%s%s' % (r['机判'], r['撰人'], r['卷'], ('、' + r['证据']) if r['证据'] else '')
    if r['机判'] == 'B?': why += '；未经人核，存疑不并'
    for o in ovr:
        if o[0] != r['题名']: continue
        ia, ib = r['Work甲'][-4:] in (o[1] or ()), r['Work乙'][-4:] in (o[1] or ())
        if o[1] is None or (ia and ib) or (len(o[1]) == 1 and (ia or ib)):
            j, why = o[2], '人判：' + o[3]; o[4] += 1
    if j in ('A', 'B') and (r['Work甲'] in hold or r['Work乙'] in hold):
        j, why = 'D', why + '；让出：涉子目-乙-并在并的 Work'
    out.append({'组': r['组'], '题名': r['题名'], '部类': r['部类'], '普查类': r['普查类'], 'Work甲': r['Work甲'], 'Work乙': r['Work乙'],
                '判定': j, '机判': r['机判'], '依据': why, '甲丛书': r['甲丛书'], '乙丛书': r['乙丛书'],
                '甲撰人': r['甲撰人'], '乙撰人': r['乙撰人'], '甲卷': r['甲卷'], '乙卷': r['乙卷']})
with open(WK + '/judged.tsv', 'w', encoding='utf-8', newline='') as fo:
    w = csv.DictWriter(fo, fieldnames=list(out[0]), delimiter='\t'); w.writeheader(); w.writerows(out)
import collections
print('对数', len(out), dict(collections.Counter(r['判定'] for r in out)))
miss = [o for o in ovr if not o[4]]
for o in miss: print('ovr 未命中：', o[0], o[1] or '*', o[2], file=sys.stderr)
