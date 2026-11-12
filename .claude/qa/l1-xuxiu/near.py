import pickle,collections,difflib
from build_idx import norm_t
W=pickle.load(open('works.pkl','rb')); rows=pickle.load(open('rows_t.pkl','rb'))
tri=collections.defaultdict(set); T={}
for i,w in W.items():
    for t in [w['t']]+w['at']:
        if not t: continue
        n=norm_t(t); T.setdefault(i,[]).append(n)
        for k in range(len(n)-2): tri[n[k:k+3]].add(i)
res={}
C=[r for r in rows if r['tier']=='C' and len(norm_t(r['main']))>=4]
print(len(C))
for r in C:
    n=norm_t(r['main']); cnt=collections.Counter()
    for k in range(len(n)-2):
        s=tri.get(n[k:k+3])
        if s and len(s)<400:
            for i in s: cnt[i]+=1
    best=[]
    for i,c in cnt.most_common(15):
        for t in T[i]:
            q=difflib.SequenceMatcher(None,n,t).ratio()
            best.append((q,i,t))
    best.sort(reverse=True)
    if best and best[0][0]>=0.8: res[r['k']]=best[:3]
print(len(res))
pickle.dump(res,open('near.pkl','wb'))
import random
random.seed(5)
for k in random.sample(list(res),40):
    r=rows[k]; q,i,t=res[k][0]; print(r['name'],'->',t,round(q,2),W[i]['au'][:1],W[i]['dyn'])
