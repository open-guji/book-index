import sys,json
sys.path.insert(0,'.')
import spec_wake_e3 as sp, ncid, os
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
res={}
if os.path.exists(S+'e_ncidpages.json'): res=json.load(open(S+'e_ncidpages.json'))
for k,w,t,sels in sp.SPEC:
    n=[]
    for s in sels: n+=sp.sel(*s)
    n=sorted(set(n))[:12]
    for x in n:
        if x in res: continue
        d=ncid.get(x)
        res[x]=d
        json.dump(res,open(S+'e_ncidpages.json','w'),ensure_ascii=False)
        print(x,flush=True)
