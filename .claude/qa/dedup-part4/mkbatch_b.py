#!/usr/bin/env python3
"""4a-B：由逐条核结果 TSV（无责id、有责id、判定、证据类型、依据）生成 batch.json，只收「同书」且证据类型属严格清单者。
用法：mkbatch_b.py <输出目录> <结果.tsv>... [--base sha]；同时把分立／存疑写入 <输出目录>/judged.tsv（dedup-judged 格式）"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
OK = {'子目同书', '子目同書', '同源', '版本馆藏', '版本館藏', '自证', '自證', '辑佚同本', '輯佚同本', '题含作者', '題含作者'}
EDROLE = {'編', '輯', '編輯', '輯錄', '纂', '彙編', '匯編'}
RULE = '去重方案部分4a-B：同题、卷数相同、一侧无责任者，逐条子 agent 核得实质证据（同源／版本馆藏／原文自证／题含作者名号／同一辑佚本）后 B 档并'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
STRICT = '--strict' in sys.argv   # 4a-B 扩展（卷缺对、子集对）复核后加严：见 b-02/抽检.md
base = sys.argv[sys.argv.index('--base') + 1] if '--base' in sys.argv else ''
if base in args: args.remove(base)
out, files = args[0], args[1:]
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
def _juans(w):
    import re
    CN = dict(zip('〇零一二兩三四五六七八九', [0, 0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9]))
    def cnum(t):
        n = cur = 0
        for ch in t:
            if ch in CN: cur = CN[ch]
            elif ch in '十百千': n += (cur or 1) * {'十': 10, '百': 100, '千': 1000}[ch]; cur = 0
        return n + cur or None
    s = set()
    j = w.get('juan_count')
    if isinstance(j, dict) and j.get('number'): s.add(j['number'])
    for i in w.get('indexed_by') or []:
        m = re.search(r'([〇零一二兩三四五六七八九十百千]+)卷', (i.get('title_info') or '') if isinstance(i, dict) else '')
        if m and cnum(m.group(1)): s.add(cnum(m.group(1)))
    return s
def strict_reason(a, n, kind):
    A, N = load(a), load(n)
    if any(isinstance(x, dict) and (x.get('role') or '') in EDROLE for x in N.get('authors') or []):
        return '有责任者一侧含編／輯類责任者（辑者或丛书编者），并后原书作者归属不清'
    if '□' in json.dumps(A, ensure_ascii=False):
        return '无责任者一侧著录有缺字责任者（□），责任者另有其人'
    if kind in ('题含作者', '題含作者'):
        ja, jn = _juans(A), _juans(N)
        if ja and jn and not (ja & jn): return '仅凭题含作者名且两侧卷数不合（%s／%s）' % (sorted(ja), sorted(jn))
    return ''
groups, judged, seen = {}, [], set()
for f in files:
    for line in open(f, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) < 5: continue
        a, n, v, kind, why = c[:5]
        v = v.replace('書', '书').replace('異', '异')
        if (a, n) in seen: continue
        seen.add((a, n))
        role = ((load(n).get('authors') or [{}])[0] or {}).get('role') or ''
        if v == '同书' and kind in OK and role in EDROLE and kind not in ('辑佚同本', '輯佚同本'):
            v, why = '存疑', '有责任者一侧首位责任方式为「%s」，或只是丛书编者（复核口径：此类不并）；原判：%s' % (role, why)
        if v == '同书' and STRICT:
            r = strict_reason(a, n, kind)
            if r: v, why = '存疑', '%s（4a-B 扩展复核口径）；原判：%s' % (r, why)
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
