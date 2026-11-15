import json,re,sys
sys.path.insert(0,'/tmp/wf5b/.claude/qa/wake-f')
from q2 import ndl
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/shard5.json'
works={}
for x in json.load(open(S)): works.setdefault(x['work'],x['title'])
out={}
for w,t in works.items():
    rs=ndl(t)
    keep=[]
    for r in rs:
        m=re.search(r'(1[0-9]{3})',r['d'] or '')
        y=int(m.group(1)) if m else None
        if y is not None and y>1911: continue
        if y is None and not re.search(r'R1000000(02|92|36)|R1000001(36|43)|R000000(050|054)',r['l']): continue
        keep.append(r)
    out[w]={'title':t,'n':len(rs),'keep':keep}
    print(w,t,len(rs),len(keep),flush=True)
json.dump(out,open('/tmp/wf5b/.claude/qa/wake-f/scan2.json','w'),ensure_ascii=False,indent=1)
