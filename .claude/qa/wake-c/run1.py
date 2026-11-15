import json,sys,re
from ndl import ndl
SP='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad'
d=json.load(open(SP+'/shard2.json')); W=json.load(open('works.json'))
lo,hi=int(sys.argv[1]),int(sys.argv[2])
out=open('cand_%d_%d.txt'%(lo,hi),'w')
def yr(s):
    m=re.search(r'\d{4}',s[0]) if s else None
    return int(m.group()) if m else None
for i in range(lo,min(hi,len(d))):
    x=d[i]; w=W[x['work']]
    t=x['title'] if len(x['title'])>2 else w['title']
    r=ndl(t)
    out.write('## %d %s %s | %s | W=%s %s | %s\n'%(i,x['id'],x['title'],x['edition'],w['title'],w['authors'],x['prov']))
    if r is None: out.write('  FAIL\n'); out.flush(); continue
    for c in r:
        y=yr(c['date'])
        if '和古書・漢籍' in c['cat'] or (y and y<1912 and 'R100000' in c['link'][0]):
            out.write('  %s | %s | %s | %s | %s | %s\n'%(c['title'][0][:50] if c['title'] else '',c['creator'][:2],c['pub'][:2],c['date'][:1],(c['cat'] or [''])[0],c['link'][0].rsplit('/',1)[1]))
    out.flush()
