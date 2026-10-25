#!/usr/bin/env python3
"""由候选 JSON（cand_alpha 产出）生成 batch.json。
用法：mkbatch.py <候选.json> <输出目录> --bulei 經部 --n 20 [--skip-ids 已用.txt] [--base sha]"""
import argparse, glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
RULE = '去重方案部分4a-α：叢書子目（總目未著撰人）按所屬叢書撰者推定責任者，與同題單行本 Work 首位責任者同人，A 档机械并'
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
ap = argparse.ArgumentParser(); ap.add_argument('cand'); ap.add_argument('out')
ap.add_argument('--bulei', nargs='+'); ap.add_argument('--n', type=int, default=20); ap.add_argument('--offset', type=int, default=0)
ap.add_argument('--base', default=''); ap.add_argument('--exclude', help='每行一个 Work id，命中即跳过整组')
a = ap.parse_args()
ex = set(open(a.exclude).read().split()) if a.exclude else set()
cs = [c for c in json.load(open(a.cand, encoding='utf-8')) if (not a.bulei or c['bulei'] in a.bulei)
      and not ({c['keeper'], *c['losers']} & ex)]
cs.sort(key=lambda c: c['key'])
cs = cs[a.offset:a.offset + a.n]
groups = []
for c in cs:
    ev = '同題：單行本《%s》%s（%s）；%s' % (c['keeper_title'], c['author'], c['dyn'] or '朝代缺', '；'.join(c['evidence']))
    notes = {}
    for l in c['losers']:
        d = load(l); notes[l] = {'ai_note': d.get('ai_note'), 'description': (d.get('description') or {}).get('text') if isinstance(d.get('description'), dict) else d.get('description')}
    groups.append({'case_id': c['keeper'], 'cluster_id': '4a-%s' % c['keeper'], 'type': 'work', 'keeper': c['keeper'], 'losers': c['losers'],
                   'keeper_source': '去重方案部分4 一侧无责任者扫描（book-index %s）' % a.base, 'evidence': ev, 'rule': RULE, 'why': ev,
                   'loser_original_notes': notes})
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
