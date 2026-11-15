import json,re,sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'.')
import ndl
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
shard=json.load(open(S+'shard1.json'));ws=json.load(open('/tmp/wb_works.json'))
def yr(r):
    m=re.match(r'(\d{4})',r['date'] or '');return int(m.group(1)) if m else None
works=[]
for x in shard:
    if x['work'] not in works: works.append(x['work'])
def job(wid):
    w=ws[wid];au=(w.get('authors') or [{}])[0].get('name');t=w['title']
    qs=[(t,None)]
    if au and au!='佚名': qs.append((t,ndl.jp(au)))
    got={}
    for q in qs:
        for r in ndl.search(q[0],q[1],50): got[r['link']]=r
    lines=['## %s %s %s'%(wid,t,au)]
    for r in got.values():
        y=yr(r)
        if ('和古書' in r['cat'] or (y and y<=1912)) and ndl.jp(t)[:2] in ndl.jp(r['title']):
            lines.append('  %s | %s | %s | %s | %s %s | %s %s | %s'%(r['link'].split('/')[-1],r['title'],r['creator'],r['pub'],r['date'],r['issued'],r['vol'],r['ext'],r['cat']))
    return '\n'.join(lines)
with ThreadPoolExecutor(5) as ex, open('/tmp/wb_ndl_raw.txt','w') as out:
    for s in ex.map(job,works): out.write(s+'\n'); out.flush()
print('done')
