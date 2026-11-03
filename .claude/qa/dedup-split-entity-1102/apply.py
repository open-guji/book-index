# -*- coding: utf-8 -*-
import sys,os,json,glob,datetime,collections
HERE=os.path.dirname(os.path.abspath(__file__)); QA=os.path.dirname(HERE); sys.path.insert(0,QA); sys.path.insert(0,HERE)
import jio,mintid,plan
ROOT=jio.ROOT; os.chdir(ROOT)
APPLY='--apply' in sys.argv
TODAY=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-7))).strftime('%Y-%m-%d')
files=[l.strip().replace('../../../','') for l in open(os.path.join(HERE,'files.txt'))]
# work_id -> Work path ; work_id -> [Book paths]
wpath={}; bpaths=collections.defaultdict(list)
for f in files:
    d=json.load(open(f))
    if d['type']=='work': wpath[d['id']]=f
    else: bpaths[d.get('work_id')].append(f)
# 另: Work 可能不在 files（新增 entity 引用不在则不会），故需要的 Work 都应在 files
cache={}
def get(rel):
    if rel not in cache: cache[rel]=jio.load(rel)
    return cache[rel]
def slots(rel,old):
    d,_=get(rel); return [i for i,a in enumerate(d.get('authors',[])) if a.get('entity_id')==old]
def eachdoc(wid):
    yield wpath[wid]
    for b in bpaths.get(wid,[]): yield b
def repoint(wid,old,new):
    n=0
    for rel in eachdoc(wid):
        d,_=get(rel)
        for i in slots(rel,old):
            if new: d['authors'][i]['entity_id']=new
            else: d['authors'][i].pop('entity_id')
            n+=1
    return n
# 校验
for g in plan.NEW+plan.REPOINT+plan.DETACH:
    for w in g['works']:
        assert w in wpath,(w,'不在')
        assert slots(wpath[w],g['old']),(g.get('key'),w,'Work 无旧实体作者位')
assert slots(wpath[plan.RENAME_AUTHOR['work']],plan.RENAME_AUTHOR['old'])
used=collections.Counter()
for g in plan.NEW+plan.REPOINT+plan.DETACH:
    for w in g['works']: used[w]+=1
assert all(v==1 for v in used.values()),[k for k,v in used.items() if v>1]
ids=mintid.mint('Entity','splitent',len(plan.NEW)) if APPLY else ['(待鑄)']*len(plan.NEW)
ledger=[]; touched_ent={}
def ent(eid):
    p=glob.glob('Entity/*/*/*/%s-*.json'%eid)[0]
    if p not in touched_ent: touched_ent[p]=jio.load(p)
    return touched_ent[p]
def oldnote(old,text):
    d,_=ent(old); jio.addnote(d,'%s 拆分混合实体（A11）：%s'%(TODAY,text))
for g,eid in zip(plan.NEW,ids):
    rec={'schema_version':1,'id':eid,'type':'entity','subtype':'people','primary_name':g['name'],'dynasty':g['dynasty'],'dynasty_basis':'據所繫作品著錄'}
    if g['native']: rec['native_place']=g['native']
    if g['alts']: rec['alt_names']=[{'name':n,'type':t} for n,t in g['alts']]
    rec['ai_note']='%s 自 %s 拆出（去重方案：混了同名人的作者實體）。依據：%s 所繫作品 %d 部（含相應 Book 作者位）。'%(TODAY,g['old'],g['note'],len(g['works']))
    rec['revision']='1.0.0'; rec['revised_at']=TODAY
    n=0
    for w in g['works']: n+=repoint(w,g['old'],eid)
    if APPLY:
        rel=mintid.path_for(eid,g['name'],'Entity'); os.makedirs(os.path.dirname(rel),exist_ok=True)
        assert not os.path.exists(rel); jio.save(rel,rec,(2,'\n'))
    oldnote(g['old'],'%s（%s）%d 部作品拆出至新條 %s。'%(g['name'],g['key'],len(g['works']),eid))
    ledger.append(dict(key=g['key'],new=eid,old=g['old'],works=g['works'],slots=n))
for g in plan.REPOINT:
    n=sum(repoint(w,g['old'],g['new']) for w in g['works'])
    oldnote(g['old'],'作品 %s 改挂 %s：%s'%('、'.join(g['works']),g['new'],g['note']))
    ledger.append(dict(key='repoint',new=g['new'],old=g['old'],works=g['works'],slots=n))
for g in plan.DETACH:
    n=sum(repoint(w,g['old'],None) for w in g['works'])
    oldnote(g['old'],'摘去作品 %s 的作者位挂接：%s'%('、'.join(g['works']),g['note']))
    ledger.append(dict(key='detach',old=g['old'],works=g['works'],slots=n))
r=plan.RENAME_AUTHOR
for rel in eachdoc(r['work']):
    d,_=get(rel)
    for i in slots(rel,r['old']):
        d['authors'][i].pop('entity_id'); d['authors'][i]['name']=r['name']
oldnote(r['old'],r['note']); ledger.append(dict(key='rename',old=r['old'],works=[r['work']]))
for a in plan.ATTR:
    d,_=ent(a['id'])
    if 'remove_alt' in a:
        d['alt_names']=[x for x in d.get('alt_names',[]) if x['name'] not in a['remove_alt']]
    if a.get('fix')=='陳榮昌':
        d['dates']={'birth':1860,'death':1935,'basis':'據所挂作品與清代進士履歷（A11 2026-11-02）'}
        d['native_place']='昆明'; d.pop('native_place_basis',None)
        d['alt_names']=[x for x in d.get('alt_names',[]) if x['name'] not in ('文峰','星閣','鳳岐')]+[{'name':'虛齋','type':'號'}]
        ei=d.get('external_ids',{}); [ei.pop(k,None) for k in('cbdb_id','cbdb_match','cbdb_source')]
    if a.get('fix')=='張大昌':
        d.pop('dates',None); d.pop('native_place',None); d.pop('native_place_entity_id',None); d.pop('native_place_basis',None)
        ei=d.get('external_ids',{}); [ei.pop(k,None) for k in('cbdb_id','cbdb_match','cbdb_source')]
    jio.addnote(d,'%s 拆分混合实体（A11）：%s'%(TODAY,a['note']))
    d['revision']='1.2.1' if False else d.get('revision'); d['revised_at']=TODAY
for p,(d,fmt) in touched_ent.items():
    d['revised_at']=TODAY
if APPLY:
    for rel,(d,fmt) in cache.items(): jio.save(rel,d,fmt)
    for p,(d,fmt) in touched_ent.items(): jio.save(p,d,fmt)
    json.dump(ledger,open(os.path.join(HERE,'ledger.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('新建',len(plan.NEW),'改挂',len(plan.REPOINT),'摘去',len(plan.DETACH),'写 Work/Book',len(cache),'改 Entity',len(touched_ent),'APPLY' if APPLY else '乾跑')
print('作者位变动',sum(x.get('slots',0) for x in ledger))
