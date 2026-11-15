import sys,pickle,json,os
sys.path.insert(0,'.claude/qa')
import entity_merge as em, jio
S=os.environ['SCR']
ent=pickle.load(open(S+'ent.pkl','rb')); W=pickle.load(open(S+'works.pkl','rb'))
G=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'groups.json')))
DRY='--dry' in sys.argv
today='2026-11-15'
def score(i):
    v=ent[i]; ds=v.get('dates') or {}
    return ((v.get('external_ids') or {}).get('cbdb_id') is not None)*4+bool(ds.get('birth') or ds.get('death'))*2+len(W.get(i,[]))*0.1+len(v.get('alt_names') or [])*0.05+bool(v.get('dynasty'))*0.5+bool(v.get('native_place'))*0.3
ledger=[]
for name,ids,why in G:
    ids=sorted(ids,key=lambda i:-score(i)); k=ids[0]
    for l in ids[1:]:
        _d,_f=jio.load(em.find_path(l))
        if _d.get('merged_into'): continue
        s=em.merge(l,k,reason=why,rule='人物去重窗口（同名同代＋著作互证）',date=today,dry=DRY,by='A12-去重窗口')
        ledger.append({'keeper':k,'loser':l,'name':name,'why':why,'redirected_works':s['redirected_works']})
        if not DRY:
            rel=em.find_path(k); kd,kf=jio.load(rel)
            lo=ent[l]
            for f in ('dynasty','period','dynasty_basis','period_basis','dates','native_place','native_place_basis','native_place_entity_id'):
                if not kd.get(f) and lo.get(f): kd[f]=lo[f]
            kd['revised_at']=today
            jio.save(rel,kd,kf)
if not DRY: json.dump(ledger,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ledger.json'),'w'),ensure_ascii=False,indent=1)
print('pairs',len(ledger))
