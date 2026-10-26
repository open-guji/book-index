#!/usr/bin/env python3
"""把 split_works.py 出的 batch-whole.json 补成 apply_3a3.py 的 batch.json（补 case_id、keeper_source、loser_original_notes）。用法：mk_whole.py <批次目录>"""
import glob, json, os, sys
D = sys.argv[1]; ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
def load(i):
    return json.load(open(glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json'))[0], encoding='utf-8'))
out = []
for g in json.load(open(os.path.join(D, 'batch-whole.json'), encoding='utf-8'))['groups']:
    k = g['keeper']; recs = {i: load(i) for i in [k] + g['losers']}
    if any(r.get('merged_into') for r in recs.values()):
        print('跳过（已被并）', g['cluster_id'], file=sys.stderr); continue
    why = '异题名同书（先拆后并：先把混入的同名别书著录拆出）：《%s》／%s；%s' % (recs[k].get('title'), '、'.join('《%s》' % recs[l].get('title') for l in g['losers']), g['why'])
    notes = {l: {f: recs[l].get(f) for f in ('ai_note', 'description') if recs[l].get(f)} for l in g['losers']}
    out.append(dict(g, case_id='A3-%s' % k, cluster_id='3a3-%s' % k, why=why, evidence=why,
                    rule='去重方案3a-3：异题名同书，著录原文自证（一名／又名／原名／即）B 档逐条复核并；先拆后并',
                    keeper_source='去重方案 3a-3 一名／又名自证扫描；先拆后并',
                    loser_original_notes={l: n for l, n in notes.items() if n}))
json.dump({'groups': out}, open(os.path.join(D, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('整并', len(out), '组', file=sys.stderr)
