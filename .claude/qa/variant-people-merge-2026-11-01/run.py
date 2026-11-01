import sys,pickle,json,datetime
sys.path.insert(0,'/tmp/w'); sys.path.insert(0,'.claude/qa')
from groups import G
import entity_merge as em, jio
ent,uri,works=pickle.load(open('/tmp/pk.pkl','rb'))
sfx={i[-6:]:i for i in ent}
DRY='--dry' in sys.argv
def score(i):
    v=ent[i]; ds=v.get('dates') or {}
    return ((v.get('external_ids') or {}).get('cbdb_id') is not None)*4+bool(ds.get('birth') or ds.get('death'))*2+len(works.get(i,[]))*0.1+len(v.get('alt_names') or [])*0.05+bool(v.get('dynasty'))*0.5
today='2026-11-01'
ledger=[]
for g,why in G:
    ids=[sfx[s] for s in g.split()]
    ids.sort(key=lambda i:-score(i))
    k=ids[0]
    for l in ids[1:]:
        s=em.merge(l,k,reason=why,rule='异写人物并条（字形异体＋朝代相容＋无矛盾标识）',date=today,dry=DRY,by='A12-异写扫描')
        ledger.append({'keeper':k,'keeper_name':ent[k]['primary_name'],'loser':l,'loser_name':ent[l]['primary_name'],'why':why,'redirected_works':s['redirected_works'],'added_alt_names':s['added_alt_names']})
        if not DRY:
            rel=em.find_path(k); kd,kf=jio.load(rel)
            lname=ent[l]['primary_name']
            if lname!=kd['primary_name'] and lname not in {(a if isinstance(a,str) else a.get('name')) for a in kd.get('alt_names') or []}:
                kd.setdefault('alt_names',[]).append({'name':lname,'type':'異體','note':'异写人物并条（A12 异写扫描 2026-11-01），记为著录所见异写'})
            lo=ent[l]
            for f in ('dynasty','period'):
                if not kd.get(f) and lo.get(f): kd[f]=lo[f]
            if not kd.get('dates') and lo.get('dates'): kd['dates']=lo['dates']
            lc=(lo.get('external_ids') or {}).get('cbdb_id'); kc=(kd.get('external_ids') or {}).get('cbdb_id')
            if lc and kc and lc!=kc:
                kd['ai_note']=(kd.get('ai_note','')+f' 并入异写条 {l}（{lname}）时，其 CBDB 号 {lc} 与本条 {kc} 不同，未采纳，待核。').strip()
            kd['revised_at']=today
            jio.save(rel,kd,kf)
json.dump(ledger,open('/tmp/w/ledger.json','w'),ensure_ascii=False,indent=1)
print('pairs',len(ledger))
