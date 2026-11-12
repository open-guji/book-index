"""对 c1_ks 做包含关系复核：已有题名 t 与新题 n 互相包含且 短/长≥0.6 → 待核（C2），不自动新建。输出 c1_final.pkl／c2.tsv"""
import pickle,collections,csv
from build_idx import norm_t
W=pickle.load(open('works.pkl','rb')); rows=pickle.load(open('rows_t.pkl','rb')); ks=pickle.load(open('c1_ks.pkl','rb'))
tri=collections.defaultdict(set); T={}
for i,w in W.items():
    for t in [w['t']]+w['at']:
        if not t: continue
        n=norm_t(t)
        if len(n)<3: continue
        T.setdefault(i,[]).append(n)
        for k in range(len(n)-2): tri[n[k:k+3]].add(i)
keep=[];hold=[]
for k in ks:
    r=rows[k]; n=norm_t(r['main']); cnt=collections.Counter()
    for j in range(len(n)-2):
        s=tri.get(n[j:j+3])
        if s and len(s)<3000:
            for i in s: cnt[i]+=1
    hit=None
    for i,c in cnt.most_common(60):
        for t in T[i]:
            if t!=n and (n in t or t in n):
                a,b=sorted([len(n),len(t)])
                if len(t)>=3 and a/b>=0.6: hit=(i,t); break
        if hit: break
    (hold if hit else keep).append((k,hit))
print(len(keep),len(hold))
pickle.dump([k for k,_ in keep],open('c1_final.pkl','wb'))
with open('c2_contain.tsv','w',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['k','部类','书名','已有Work','已有题名','作者'])
    for k,(i,t) in hold: w.writerow([k,rows[k]['sort'],rows[k]['name'],i,W[i]['t'],','.join(W[i]['au'][:2])])
