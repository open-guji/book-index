import pickle,json,collections,hashlib,sys,re
sys.path[:0]=['.claude/qa','scripts']
import importlib.util
spec=importlib.util.spec_from_file_location('dc','scripts/dedup-census.py'); dc=importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)
SP='/tmp/claude-0/-home-claude/092cb9df-56d3-58b4-85bf-4d6645dab605/scratchpad/j/'
P,R=pickle.load(open(SP+'db.pkl','rb'))
live={k:v for k,v in P.items() if not v[1].get('merged_into')}
idx=collections.defaultdict(list)
for eid,(f,d) in live.items():
    idx[d['primary_name']].append((eid,'主名'))
    for a in d.get('alt_names') or []:
        n=a['name'] if isinstance(a,dict) else a; t=a.get('type') if isinstance(a,dict) else 'str'
        idx[n].append((eid,t))
def shard(n): return int(hashlib.md5(dc.norm_name(n).encode()).hexdigest(),16)%4
rows=[]; tot=collections.Counter()
for t,f,d in R:
    if d.get('merged_into'): continue
    for i,a in enumerate(d.get('authors') or []):
        if not isinstance(a,dict) or a.get('entity_id'): continue
        n=a.get('name') or ''
        if not n or n in ('佚名',): continue
        c=idx.get(n)
        if not c: continue
        tot[shard(n)]+=1
        if shard(n)!=0: continue
        rows.append(dict(type=t,path=f,slot=i,name=n,role=a.get('role'),dyn=a.get('dynasty'),cands=sorted(set(c))))
print('各份作者位',dict(tot),'合计',sum(tot.values()))
pickle.dump(rows,open(SP+'rows0.pkl','wb'))
c=collections.Counter()
for r in rows:
    ids={e for e,_ in r['cands']}
    kind='多候选' if len(ids)>1 else ('唯一·主名' if any(t=='主名' for _,t in r['cands']) else '唯一·仅别名')
    c[(r['type'],kind)]+=1
for k,v in sorted(c.items()): print(k,v)
print('名字数',len({r['name'] for r in rows}))
