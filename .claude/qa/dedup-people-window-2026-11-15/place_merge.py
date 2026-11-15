"""同名同上級鏈地名條並條（P09 真重複）：沿革段並集、別名/出處並集、全庫引用改指、loser 留墓碑。"""
import sys,os,glob,json,subprocess
sys.path.insert(0,'.claude/qa')
import entity_merge as em, jio
def seg_key(h): return (h.get('start'),h.get('end'),h.get('parent_id'))
def merge_place(l,k,why,date='2026-11-15'):
    lrel=em.find_path(l); krel=em.find_path(k)
    ld,lf=jio.load(lrel); kd,kf=jio.load(krel)
    assert not ld.get('merged_into') and not kd.get('merged_into')
    # 引用改指
    out=subprocess.run(['grep','-rlF',f'"{l}"','Entity','Work','Book','Collection'],capture_output=True,text=True).stdout.split()
    refs=[]
    for p in out:
        if p==lrel or p==krel: continue
        s=open(p,encoding='utf-8').read()
        n=s.count(f'"{l}"')
        if n: open(p,'w',encoding='utf-8').write(s.replace(f'"{l}"',f'"{k}"')); refs.append((p,n))
    # 沿革
    seen={seg_key(h) for h in kd.get('history') or []}
    hist=list(kd.get('history') or [])
    for h in ld.get('history') or []:
        if seg_key(h) not in seen: hist.append(h)
    hist.sort(key=lambda h:(h.get('start') if h.get('start') is not None else -9999))
    if hist: kd['history']=hist
    have={a['name'] for a in kd.get('alt_names') or [] if isinstance(a,dict)}
    for a in ld.get('alt_names') or []:
        if isinstance(a,dict) and a['name'] not in have: kd.setdefault('alt_names',[]).append(a)
    if not kd.get('modern') and ld.get('modern'): kd['modern']=ld['modern']
    ds=kd.setdefault('description',{}) if ld.get('description') else kd.get('description')
    if ld.get('description') and ds is not None:
        src=ds.setdefault('sources',[]); names={json.dumps(s,sort_keys=True,ensure_ascii=False) for s in src}
        for s in ld['description'].get('sources') or []:
            if json.dumps(s,sort_keys=True,ensure_ascii=False) not in names: src.append(s)
    kd['revised_at']=date; jio.save(krel,kd,kf)
    t=em.tombstone(ld,k,date,{'rule':'地名同名同上級鏈真重複並條（check_v2 P09）','at':date,'by':'A12-去重窗口','why':why})
    jio.save(lrel,t,lf)
    return refs
if __name__=='__main__':
    G=json.load(open(sys.argv[1])); led=[]
    for l,k,why in G:
        r=merge_place(l,k,why); led.append({'loser':l,'keeper':k,'why':why,'refs_repointed':r}); print(l,'->',k,len(r))
    json.dump(led,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
