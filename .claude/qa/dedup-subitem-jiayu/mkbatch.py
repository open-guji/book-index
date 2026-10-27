#!/usr/bin/env python3
"""由 cand.py 产出的 jia2.json 生成 batch.json。
用法：mkbatch.py <jia2.json> <输出目录> [--bulei 子部 集部] [--n 20] [--offset 0] [--sample] [--base sha]
--sample：各部类轮流取，供样本批。"""
import argparse, glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
RULE_B = '去重第二轮细拆单元新-子目甲余：同名丛书不同版次里的同题叢書子目 Work，各版次丛书编者著录写法不同而经核为同一部书（编者异写／先后编者），责任者与卷数不矛盾，B 档证据并（子 agent 逐条核）'
RULE = '去重第二轮细拆单元新-子目甲余：同名丛书不同版次里的同题叢書子目 Work（叢書线按丛书版本记录各建一条），丛书撰者相同、责任者与卷数不矛盾，A 档机械并'
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
ap = argparse.ArgumentParser(); ap.add_argument('cand'); ap.add_argument('out')
ap.add_argument('--bulei', nargs='+'); ap.add_argument('--n', type=int, default=20); ap.add_argument('--offset', type=int, default=0)
ap.add_argument('--sample', action='store_true'); ap.add_argument('--base', default='')
a = ap.parse_args()
cs = [c for c in json.load(open(a.cand, encoding='utf-8')) if not a.bulei or c['bulei'] in a.bulei]
cs.sort(key=lambda c: (c['congshu'], c['key']))
if a.sample:
    by = {}
    for c in cs:
        by.setdefault(c['bulei'], []).append(c)
    step = {b: max(1, len(v) // a.n) for b, v in by.items()}
    pick, k = [], 0
    while len(pick) < a.n and k < 100:
        for b in sorted(by):
            j = k * step[b]
            if j < len(by[b]) and len(pick) < a.n:
                pick.append(by[b][j])
        k += 1
    cs = pick
else:
    cs = cs[a.offset:a.offset + a.n]
groups = []
for c in cs:
    ev = '同名丛书《%s》不同版次的同题子目%s；%s' % (c['congshu'], '（责任者 %s，%s）' % (c['author'], c['dyn'] or '朝代缺') if c['author'] else '（均未著撰人或仅一侧著）',
                                       '；'.join(c['evidence']))
    if c['juan']:
        ev += '；卷数 %s' % '／'.join(map(str, c['juan']))
    notes = {}
    for l in c['losers']:
        d = load(l)
        notes[l] = {'ai_note': d.get('ai_note'), 'description': (d.get('description') or {}).get('text') if isinstance(d.get('description'), dict) else d.get('description')}
    groups.append({'case_id': c['keeper'], 'cluster_id': 'jiayu-%s' % c['keeper'], 'type': 'work', 'keeper': c['keeper'], 'losers': c['losers'],
                   'keeper_source': '去重第二轮细拆单元新-子目甲余 同名丛书子目扫描（book-index %s）' % a.base, 'evidence': ev, 'rule': RULE_B if c.get('tier') == 'B' else RULE, 'why': ev,
                   'loser_original_notes': notes})
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '簇', sum(len(g['losers']) for g in groups), '条被并')
