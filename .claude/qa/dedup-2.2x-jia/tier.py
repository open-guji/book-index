import pickle,json,collections,sys,re
sys.path[:0]=['.claude/qa/entity-governance-1025']
import dyn
SP='/tmp/claude-0/-home-claude/092cb9df-56d3-58b4-85bf-4d6645dab605/scratchpad/j/'
P,R=pickle.load(open(SP+'db.pkl','rb')); rows=pickle.load(open(SP+'rows0.pkl','rb'))
D={f:(t,d) for t,f,d in R}
W={d['id']:d for t,f,d in R if t=='Work'}
refs=collections.defaultdict(list)
for t,f,d in R:
    if d.get('merged_into'): continue
    for a in d.get('authors') or []:
        if isinstance(a,dict) and a.get('entity_id'): refs[a['entity_id']].append(f)
URI=re.compile(r'entity/person/(\w+)')
c=collections.Counter()
for r in rows:
    t,d=D[r['path']]
    ids=sorted({e for e,_ in r['cands']})
    r['ids']=ids
    # 继承：Book/Collection 的 Work 同名位已挂候选之一
    inh=None
    wid=d.get('work_id')
    if t!='Work' and wid in W:
        for a in W[wid].get('authors') or []:
            if isinstance(a,dict) and a.get('name')==r['name'] and a.get('entity_id') in ids: inh=a['entity_id']
    r['inherit']=inh
    if inh: r['tier']='T1继承Work'; c[(t,r['tier'])]+=1; continue
    if len(ids)>1: r['tier']='M多候选'; c[(t,r['tier'])]+=1; continue
    e=P[ids[0]][1]
    rel=dyn.rel(r['dyn'],e.get('dynasty'))
    r['rel']=rel
    su=set(URI.findall(json.dumps(d['authors'][r['slot']].get('source'),ensure_ascii=False)))
    eu=set(URI.findall(json.dumps(e.get('description'),ensure_ascii=False)))
    r['uri']= 'same' if su&eu else ('diff' if su and eu else 'na')
    r['nref']=len(refs.get(ids[0],()))
    alias_only=not any(tt=='主名' for _,tt in r['cands'])
    if alias_only: r['tier']='A仅别名'
    elif rel=='same': r['tier']='S同朝'
    elif rel=='adj': r['tier']='J邻朝'
    elif rel=='unk': r['tier']='U缺朝代'
    else: r['tier']='X朝代冲突'
    c[(t,r['tier'])]+=1
for k,v in sorted(c.items()): print(k,v)
cc=collections.Counter((r['tier'],r.get('uri'),r.get('nref',0)>0) for r in rows if r['tier']=='S同朝')
print(cc)
pickle.dump(rows,open(SP+'rows0t.pkl','wb'))
