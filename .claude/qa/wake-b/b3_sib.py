# -*- coding: utf-8 -*-
import sys,json,re,collections;sys.path.insert(0,'.')
import b3_an as a,b3_cinii as c
from b3_group import shops
rows=json.load(open('/tmp/wb3_pre.json'))
g=a.clusters()
byty=collections.defaultdict(list)
for (t,y,p),l in g.items(): byty[(t,y)].extend(l)
def sibs(i):
    x=rows[i];sh=set(x['shops']);out=[]
    for it in byty[(x['t'],x['y'])]:
        d=c.ncid(it['ncid'])
        if not d: continue
        s=set(shops(d))
        if (s&sh) or it['ncid'] in x['ncids']: out.append(d)
    return out
if __name__=='__main__':
    for i in map(int,sys.argv[1:]):
        x=rows[i];print('###',i,x['t'],x['y'])
        for d in sibs(i): print('   ',d['ncid'],d['date'],(d['pubdate'] or [''])[-1],d['pub'],[o['name'][:10] for o in d['owners']][:3])
