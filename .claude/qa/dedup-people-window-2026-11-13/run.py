import sys,pickle,json,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'.claude/qa')
from groups import G
import entity_merge as em, jio
S='/tmp/claude-0/-home-user/40333046-8387-51f5-8289-984982adc5b4/scratchpad/'
ent=pickle.load(open(S+'ent.pkl','rb')); W=pickle.load(open(S+'works.pkl','rb'))
sfx={i[-6:]:i for i in ent}
DRY='--dry' in sys.argv
def score(i):
    v=ent[i]; ds=v.get('dates') or {}
    return ((v.get('external_ids') or {}).get('cbdb_id') is not None)*4+bool(ds.get('birth') or ds.get('death'))*2+len(W.get(i,[]))*0.1+len(v.get('alt_names') or [])*0.05+bool(v.get('dynasty'))*0.5+bool(v.get('native_place'))*0.3
today='2026-11-13'
ledger=[]
for g,why in G:
    ids=[sfx[s[-6:]] for s in g.split()]
    ids.sort(key=lambda i:-score(i))
    k=ids[0]
    for l in ids[1:]:
        _d,_f=jio.load(em.find_path(l))
        if _d.get('merged_into'):
            ledger.append({'keeper':_d['merged_into'],'keeper_name':ent[_d['merged_into']]['primary_name'],'loser':l,'loser_name':ent[l]['primary_name'],'why':why,'resumed':True}); continue
        s=em.merge(l,k,reason=why,rule='人物去重窗口（别名/异写互证＋朝代相容＋无矛盾标识）',date=today,dry=DRY,by='A12-去重窗口')
        ledger.append({'keeper':k,'keeper_name':ent[k]['primary_name'],'loser':l,'loser_name':ent[l]['primary_name'],'why':why,'redirected_works':s['redirected_works'],'added_alt_names':s['added_alt_names']})
        if not DRY:
            rel=em.find_path(k); kd,kf=jio.load(rel)
            lname=ent[l]['primary_name']
            if lname!=kd['primary_name'] and lname not in {(a if isinstance(a,str) else a.get('name')) for a in kd.get('alt_names') or []}:
                kd.setdefault('alt_names',[]).append({'name':lname,'type':'別名','note':'人物去重窗口并条（A12 2026-11-13），记为著录所见异称'})
            lo=ent[l]
            for f in ('dynasty','period','dynasty_basis','period_basis'):
                if not kd.get(f) and lo.get(f): kd[f]=lo[f]
            for f in ('dates','native_place','native_place_basis','native_place_entity_id'):
                if not kd.get(f) and lo.get(f): kd[f]=lo[f]
            lc=(lo.get('external_ids') or {}).get('cbdb_id'); kc=(kd.get('external_ids') or {}).get('cbdb_id')
            if lc and kc and lc!=kc:
                kd['ai_note']=(kd.get('ai_note','')+f'\n并入同人条 {l}（{lname}）时，其 CBDB 号 {lc} 与本条 {kc} 不同，未采纳（CBDB 对同一人可能分立两号），待核。').strip()
            kd['revised_at']=today
            jio.save(rel,kd,kf)
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'ledger.json')
if not DRY: json.dump(ledger,open(out,'w'),ensure_ascii=False,indent=1)
print('pairs',len(ledger))
