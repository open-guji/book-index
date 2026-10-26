# 用法：P4WORK=<工作目录> python3 load.py；python3 scripts/dedup-census.py --out $P4WORK/census；再跑 cand_alpha.py／cand_beta.py／audit_4c.py
import pickle,re,collections,csv,sys
sys.path.insert(0,__import__('os').path.abspath(__import__('os').path.dirname(__file__)+'/../../..')+'/scripts'); sys.path.insert(0,__import__('os').path.abspath(__import__('os').path.dirname(__file__)+'/../../..')+'/.claude/qa')
from importlib import import_module
cen=import_module('dedup-census')
norm,norm_name,ANON=cen.norm,cen.norm_name,cen.ANONYMOUS
W,B,C=pickle.load(open(__import__('os').environ.get('P4WORK','/tmp/p4')+'/cache.pkl','rb'))
books_of=collections.defaultdict(list)
for b in B.values():
    if b.get('work_id'): books_of[b['work_id']].append(b)
SRC=re.compile(r'源記錄：([0-9a-z]{16})')
def first_author(w):
    if '【獨撰子目补撰人】' in (w.get('ai_note') or ''): return ''   # 他串据丛书补的撰人，视同无责任者
    au=[a for a in w.get('authors') or [] if isinstance(a,dict)]
    if not au: return ''
    n=norm_name(au[0].get('name'))
    return '' if n in ANON else n
def dyn(w):
    au=[a for a in w.get('authors') or [] if isinstance(a,dict)]
    return (au[0].get('dynasty') if au else None) or w.get('dynasty') or ''
def juan(x):
    j=x.get('juan_count')
    return j.get('number') if isinstance(j,dict) else None
CN=dict(zip('〇零一二兩三四五六七八九',[0,0,1,2,2,3,4,5,6,7,8,9]))
def cnum(t):
    n=cur=0
    for ch in t:
        if ch in CN: cur=CN[ch]
        elif ch in '十百千':
            n+=(cur or 1)*{'十':10,'百':100,'千':1000}[ch]; cur=0
    return n+cur or None
TJ=re.compile(r'([〇零一二兩三四五六七八九十百千]+)卷')
def tijuan(x):   # 題下（indexed_by.title_info）首个「N卷」，补 juan_count 缺时的卷数悬殊判断（4a-α乙 抽检发现）
    s=set()
    for i in x.get('indexed_by') or []:
        m=TJ.search((i.get('title_info') or '') if isinstance(i,dict) else '')
        if m: s.add(cnum(m.group(1)))
    return s-{None}
def srcids(x):
    s=set(SRC.findall(x.get('ai_note') or ''))
    for r in x.get('sources') or []:
        if isinstance(r,dict) and r.get('id') and re.fullmatch(r'[0-9a-z]{16}',r['id']): s.add(r['id'])
    return s
def feat(wid):
    w=W[wid]; bs=books_of.get(wid,[])
    cols=[]
    for b in bs:
        for c in b.get('contained_in') or []:
            cid=c.get('id') if isinstance(c,dict) else c
            if cid in C: cols.append(C[cid])
    src=srcids(w)
    for b in bs: src|=srcids(b)
    secs={i.get('section') for i in w.get('indexed_by') or [] if i.get('section')}
    return dict(id=wid,title=w.get('title'),fa=first_author(w),dyn=dyn(w),juan=juan(w),
        nbooks=len(bs),eds=[b.get('edition') or '' for b in bs],
        bjuan=({juan(b) for b in bs}|tijuan(w))-{None},
        cols=[(c['id'],c.get('title'),first_author(c)) for c in cols],
        src=src,secs=secs,note=w.get('ai_note') or '',
        congshu='叢書子目' in (w.get('ai_note') or ''),
        nlc=any(any(isinstance(r,dict) and r.get('id')=='nlc' for r in b.get('resources') or []) for b in bs),
        sources={i.get('source') for i in w.get('indexed_by') or []})
groups=[]
for r in csv.DictReader(open(__import__('os').environ.get('P4WORK','/tmp/p4')+'/census/同题组.tsv'),delimiter='\t'):
    groups.append(r)
