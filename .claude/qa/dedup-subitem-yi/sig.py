import json, glob, os, re, sys, itertools, collections
ROOT=os.environ.get('BOOK_INDEX','.')
sys.path.insert(0, ROOT+'/.claude/qa')
from scan import VARIANTS
S=os.environ.get('OUT','/tmp/subitem-yi')
feat=json.load(open(S+'/feat.json'))
# Collection by source record
col={}
for p in glob.glob(ROOT+'/Collection/*/*/*/*.json'):
    c=json.load(open(p))
    for s in c.get('sources',[]) or []:
        if s.get('id'): col[s['id']]=c
print('载入 Collection', len(col), file=sys.stderr)
CN='〇零一二三四五六七八九十百千'
def cn2i(s):
    if not s: return None
    d={c:i for i,c in enumerate('零一二三四五六七八九')}; d['〇']=0
    tot=0; cur=0
    for ch in s:
        if ch in d: cur=d[ch]
        elif ch=='十': tot+=(cur or 1)*10; cur=0
        elif ch=='百': tot+=(cur or 1)*100; cur=0
        elif ch=='千': tot+=(cur or 1)*1000; cur=0
    return tot+cur
CORE=re.compile(r'[（(][^）)]*[）)]|[一二三四五六七八九十百千〇零]+種.*$|第[一二三四五六七八九十]+[集輯].*$')
def core(t): return CORE.sub('', t or '').translate(VARIANTS).strip()
def nm(s): return (s or '').translate(VARIANTS).replace(' ','')
def juan_of(w):
    """叢書部 title_info 去题名后的卷数串；取首卷数"""
    res=[]
    for ti,ai,sec,sm in w['ib']:
        if not ti: continue
        rest=ti
        t=w['title']
        rest=nm(ti); tt=nm(t)
        if rest.startswith(tt): rest=rest[len(tt):]
        m=re.match(r'([一二三四五六七八九十百千〇零]+)卷',rest)
        res.append((rest, cn2i(m.group(1)) if m else ('不分卷' if '不分卷' in rest else None)))
    return res
DYN=sorted(['先秦','周','秦','漢','西漢','東漢','後漢','三國','魏','蜀','吳','晉','西晉','東晉','南朝','宋','齊','梁','陳','北魏','北齊','北周','隋','唐','五代','前蜀','後蜀','南唐','後唐','後晉','遼','金','元','明','清','民國','日本','朝鮮','高麗','南宋','北宋'],key=len,reverse=True)
ROLE=re.compile(r'(等)?(撰|輯|編|錄|譯|注|註|著|纂|述|校|補遺|補|並考|考|鈔|抄|選|評|訂|集|敕撰|奉敕撰|筆述|口授|增訂|重訂|彙編|參訂|同撰|合撰|箋|疏|釋|音義|講|說|記|書|刪|定|批|點|圈點|手輯)+.*$')
def parse_ai(ai):
    names=set()
    for seg in re.split(r'[;；]', ai or ''):
        seg=seg.strip()
        seg=re.sub(r'^(舊題|題)','',seg)
        for d in DYN:
            if seg.startswith(d): seg=seg[len(d):]; break
        seg=ROLE.sub('',seg)
        m=re.match(r'^(.*?)（(.*?)）',seg)
        if m: cands=[m.group(1),m.group(2)]
        else: cands=[seg]
        for c in cands:
            c=nm(c)
            if c and '□' not in c and len(c)<=6: names.add(c)
    return names
def names_of(w):
    ns=set(); dy=set()
    for a in w['authors']:
        for x in re.split(r'[;；]', a[0] or ''):
            if x: ns.add(nm(x))
        if a[2]: dy.add(a[2])
    for ti,ai,sec,sm in w['ib']:
        ns|=parse_ai(ai)
    src='self' if ns else None
    if not ns and any((sec or '').find('獨撰類')>=0 for ti,ai,sec,sm in w['ib']):
        c=col.get(w['colrec'])
        if c:
            for a in c.get('authors') or []:
                if a.get('name'): ns.add(nm(a['name']))
                if a.get('dynasty'): dy.add(a['dynasty'])
            src='col' if ns else None
    return ns, dy, src
def eff_author(w):
    ns,dy,src=names_of(w)
    return sorted(ns), sorted(dy), src
def huxian(a,b):
    """a 的非叢書部著录 summary 里出现 b 所在丛书名＋本"""
    k=core(b['col'])
    if len(k)<2: return False
    for ti,ai,sec,sm in a['ib']:
        if sec and sec.startswith('叢書部'): continue
        if k+'本' in sm.translate(VARIANTS) or (k in sm.translate(VARIANTS)): return True
    return False
def yingyin(a,b):
    k=core(b['col'])
    for ti,ai,sec,sm in a['ib']:
        s=sm.translate(VARIANTS)
        if len(k)>=2 and ('影印'+k in s or '據'+k in s): return True
    return False
out=[]
for gi,g in enumerate(feat):
    for a,b in itertools.combinations(g['works'],2):
        ja=[x[1] for x in juan_of(a) if x[1] is not None]; jb=[x[1] for x in juan_of(b) if x[1] is not None]
        jsa={x[0] for x in juan_of(a)}; jsb={x[0] for x in juan_of(b)}
        jconf = bool(ja and jb and not (set(ja)&set(jb)))
        jsame = bool(jsa & jsb)
        ea=eff_author(a); eb=eff_author(b)
        if ea[0] and eb[0]:
            asame = bool(set(ea[0])&set(eb[0]))
            acat = '同' if asame else ('同姓' if {x[0] for x in ea[0]}&{x[0] for x in eb[0]} else '异')
        else: acat='缺'
        hx = huxian(a,b) or huxian(b,a)
        yy = yingyin(a,b) or yingyin(b,a)
        out.append(dict(g=gi,key=g['key'],bulei=g['bulei'],cat=g['cat'],a=a['id'],b=b['id'],
            cola=a['col'],colb=b['col'],aa=ea,ab=eb,acat=acat,ja=sorted(jsa),jb=sorted(jsb),jconf=jconf,jsame=jsame,hx=hx,yy=yy))
json.dump(out,open(S+'/pairs.json','w'),ensure_ascii=False)
c=collections.Counter((p['acat'],'卷矛盾' if p['jconf'] else ('卷串同' if p['jsame'] else '卷不明'),'互见' if p['hx'] else ('影印' if p['yy'] else '-')) for p in out)
for k,v in sorted(c.items(),key=lambda x:-x[1]): print(k,v)
print(len(out))
