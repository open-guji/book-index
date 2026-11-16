# -*- coding: utf-8 -*-
import sys; sys.path.insert(0,'/tmp/wa3')
from a3_analyze import *
def head(x):
    t=re.sub(r'[\s,，.．].*$','',x['title']); t=re.sub(r'\d+[巻卷].*','',t); return t
def clusters(Q,hre):
    S=allitems(Q); cl=collections.defaultdict(list)
    for k,x in S.items():
        c=cand(x)
        if not c: continue
        h=head(x)
        if not re.search(hre,nz(h)): continue
        cl[(nz(h),c[0],nz(c[1])[:14])].append(x)
    return cl
def show(cl):
    for k,v in sorted(cl.items(),key=lambda kv:(kv[0][0],kv[0][1])):
        x=v[0]
        print('%s|%d|%s|%s|n%d o%d|%s'%(k[0],k[1],'/'.join(x['dc:publisher'])[:28],x.get('dc:creator','')[:22],len(v),sum(int(y.get('cinii:ownerCount') or 0) for y in v),','.join(y['@id'][-10:] for y in v[:3])))
if __name__=='__main__':
    cl=clusters(sys.argv[2].split(','),sys.argv[1]); print(len(cl)); show(cl)
