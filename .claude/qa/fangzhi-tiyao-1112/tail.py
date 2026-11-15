"""尾部处理（2026-11-15）。输入 classify.py 对「未挂条目」的分类（rem 分类 json），在仓根执行：
  python3 .claude/qa/fangzhi-tiyao-1112/tail.py <cl_rem.json> <skip.tsv> [--apply]
B3 精确同题唯一 → 挂；同地多年且库内无该年 → 新建（related 指向同题候选，census 视为已判分立）；
D2b／D1／D4／C 新建；D0 若有同朝代候选则留账；总目内跨地同名、无年份、提及多个、无从判别、无年号前缀一律留账。不确定不挂不建。"""
import sys,os,json,re,collections,datetime
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..'))
from classify import key,split,isfz
import mintid
SRC='中國地方志總目提要'
QING='順治 康熙 雍正 乾隆 嘉慶 道光 咸豐 同治 光緒 宣統 清'.split()
MING='洪武 建文 永樂 洪熙 宣德 正統 景泰 天順 成化 弘治 正德 嘉靖 隆慶 萬曆 泰昌 天啓 崇禎 明'.split()
YUAN='至正 至元 大德 泰定 元'.split(); SONG='淳祐 咸淳 宋'.split()
def dyn(rg):
    for n,l,p in(('清',QING,'qing'),('明',MING,'ming'),('元',YUAN,'liao-jin-yuan'),('宋',SONG,'song')):
        if rg in l: return n,p
    return (None,'modern') if rg=='民國' else (None,None)
cl=json.load(open(sys.argv[1])); apply='--apply' in sys.argv
W={}
for r,_,fs in os.walk('Work'):
    for f in fs:
        if not f.endswith('.json'): continue
        p=os.path.join(r,f); d=json.load(open(p))
        if d.get('merged_into'): continue
        ib=[i for i in d.get('indexed_by',[]) if isinstance(i,dict)]
        secs=[(i.get('source'),i.get('section') or '') for i in ib]
        sm=' '.join((i.get('summary') or '')+(i.get('title_info') or '') for i in ib)
        W[d['id']]=dict(title=d['title'],dyn=d.get('dynasty',''),fz=isfz(secs) or any(a==SRC for a,_ in secs),sm=sm,path=p,has=any(i.get('source')==SRC and i.get('title_info')==None for i in ib),
                        srcs=[i.get('title_info') for i in ib if i.get('source')==SRC])
idx=collections.defaultdict(list)
for i,w in W.items(): idx[key(w['title'])[1]].append(i)
cnt=collections.Counter(key(x['bookName']) for x in cl)
sorts=collections.defaultdict(set)
for x in cl: sorts[key(x['bookName'])].add(x['sort'])
yre=re.compile(r'^[元二三四五六七八九十廿卅百]+年')
attach=[];create=[];skip=[]
for x in cl:
    rg,b=key(x['bookName']); k=(rg,b); name=x['bookName']
    def S(why): skip.append((why,x['sort'],name))
    if x['cls']=='A唯一对唯一': continue
    if not rg: S('E无年号前缀'); continue
    if x['cls']=='B3命中非方志类Work':
        if len(x['ids'])==1 and cnt[k]==1: attach.append((x,x['ids'][0]))
        else: S('B3不唯一')
        continue
    if x['cls']=='C库内无': create.append((x,[])); continue
    cands=[i for i in idx[b] if W[i]['fz']]
    if len(sorts[k])>1 or (x['cls']=='B1总目内重名' and False): S('跨地同名'); continue
    raw=name[len(rg):] if name.startswith(rg) else name
    m=yre.match(raw); ys=rg+m.group(0) if m else None
    if x['cls'] in('B1总目内重名','B2库内多候选'):
        same=[i for i in cands if key(W[i]['title'])[0]==rg]
        if not ys: S('同键无年份'); continue
        hit=[i for i in same if ys in W[i]['sm']]
        if hit: S('已被同年条目覆盖'); continue
        if not same or not all(re.search(rg+r'[元二三四五六七八九十廿卅百]+年',W[i]['sm']) for i in same): S('同键候选无明确年份,不能断言异修'); continue
        create.append((x,same)); continue
    # D 类
    reigns={key(W[i]['title'])[0] for i in cands}
    if not cands:
        d_=dyn(rg)[0]
        nf=[i for i in idx[b]]
        if nf: S('D0同题非方志类(任何朝代)'); continue
        create.append((x,[])); continue
    if rg in reigns: S('D3同年号多候选'); continue
    named=[i for i in cands if key(W[i]['title'])[0]=='']
    if named and any(rg in W[i]['sm'] for i in named): S('D3提及'); continue
    if named and not all(any(r_ in W[i]['sm'] for r_ in ['康熙','乾隆','光緒','道光','嘉慶','同治','順治','雍正','咸豐','宣統','民國','萬曆','嘉靖','崇禎']) for i in named): S('D5无从判别'); continue
    create.append((x,[i for i in cands][:12]))
print('挂',len(attach),'建',len(create),'留账',len(skip),collections.Counter(w for w,_,_ in skip))
open(sys.argv[2],'w').write('\n'.join('\t'.join(s) for s in skip)+'\n')
if not apply: sys.exit()
today=datetime.date.today().isoformat()
for x,wid in attach:
    p=W[wid]['path']; d=json.load(open(p))
    if any(i.get('source')==SRC for i in d.get('indexed_by',[])): continue
    e={'source':SRC,'title_info':x['bookName'],'section':x['sort']}
    if x.get('page'): e['page']=x['page']
    d.setdefault('indexed_by',[]).append(e); a,b2,c=map(int,d['revision'].split('.')); d['revision']=f'{a}.{b2+1}.0'; d['revised_at']=today
    open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
ids=mintid.mint('Work','l3fangzhi',len(create))
made=collections.defaultdict(list)
for (x,sib),i in zip(create,ids):
    rg,b=split(x['bookName'])
    d={'schema_version':1,'id':i,'type':'work','title':f'[{rg}]{b}'}
    dy,p=dyn(rg)
    if dy: d['dynasty']=dy
    if p: d['period']=p
    e={'source':SRC,'title_info':x['bookName'],'section':x['sort']}
    if x.get('page'): e['page']=x['page']
    d['indexed_by']=[e]
    rel=[{'id':s,'relation':'related','note':f'同名異修，分立：總目1996另著錄「{x["bookName"]}」，與本條版本不同'} for s in (list(sib)+made[key(x['bookName'])])[:12]]
    if rel: d['related_works']=rel
    d['ai_note']=f'L3 方志專項補遺（2026-11-15）據《中國地方志總目提要》（1996）新建：異體歸一後庫內無同年號同題之條{"，且庫內同題候選版本年份不含此年" if sib else ""}；總目僅著錄題名與地區（{x["sort"]}），無責任者、卷數，未核他目。'
    d['revision']='1.0.0'; d['revised_at']=today
    made[key(x['bookName'])].append(i)
    p_=mintid.path_for(i,f'{rg}{b}'); os.makedirs(os.path.dirname(p_),exist_ok=True)
    open(p_,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
