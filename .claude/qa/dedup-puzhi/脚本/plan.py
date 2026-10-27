import csv,pickle,collections,json,sys,re
sys.path.insert(0,'/home/user/book-index/scripts')
import importlib.util
spec=importlib.util.spec_from_file_location('dc','/home/user/book-index/scripts/dedup-census.py'); dc=importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)
S='/tmp/claude-0/-home-user/5591bfc6-2a1d-5234-a874-c71f493524e6/scratchpad'
D=pickle.load(open('data.pkl','rb')); W=D['W']
exec(open('an.py').read().split('res=[]')[0].split('D=pickle')[1].split('\n',1)[1])  # UF, uf, pv
def fa(w):
    a=[x for x in W[w].get('authors') or [] if isinstance(x,dict)][:1]; return a[0] if a else {}
def named(w):
    n=dc.norm_name(fa(w).get('name')); return '' if n in dc.ANONYMOUS else n
groups=[]
for u in D['units']:
    ids=u[6].split(','); comps=collections.defaultdict(list)
    for i in ids: comps[uf.find(i)].append(i)
    cl=list(comps.values()); cross=[]
    for a in range(len(cl)):
        for b in range(a+1,len(cl)):
            for x in cl[a]:
                for y in cl[b]:
                    v=pv.get(frozenset((x,y)))
                    k=v[1] if v else 'none'; why=v[2] if v else ''
                    src=v[0] if v else ''
                    if k in('none','X'):
                        nx,ny=named(x),named(y); ex,ey=fa(x).get('entity_id'),fa(y).get('entity_id')
                        if nx and ny and ex and ey and ex!=ey and nx!=ny: k,why='C','首位责任者异人（entity 不同、名不同）：%s／%s'%(fa(x).get('name'),fa(y).get('name'))
                    cross.append((x,y,src,k,why))
    groups.append({'key':u[5],'bl':u[1],'ids':ids,'comps':cl,'cross':cross})
pickle.dump(groups,open('groups.pkl','wb'))
c=collections.Counter(); gneed=collections.Counter()
for g in groups:
    ks=set(k[:1] if k!='none' else 'none' for *_,k,_ in g['cross'])
    for *_,k,_ in g['cross']: c[k[:1] if k!='none' else 'none']+=1
    need=ks&{'A','B','X','n','E'}
    gneed[tuple(sorted(need))]+=1
print(c); print(gneed)
