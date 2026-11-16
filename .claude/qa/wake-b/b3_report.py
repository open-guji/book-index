# -*- coding: utf-8 -*-
import sys,json,collections,re;sys.path.insert(0,'.')
import b3_an as a
g=a.clusters()
# merge by (title,year)
m=collections.OrderedDict()
for (t,y,p),l in g.items(): m.setdefault((t,y),[]).extend(l)
ex=collections.defaultdict(list)
for b in a.jb: ex[a.nt(b['title'])].append(b)
out=[]
for (t,y),l in m.items():
    mt=[]
    for et,bl in ex.items():
        if et==t or (len(t)>=3 and len(et)>=3 and (t in et or et in t)):
            for b in bl:
                if a.ey(b)==y: mt.append(b['id'])
    pubs=collections.Counter(' / '.join(x['pub'])[:40] for x in l)
    out.append((t,y,len(l),sorted({x['ncid'] for x in l})[:6],mt,pubs.most_common(2),[x['cr'][:16] for x in l][:2]))
json.dump(out,open('/tmp/wb3_rep.json','w'),ensure_ascii=False)
for r in sorted(out,key=lambda r:(r[0],r[1])):
    print(r[0],r[1],'n=%d'%r[2],'EX:'+','.join(r[4]) if r[4] else 'NEW',r[5][0][0],'|',r[6][0] if r[6] else '')
