#!/usr/bin/env python3
"""方志同题判定（研-方志，只读）

    BOOK_INDEX=. python3 .claude/qa/dedup-fangzhi/fangzhi_judge.py <普查 --out 目录>/同题组.tsv <输出目录>

取 dedup-census.py 同题组.tsv 中「未判」且题名键以「志」结尾的组，逐条读 Work，抽修次特征
（修次年号：题名／总目著录题的 [年号]、千頃堂式「某某間修」；版本年：故宫等无 indexed_by 记录
描述里的刊年；修纂人：authors＋author_info 拆名；卷数；史志书目的断代上限），两两判定：

  A 同修次·同人      修纂人相同（或三字名差一字／名互含），年号相同或相容，卷数不矛盾 → 并（证据并，逐条核）
  B 同修次·同年同卷  修次年号相同、年份相距 ≤2、卷数相同，但修纂人未对上 → 并前须逐条核
  C 异修次          修次年号不同／同号年份相距 >3／书目断代（千頃堂等明代书目 vs 清修）／
                    无同人且卷数不同 → 分立，不并
  E 续修增修        修纂人相同但修次年号不同（原纂＋续修、同人再修）→ 分立，待用户定是否互链
  D 存疑            以上都不足 → 不并，登记待核
  X 非方志          组内多数成员分类不在方志／地理，交其他单元（叢書子目、同题异书）

口径见 ai-team 去重方案目录「研-方志-判定口径.md」。只读，不改任何文件。启动打印载入条数，为 0 报错。
"""
import collections, glob, itertools, json, os, re, sys

# ---- 年号 ----
R={'紹興':(1131,32),'隆興':(1163,2),'乾道':(1165,9),'淳熙':(1174,16),'紹熙':(1190,5),'慶元':(1195,6),'嘉泰':(1201,4),'開禧':(1205,3),'嘉定':(1208,17),'寶慶':(1225,3),'紹定':(1228,6),'端平':(1234,3),'嘉熙':(1237,4),'淳祐':(1241,12),'寶祐':(1253,6),'開慶':(1259,1),'景定':(1260,5),'咸淳':(1265,10),
'大德':(1297,11),'皇慶':(1312,2),'延祐':(1314,7),'至治':(1321,3),'泰定':(1324,5),'天曆':(1328,2),'至順':(1330,4),'元統':(1333,2),'至正':(1341,28),
'洪武':(1368,31),'建文':(1399,4),'永樂':(1403,22),'洪熙':(1425,1),'宣德':(1426,10),'正統':(1436,14),'景泰':(1450,8),'天順':(1457,8),'成化':(1465,23),'弘治':(1488,18),'正德':(1506,16),'嘉靖':(1522,45),'隆慶':(1567,6),'萬曆':(1573,48),'泰昌':(1620,1),'天啓':(1621,7),'崇禎':(1628,17),'弘光':(1645,1),'隆武':(1645,2),'永曆':(1647,16),
'順治':(1644,18),'康熙':(1662,61),'雍正':(1723,13),'乾隆':(1736,60),'嘉慶':(1796,25),'道光':(1821,30),'咸豐':(1851,11),'同治':(1862,13),'光緒':(1875,34),'宣統':(1909,3),'民國':(1912,38)}
ALIAS={'萬厯':'萬曆','万历':'萬曆','萬歷':'萬曆','天啟':'天啓','崇正':'崇禎','民摑':'民國','宏治':'弘治','乾嘉':None}
GZ_T='甲乙丙丁戊己庚辛壬癸'; GZ_D='子丑寅卯辰巳午未申酉戌亥'
CN={'〇':0,'零':0,'一':1,'二':2,'兩':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def cn2i(s):
    if s=='元': return 1
    if s.isdigit(): return int(s)
    tot=0;cur=0
    for ch in s:
        if ch in CN: cur=CN[ch]
        elif ch=='十': tot+=(cur or 1)*10;cur=0
        else: return None
    return tot+cur
names='|'.join(sorted(list(R)+[k for k in ALIAS if ALIAS[k]],key=len,reverse=True))
PAT=re.compile(r'('+names+r')(?:(元|[〇零一二兩三四五六七八九十]+)年|([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]))?')
def era_of(text):
    """返回 (年号, 年 or None)"""
    if not text: return None
    m=PAT.search(text)
    if not m: return None
    r=ALIAS.get(m.group(1),m.group(1)); st,span=R[r]; y=None
    if m.group(2):
        n=cn2i(m.group(2))
        if n and n<=span+1: y=st+n-1
    elif m.group(3):
        idx=None
        for k in range(60):
            if GZ_T[k%10]+GZ_D[k%12]==m.group(3): idx=k
        for yy in range(st,st+span+1):
            if (yy-4)%60==idx: y=yy;break
    return (r,y)

# ---- 抽取 ----
JR = re.compile(r'([〇零一二兩三四五六七八九十百千\d]+)卷')
def cn2i_big(s):
    if s.isdigit(): return int(s)
    tot = cur = 0
    for ch in s:
        if ch in CN: cur = CN[ch]
        elif ch == '十': tot += (cur or 1) * 10; cur = 0
        elif ch == '百': tot += (cur or 1) * 100; cur = 0
        elif ch == '千': tot += (cur or 1) * 1000; cur = 0
        else: return None
    return tot + cur
BR = re.compile(r'^《?\s*[\[［〔(（]([^\]］〕)）]*)[\]］〕)）]')

def load(bi, tsv):
    groups = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8')]
    groups = [p for p in groups if len(p) >= 6 and p[2] == '未判' and p[3].endswith('志')]
    books = collections.defaultdict(list)
    for f in glob.glob(os.path.join(bi, 'index/books/*.json')):
        for v in json.load(open(f, encoding='utf-8')).values():
            if v.get('work_id'): books[v['work_id']].append(v)
    W = []
    for p in groups:
        for i in p[5].split(','):
            fs = glob.glob(os.path.join(bi, f"Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}*.json"))
            d = json.load(open(fs[0], encoding='utf-8'))
            t = d['title']; m = BR.match(t)
            ib = d.get('indexed_by', [])
            tinfos = [x.get('title_info', '') for x in ib]
            jc = None
            for ti in tinfos + [d.get('measure_info') or '']:
                mm = JR.search(ti.replace(t, ''))
                if mm: jc = cn2i_big(mm.group(1)); break
            if jc is None and isinstance(d.get('juan_count'), dict): jc = d['juan_count'].get('number')
            bk = books.get(i, [])
            w = dict(group=p[3], bulei=p[0], cat=p[1], id=i, title=t, era=m.group(1) if m else '', juan=jc,
                     authors=[(a.get('name'), a.get('role'), a.get('dynasty')) for a in d.get('authors', [])],
                     dynasty=d.get('dynasty'), sources=[x.get('source') for x in ib],
                     sections=[x.get('section') for x in ib if x.get('section')],
                     tinfo=tinfos, ainfo=[x.get('author_info', '') for x in ib],
                     summ=[(x.get('summary') or '')[:300] for x in ib],
                     desc=((d.get('description') or {}).get('text') or '')[:300],
                     beds=[(b.get('edition'), b.get('sort_year'), b.get('holder')) for b in bk][:8],
                     path=os.path.relpath(fs[0], bi))
            cands = [('题名', w['era'])] + [('著录题', (BR.match(x).group(1) if BR.match(x) else '')) for x in tinfos]
            cands += [('责任', a) for a in w['ainfo']] + [('版本', s) for s in w['summ']] + [('描述', w['desc'])]
            cands += [('Book', ' '.join(str(b[0]) for b in w['beds']))]
            e = None; how = ''
            for how_, tx in cands:
                e = era_of(tx)
                if e: how = how_; break
            w['reign'] = e[0] if e else None; w['year'] = e[1] if e else None; w['era_how'] = how
            if e and not e[1]:
                for _, tx in cands:
                    ee = era_of(tx)
                    if ee and ee[0] == e[0] and ee[1]: w['year'] = ee[1]; break
            W.append(w)
    return groups, W

# ---- 修纂人、方志判别 ----
DYN_OF={}
for k,(st,_) in R.items(): DYN_OF[k]='宋' if st<1280 else '元' if st<1368 else '明' if st<1644 and k not in('順治',) else '清'
DYN_OF['民國']='民國'; DYN_OF['順治']='清'
for k in ('弘光','隆武','永曆'): DYN_OF[k]='明'
ROLE=re.compile(r'(等)?(重修|增修|續修|纂修|修纂|編纂|總纂|分纂|監修|主修|同修|纂輯|編輯|修|纂|撰|輯|編|訂|校|著|述|錄|鑒定|參閱|序)$')
DYNP=re.compile(r'^(宋|元|明|清|民國|後周|唐|金)')
def names(w):
    s={a[0] for a in w['authors'] if a[0] and a[0] not in('佚名',)}
    for ai in w['ainfo']:
        for part in re.split(r'[;；,，、]',ai or ''):
            part=part.strip(); part=DYNP.sub('',part); part=ROLE.sub('',part).strip()
            if 2<=len(part)<=4 and not re.search(r'[間年修]',part): s.add(part)
    # 史志合条：「某志X卷。某某修。」
    for sm in w['summ']:
        for m in re.finditer(re.escape(w['group'])+r'[^。]{0,12}卷。([^。；，]{2,4}?)(?:等)?(?:修|撰|纂|纂修)。',sm):
            s.add(m.group(1))
    return s
FZSEC=('方志','地理','山水志','專志','郡邑')
FZT=re.compile(r'(縣|州|府|廳|衛|所|鎮|鄉|里|村|通|郡|邑|城|關|山|寺|書院|湖|江|河)(續|新|小|備|鄉土|合|總|全)?志$')
def isfz(w): return any(any(k in s for k in FZSEC) for s in w['sections']) or bool(FZT.search(w['group']))

# ---- 两两判定 ----
def kind(w):
    if not w['sources']: return 'G'
    if '中國古籍總目' in w['sources']: return 'Z'
    return 'B'
def xiuci(w):
    """修次年号：只认题名／总目著录题里的 [年号]，及千頃堂式『某某間修』；其余（版本年、描述年）记为版本年"""
    if w['era_how'] in ('题名','著录题'): return ('修',w['reign'],w['year'])
    if w['era_how']=='责任' and kind(w)!='G' and re.search(r'修',' '.join(w['ainfo'])): return ('修',w['reign'],w['year'])
    if w['era_how'] in ('描述','版本','Book') and kind(w)=='G': return ('版',w['reign'],w['year'])
    if w['era_how']=='版本' and kind(w)=='Z': return ('版',w['reign'],w['year'])
    return (None,None,None)
ORD={'宋':0,'元':1,'明':2,'清':3,'民國':4}
CAP={'千頃堂書目':'明','明史藝文志':'明','國史經籍志':'明','宋史藝文志':'宋','直齋書錄解題':'宋','崇文總目':'宋','新唐書藝文志':'宋','舊唐書經籍志':'宋','隋書經籍志':'宋','元史藝文志':'元','補遼金元藝文志':'元','清史稿藝文志':'清','欽定四庫全書總目':'清','四庫全書存目叢書':'清'}
def cap(w):
    if 'G'==kind(w) or '中國古籍總目' in w['sources']: return None
    cs=[ORD[CAP[s]] for s in w['sources'] if s in CAP]
    return min(cs) if cs else None
def lower(w):
    x=xiuci(w)
    if x[0]=='修' and x[1]: return ORD.get(DYN_OF.get(x[1]))
    return None
def ystart(r): return R[r][0] if r in R else None
def fuzzy(sa,sb):
    for x in sa:
        for y in sb:
            if x==y: return 'eq'
    for x in sa:
        for y in sb:
            if len(x)==len(y)>=3 and sum(c1!=c2 for c1,c2 in zip(x,y))==1: return 'near'
            if len(x)>=2 and len(y)>=2 and (x in y or y in x) and abs(len(x)-len(y))==1: return 'near'
    return None
def judge(a,b):
    sa,sb=names(a),names(b); sh=fuzzy(sa,sb)
    ja,jb=a['juan'],b['juan']; jeq= ja is not None and ja==jb; jconf= ja is not None and jb is not None and ja!=jb
    xa,xb=xiuci(a),xiuci(b)
    # 修次标记对比
    both_xiu= xa[0]=='修' and xb[0]=='修'
    if both_xiu:
        if xa[1]!=xb[1]: era='异'
        elif xa[2] and xb[2] and abs(xa[2]-xb[2])>3: era='同号远年'
        else: era='同'
    elif xa[1] and xb[1]:
        # 一侧是版本年：版本年不早于修次年即相容
        (p,q)=(xa,xb) if xa[0]=='修' else (xb,xa)
        if p[0]=='修':
            yp=p[2] or ystart(p[1]); yq=q[2] or ystart(q[1])
            era='同' if p[1]==q[1] else ('容' if yq and yp and yq>=yp else '异')
        else:
            era='同' if xa[1]==xb[1] else '版异'
    else: era='缺'
    J='同卷' if jeq else '异卷' if jconf else '缺卷'
    ca,cb=cap(a),cap(b); la,lb=lower(a),lower(b)
    if not sh and ((ca is not None and lb is not None and lb>ca) or (cb is not None and la is not None and la>cb)):
        return 'C异修次·书目断代'
    if sh == 'near' and xa[2] and xb[2] and abs(xa[2] - xb[2]) > 3:
        return 'D存疑·近形名远年'
    if sh:
        if era in('同','容','缺','版异') and not jconf: return 'A同修次·同人'+('' if sh=='eq' else '(近形)')+'·'+J+'·年号'+era
        if era in('异','同号远年'): return 'E续修重修·同人·'+J+'·年号'+era
        return 'D存疑·同人异卷·年号'+era
    if era=='同' and not jconf:
        ya=xa[2]; yb=xb[2]
        if jeq and (not ya or not yb or abs(ya-yb)<=2): return 'B同修次·同年号同卷·无同名'
        return 'D存疑·同年号·'+J
    if era in('异','同号远年'): return 'C异修次·'+J
    if era=='同' and jconf:
        if xa[2] and xb[2] and abs(xa[2]-xb[2])<=2: return 'D存疑·同年近年异卷'
        return 'C异修次·同年号异卷'
    if jconf: return 'C异修次·无同人异卷·年号'+era
    def rdyn(w,x):
        if x[0]=='修': return DYN_OF.get(x[1])
        return w['dynasty'] or (w['authors'][0][2] if w['authors'] and w['authors'][0][2] else None)
    da=rdyn(a,xa); db=rdyn(b,xb)
    if da and db and da!=db and era!='容' and not jeq: return 'C异修次·朝代异'
    return 'D存疑·'+J+'·年号'+era
def brief(w):
    return '%s《%s》%s%s 卷%s %s 源%s' % (w['id'], w['title'], w['reign'] or '', w['year'] or '', w['juan'],
        '、'.join((a[0] or '') + (a[1] or '') for a in w['authors'][:3]), '/'.join(dict.fromkeys(w['sources'])) or '无indexed_by')

def main(argv):
    bi = os.environ.get('BOOK_INDEX', '.')
    tsv, out = argv[1], argv[2]
    os.makedirs(out, exist_ok=True)
    groups, W = load(bi, tsv)
    print('载入：方志同题未判组 %d，Work %d' % (len(groups), len(W)))
    if not groups or not W: sys.exit('载入为 0，停')
    G = collections.defaultdict(list)
    for w in W: G[w['group']].append(w)
    rows = []; gsum = {}
    for g, ms in G.items():
        fz = sum(isfz(w) for w in ms); nonfz = sum(1 for w in ms if w['sections'] and not isfz(w))
        labs = set()
        for a, b in itertools.combinations(ms, 2):
            l = 'X非方志' if nonfz > fz else judge(a, b)
            labs.add(l[0]); rows.append((g, a, b, l))
        gsum[g] = ''.join(sorted(labs))
    hdr = '题名键\tWork甲\tWork乙\t判定\t甲\t乙\n'
    with open(os.path.join(out, '判定-全部对.tsv'), 'w', encoding='utf-8') as f:
        f.write(hdr)
        for g, a, b, l in rows: f.write('\t'.join([g, a['id'], b['id'], l, brief(a), brief(b)]) + '\n')
    for k, name in (('A', '候选A-同修次同人.tsv'), ('B', '候选B-同年同卷待核.tsv'), ('E', '续修增修E.tsv'), ('D', '存疑D.tsv')):
        with open(os.path.join(out, name), 'w', encoding='utf-8') as f:
            f.write(hdr)
            for g, a, b, l in rows:
                if l[0] == k: f.write('\t'.join([g, a['id'], b['id'], l, brief(a), brief(b)]) + '\n')
    with open(os.path.join(out, '非方志X-组.tsv'), 'w', encoding='utf-8') as f:
        f.write('题名键\t条数\tids\n')
        for g, v in gsum.items():
            if v == 'X': f.write('%s\t%d\t%s\n' % (g, len(G[g]), ','.join(w['id'] for w in G[g])))
    # 纯 C 组：组内每对都判异修次，可整组登记分立（写 dedup-judged 用）
    with open(os.path.join(out, '纯C组-分立对.tsv'), 'w', encoding='utf-8') as f:
        f.write('# 研-方志：组内两两皆判异修次（C），分立不并；列：Work甲 Work乙 判定 理由\n')
        for g, a, b, l in rows:
            if gsum[g] == 'C':
                f.write('\t'.join([a['id'], b['id'], 'C分立', '%s：《%s》%s／《%s》%s' % (l, a['title'], a['reign'] or '', b['title'], b['reign'] or '')]) + '\n')
    pc = collections.Counter(l for *_, l in rows); tc = collections.Counter(l[0] for *_, l in rows)
    gc = collections.Counter(gsum.values())
    # 并 A、B 后的组况
    after = collections.Counter()
    for g, ms in G.items():
        if gsum[g] == 'X': after['X'] += 1; continue
        par = {w['id']: w['id'] for w in ms}
        def f(x):
            while par[x] != x: x = par[x]
            return x
        grows = [r for r in rows if r[0] == g]
        for _, a, b, l in grows:
            if l[0] in 'AB': par[f(a['id'])] = f(b['id'])
        rest = {l[0] for _, a, b, l in grows if f(a['id']) != f(b['id'])}
        after['合并后组内只剩一条' if not rest else ('合并后余对全 C' if rest == {'C'} else '合并后仍有 ' + ''.join(sorted(rest - {'C'})))] += 1
    rep = dict(组=len(G), Work=len(W), 对=len(rows), 按类=dict(tc), 细类=dict(pc), 组类型=dict(gc.most_common()), 并AB后=dict(after))
    json.dump(rep, open(os.path.join(out, '统计.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(sys.argv)
