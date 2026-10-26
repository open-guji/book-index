"""研-族谱：题名以「譜」结尾的未判同题组逐对比较（只读，不改数据）。
用法：BOOK_INDEX=../book-index python3 zupu_pairs.py <普查 --out 目录>/同题组.tsv <输出目录>
输出：族谱逐对判定-*.tsv（每对一行）、族谱-B候选与存疑D-详表-*.tsv。口径见上级目录 研-族谱-族谱同题判定口径.md。
"""
import os,sys,json,csv,re,collections,itertools
ROOT=os.environ.get('BOOK_INDEX','../book-index')
sys.path.insert(0,ROOT+'/.claude/qa'); import backrefs
TSV,OUT=sys.argv[1],sys.argv[2]
rows=[r for r in csv.reader(open(TSV),delimiter='\t')][1:]
pu=[r for r in rows if r[3].endswith('譜') and r[2]=='未判']
need=set(i for r in pu for i in r[5].split(','))
W={};B=collections.defaultdict(list)
for t,p,d in backrefs.iter_records(ROOT):
    if d.get('merged_into'): continue
    if t=='Work' and d['id'] in need: W[d['id']]=d
    elif t=='Book' and d.get('work_id') in need: B[d['work_id']].append(d)
print('载入 未判譜组 %d，Work %d，Book %d'%(len(pu),len(W),sum(map(len,B.values()))),file=sys.stderr)
if not W: sys.exit('载入 Work 为 0，检查 BOOK_INDEX')
G=[{'bulei':r[0],'cat':r[1],'key':r[3],'works':[{'work':W[i],'books':B.get(i,[])} for i in r[5].split(',') if i in W]} for r in pu]
BRS=re.compile(r'[\[［〔]([^\]］〕]*)[\]］〕]')
CN={'〇':0,'零':0,'一':1,'二':2,'兩':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def cn2i(s):
    if not s or re.search(r'[^〇零一二兩三四五六七八九十百千]',s): return None
    n=0;cur=0
    for ch in s:
        if ch in CN: cur=CN[ch]
        elif ch=='十': n+= (cur or 1)*10; cur=0
        elif ch=='百': n+= (cur or 1)*100; cur=0
        elif ch=='千': n+= (cur or 1)*1000; cur=0
    return n+cur
def sub(key):
    if key.endswith('年譜'): return '年譜'
    if re.search(r'(說文|諧聲|荔支|韻|音)',key): return '他譜'
    if re.search(r'(氏|族|宗|家|支|房|世|統|譜系|祠).*譜$',key) and not re.search(r'(畫|棋|琴|曲|花|菊|蘭|竹|梅|茶|香|錢|印|墨|硯|石|蟹|酒|牌|戲|拳|弈|樂|詞|韻|律|算)譜$',key): return '族譜'
    return '他譜'
ANON={'','佚名','不著撰人','無名氏','闕名'}
def juan_of(w):
    t=re.sub(r'[\[［〔][^\]］〕]*[\]］〕]','',w.get('title') or '')
    out=set()
    for i in w.get('indexed_by') or []:
        ti=re.sub(r'[\[［〔][^\]］〕]*[\]］〕]','',i.get('title_info') or '')
        rest=ti[len(t):] if ti.startswith(t) else ti
        m=re.match(r'([〇零一二兩三四五六七八九十百千□]+|不分)卷',rest)
        if m:
            v=m.group(1)
            if v=='不分': out.add('不分卷')
            elif '□' in v: pass
            else:
                n=cn2i(v)
                if n is not None:
                    extra=re.findall(r'(首|末|附|補遺|續)([〇一二三四五六七八九十]+)?卷',rest[m.end():])
                    out.add(str(n))
    return out
def places(t):
    return BRS.findall(t or '')
def pl_rel(A,B):
    if not A or not B: return '缺'
    a,b=A[0],B[0]
    if a==b: return '同'
    if a.startswith(b) or b.startswith(a): return '含'
    return '异'
def info(x):
    w=x['work'];bs=x['books']
    eds=[re.sub(r'\s','',b.get('edition') or '') for b in bs]
    yrs=set()
    for b in bs:
        y=(b.get('publication_info') or {}).get('year')
        if y and re.fullmatch(r'\d{4}',str(y)): yrs.add(str(y))
    tang=set(t for e in eds for t in re.findall(r'([一-鿿]{2}堂|[一-鿿]{2}義莊|[一-鿿]{2}祠)',e))
    tang={re.sub(r'^(本|刻|年|間|清|明)','',t) for t in tang}
    au=[a.get('name') for a in w.get('authors') or [] if isinstance(a,dict) and a.get('name') not in ANON]
    ai=[i.get('author_info') for i in w.get('indexed_by') or [] if i.get('author_info')]
    inst={p.get('institution') for b in bs for p in b.get('provenance') or []}-{None,''}
    m=re.search(r'源記錄：([0-9a-z、]+)',w.get('ai_note') or '')
    src=set(m.group(1).split('、')) if m else set()
    agg=len(src)>1
    return dict(id=w['id'],pl=places(w.get('title')),eds=set(eds)-{''},yrs=yrs,juan=juan_of(w),tang=tang,au=set(au),ai=ai,inst=inst,src=src,agg=agg,title=w.get('title'),nb=len(bs))
def rel(A,B):
    if not A or not B: return '缺'
    return '同' if A&B else '异'

def prim(w):
    """总目著录本身的版本（Work.indexed_by 总目 summary），不含后来补挂的 Book。"""
    vs=[];libs=set()
    for i in w.get('indexed_by') or []:
        s=i.get('summary') or ''
        m=re.match(r'共\s*\d+\s*個版本：(.*)',s)
        if not m: continue
        for part in m.group(1).split('；'):
            mm=re.match(r'(.*?)（(.*)）$',part.strip())
            if mm: vs.append(re.sub(r'\s','',mm.group(1))); libs|=set(mm.group(2).split('、'))
            else: vs.append(re.sub(r'\s','',part))
    return vs,libs

NH=re.compile(r'(洪武|建文|永樂|洪熙|宣德|正統|景泰|天順|成化|弘治|正德|嘉靖|隆慶|萬曆|泰昌|天啓|天啟|崇禎|順治|康熙|雍正|乾隆|嘉慶|道光|咸豐|同治|光緒|宣統|民國)([元〇一二三四五六七八九十]+|\d+)年')
def yr(e):
    s=set()
    for m in NH.finditer(e):
        v=m.group(2); v='1' if v=='元' else v
        s.add(m.group(1)+(str(cn2i(v)) if not v.isdigit() else v))
    return s
TANG=re.compile(r'([一-鿿]{2}(?:堂|義莊|祠|齋|軒|樓))')
def tang(e): return {t for t in TANG.findall(e) if not re.match(r'^(本|年|刻|印)',t)}
def info2(x):
    a=info(x); w=x['work']
    vs,libs=prim(w); a['pv']=vs; a['plib']=libs
    a['pyr']=set().union(*[yr(v) for v in vs]) if vs else set()
    a['ptang']=set().union(*[tang(v) for v in vs]) if vs else set()
    a['pagg']=len(vs)>1
    return a
def pcls(a,b):
    pl=pl_rel(a['pl'],b['pl'])
    if pl=='异': return 'C1异地望'
    if a['pagg'] or b['pagg']: return 'Z聚合'
    if not a['pv'] or not b['pv']: return 'N非总目著录'
    y=rel(a['pyr'],b['pyr']); j=rel({x for x in a['juan'] if x.isdigit()},{x for x in b['juan'] if x.isdigit()}); t=rel(a['ptang'],b['ptang'])
    lib=rel(a['plib'],b['plib'])
    if j=='异': return 'S卷异'
    if y=='异': return 'S年异'
    if t=='异': return 'S堂异'
    if y=='同':
        if j=='同' and lib=='同': return 'A1同年同卷同馆'
        if j=='同': return 'A2同年同卷异馆'
        if lib=='同' and t=='同': return 'A3同年同堂同馆卷缺'
        if lib=='同': return 'A4同年同馆卷缺'
        return 'D1同年余缺'
    if a['pv']==b['pv'] and lib=='同': return 'D2无年同版同馆'
    return 'D3证据不足'

import os
os.makedirs(OUT,exist_ok=True)
def verdict(c,a,b):
    if c.startswith('C1'): return 'C','地望不同：同名异族'
    if c.startswith('S卷异'): return 'S','卷数不同：异修或异支'
    if c.startswith('S年异'): return 'S','总目版本年份不同：异修'
    if c.startswith('S堂异'): return 'S','堂号不同：异支或异修'
    if c.startswith('A1'): return 'B候选','同年同卷同馆'
    if c.startswith('A2'): return 'B候选','同年同卷（异馆）'
    if c.startswith('A3'): return 'B候选','同年同堂同馆，卷数一侧缺'
    if c.startswith('A4'): return 'B候选·逐条核','同年同馆，卷数一侧缺，无堂号可比'
    if c.startswith('D1'): return 'D','同年但卷、馆或堂一侧缺'
    if c.startswith('D2'): return 'D','无确切年份，版本项与馆相同'
    if c.startswith('D3'): return 'D','证据不足（年份或卷数一侧缺）'
    if c.startswith('N'): return 'D','一侧非总目现存著录（史志目录等），待按纂修者比'
    if c.startswith('Z'): return 'D','一侧是多版本聚合 Work，先拆再判'
    return 'D',c
cnt=collections.Counter()
full=open(OUT+'/族谱逐对判定-20261025.tsv','w')
full.write('# 研-族谱 逐对判定（只读研究产物，基线 book-index main 07fc66fc）。判定：C＝同名异族不并；S＝同族异修／异支（处理待用户定）；B候选＝疑同一修重复著录；D＝存疑\n')
full.write('Work甲\tWork乙\t判定\t对类\t理由\t题名键\n')
cand=open(OUT+'/族谱-B候选与存疑D-详表-20261025.tsv','w')
cand.write('题名键\t判定\t对类\tWork甲\t题甲\t纂修甲\t版本甲\t卷甲\t馆甲\tWork乙\t题乙\t纂修乙\t版本乙\t卷乙\t馆乙\t建议\n')
for g in G:
    if sub(g['key'])!='族譜': continue
    I=[info2(x) for x in g['works']]
    for a,b in itertools.combinations(I,2):
        c=pcls(a,b); pl=pl_rel(a['pl'],b['pl'])
        if c[0] in 'SAD': c+=('·地望同' if pl=='同' else '·地望含' if pl=='含' else '·地望缺')
        v,why=verdict(c,a,b); cnt[v]+=1
        full.write('\t'.join([a['id'],b['id'],v,c,why,g['key']])+'\n')
        if v.startswith('B') or c.startswith(('D1','D2')):
            f=lambda x:[x['id'],x['title'],'/'.join(x['ai']),'/'.join(x['pv']),'/'.join(sorted(x['juan'])),'/'.join(sorted(x['plib']))]
            cand.write('\t'.join([g['key'],v,c]+f(a)+f(b)+[''])+'\n')
print(cnt)
