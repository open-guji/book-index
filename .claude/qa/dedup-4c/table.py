"""4c 复核：国图重配「挂最接近 Work」的 Book，逐条列出国图著者与各同题候选 Work 的著者、年份比对。
用法：P4WORK=<目录> python3 .claude/qa/dedup-part4/load.py；P4WORK=<目录> python3 .claude/qa/dedup-4c/table.py
输出 $P4WORK/4c_table.json（每个国图 Book 一行）。需 opencc-python-reimplemented。"""
import os,re,json,glob,pickle,collections,sys
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)+'/../../../scripts'))
from importlib import import_module
cen=import_module('dedup-census'); norm,norm_name,ANON=cen.norm,cen.norm_name,cen.ANONYMOUS
import opencc; _T=opencc.OpenCC('s2t').convert
T=lambda s:_T((s or '').replace('杨','楊'))
ROOT=os.path.abspath(os.path.dirname(__file__)+'/../../..')
P=os.environ.get('P4WORK','/tmp/p4')
W,B,C=pickle.load(open(P+'/cache.pkl','rb'))
print('载入',len(W),len(B),len(C)); assert W and B
ENT={}
for p in glob.glob(ROOT+'/Entity/*/*/*/*.json'):
    d=json.load(open(p,encoding='utf-8')); ENT[d['id']]=d
print('Entity',len(ENT)); assert ENT
books_of=collections.defaultdict(list)
for b in B.values():
    if b.get('work_id'): books_of[b['work_id']].append(b)
RX=re.compile(r'國圖數字古籍重配（[^）]*）新建；國圖著錄題名「([^」]*)」、責任者「([^」]*)」、版本項「([^」]*)」；?([^\n]*)')
JUAN=re.compile(r'[\s　]*[一二三四五六七八九十百千〇零兩]+卷.*$|[\s　]+.*$')
def tkey(s): return norm(T(JUAN.sub('',(s or '').strip()) or s or ''))
bytitle=collections.defaultdict(set)
for wid,w in W.items():
    if w.get('title'): bytitle[norm(T(w['title']))].add(wid)
DYN=re.compile(r'^[\s]*[\(（\[〔【]([^\)）\]〕】]{1,4})[\)）\]〕】]\s*')
ROLE='撰著編编輯辑注註校纂述評评選选譯译修訂订補补增刪删箋笺疏解釋释考集錄录刻鈔抄錄書书繪绘圖图定等原重序跋批點点句讀讀音義义'
ROLERX=re.compile(r'(等)?(?:章句|音義|集注|集註|集解|集說|纂修|重修|主修|續修|編次|選輯|彙評|批點|評點|參訂|重訂|校注|校註|校刊|校正|補注|直解|增訂|撰|著|編|编|輯|辑|注|註|校|纂|述|評|评|選|选|譯|译|修|訂|订|補|补|增|刪|删|箋|笺|疏|解|考|集|錄|录|刻|鈔|抄|繪|绘|批|點|点|序|跋|書|题|題|傳|述)+$')
def nlc_people(s):
    out=[]
    s=re.sub(r'(?<=[^\s;；,，、@])(?=[\(（\[〔][^\)）\]〕]{1,4}[\)）\]〕])',' ',T(s or ''))
    for part in re.split(r"[;；,，、\s　]+|@@@",s):
        part=part.strip()
        if not part: continue
        dyn=''
        m=DYN.match(part)
        if m: dyn=m.group(1); part=part[m.end():]
        part=re.sub(r'^(題|题|舊題|旧题)','',part)
        part=re.sub(r'[\[\]［］〔〕]','',part)
        name=ROLERX.sub('',part)
        role=part[len(name):]
        name=norm_name(name)
        if len(name)>=2 and name not in ANON: out.append((dyn,name,role))
    return out
def work_names(w):
    """Work 的著者文本：authors 名、所挂 Entity 主名与别名、indexed_by.author_info 原文（繁体化）。"""
    names=set(); text=[]
    for a in w.get('authors') or []:
        if not isinstance(a,dict): continue
        n=norm_name(T(a.get('name') or ''))
        if n and n not in ANON: names.add(n)
        e=ENT.get(a.get('entity_id'))
        if e:
            names.add(norm_name(T(e.get('name') or '')))
            for x in e.get('alt_names') or []:
                x=x.get('name') if isinstance(x,dict) else x
                if x: names.add(norm_name(T(x)))
    for i in w.get('indexed_by') or []:
        if i.get('author_info'): text.append(T(i['author_info']))
    names.discard('')
    return names,' '.join(text)
def match(pn,w):
    names,text=work_names(w)
    for dyn,n,role in pn:
        if n in names or any(len(x)>=2 and (x in n) for x in names) or n in text: return True
    return False
def has_auth(w):
    names,text=work_names(w); return bool(names or text.strip())
def dyn_of(w):
    au=[a for a in w.get('authors') or [] if isinstance(a,dict)]
    return (au[0].get('dynasty') if au else None) or w.get('dynasty') or ''
def years(v): return set(re.findall(r'(?<!\d)(1[0-9]{3})(?!\d)',v or ''))
def byears(wid,skip):
    ys=set()
    for x in books_of.get(wid,[]):
        if x['id']==skip: continue
        d=x.get('dating') or {}
        if isinstance(d.get('year'),int): ys.add(str(d['year']))
        pi=x.get('publication_info') or {}
        if re.fullmatch(r'\d{4}.*',str(pi.get('year') or '')): ys.add(str(pi['year'])[:4])
    return ys
def wbrief(wid,bid,ey):
    w=W[wid]; names,text=work_names(w)
    return dict(id=wid,title=w.get('title'),authors=[(a.get('dynasty'),a.get('name'),a.get('role')) for a in w.get('authors') or [] if isinstance(a,dict)],
        author_info=text[:120],dyn=dyn_of(w),juan=(w.get('juan_count') or {}).get('number') if isinstance(w.get('juan_count'),dict) else None,
        nbooks=len(books_of.get(wid,[])),same_year=bool(ey and ey in byears(wid,bid)),
        section=[i.get('section') for i in w.get('indexed_by') or [] if i.get('section')][:2],
        congshu='叢書子目' in (w.get('ai_note') or ''),reign=sorted(bracket_reign(w.get('title'))),eds=eds(wid,bid))
REIGN=[('洪武',1368,1398),('建文',1399,1402),('永樂',1403,1424),('洪熙',1425,1425),('宣德',1426,1435),('正統',1436,1449),('景泰',1450,1457),('天順',1457,1464),('成化',1465,1487),('弘治',1488,1505),('正德',1506,1521),('嘉靖',1522,1566),('隆慶',1567,1572),('萬曆',1573,1620),('泰昌',1620,1620),('天啓',1621,1627),('崇禎',1628,1644),('順治',1644,1661),('康熙',1662,1722),('雍正',1723,1735),('乾隆',1736,1795),('嘉慶',1796,1820),('道光',1821,1850),('咸豐',1851,1861),('同治',1862,1874),('光緒',1875,1908),('宣統',1909,1911),('民國',1912,1949)]
RALIAS={'萬厯':'萬曆','万历':'萬曆','天啟':'天啓','永乐':'永樂','正统':'正統','天顺':'天順','隆庆':'隆慶','崇祯':'崇禎','顺治':'順治','嘉庆':'嘉慶','咸丰':'咸豐','光绪':'光緒','宣统':'宣統','民国':'民國'}
def reigns(s):
    s=T(s or '')
    for a,b2 in RALIAS.items(): s=s.replace(a,b2)
    out={r for r,_,_ in REIGN if r in s}
    ys=years(s)
    if not out and len(ys)==1:
        y=int(ys.pop()); out={r for r,a,b2 in REIGN if a<=y<=b2}
        if len(out)>1: out=set()
    return out
def bracket_reign(t):
    m=re.match(r'^\s*[\[［【〔(（]([^\]］】〕)）]{2,4})[\]］】〕)）]',T(t or ''))
    return reigns(m.group(1)) if m else set()
BYNAME=collections.defaultdict(set)
for wid,w in W.items():
    for a in w.get('authors') or []:
        if not isinstance(a,dict): continue
        n=norm_name(T(a.get('name') or ''))
        if len(n)>=2 and n not in ANON: BYNAME[n].add(wid)
        e=ENT.get(a.get('entity_id'))
        if e:
            for x in [e.get('name')]+[(y.get('name') if isinstance(y,dict) else y) for y in e.get('alt_names') or []]:
                x=norm_name(T(x or ''))
                if len(x)>=2: BYNAME[x].add(wid)
def cross(pn,tk,cands):
    out=[]
    for dyn,n,role in pn:
        for wid in BYNAME.get(n,()):
            if wid in cands: continue
            t2=norm(T(W[wid].get('title') or ''))
            if not t2: continue
            share=len(set(tk)&set(t2))/max(1,len(set(tk)))
            if share>=0.5: out.append((wid,W[wid].get('title'),n,round(share,2)))
    return sorted(out,key=lambda x:-x[3])[:6]
def eds(wid,skip):
    return [f"{x.get('edition') or ''}|{(x.get('dating') or {}).get('year') or ''}" for x in books_of.get(wid,[]) if x['id']!=skip][:8]
rows=[]
for b in B.values():
    m=RX.search(b.get('ai_note') or '')
    if not m: continue
    t,au,ver,rest=m.groups()
    kind='同題多書' if '同題多書' in rest else '前輪未定' if '前輪未能確定' in rest else None
    if not kind: continue
    cur=b.get('work_id')
    cands=set(bytitle.get(tkey(b.get('title')),()))|set(bytitle.get(tkey(t),()))
    if cur in W: cands.add(cur)
    pn=nlc_people(au)
    ey=(lambda m:m.group(1) if m else None)(re.search(r'\[(\d{4})\]',ver))
    info={}
    for c in cands:
        info[c]=wbrief(c,b['id'],ey); info[c]['match']=match(pn,W[c]) if pn else None; info[c]['has_auth']=has_auth(W[c])
    cm=info.get(cur,{}).get('match')
    others=[c for c in cands if c!=cur and info[c]['match']]
    if not pn: cat='国图无著者'
    elif cm: cat='现挂著者合'
    elif others: cat='他候选著者合'
    elif cur in info and not info[cur]['has_auth']: cat='现挂无著者·无他候选合'
    else: cat='现挂著者异·无他候选合'
    nr=sorted(bracket_reign(t) or reigns(ver))
    rows.append(dict(reign=nr,cross=cross(pn,tkey(t),cands),book=b['id'],path=b['_path'],kind=kind,cat=cat,nlc_title=t,nlc_author=au,people=pn,ver=ver,year=ey,
        cur=cur,why=rest,others=others,cands=info))
cnt=collections.Counter((r['kind'],r['cat']) for r in rows)
for k in sorted(cnt): print(k,cnt[k])
print('合计',len(rows))
json.dump(rows,open(P+'/4c_table.json','w'),ensure_ascii=False,indent=1)
