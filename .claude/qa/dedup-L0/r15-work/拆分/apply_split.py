"""L0 第十五轮混条拆分：只执行独立复核判 OK 的动作。
用法（cwd=book-index）：apply_split.py <plan.json> <vsplit.tsv> <outdir> [--apply]"""
import json,sys,glob,subprocess,os,re,collections,copy
sys.path.insert(0,'.claude/qa'); sys.path.insert(0,'.claude/qa/split-mixed-works')
import mintid
from split_works import juan_of, set_juan
TODAY='2026-11-15'; NOTE='2026-11-15 L0 第十五輪混條拆分：'
plan=json.load(open(sys.argv[1])); V=collections.defaultdict(dict)
for l in open(sys.argv[2],encoding='utf8'):
    p=l.rstrip('\n').split('\t')
    if len(p)<3 or l.startswith('#'): continue
    V[p[0]][p[1].strip().replace('組:','组:')]=p
out=sys.argv[3]; APPLY='--apply' in sys.argv; os.makedirs(out,exist_ok=True)
def wpath(i):
    g=glob.glob(f'Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); return g[0] if g else None
def ld(p): return json.load(open(p,encoding='utf8'))
def dump(o): return json.dumps(o,ensure_ascii=False,indent=2)+'\n'
def bump(r): r['revision']=f'{int((r.get("revision") or "1.0.0").split(".")[0])+1}.0.0'; r['revised_at']=TODAY
def note(r,s): r['ai_note']=(r['ai_note']+'\n' if r.get('ai_note') else '')+NOTE+s
def books_of(w):
    fs=subprocess.run(['git','-c','core.quotepath=off','grep','-l',f'"work_id": "{w}"','--','Book'],capture_output=True,text=True).stdout.split('\n')
    r={}
    for f in filter(None,fs):
        d=ld(f)
        if d.get('work_id')==w: r[d['id']]=f
    return r
def ok(w,k): v=V.get(w,{}).get(k); return v if v and v[2]=='OK' else None
into={tuple(m['from'].split(':',1)):m['into'] for m in plan.get('merges',[]) if ':' in m['from']}
cls={}
for p in sorted(glob.glob('classification/**/members/*.json',recursive=True)):
    for wid,src in ld(p)['members']: cls.setdefault(wid,(p,src))
recs={}; newrecs=[]; bookmv={}; log=[]; stat=collections.Counter(); addcls=collections.defaultdict(list)
used=set()
seq=[0]; import time; ts=[int(time.time())]
def mint():
    while True:
        if seq[0]>255: ts[0]+=1; seq[0]=0
        raw=(3<<59)|((ts[0]&((1<<40)-1))<<19)|(1920<<8)|seq[0]; seq[0]+=1
        i=mintid.b36(raw)
        if i not in used and not wpath(i): used.add(i); return i
def W(i):
    if i not in recs: p=wpath(i); recs[i]=[p,ld(p),False]
    return recs[i][1]
def ibkey(x): return (x.get('source'),x.get('title_info'))
for wid,spec in plan['works'].items():
    if not spec.get('mixed') or spec.get('uncertain'):
        # author_fixes on 不混 entries
        pass
    R=W(wid)
    if R.get('merged_into'): log.append((wid,'墓碑，跳过')); continue
    # author fixes
    for af in spec.get('author_fixes') or []:
        if not ok(wid,'作者:'+af['drop']): stat['作者删·未过']+=1; continue
        before=len(R.get('authors') or [])
        R['authors']=[a for a in R.get('authors') or [] if a.get('name')!=af['drop']]
        if len(R['authors'])<before:
            note(R,f'撰人刪「{af["drop"]}」：{V[wid]["作者:"+af["drop"]][5]}'); recs[wid][2]=True; stat['作者删']+=1
    if not spec.get('mixed') or spec.get('uncertain'): continue
    gs=spec.get('groups') or []
    if len(gs)<2: continue
    if not ok(wid,'stay'): log.append((wid,'stay 未过，整条不拆')); stat['整条不拆']+=1; continue
    have=books_of(wid); ibs=R.get('indexed_by') or []
    stay=[g for g in gs if g['stay']][0]; moved=set(); outs=[]
    for g in gs:
        if g['stay']: continue
        v=ok(wid,'组:'+g['name'])
        if not v: stat['组·未过']+=1; log.append((wid,g['name'],'未过')); continue
        sel=set()
        for y in g['indexed_by']:
            if 'idx' in y and y['idx']<len(ibs) and ibkey(ibs[y['idx']])==ibkey(y): sel.add(y['idx'])
            else:
                hit=[k for k,x in enumerate(ibs) if ibkey(x)==ibkey(y) and k not in sel]
                if len(hit)!=1 and not hit: raise SystemExit(f'找不到著录 {wid} {y}')
                sel.add(hit[0])
        gib=[ibs[k] for k in sorted(sel)]
        bks=[b for b in g['books'] if b in have]
        tgt=into.get((wid,g['name']))
        if tgt:
            T=W(tgt)
            if T.get('merged_into'): log.append((wid,g['name'],'目标是墓碑')); continue
            T['indexed_by']=(T.get('indexed_by') or [])+[copy.deepcopy(x) for x in gib if ibkey(x) not in {ibkey(z) for z in T.get('indexed_by') or []}]
            if not T['indexed_by']: T.pop('indexed_by')
            note(T,f'由 {wid}（{R["title"]}）拆出「{g["name"]}」一組併入本條（著錄 {len(gib)} 條，Book {",".join(bks) or "無"}）；複核：{v[5]}')
            recs[tgt][2]=True; nid=tgt; stat['组并入']+=1
        else:
            nid=mint(); title=(v[4] or '').strip() or R['title']
            try: au=json.loads(v[3]) if v[3].strip() else None
            except Exception: au=None
            if au is None: log.append((wid,g['name'],'新建组缺 authors，未拆')); stat['新建·缺作者']+=1; continue
            nw={'schema_version':R.get('schema_version',1),'id':nid,'type':'work','title':title,'authors':au}
            if gib: nw['indexed_by']=[copy.deepcopy(x) for x in gib]
            set_juan(nw,g['name'],gib)
            nw['ai_note']=NOTE+f'原 Work {wid}（{R["title"]}）混條，拆出「{g["name"]}」另立；依據：{g.get("note","")}；複核：{v[5]}'
            nw['revision']='1.0.0'; nw['revised_at']=TODAY
            newrecs.append((nid,mintid.path_for(nid,re.sub(r'[\\/:*?"<>|\s]','',title)[:40],'Work'),nw,wid))
            if wid in cls: addcls[cls[wid][0]].append([nid,cls[wid][1]])
            stat['组新建']+=1
        moved|=sel
        for b in bks: bookmv[b]=(have[b],nid,wid,g['name'])
        outs.append(f'「{g["name"]}」→{nid}')
    if not outs: continue
    R['indexed_by']=[x for k,x in enumerate(ibs) if k not in moved]
    if not R['indexed_by']: R.pop('indexed_by')
    d=R.get('description'); ds=set((d or {}).get('sources') or []) if isinstance(d,dict) else set()
    if ds and ds<= {ibs[k].get('source') for k in moved} and not ds & {x.get('source') for x in R.get('indexed_by') or []}:
        R.pop('description'); note(R,'說明出自拆走之著錄，刪去，原文：'+(d.get('text') or ''))
    note(R,f'本條混條，留「{stay["name"]}」，拆出：'+'；'.join(outs)); recs[wid][2]=True; stat['拆的 Work']+=1
print(dict(stat)); [print(*x) for x in log]
json.dump({'stat':stat,'log':log,'new':[(n[0],n[3],n[2]['title']) for n in newrecs],'books':{b:v[1:] for b,v in bookmv.items()}},open(out+'/ledger.json','w'),ensure_ascii=False,indent=1)
if APPLY:
    for i,(p,r,t) in recs.items():
        if t: bump(r); open(p,'w',encoding='utf8').write(dump(r))
    for nid,p,r,wid in newrecs:
        os.makedirs(os.path.dirname(p),exist_ok=True); assert not os.path.exists(p); open(p,'w',encoding='utf8').write(dump(r))
    for b,(p,nid,wid,gn) in bookmv.items():
        r=ld(p); r['work_id']=nid; bump(r); note(r,f'原掛 {wid}（混條），按「{gn}」改掛 {nid}'); open(p,'w',encoding='utf8').write(dump(r))
    for p,add in addcls.items():
        raw=open(p,encoding='utf8').read(); d=json.loads(raw)
        d['members']=sorted(d['members']+add,key=lambda x:x[0])
        head={k:v for k,v in d.items() if k!='members'}
        s=json.dumps(head,ensure_ascii=False,indent=2)[:-2]
        s+=',\n  "members": [\n'+',\n'.join('    '+json.dumps(m,ensure_ascii=False) for m in d['members'])+'\n  ]\n}'+('\n' if raw.endswith('\n') else '')
        open(p,'w',encoding='utf8').write(s)
    print('written')
