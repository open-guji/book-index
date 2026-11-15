import sys,json,os
sys.path.insert(0,'.claude/qa')
import entity_merge as em, jio
D=os.path.dirname(os.path.abspath(__file__))
P=json.load(open(os.path.join(D,'pairs.json')))
LED=os.path.join(D,'ledger.json')
import glob,subprocess
def fix(eid):
    sub=os.path.join('Entity',*list(eid[-3:]))
    if glob.glob(os.path.join(em.jio.ROOT,sub,eid+'-*.json')): return
    hits=glob.glob(os.path.join(em.jio.ROOT,'Entity','*','*','*',eid+'-*.json'))
    assert len(hits)==1,(eid,hits)
    dst=os.path.join(em.jio.ROOT,sub); os.makedirs(dst,exist_ok=True)
    subprocess.run(['git','mv',hits[0],os.path.join(dst,os.path.basename(hits[0]))],check=True,cwd=em.jio.ROOT)
    print('moved',eid)
led=json.load(open(LED)) if os.path.exists(LED) else []
done={x['loser'] for x in led}
for l,k,why,tag in P:
    if l in done: continue
    fix(l); fix(k)
    ld,_=jio.load(em.find_path(l)); name=ld['primary_name']
    if ld.get('merged_into'): continue
    s=em.merge(l,k,reason=why,rule='人物去重窗口（新建批同名／異寫複查，A12 2026-11-16）',date='2026-11-15',by='A12-去重窗口')
    rel=em.find_path(k); kd,kf=jio.load(rel)
    have={(a if isinstance(a,str) else a.get('name')) for a in kd.get('alt_names') or []}
    if name!=kd['primary_name'] and name not in have:
        typ='避諱' if tag=='bihui' else '別名'
        kd.setdefault('alt_names',[]).append({'name':name,'type':typ,'note':'人物去重窗口並條（A12 2026-11-15），記為著錄所見異稱'})
    for f in ('dynasty','period','dates','native_place','native_place_basis','native_place_entity_id'):
        if not kd.get(f) and ld.get(f): kd[f]=ld[f]
    ls=(ld.get('description') or {}).get('sources') or []
    if ls:
        desc=kd.setdefault('description',{}) if kd.get('description') else {}
        if not kd.get('description'): kd['description']=desc
        ks=desc.setdefault('sources',[])
        for x in ls:
            if x not in ks: ks.append(x)
    kd['revised_at']='2026-11-15'; jio.save(rel,kd,kf)
    led.append({'keeper':k,'loser':l,'name':name,'why':why,'redirected_works':s['redirected_works']})
    json.dump(led,open(LED,'w'),ensure_ascii=False,indent=1)
print(len(led))
