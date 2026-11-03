#!/usr/bin/env python3
"""补 Work.dynasty_basis 缺口（schema 审查可做可不做 第 4 组）。默认只报告，--apply 写入。
只补机械可推的：
  A. dynasty == authors[0].dynasty         → 「author_propagation：據 authors[0].dynasty「X」」
  C. 无作者或作者无朝代，而 period_basis 正文已含该朝代名 → 「與 period 同源判定，見 period_basis」
  B. authors[0] 无 dynasty 但有 entity_id，且 Entity.dynasty == Work.dynasty
                                           → 「author_propagation：據 authors[0] 所繫 Entity「名」之 dynasty「X」」
其余（无作者、作者朝代与 Work 不同、作者无朝代且无实体可证）写入清单 --list FILE，不猜。"""
import json, glob, sys, os
R = '.'; APPLY = '--apply' in sys.argv
LIST = sys.argv[sys.argv.index('--list') + 1] if '--list' in sys.argv else None
def entity(i):
    t = i[-3:]; fs = glob.glob(f'{R}/Entity/{t[0]}/{t[1]}/{t[2]}/{i}-*.json')
    return json.load(open(fs[0], encoding='utf-8')) if len(fs) == 1 else None
n = {'A': 0, 'B': 0, 'C': 0, 'rest': 0}; rest = []
for p in glob.iglob(f'{R}/Work/*/*/*/*.json'):
    s = open(p, encoding='utf-8').read()
    if '"dynasty"' not in s: continue
    d = json.loads(s)
    if 'dynasty' not in d or 'dynasty_basis' in d or d.get('merged_into'): continue
    nl = '\n' if s.endswith('\n') else ''
    a = d.get('authors') or []; a0 = a[0] if a else {}
    basis = None
    if a0.get('dynasty') == d['dynasty']:
        basis = f"author_propagation：據 authors[0].dynasty「{d['dynasty']}」"; k = 'A'
    elif a0.get('entity_id') and not a0.get('dynasty'):
        e = entity(a0['entity_id'])
        if e and e.get('dynasty') == d['dynasty']:
            basis = f"author_propagation：據 authors[0] 所繫 Entity「{a0.get('name')}」之 dynasty「{d['dynasty']}」"; k = 'B'
    if basis is None and not a0.get('dynasty') and d['dynasty'] in (d.get('period_basis') or ''):
        basis = '與 period 同源判定，見 period_basis（该条朝代与时代轴出自同一依据）'; k = 'C'
    if basis is None:
        n['rest'] += 1
        reason = 'noauth' if not a else ('a0_dyn_differs' if a0.get('dynasty') else 'a0_nodyn_unproven')
        rest.append((d['id'], d['title'], d['dynasty'], a0.get('dynasty') or '', a0.get('entity_id') or '', reason, (d.get('period_basis') or '')[:80])); continue
    n[k] += 1
    ind = 2
    for l in s.split('\n')[1:3]:
        if len(l) - len(l.lstrip()): ind = len(l) - len(l.lstrip()); break
    if json.dumps(d, ensure_ascii=False, indent=ind) + nl != s:
        n['rest'] += 1; rest.append((d['id'], d['title'], d['dynasty'], '', '', 'format_nonstandard', '')); continue
    if APPLY:
        new = {}
        for kk, v in d.items():
            new[kk] = v
            if kk == 'dynasty': new['dynasty_basis'] = basis
        open(p, 'w', encoding='utf-8').write(json.dumps(new, ensure_ascii=False, indent=ind) + nl)
print(n)
if LIST:
    with open(LIST, 'w', encoding='utf-8') as f:
        f.write('work_id\ttitle\tdynasty\tauthors[0].dynasty\tauthors[0].entity_id\treason\tperiod_basis\n')
        for r in rest: f.write('\t'.join(r) + '\n')
