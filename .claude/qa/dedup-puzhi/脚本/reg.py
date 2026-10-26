# 生成登记 TSV：每组生成树；SAME 对（经复核）视为并（不登记），E→C续修＋互链清单
import pickle,json,glob,collections,sys,os
H=os.path.dirname(os.path.abspath(__file__))
G=pickle.load(open(H+'/groups.pkl','rb'))
J={}
for f in sorted(glob.glob(H+'/judge/out-*.jsonl')):
    for l in open(f):
        d=json.loads(l); J[frozenset((d['a'],d['b']))]=d
SAMEOK=set()   # 复核确认的 SAME 对
if os.path.exists(H+'/verify/same_ok.json'):
    SAMEOK={frozenset(p) for p in json.load(open(H+'/verify/same_ok.json'))}
LBL={'zp':{'C':'C分立','S':'C异修','D':'D存疑'},'fz':{'C':'C分立','D':'D存疑','E':'C续修'}}
OV=json.load(open(H+'/verify/overrides.json'))
rows=[];elinks=[];merges=[];missing=0;pend=[]
for g in G:
    p={i:i for i in g['ids']}
    def f(x):
        while p[x]!=x: x=p[x]
        return x
    for c in g['comps']:
        for i in c[1:]: p[f(i)]=f(c[0])
    cands=[]
    for x,y,src,k,why in g['cross']:
        j=J.get(frozenset((x,y)))
        if j:
            v=j['verdict']
            if v=='SAME':
                if frozenset((x,y)) in SAMEOK: merges.append((g['key'],x,y,j['reason'])); cands.append((0,x,y,None,None))
                else: cands.append((3,x,y,'D存疑','agent判同书、复核未确认：'+j['reason']))
            elif v=='C': cands.append((1,x,y,'C分立',j['reason']))
            elif v=='E':
                cands.append((1,x,y,'C续修',j['reason']))
                if OV.get('|'.join(sorted((x,y))),('',))[0]=='C续修': elinks.append((x,y,j['reason']))
            else: cands.append((2,x,y,'D存疑',j['reason']))
        elif k=='none' or k[0] in 'ABXE' or (src=='fz' and k[0]=='D'):
            missing+=1; continue
        else:
            lab=LBL[src].get(k[0]) if src else 'C分立'
            if k[0]=='S': lab='C异修'
            cands.append((1 if lab.startswith('C') else 2,x,y,lab,('研-族谱口径：' if src=='zp' else '研-方志口径：' if src=='fz' else '')+why+'：《%s》'%g['key']))
    c2=[]
    for pri,x,y,lab,why in cands:
        o=OV.get('|'.join(sorted((x,y))))
        if o and lab: lab,why=o[0],o[1]+'（初判：'+why+'）'; pri=1 if lab.startswith('C') else 2
        c2.append((pri,x,y,lab,why))
    cands=c2
    for pri,x,y,lab,why in sorted(cands,key=lambda c:c[0]):
        if f(x)!=f(y):
            p[f(x)]=f(y)
            if lab: rows.append((x,y,lab,why))
    if len({f(i) for i in g['ids']})>1: pend.append(g['key'])
print('rows',len(rows),collections.Counter(r[2] for r in rows),'E',len(elinks),'merge',len(merges),'missing',missing,'pending groups',len(pend),pend[:20],file=sys.stderr)
pickle.dump({'rows':rows,'elinks':elinks,'merges':merges},open(H+'/reg.pkl','wb'))
