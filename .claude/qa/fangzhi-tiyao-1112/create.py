"""C 类（库内无同题）新建 Work：题名「[年号]主体」，indexed_by 仅总目 1996。
用法：在 book-index 仓根 python3 .claude/qa/fangzhi-tiyao-1112/create.py <classified.json> [--apply] [--limit N]
总目内同键重名（不同地区同名）的不建，留待人判。民國只写 period=modern，不写 dynasty。"""
import sys,os,json,datetime,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..'))
from norm import split
from classify import key
import mintid
SRC='中國地方志總目提要'
QING='順治 康熙 雍正 乾隆 嘉慶 道光 咸豐 同治 光緒 宣統 清'.split()
MING='洪武 建文 永樂 洪熙 宣德 正統 景泰 天順 成化 弘治 正德 嘉靖 隆慶 萬曆 泰昌 天啓 崇禎 明'.split()
YUAN='至正 至元 大德 泰定 元'.split(); SONG='淳祐 咸淳 宋'.split()
def dyn(rg):
    for n,l,p in(('清',QING,'qing'),('明',MING,'ming'),('元',YUAN,'liao-jin-yuan'),('宋',SONG,'song')):
        if rg in l: return n,p
    if rg=='民國': return None,'modern'
    return None,None
res=json.load(open(sys.argv[1])); apply='--apply' in sys.argv
lim=int(sys.argv[sys.argv.index('--limit')+1]) if '--limit' in sys.argv else 10**9
NEW=('D1新修次','D4无年号且摘要有他年号→新修次')
C=[r for r in res if r['cls']=='C库内无' or r.get('d') in NEW]
cnt=collections.Counter(key(r['bookName']) for r in C)
todo=[r for r in C if cnt[key(r['bookName'])]==1][:lim]
print('C',len(C),'总目内重名跳过',len(C)-len([r for r in C if cnt[key(r['bookName'])]==1]),'待建',len(todo))
ids=mintid.mint('Work','l3fangzhi',len(todo)) if apply else ['x']*len(todo)
today=datetime.date.today().isoformat()
for r,i in zip(todo,ids):
    rg,b=split(r['bookName']); title=f'[{rg}]{b}'
    d={'schema_version':1,'id':i,'type':'work','title':title}
    dy,p=dyn(rg)
    if dy: d['dynasty']=dy
    if p: d['period']=p
    e={'source':SRC,'title_info':r['bookName'],'section':r['sort']}
    if r.get('page'): e['page']=r['page']
    d['indexed_by']=[e]
    d['ai_note']=f'L3 方志專項（2026-11-12）據《中國地方志總目提要》（1996）新建：'+('正式庫無同題方志 Work' if r['cls'].startswith('C') else '正式庫同題方志 Work 皆為他年號／他修次')+f'；總目僅著錄題名與地區（{r["sort"]}），無責任者、卷數，未核他目；題名年號取總目題名前綴。'
    d['revision']='1.0.0'; d['revised_at']=today
    if apply:
        p_=mintid.path_for(i,f'{rg}{b}'); os.makedirs(os.path.dirname(p_),exist_ok=True)
        open(p_,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('apply' if apply else 'dry')
