"""消化子 agent（有史地知识的人工判断）对留账的判定。只采 confidence=high。
用法（仓根）：apply_agents.py <tasksdir> [--apply]
 cross: assign(high, sort≠unsure)→挂；no_candidate_sorts 仅当该键已有候选 high 判给了别的地区才新建（related 指向这些候选）。
 rest: same(high)→挂（候选已挂他条的跳过）；new(high)→新建（related 指向同题候选）。"""
import sys,os,json,glob,collections,datetime
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..'))
from classify import key,split
import mintid
SRC='中國地方志總目提要'
td=sys.argv[1]; apply='--apply' in sys.argv
L=json.load(open('/home/user/book_index_json/tiyao_data/地方志總目1996.json'))
ent={(x['sort'],x['bookName']):x for x in L}
bys=collections.defaultdict(list)
for x in L: bys[x['sort']].append(x)
paths={}
for f in glob.glob('Work/*/*/*/*.json'): paths[os.path.basename(f).split('-')[0]]=f
today=datetime.date.today().isoformat()
QING='順治 康熙 雍正 乾隆 嘉慶 道光 咸豐 同治 光緒 宣統 清'.split()
MING='洪武 建文 永樂 洪熙 宣德 正統 景泰 天順 成化 弘治 正德 嘉靖 隆慶 萬曆 泰昌 天啓 崇禎 明'.split()
def dyn(rg):
    if rg in QING: return '清','qing'
    if rg in MING: return '明','ming'
    if rg=='民國': return None,'modern'
    return None,None
att=[];cre=[]
def find_entry(sort,keystr):
    rg,b=keystr.split('|')
    for x in bys.get(sort,[]):
        if key(x['bookName'])==(rg,b): return x
for f in sorted(glob.glob(td+'/out_cross*.json')):
    for k in json.load(open(f)):
        if any(w in k['key'] for w in('瀘溪','石門')): continue
        good=[a for a in k['assign'] if a['confidence']=='high' and a['sort']!='unsure']
        for a in good:
            e=find_entry(a['sort'],k['key'])
            if e: att.append((e,a['candidate_id']))
        if good:
            for s in k.get('no_candidate_sorts',[]):
                e=find_entry(s,k['key'])
                if e and e['sort'] not in {a['sort'] for a in good}: cre.append((e,[a['candidate_id'] for a in good]))
for f in sorted(glob.glob(td+'/out_rest*.json')):
    for r in json.load(open(f)):
        if r['confidence']!='high': continue
        e=ent.get(tuple(r['entry']))
        if not e: continue
        if r['verdict']=='same' and r.get('candidate_id'): att.append((e,r['candidate_id']))
        elif r['verdict']=='new': cre.append((e,[]))  # related 由 rest 的候选信息补不到，留空；下面按同题 Work 补
print('挂',len(att),'建',len(cre))
if not apply: sys.exit()
n=0
for e,wid in att:
    p=paths.get(wid)
    if not p: continue
    d=json.load(open(p))
    if any(i.get('source')==SRC for i in d.get('indexed_by',[])): continue
    x={'source':SRC,'title_info':e['bookName'],'section':e['sort']}
    if e.get('summaryPage'): x['page']=e['summaryPage']
    d.setdefault('indexed_by',[]).append(x); a,b,c=map(int,d['revision'].split('.')); d['revision']=f'{a}.{b+1}.0'; d['revised_at']=today
    open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n'); n+=1
print('已挂',n)
# 新建：related 到同题（去年号主体相同、含 SRC 条目的 fz）Work
base={}
for i,p in paths.items():
    try: d=json.load(open(p))
    except Exception: continue
    if d.get('merged_into'): continue
    base.setdefault(key(d['title'])[1],[]).append(i)
ids=mintid.mint('Work','l3fangzhi',len(cre)); made=collections.defaultdict(list)
for (e,sib),i in zip(cre,ids):
    rg,b=split(e['bookName']); k=key(e['bookName'])
    sib=list(sib) or base.get(k[1],[])
    d={'schema_version':1,'id':i,'type':'work','title':f'[{rg}]{b}' if rg else b}
    dy,p=dyn(rg)
    if dy: d['dynasty']=dy
    if p: d['period']=p
    x={'source':SRC,'title_info':e['bookName'],'section':e['sort']}
    if e.get('summaryPage'): x['page']=e['summaryPage']
    d['indexed_by']=[x]
    rel=[{'id':s,'relation':'related','note':'同名異修／異地同名，分立：總目1996另著錄「%s」'%e['bookName']} for s in (sib+made[k])[:12] if s!=i]
    if rel: d['related_works']=rel
    d['ai_note']=f'L3 方志專項補遺（2026-11-15）據《中國地方志總目提要》（1996）新建（{e["sort"]}）：經逐條按作者、朝代、地區判定與庫內同題條不同；總目僅著錄題名與地區，無責任者、卷數。'
    d['revision']='1.0.0'; d['revised_at']=today
    made[k].append(i)
    pp=mintid.path_for(i,(rg+b) if rg else b); os.makedirs(os.path.dirname(pp),exist_ok=True)
    open(pp,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
