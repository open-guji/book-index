#!/usr/bin/env python3
"""4a-B：由逐条核结果 TSV（无责id、有责id、判定、证据类型、依据）生成 batch.json，只收「同书」且证据类型属严格清单者。
用法：mkbatch_b.py <输出目录> <结果.tsv>... [--base sha]；同时把分立／存疑写入 <输出目录>/judged.tsv（dedup-judged 格式）"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
OK = {'同源', '版本馆藏', '自证', '自證', '辑佚同本', '题含作者', '題含作者'}
RULE = '去重方案部分4a-B：同题、卷数相同、一侧无责任者，逐条子 agent 核得实质证据（同源／版本馆藏／原文自证／题含作者名号／同一辑佚本）后 B 档并'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
base = sys.argv[sys.argv.index('--base') + 1] if '--base' in sys.argv else ''
if base in args: args.remove(base)
out, files = args[0], args[1:]
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
groups, judged, seen = {}, [], set()
for f in files:
    for line in open(f, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) < 5: continue
        a, n, v, kind, why = c[:5]
        v = v.replace('書', '书').replace('異', '异')
        if (a, n) in seen: continue
        seen.add((a, n))
        if v == '同书' and kind in OK:
            if load(a).get('merged_into') or load(n).get('merged_into'): continue
            groups.setdefault(n, []).append((a, kind, why))
        else:
            judged.append((a, n, 'C' if v == '异书' else 'D', why))
bat = []
for n, ls in groups.items():
    k = load(n); ev = '；'.join(f'《{load(a).get("title")}》（{a}，無責任者）：{kind}——{why}' for a, kind, why in ls)
    ev = f'同題同卷：有責任者《{k.get("title")}》（{(k.get("authors") or [{}])[0].get("name")}）；{ev}'
    notes = {a: {'ai_note': load(a).get('ai_note'), 'description': (load(a).get('description') or {}).get('text') if isinstance(load(a).get('description'), dict) else load(a).get('description')} for a, _, _ in ls}
    bat.append({'case_id': n, 'cluster_id': '4aB-%s' % n, 'type': 'work', 'keeper': n, 'losers': [a for a, _, _ in ls],
                'keeper_source': '去重方案部分4a-B 逐条核（book-index %s）' % base, 'evidence': ev, 'rule': RULE, 'why': ev, 'loser_original_notes': notes})
os.makedirs(out, exist_ok=True)
json.dump({'groups': bat}, open(os.path.join(out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(out, 'judged.tsv'), 'w', encoding='utf-8').write(''.join('\t'.join(r) + '\n' for r in judged))
print(len(bat), '组', sum(len(g['losers']) for g in bat), '条被并；分立/存疑', len(judged))
