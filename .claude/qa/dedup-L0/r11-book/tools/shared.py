import json,glob,collections
def K(p):
    s=str(p.get('source'))
    return s+'|'+str(p.get('call_number')) if 'npm' in s or s.startswith('NDL') else s
S='/tmp/claude-0/-home-user/e59db2b9-8fd4-5ed9-a492-942f4a225576/scratchpad/r11'
g=json.load(open(S+'/groups.json'))
colls={x['key'][1] for x in g}
# count prov items per collection across all member books
cnt=collections.defaultdict(collections.Counter)
for f in glob.glob('Book/*/*/*/*.json'):
    d=json.load(open(f))
    if d.get('merged_into'): continue
    for c in d.get('contained_in') or []:
        cid=c.get('id') if isinstance(c,dict) else c
        if cid in colls:
            for p in d.get('provenance') or []:
                cnt[cid][K(p)]+=1
json.dump({k:dict(v) for k,v in cnt.items()},open(S+'/provcnt.json','w'),ensure_ascii=False)
C=collections.Counter();res=[]
for x in g:
    cid=x['key'][1]
    def indep(b):
        ps=[K(p) for p in b['provenance'] or []]
        return bool(ps) and any(cnt[cid][s]<2 for s in ps)
    def shared(b):
        ps=[K(p) for p in b['provenance'] or []]
        return bool(ps) and all(cnt[cid][s]>=2 for s in ps)
    ni=sum(indep(b) for b in x['books']); ns=sum(shared(b) for b in x['books'])
    x['ni']=ni;x['ns']=ns
    C[(ni,ns)]+=1
print(C)
json.dump(g,open(S+'/groups2.json','w'),ensure_ascii=False)
