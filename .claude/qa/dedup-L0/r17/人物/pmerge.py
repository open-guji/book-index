import sys,json,os,subprocess,collections
sys.path.insert(0,'.claude/qa')
import entity_merge as em, jio
S=sys.argv[1]; DRY='--dry' in sys.argv
C=json.load(open(S+'/pcomb.json'))
r1={};r2={}
for fn,r in (('p1',r1),('p2',r2)):
    for k in ('00','01'):
        for l in open(f'{S}/out/{fn}-{k}.tsv'):
            c=l.rstrip('\n').split('\t')
            if len(c)>=4: r[tuple(c[:2])]=c[3]
par={}
def f(x):
    par.setdefault(x,x)
    while par[x]!=x: x=par[x]
    return x
for a,b in C['both']: par[f(a)]=f(b)
comp=collections.defaultdict(set); why={}
for a,b in C['both']:
    comp[f(a)]|={a,b}; why.setdefault(f(a),[]).append(r2.get((a,b),'')[:120])
def load(i): return jio.load(em.find_path(i))[0]
def score(i,d):
    new='2026-11-15' in (d.get('ai_note') or '') and '單篇詩文' in (d.get('ai_note') or '')
    ds=d.get('dates') or {}
    return (not new)*10+((d.get('external_ids') or {}).get('cbdb_id') is not None)*4+bool(ds.get('birth') or ds.get('death'))*2+bool(d.get('dynasty'))*0.5+bool(d.get('description'))*0.5+len(d.get('alt_names') or [])*0.05
allids=sorted({x for v in comp.values() for x in v})
open(S+'/ids.txt','w').write('\n'.join(allids)+'\n')
out=subprocess.run(['grep','-rlF','-f',S+'/ids.txt','Work','Book','Collection'],capture_output=True,text=True).stdout.split()
cand=collections.defaultdict(list)
for p in out:
    t=open(p).read()
    for i in allids:
        if i in t: cand[i].append(p)
def scan(eid):
    hits=[]
    for rel in cand.get(eid,[]):
        d,fmt=jio.load(rel)
        if any(isinstance(a,dict) and a.get('entity_id')==eid for a in d.get('authors') or []) or em._marks_of(d,eid): hits.append((rel,d,fmt))
    return hits
em.scan_referencing_works=scan
ledger=[]; today='2026-11-15'
for root,v in comp.items():
    D={i:load(i) for i in v}
    ids=sorted(v,key=lambda i:(-score(i,D[i]),i)); k=ids[0]
    w='；'.join(x for x in why[root] if x)[:300] or '兩道獨立複核皆判同人'
    for l in ids[1:]:
        s=em.merge(l,k,reason=w,rule='人物去重 L0 第十七轮（同名同代＋佐證，兩道獨立複核皆同）',date=today,dry=DRY,by='A11-L0')
        # 新增的墓碑 works 引用候选 → keeper 也要被后续 scan 看到
        cand[k]+=cand.get(l,[])
        ledger.append({'keeper':k,'loser':l,'name':D[l].get('primary_name'),'why':w,'redirected_works':s['redirected_works']})
        if not DRY:
            rel=em.find_path(k); kd,kf=jio.load(rel); lo=D[l]; ch=False
            for fld in ('dynasty','period','dynasty_basis','period_basis','dates','native_place','native_place_basis','native_place_entity_id','description'):
                if not kd.get(fld) and lo.get(fld): kd[fld]=lo[fld]; ch=True
            kd['revised_at']=today
            jio.save(rel,kd,kf)
json.dump(ledger,open(S+'/pledger.json','w'),ensure_ascii=False,indent=1)
print('merged',len(ledger))
