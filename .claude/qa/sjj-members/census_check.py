"""本地模擬 dedup-census 的 W 段：新建 Work 所在的同題組是否經 related_works／白名單連成一片。"""
import sys, os, re, glob, json, pickle, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from common import *
from scan import VARIANTS
idx = sys.argv[1]
I = pickle.load(open(idx, 'rb'))
BR = re.compile(r'（[^（）]*）|\([^()]*\)|〔[^〔〕]*〕|【[^【】]*】|\[[^\[\]]*\]')
PU = re.compile(r'[\s·・、，,。．.：:；;「」『』《》〈〉()（）〔〕【】\[\]]')
def cn(s): return PU.sub('', BR.sub('', s or '').translate(VARIANTS))
res = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'result.json'), encoding='utf-8'))
new = {}
for wid, p in res['work'].items():
    d = json.load(open(os.path.join(BI, p), encoding='utf-8')); new[wid] = d
W = {w['id']: (w['title'], w['rel']) for w in I['Work'] if not w['mg']}
for wid, d in new.items(): W[wid] = (d['title'], [r['id'] for r in d.get('related_works', [])])
groups = collections.defaultdict(list)
for wid, (t, rel) in W.items(): groups[cn(t)].append(wid)
wl = set()
for f in glob.glob(os.path.join(BI, '.claude/qa/dedup-judged/*.tsv')):
    for l in open(f, encoding='utf-8'):
        if l.startswith('#') or not l.strip(): continue
        c = l.rstrip('\n').split('\t')
        if len(c) >= 2: wl.add((c[0], c[1]))
bad = 0
for k, ms in groups.items():
    if not any(m in new for m in ms) or len(ms) < 2: continue
    p = {m: m for m in ms}
    def f(x):
        while p[x] != x: p[x] = p[p[x]]; x = p[x]
        return x
    s = set(ms)
    for m in ms:
        for r in W[m][1]:
            if r in s: p[f(m)] = f(r)
    for a, b in wl:
        if a in s and b in s: p[f(a)] = f(b)
    comps = len({f(m) for m in ms})
    if comps > 1:
        bad += 1; print('未判組', k, comps, [m for m in ms if m in new], len(ms))
print('含新建 Work 的同題組檢查完；未判組', bad)
