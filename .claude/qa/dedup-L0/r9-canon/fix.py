import json,re,sys,collections
S='/tmp/claude-0/-home-user/e59db2b9-8fd4-5ed9-a492-942f4a225576/scratchpad/r9'
APPLY='--apply' in sys.argv
PR=re.compile('普寧寺|磧砂延聖|東禪等覺院|開元禪寺|福州開元寺|圓覺禪院|資福禪寺|管主八')
R=[('洪武',1368),('建文',1399),('永樂',1403),('洪熙',1425),('宣德',1426),('正統',1436),('景泰',1450),('天順',1457),('成化',1465),('弘治',1488),('正德',1506),('嘉靖',1522),('隆慶',1567),('萬曆',1573),('泰昌',1620),('天啓',1621),('崇禎',1628),('順治',1644),('康熙',1662),('雍正',1723),('乾隆',1736),('嘉慶',1796),('道光',1821),('咸豐',1851),('同治',1862),('光緒',1875),('宣統',1909),('民國',1912)]
RE={n:(s,(R[i+1][1]-1) if i+1<len(R) else 1949) for i,(n,s) in enumerate(R)}
RE['宣統']=(1909,1911); RE['天啟']=RE['天啓']
D={'元':1,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def num(s):
    if s in ('元',): return 1
    if '十' in s:
        a,b=s.split('十'); return (D[a] if a else 1)*10+(D[b] if b else 0)
    return D.get(s)
N='[元一二三四五六七八九十]+'
def parse(e):
    m=re.search('(%s)(%s)年至(?:(%s))?(%s)年'%('|'.join(RE),N,'|'.join(RE),N),e)
    if m:
        r1=m.group(1); r2=m.group(3) or r1
        return [RE[r1][0]+num(m.group(2))-1, RE[r2][0]+num(m.group(4))-1]
    m=re.search('(%s)(%s)至(%s)年'%('|'.join(RE),N,N),e)
    if m: r=m.group(1); return [RE[r][0]+num(m.group(2))-1, RE[r][0]+num(m.group(3))-1]
    m=re.search('(%s)(%s)年'%('|'.join(RE),N),e)
    if m: return RE[m.group(1)][0]+num(m.group(2))-1
    m=re.search('(%s)間'%'|'.join(RE),e)
    if m: return list(RE[m.group(1)])
    if re.match('清',e): return [1644,1911]
    if re.match('明',e): return [1368,1644]
    return None
def etype(e):
    for k,v in [('影印','影印本'),('鉛印','鉛印本'),('铅印','鉛印本'),('石印','石印本'),('活字','活字本'),('謄寫','油印本'),('抄','抄本'),('鈔','抄本'),('寫本','抄本'),('刻','刻本')]:
        if k in e: return v
    return None
h=json.load(open(S+'/hits.json'))
o=[x for x in h if x['key'][0]=='other' and x['key'][1]=='multi']
C=collections.Counter(); log=[]
for x in o:
    d=json.load(open(x['f']))
    segs=[s for s in d['edition'].split(';') if s]
    bad=[s for s in segs if PR.search(s)]; good=[s for s in segs if not PR.search(s)]
    old={k:d.get(k) for k in ('edition','publication_info','dating','edition_type','ai_note')}
    d['edition']=';'.join(good)
    pi=d.get('publication_info')
    if pi and PR.search(pi.get('details','')):
        parts=[p for p in re.split('[；;]',pi['details']) if p and not PR.search(p)]
        if parts: pi['details']='；'.join(parts)
        else:
            pi.pop('details')
        if not pi: d.pop('publication_info'); C['pi-del']+=1
        else: C['pi-trim']+=1
    dt=d.get('dating')
    if dt and dt.get('source')=='catalog':
        lo=dt.get('year', (dt.get('year_range') or [None])[0])
        early=re.match('(宋|元|唐|隋|五代)',d['edition'])
        if lo is not None and lo<1370 and not early:
            p=parse(d['edition'])
            nd={'certainty':'inferred','source':'catalog','basis':'版本項年號推得（2026-11-13 L0 去除誤拼的藏經刻印項後重算）'}
            if isinstance(p,int): nd={'year':p,**nd}; d['dating']=nd; C['dating-year']+=1
            elif p: nd={'year_range':p,**nd}; d['dating']=nd; C['dating-range']+=1
            else: d.pop('dating'); C['dating-del']+=1
    et=etype(d['edition'])
    if et and d.get('edition_type')!=et: d['edition_type']=et; C['et']+=1
    note=d.get('ai_note') or ''
    note=re.sub(r'後印／補刻："[^"]*"\s*','',note).strip()
    note=(note+'\n' if note else '')+'2026-11-13 L0：版本項原誤拼藏經刻印「%s」（與本書無關，總目錄入時串入），已刪；出版者、年代、版本類型隨之改正。'%'；'.join(bad)
    d['ai_note']=note
    d['revision']='%d.0.0'%(int(str(d.get('revision') or '1.0.0').split('.')[0])+1); d['revised_at']='2026-11-13'
    C['n']+=1
    log.append({'id':d['id'],'old':old,'new':{k:d.get(k) for k in old}})
    if APPLY: open(x['f'],'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(C)
json.dump(log,open(S+'/fixlog.json','w'),ensure_ascii=False,indent=0)
