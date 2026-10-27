#!/usr/bin/env python3
"""新-无责任者余（4a-B 口径）：由逐对判定 TSV 生成 batch.json 与 judged.tsv。
用法：mkbatch_nr.py <输出目录> <pairs.tsv> <groups.jsonl> <判定.tsv>... [--gids 1,2,...] [--base sha]
pairs.tsv：gid、类别（一侧有一侧无／全无）、id甲、id乙；判定 TSV：id甲、id乙、判定、证据类型、依据。
一侧有一侧无：无责任者并入有责任者，沿用 ../dedup-part4/mkbatch_b.py 的加严口径（編輯类责任者、缺字责任者、卷数不合）。
全无：同书对取连通分量；分量内若有一对判非同书则整分量改存疑；keeper 取挂 Book 最多者（同则卷数有著录者、再取 id 小者）。
同一条无责任者 Work 判与两条以上不同 Work 同书时，全部改存疑。"""
import glob, json, os, sys, re, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
OK = {'同源', '版本馆藏', '版本館藏', '自证', '自證', '辑佚同本', '輯佚同本', '题含作者', '題含作者'}
EDROLE = {'編', '輯', '編輯', '輯錄', '纂', '彙編', '匯編'}
RULE = '去重方案细拆单元「新-无责任者余」（4a-B 口径）：同题、卷数相合、至少一侧无责任者，逐对子 agent 核得实质证据（同源／版本馆藏／原文自证／题含作者名号／同一辑佚本）后 B 档并'
argv = sys.argv[1:]
def opt(k):
    if k in argv: i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return v
    return ''
gids = set(opt('--gids').split(',')) - {''}; base = opt('--base')
out, pairsf, groupsf, files = argv[0], argv[1], argv[2], argv[3:]
_cache = {}
def load(i):
    if i not in _cache:
        p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
        _cache[i] = json.load(open(p[0], encoding='utf-8'))
    return _cache[i]
CN = dict(zip('〇零一二兩三四五六七八九', [0, 0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9]))
def cnum(t):
    n = cur = 0
    for ch in t:
        if ch in CN: cur = CN[ch]
        elif ch in '十百千': n += (cur or 1) * {'十': 10, '百': 100, '千': 1000}[ch]; cur = 0
    return n + cur or None
def juans(w):
    s = set(); j = w.get('juan_count')
    if isinstance(j, dict) and j.get('number'): s.add(j['number'])
    for i in w.get('indexed_by') or []:
        m = re.search(r'([〇零一二兩三四五六七八九十百千]+)卷', (i.get('title_info') or '') if isinstance(i, dict) else '')
        if m and cnum(m.group(1)): s.add(cnum(m.group(1)))
    return s
nbooks = {}; gtitle = {}
for l in open(groupsf, encoding='utf-8'):
    g = json.loads(l)
    for w in g['works']: nbooks[w['id']] = w.get('nbooks', 0)
kind = {}; gid_of = {}
for l in open(pairsf, encoding='utf-8'):
    g, k, a, b = l.rstrip('\n').split('\t'); kind[(a, b)] = k; gid_of[(a, b)] = g
res = {}
for f in files:
    for line in open(f, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) < 5: continue
        a, b, v, ev, why = c[:5]
        if (a, b) not in kind: continue
        if gids and gid_of[(a, b)] not in gids: continue
        v = v.replace('書', '书').replace('異', '异')
        res.setdefault((a, b), [a, b, v, ev, why])
def downgrade(r, reason):
    r[2] = '存疑'; r[4] = '%s；原判：%s' % (reason, r[4])
for (a, b), r in res.items():
    if r[2] != '同书': continue
    if r[3] not in OK: downgrade(r, '证据类型不在严格清单'); continue
    A, N = load(a), load(b)
    if A.get('merged_into') or N.get('merged_into'): r[2] = 'skip'; continue
    ja, jn = juans(A), juans(N)
    if ja and jn and not (ja & jn): downgrade(r, '两侧卷数不合（%s／%s）' % (sorted(ja), sorted(jn))); continue
    if kind[(a, b)] == '一侧有一侧无':
        role = ((N.get('authors') or [{}])[0] or {}).get('role') or ''
        if role in EDROLE and r[3] not in ('辑佚同本', '輯佚同本'):
            downgrade(r, '有责任者一侧首位责任方式为「%s」，或只是丛书编者' % role); continue
        if any(isinstance(x, dict) and (x.get('role') or '') in EDROLE for x in N.get('authors') or []) and r[3] not in ('辑佚同本', '輯佚同本'):
            downgrade(r, '有责任者一侧含編／輯類责任者'); continue
        if '□' in json.dumps(A.get('authors') or [], ensure_ascii=False) + json.dumps(A.get('indexed_by') or [], ensure_ascii=False):
            downgrade(r, '无责任者一侧著录有缺字责任者（□）'); continue
# 一侧有一侧无：一条无责任者 Work 只能并入一处
cnt = collections.Counter(a for (a, b), r in res.items() if r[2] == '同书' and kind[(a, b)] == '一侧有一侧无')
for (a, b), r in res.items():
    if r[2] == '同书' and kind[(a, b)] == '一侧有一侧无' and cnt[a] > 1: downgrade(r, '同一无责任者条判与多条有责任者 Work 同书，归属不定')
# 全无：连通分量
par = {}
def fd(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for (a, b), r in res.items():
    if kind[(a, b)] == '全无' and r[2] == '同书': par[fd(a)] = fd(b)
comp = collections.defaultdict(set)
for x in list(par): comp[fd(x)].add(x)
for (a, b), r in res.items():
    if kind[(a, b)] == '全无' and r[2] != '同书' and r[2] != 'skip' and a in par and b in par and fd(a) == fd(b):
        bad = fd(a)
        for (x, y), s in res.items():
            if kind[(x, y)] == '全无' and s[2] == '同书' and x in par and fd(x) == bad: downgrade(s, '同组传递不一致（分量内另有一对判非同书）')
groups = collections.OrderedDict()
for (a, b), r in res.items():
    if r[2] != '同书': continue
    if kind[(a, b)] == '一侧有一侧无': groups.setdefault(b, []).append((a, r[3], r[4]))
for root, mem in comp.items():
    live = [x for x in mem if any(r[2] == '同书' and (x in (a, b)) and kind[(a, b)] == '全无' for (a, b), r in res.items())]
    if len(live) < 2: continue
    k = sorted(live, key=lambda x: (-nbooks.get(x, 0), not juans(load(x)), x))[0]
    for (a, b), r in res.items():
        if kind[(a, b)] == '全无' and r[2] == '同书' and a in live and b in live:
            l = b if a == k else a if b == k else None
            if l is None: l = a if a != k else b   # 非 keeper 之间的对：仍并入 keeper
            if l not in [x for x, _, _ in groups.get(k, [])]: groups.setdefault(k, []).append((l, r[3], r[4] + '（與 %s／%s 判同書）' % (a, b)))
judged = [(r[0], r[1], 'C' if r[2] == '异书' else 'D', r[4]) for r in res.values() if r[2] in ('异书', '存疑')]
def au(w): return (w.get('authors') or [{}])[0].get('name') if w.get('authors') else None
bat = []
for k, ls in groups.items():
    K = load(k)
    ev = '；'.join(f'《{load(a).get("title")}》（{a}）：{kind_}——{why}' for a, kind_, why in ls)
    head = f'同題同卷：保留《{K.get("title")}》（{au(K) or "無責任者"}）'
    ev = f'{head}；{ev}'
    notes = {a: {'ai_note': load(a).get('ai_note'), 'description': (load(a).get('description') or {}).get('text') if isinstance(load(a).get('description'), dict) else load(a).get('description')} for a, _, _ in ls}
    bat.append({'case_id': k, 'cluster_id': 'NR-%s' % k, 'type': 'work', 'keeper': k, 'losers': [a for a, _, _ in ls],
                'keeper_source': '去重细拆单元 新-无责任者余 逐对核（book-index %s）' % base, 'evidence': ev, 'rule': RULE, 'why': ev, 'loser_original_notes': notes})
os.makedirs(out, exist_ok=True)
json.dump({'groups': bat}, open(os.path.join(out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(out, 'judged.tsv'), 'w', encoding='utf-8').write(''.join('\t'.join(r) + '\n' for r in judged))
print(len(bat), '组', sum(len(g['losers']) for g in bat), '条被并；分立/存疑', len(judged), '；未判', sum(1 for p in kind if (not gids or gid_of[p] in gids) and p not in res))
