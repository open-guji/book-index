import sys,pickle,json,re,collections
sys.path.insert(0,'.claude/qa')
import entity_merge as em, jio
exec(open('/tmp/w/plan.py').read().split("res=pickle.load")[0])
pairs,why,out,defer=pickle.load(open('/tmp/w/plan.pkl','rb'))
DRY='--dry' in sys.argv
today='2026-11-02'
# 补充：僧祐→釋僧祐 ；沙門X 单条
extra=[]
sengyou=[i for i,d in live.items() if d['primary_name']=='僧祐'][0]; sy2=[i for i,d in live.items() if d['primary_name']=='釋僧祐'][0]
pairs.append((sengyou,sy2,'僧祐＝釋僧祐（著录前缀异写），同为南朝梁'))
a1=[i for i,d in live.items() if d['primary_name']=='沙門釋惠遠'][0]; a2=[i for i,d in live.items() if d['primary_name']=='釋惠遠'][0]
pairs.append((a1,a2,'沙門釋惠遠＝釋惠遠（著录前缀），同为晉'))
# rebuild clusters
par={}
def f(x):
    while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
    return x
targets=set()
CUR_T=set(sfx[x] for x in ['h9bu0q','h9bo40','h9bf8q','h9btx5','h9bu0v','h9bhv5','h9bmlv','h9btzo','h9bd7u','unrksj','h9bryt','h9bdjf','h9bdj8','up0iyr','8gbgkh','h9bhwl'])
for a,b,w in pairs: par[f(a)]=f(b)
cl=collections.defaultdict(set)
for a,b,w in pairs: cl[f(a)].update([a,b])
def score(i):
    v=live[i]; ds=v.get('dates') or {}
    return (cbdb(v) is not None)*4+bool(ds.get('birth') or ds.get('death'))*2+len(W.get(i,[]))*0.1+len(alts(v))*0.05+bool(v.get('dynasty'))*0.5
femt={}
fem_targets=[l for l in []]
ledger=[]
whyof={}
for a,b,w in pairs: whyof[a]=w; whyof.setdefault(b,w)
for r,mem in cl.items():
    mem=list(mem)
    tg=[m for m in mem if m in CUR_T or (live[m]['primary_name'] in ('徐燦','蔡琬','梁德繩','席佩蘭') and live[m].get('dynasty')=='清' and m not in [p[0] for p in pairs])]
    # 徐燦 多条：目标取 4 works 那条（已在 pairs 的 b 位）
    bs={b for a,b,w in pairs}-{a for a,b,w in pairs}
    tg2=[m for m in mem if m in bs and m in (set(CUR_T)|set(sfx[x] for x in ['unrksj']) )]
    if tg2: k=tg2[0]
    else:
        sup=[m for m in mem if live[m]['primary_name'].startswith('釋')]
        pool=sup or mem
        k=max(pool,key=score)
        if cbdb(live[k]) is None:
            pass
    # 女性目标：pairs 里 fem 条的 b
    for m in mem:
        if re.search(r'(妻|室)',live[m]['primary_name']) or live[m]['primary_name'].startswith('閨秀'): pass
    fk=[b for a,b,w in pairs if a in mem and ('妻' in live[a]['primary_name'] or '室' in live[a]['primary_name'] or live[a]['primary_name'].startswith('閨秀'))]
    if fk: k=fk[0]
    for l in mem:
        if l==k: continue
        w=whyof.get(l) or whyof.get(k)
        s=em.merge(l,k,reason=f'{live[l]["primary_name"]}→{live[k]["primary_name"]}：{w}（A12 僧道女性规范 2026-11-02）',rule='A12 僧道与女性人物条规范并条',date=today,dry=DRY,by='A12-僧道女性规范')
        ledger.append({'keeper':k,'keeper_name':live[k]['primary_name'],'loser':l,'loser_name':live[l]['primary_name'],'why':w,'redirected_works':s['redirected_works'],'added_alt_names':s['added_alt_names']})
        if DRY: continue
        rel=em.find_path(k); kd,kf=jio.load(rel)
        lo=live[l]; ln=lo['primary_name']
        names={kd['primary_name']}|{a['name'] for a in kd.get('alt_names') or [] if isinstance(a,dict)}
        if ln not in names:
            note='著录所见前缀／异写' if core(ln)==core(kd['primary_name']) else ('夫姓前缀称谓' if re.search('[妻室]',ln) else '并条保留的原主名')
            kd.setdefault('alt_names',[]).append({'name':ln,'type':'異寫' if core(ln)==core(kd['primary_name']) else '別名','note':note+'（A12 僧道女性规范 2026-11-02）'})
        for fl in ('dynasty','period'):
            if not kd.get(fl) and lo.get(fl):
                kd[fl]=lo[fl]
                if fl=='dynasty' and lo.get('dynasty_basis'): kd['dynasty_basis']=lo['dynasty_basis']
                if fl=='period' and lo.get('period_basis'): kd['period_basis']=lo['period_basis']
        if not kd.get('dates') and lo.get('dates'): kd['dates']=lo['dates']
        lc,kc=cbdb(lo),cbdb(kd)
        if lc and kc and lc!=kc:
            kd['ai_note']=(kd.get('ai_note','')+f' 并入 {l}（{ln}）时其 CBDB 号 {lc} 与本条 {kc} 不同，未采纳，待核。').strip()
        kd['revised_at']=today
        jio.save(rel,kd,kf)
# 沙門X 单条改名 / 閨秀梁端
ren=[]
for i,d in live.items():
    n=d['primary_name']
    if i in {x for p in pairs for x in p[:2]}: continue
    new=None
    if n=='沙門釋惠遠': new='釋惠遠'
    elif n.startswith('沙門'): new='釋'+n[2:]
    elif n=='閨秀梁端': new='梁端'
    if new:
        exist=[j for j,e in live.items() if e['primary_name']==new and j!=i]
        ren.append((i,n,new,exist))
for i,n,new,exist in ren:
    print('rename',n,'->',new,'exist',[(live[j]['primary_name'],live[j].get('dynasty'),live[i].get('dynasty')) for j in exist])
    if DRY or exist: continue
    rel=em.find_path(i); d,fm=jio.load(rel)
    d['primary_name']=new
    d.setdefault('alt_names',[]).append({'name':n,'type':'異寫','note':'著录前缀，主名统一为規範體例（A12 僧道女性规范 2026-11-02）'})
    d['revised_at']=today; jio.save(rel,d,fm)
json.dump(ledger,open('/tmp/w/ledger.json','w'),ensure_ascii=False,indent=1)
print('merged',len(ledger),'renames',len(ren))
