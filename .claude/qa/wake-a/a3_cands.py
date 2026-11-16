# -*- coding: utf-8 -*-
import sys; sys.path.insert(0,'/tmp/wa3')
from a3_resolve import *
from a3_clusters import clusters
from a3_run1 import Q,HRE
FAM=r'易|書|尚書|詩|禹貢|洪範'
def pubtok(p):
    t=nz(p)
    return t
out=[]
cl=clusters(Q,HRE)
for k,v in sorted(cl.items(),key=lambda kv:(kv[0][0],kv[0][1])):
    x=v[0]
    w,why=resolve(k[0],x.get('dc:creator',''),x['title'])
    if not w: continue
    Y=k[1]
    same=[r for r in LIB if r['y']==Y and (r['work']==w or re.search(FAM,r['nt'][:3]))]
    pubs=[nz(p) for p in x['dc:publisher']]
    first=[re.sub(r'[\[\]\s]','',p) for p in x['dc:publisher']]
    out.append(dict(head=k[0],year=Y,work=w,why=why,pub=x['dc:publisher'],cre=x.get('dc:creator',''),ncids=[y['@id'][-10:] for y in v],own=sum(int(y.get('cinii:ownerCount') or 0) for y in v),titles=sorted({y['title'] for y in v})[:3],lib=[(r['id'],r['title'],r['edition']) for r in same]))
json.dump(out,open('/tmp/wa3/cands.json','w'),ensure_ascii=False)
print(len(out),sum(1 for o in out if not o['lib']))
