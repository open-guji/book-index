import sys,re
from ndl import ndl
def yr(s):
    m=re.search(r'\d{4}',s[0]) if s else None
    return int(m.group()) if m else None
for a in sys.argv[1:]:
    t,_,c=a.partition('/')
    r=ndl(t,c)
    print('##',a)
    if not r: print('  FAIL'); continue
    seen=set()
    for x in r:
        y=yr(x['date'])
        if '和古書・漢籍' in x['cat'] or (y and y<1912 and 'R100000' in x['link'][0]):
            k=(x['title'][0] if x['title'] else '',tuple(x['pub'][:1]),y)
            if k in seen: continue
            seen.add(k)
            print('  %s | %s | %s | %s | %s | %s'%(k[0][:40],x['creator'][:2],x['pub'][:2],x['date'][:1],(x['cat'] or [''])[0],x['link'][0].rsplit('/',1)[1]))
