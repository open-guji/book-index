import sys, csv, collections, json; sys.path.insert(0,'.')
from common import *
S=os.environ.get('SJJ_TMP', '/tmp/sjj-members')
I = load_idx(S+'/idx.pkl')
W = collections.defaultdict(list)
for w in I['Work']:
    if w['mg']: continue
    W[norm(w['title'])].append(w)
    if w.get('orig'): W[norm(w['orig'])].append(w)
rows = list(csv.reader(open(os.path.join(BI,'.claude/qa/sjj-collections/members-todo.tsv'), encoding='utf-8'), delimiter='\t'))[1:]
GEN = {norm(x) for x in ['老子道德經','老子道德真經','道德經','老子','道德真經','老子經','道德真經註','論語','孟子','莊子','列子']}
def auth_match(aus, w):
    wn = [nname(a[0]) for a in w['au']]
    for n, r, h in aus:
        nn = nname(n)
        for x in wn:
            if x and (nn == x or (len(nn)>=2 and x[:2]==nn[:2])): return True
    return False
import difflib
byau = collections.defaultdict(list)
for w in I['Work']:
    if w['mg']: continue
    for a_ in w['au']:
        if a_[0]: byau[nname(a_[0].lstrip('釋'))[:2]].append(w)
res = []
for i, r in enumerate(rows, 2):
    coll, ncid, t, au, vol, note, ex, ex2, st = r[:9]
    ct = clean_title(t); nt = norm(ct)
    aus, comp = parse_au(au)
    hit = W.get(nt, [])
    same = [h for h in hit if aus and auth_match(aus, h)]
    near = []
    if not hit:
        for k, v in W.items():
            if k != nt and len(k)>=4 and len(nt)>=4 and k not in GEN and (k in nt or nt in k) and min(len(k),len(nt))/max(len(k),len(nt))>=0.6:
                near.append((k, v[0]['id'], [a[0] for a in v[0]['au']]))
    simau = []
    for n, rl, h in (aus or []):
        for w in byau.get(nname(n.lstrip('釋'))[:2], []):
            r_ = difflib.SequenceMatcher(None, norm(w['title']), nt).ratio()
            if r_ >= 0.7: simau.append((round(r_,2), w['id'], w['title'], [a_[0] for a_ in w['au']]))
    res.append(dict(simau=sorted(set((a_,b,c,tuple(d)) for a_,b,c,d in simau),reverse=True)[:3], row=i, coll=coll, ncid=ncid, title=ct, raw=t, au=au, aus=aus, comp=comp, vol=vol, note=note, st=st, same=[(h['id'],h['title'],[a[0] for a in h['au']]) for h in same], hit=[(h['id'],h['title'],[a[0] for a in h['au']]) for h in hit], near=near[:3]))
pickle.dump(res, open(S+'/res.pkl','wb'))
c = collections.Counter()
for x in res:
    k = (x['st'], 'comp' if x['comp'] else ('same' if x['same'] else ('sim' if x['simau'] else ('hit' if x['hit'] else ('near' if x['near'] else 'none')))))
    c[k]+=1
for k,v in sorted(c.items()): print(k,v)
