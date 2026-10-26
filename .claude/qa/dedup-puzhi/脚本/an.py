import csv,pickle,collections,os,sys
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=pickle.load(open(S+'/w/data.pkl','rb'))
class UF:
    def __init__(s): s.p={}
    def find(s,x):
        s.p.setdefault(x,x)
        while s.p[x]!=x: s.p[x]=s.p[s.p[x]]; x=s.p[x]
        return x
    def union(s,a,b): s.p[s.find(a)]=s.find(b)
uf=UF()
for a,b in D['links']: uf.union(a,b)
pv={}
for r in csv.reader(open(S+'/zp2/族谱逐对判定-20261025.tsv'),delimiter='\t'):
    if len(r)>4 and r[2] in('C','S','D','B候选','B候选·逐条核'): pv[frozenset(r[:2])]=('zp',r[2],r[4])
fzrows=list(csv.reader(open(S+'/fz/判定-全部对.tsv'),delimiter='\t'))
hdr=fzrows[0]
for r in fzrows[1:]:
    if len(r)>3: pv[frozenset(r[1:3])]=('fz',r[3],r[3])
res=[]
for u in D['units']:
    ids=u[6].split(','); comps=collections.defaultdict(list)
    for i in ids: comps[uf.find(i)].append(i)
    cl=list(comps.values())
    # cross pairs
    kinds=collections.Counter()
    for a in range(len(cl)):
        for b in range(a+1,len(cl)):
            for x in cl[a]:
                for y in cl[b]:
                    v=pv.get(frozenset((x,y)))
                    kinds[(v[0],v[1][:1]) if v else ('none','')]+=1
    res.append((u[5],len(ids),len(cl),dict(kinds)))
src=collections.Counter()
for t,n,c,k in res:
    s=set(x[0] for x in k); src[tuple(sorted(s))]+=1
print(src)
pickle.dump(res,open(S+'/w/res.pkl','wb'))
