import json,pickle,re,collections,csv
from build_idx import norm_t
W=pickle.load(open('works.pkl','rb'))
SRC='續修四庫全書總目提要'
idx=collections.defaultdict(set)
for i,w in W.items():
    for t in [w['t'],w['ot']]+w['at']:
        if t:
            idx[norm_t(t)].add(i)
            t2=re.sub(r'（[^（）]*）|\([^()]*\)|〔[^〔〕]*〕|【[^【】]*】|\[[^\[\]]*\]','',t)
            if t2!=t and t2: idx[norm_t(t2)].add(i)
NUM='零〇一二三四五六七八九十百千萬兩'
def cn(s):
    s=s.replace('兩','二').replace('〇','零')
    if s=='': return None
    v=0;cur=0;tot=0
    m={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'零':0}
    for c in s:
        if c in m: cur=cur*10+m[c] if False else m[c]; last=cur
        elif c=='十': tot+=(cur or 1)*10; cur=0
        elif c=='百': tot+=(cur or 1)*100; cur=0
        elif c=='千': tot+=(cur or 1)*1000; cur=0
        elif c=='萬': tot=(tot+cur)*10000; cur=0
    return tot+cur
MEAS=re.compile(r'(不分卷|無卷數|无卷数|['+NUM+r']+(?:卷|種|冊|册|張|篇|葉|頁|幅|圖)(?:首|末|附)?)')
def parse(name):
    """返回 (主题名, 卷数或None, 复合标志, 余部)"""
    m=MEAS.search(name)
    if not m: return name,None,False,''
    main=name[:m.start()]
    rest=name[m.end():]
    juan=None
    if m.group(1).endswith('卷') and m.group(1)[0] in NUM: juan=cn(m.group(1)[:-1])
    elif m.group(1)=='不分卷': juan=0
    rs=rest.strip()
    SUPP=('附','續','续','補','补','卷首','首','外集','考異','二集','三集','別集','遺','拾遺','總綱','目錄','卷末','末','校','訂','又','外編','餘','續編','後編','附錄','年譜')
    comp=bool(rs) and not rs.startswith(SUPP) and not re.match(r'^[首末卷附]',rs)
    return main,juan,comp,rest
rows=[]
d=json.load(open('/home/user/book_index_json/tiyao_data/續四庫總目1931.json'))
for k,x in enumerate(d):
    main,juan,comp,rest=parse(x['bookName'])
    n=norm_t(main)
    c=sorted(idx.get(n,()))
    rows.append(dict(k=k,sort=x['sort'],name=x['bookName'],page=x['summaryPage'],main=main,juan=juan,comp=comp,rest=rest,cands=c))
pickle.dump(rows,open('rows.pkl','wb'))
st=collections.Counter(('0' if not r['cands'] else '1' if len(r['cands'])==1 else 'n', r['comp'], r['sort'].split('/')[0]) for r in rows)
for k,v in sorted(st.items()): print(k,v)
print(collections.Counter(('0' if not r['cands'] else '1' if len(r['cands'])==1 else 'n') for r in rows))
