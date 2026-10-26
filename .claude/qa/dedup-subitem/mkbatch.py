#!/usr/bin/env python3
"""由 cand_sub.py 产出的候选生成 batch.json（供 ../dedup-part4/apply_4.py 式的 apply_sub.py 使用）。
用法：mkbatch.py <cand_sub.json> <输出目录> [--bulei 經部 史部] [--n 20] [--offset 0] [--exclude 已用id.txt] [--base sha]"""
import argparse, glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
RULE = '去重方案子目-甲：同名叢書不同版次中的同題子目 Work（卷數、責任者不矛盾），A 档机械并'
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
ap = argparse.ArgumentParser(); ap.add_argument('cand'); ap.add_argument('out')
ap.add_argument('--bulei', nargs='+'); ap.add_argument('--n', type=int, default=20); ap.add_argument('--offset', type=int, default=0)
ap.add_argument('--base', default=''); ap.add_argument('--exclude')
a = ap.parse_args()
ex = set(open(a.exclude).read().split()) if a.exclude else set()
cs = [c for c in json.load(open(a.cand, encoding='utf-8')) if (not a.bulei or c['bulei'] in a.bulei) and not ({c['keeper'], *c['losers']} & ex)]
cs.sort(key=lambda c: (c['key'], c['keeper']))
cs = cs[a.offset:a.offset + a.n]
groups = []
for c in cs:
    for i in [c['keeper'], *c['losers']]:
        assert not load(i).get('merged_into'), i
    ev = '同名叢書（%s）不同版次之同題子目：%s；卷數%s；子目責任者%s；叢書撰者%s' % (
        c['parent'], '；'.join(c['evidence']), '／'.join(map(str, c['juan'])) or '皆缺', c['author'] or '皆缺', '、'.join(c['col_authors']) or '缺')
    notes = {}
    for l in c['losers']:
        d = load(l); notes[l] = {'ai_note': d.get('ai_note'), 'description': (d.get('description') or {}).get('text') if isinstance(d.get('description'), dict) else d.get('description')}
    groups.append({'case_id': c['keeper'], 'cluster_id': 'sub-%s' % c['keeper'], 'type': 'work', 'keeper': c['keeper'], 'losers': c['losers'],
                   'keeper_source': '去重方案子目-甲 同名叢書子目扫描（book-index %s）' % a.base, 'evidence': ev, 'rule': RULE, 'why': ev,
                   'loser_original_notes': notes})
os.makedirs(a.out, exist_ok=True)
json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
