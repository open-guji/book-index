"""汇总机判（pairs.tsv）与子 agent 逐组判定（verdict-*.json），产出：
  $OUT/clusters.json   可并簇（每簇 keeper、losers、档、依据）
  $OUT/judged.tsv      簇间（keeper 对 keeper）分立 C／存疑 D 的生成树边，写入 dedup-judged 用
  $OUT/conflict.tsv    agent 判同但机判 C 的对（需人看）
用法：BOOK_INDEX=. OUT=... python3 combine.py [--exclude 簇内id ...]"""
import csv, glob, json, os, sys, collections, itertools
ROOT = os.environ.get('BOOK_INDEX', '.'); S = os.environ.get('OUT', '/tmp/yiming')
ACC = '--accept-conflicts' in sys.argv  # 冲突对已人工逐条看过、认可逐组判定
EXC = set([x for x in sys.argv[sys.argv.index('--exclude') + 1:] if not x.startswith('--')]) if '--exclude' in sys.argv else set()
feat = json.load(open(S + '/feat.json'))
P = list(csv.DictReader(open(S + '/pairs.tsv'), delimiter='\t'))
V = {}
for f in sorted(glob.glob(S + '/verdict-*.json')):
    for v in json.load(open(f)): V[int(v['g'])] = v
M = collections.defaultdict(dict)
for p in P: M[int(p['组'])][frozenset((p['Work甲'], p['Work乙']))] = (p['判定'], p['依据'])
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
def kkey(w):
    sub = '所屬叢書記錄' in (w.get('ai_note') or '')
    return (not sub, bool(w.get('authors')), len(w.get('indexed_by') or []), len(w.get('resources') or []), -int(w['id'], 36))
clusters, judged, conflict, missing = [], [], [], []
for gi, g in enumerate(feat):
    ids = [w['id'] for w in g['works']]
    m = M[gi]; v = V.get(gi)
    need = any(x[0] in ('R', 'A') for x in m.values())
    if need and v is None: missing.append(gi); continue
    par = {i: i for i in ids}
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    why = collections.defaultdict(list); lvl = collections.defaultdict(set)
    doubt = {}
    if v:
        for d in v.get('doubt') or []:
            for a, b in itertools.combinations([x for x in d['ids'] if x in par], 2): doubt[frozenset((a, b))] = d['why']
        for s in v.get('same') or []:
            sid = [x for x in s['ids'] if x in par]
            bad = [(a, b) for a, b in itertools.combinations(sid, 2) if m.get(frozenset((a, b)), ('',))[0] in ('C', 'D')]
            if bad:
                for a, b in bad: conflict.append((gi, g['key'], a, b, m[frozenset((a, b))][1], s['why']))
                if not ACC: continue
            for x in sid[1:]: par[f(x)] = f(sid[0])
            r = f(sid[0]); why[r].append(s['why']); lvl[r].add(s.get('level', 'B'))
        for k, (vv, w) in m.items():  # 机判 A 而 agent 未判同 → 存疑
            a, b = tuple(k)
            if vv == 'A' and f(a) != f(b): doubt.setdefault(k, '機判同撰人（%s），逐組複核未判同，待核' % w)
    comp = collections.defaultdict(list)
    for i in ids: comp[f(i)].append(i)
    # 合并后的 why/lvl 归到最终根
    W2 = collections.defaultdict(list); L2 = collections.defaultdict(set)
    for r in list(why): W2[f(r)] += why[r]; L2[f(r)] |= lvl[r]
    keep = {}
    for r, ms in comp.items():
        ds = {i: load(i) for i in ms}
        keep[r] = k = max(ms, key=lambda i: kkey(ds[i]))
        if len(ms) > 1 and not set(ms) & EXC and not any(ds[i].get('merged_into') for i in ms):
            clusters.append(dict(g=gi, key=g['key'], keeper=k, losers=sorted(set(ms) - {k}), level='/'.join(sorted(L2[r])) or 'B',
                                 why='；'.join(dict.fromkeys(W2[r]))))
    # 簇间边：D 优先记（任一跨簇对存疑即 D），否则 C；生成树
    roots = sorted(comp)
    edges = []
    for r1, r2 in itertools.combinations(roots, 2):
        ds = [doubt[frozenset((a, b))] for a in comp[r1] for b in comp[r2] if frozenset((a, b)) in doubt]
        mv = [m.get(frozenset((a, b)), ('', '')) for a in comp[r1] for b in comp[r2]]
        dm = [w for vv, w in mv if vv == 'D']
        if ds or dm: edges.append((1, r1, r2, 'D', (ds or dm)[0]))
        else:
            cw = [w for vv, w in mv if vv == 'C']
            edges.append((0, r1, r2, 'C', cw[0] if cw else ((v or {}).get('distinct_why') or '同題異書')))
    up = {r: r for r in roots}
    def u(x):
        while up[x] != x: up[x] = up[up[x]]; x = up[x]
        return x
    for _, r1, r2, vv, w in sorted(edges, key=lambda e: -e[0]):  # 存疑边全记，分立边只补生成树
        if vv == 'D' or u(r1) != u(r2):
            up[u(r1)] = u(r2); judged.append((keep[r1], keep[r2], vv, '%s：%s' % (g['key'], w)))
json.dump(clusters, open(S + '/clusters.json', 'w'), ensure_ascii=False, indent=1)
with open(S + '/judged.tsv', 'w') as fo:
    for r in judged: fo.write('\t'.join(r) + '\n')
with open(S + '/conflict.tsv', 'w') as fo:
    for r in conflict: fo.write('\t'.join(map(str, r)) + '\n')
c = collections.Counter(x[2] for x in judged)
print('簇', len(clusters), '被并', sum(len(x['losers']) for x in clusters), '档', collections.Counter(x['level'] for x in clusters))
print('登记', dict(c), '冲突', len(conflict), '缺判组', missing)
