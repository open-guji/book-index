"""新-子目异名-子：含叢書子目、丛书异名或对单行本的同题组逐对初判。
输入：$OUT/feat.json（dedup-subitem-yi/feat.py 产出）。输出 $OUT/pairs_zi.tsv、$OUT/clusters.json。
判据：子目-乙（有效撰人含獨撰类继承丛书撰人；卷数串）＋4a-α（獨撰子目→同撰人单行本）＋总目互见（单书著录版本列出该丛书本）。"""
import json, os, re, sys, glob, csv, itertools, collections
S=os.environ.get('OUT','/tmp/zi'); ROOT=os.environ.get('BOOK_INDEX','.')
HERE=os.path.dirname(os.path.abspath(__file__))
sys.argv=[sys.argv[0]]
exec(open(os.path.join(HERE,'..','dedup-subitem-yi','sig.py')).read().split('out=[]\nfor gi')[0])
idx={os.path.basename(p)[:12]:p for p in glob.glob(ROOT+'/Work/*/*/*/*.json')}
def full(i): return json.load(open(idx[i]))
# 子目-乙 判定表里的对归子目-乙-并（在跑），本单元跳过
YI=set()
for r in csv.DictReader(open(os.path.join(HERE,'..','dedup-subitem-yi','judged-07fc66fc.tsv')),delimiter='\t'):
    YI.add(frozenset((r['Work甲'],r['Work乙'])))
GENERIC=set('詞 札記 雜志 雜誌 雜箸 藝文 水利 荒政 選舉 試帖 遊記 詞稿 對策 備忘 内篇 函稿 校勘記 詩訣 詩筏'.split())
DUNHUANG=['鳴沙石室','敦煌','西陲祕籍']
GEN=GENERIC|set('文集 續集 雜著 詩集 文稿 詩稿 集 外集 別集 遺集 遺稿 文鈔 詩鈔 年譜 筆記 隨筆 日記 家訓 雜記 雜說 說 叢談 雜錄 語錄 書目 題跋 尺牘 奏議 詩話 詞話 圖說 圖 序 記 銘 贊 頌 論 表 疏'.split())
DEL=set('：；，。、（）() 　\n印刻鈔抄排')
def vnames(sm):
    return sm.translate(VARIANTS)
def lists_col(a, b):
    """a 的非叢書部著录 summary 是否列出 b 所在丛书本：取丛书题名最长前缀 P（≥2 字）使 summary 出现「P本」且前一字为分隔"""
    T=(b['col'] or '').translate(VARIANTS)
    if len(T)<2: return None
    for ib in a['ibfull']:
        if (ib.get('section') or '').startswith('叢書部'): continue
        sm=vnames(ib.get('summary') or '')
        for L in range(len(T),1,-1):
            P=T[:L]+'本'; k=sm.find(P)
            while k>=0:
                if (k==0 or sm[k-1] in DEL) and not re.match(r'[續补補外再後后]', T[L:]): return T[:L]
                k=sm.find(P,k+1)
    return None
NUMC='一二三四五六七八九十百千〇□'
def ccore(T):
    T=(T or '').translate(VARIANTS)
    T=re.sub(r'[（(].*$','',T)
    T=re.sub('['+NUMC+']+[種卷𢎥集冊函編輯].*$','',T)
    return T.strip()
FAMS=[['說郛','唐宋叢書','說集'],['寶顏堂祕笈','寶顏堂秘笈','尚白齋鐫陳眉公寶顏堂秘笈','尚白齋鐫陳眉公寶顏堂祕笈','陳眉公家藏秘笈','尚白齋鐫陳眉公家藏秘笈續函'],
      ['平津館叢書','新斠平津館叢書'],['夷門廣牘','景印元明善本叢書'],['文淵閣四庫全書','摛藻堂四庫全書薈要','欽定四庫全書薈要'],
      ['海寧王忠慤公遺書','海寧王靜安先生遺書'],['格致叢書','百家名書','壽養叢書','胡氏粹編'],['微波榭叢書','微波榭遺書','戴氏遺書'],['函海','續函海'],
      ['麗廔叢書','郋園先生全書','雙楳景闇叢書','觀古堂彙刻書'],['海虞雜志','虞陽說苑','虞陽說彙','素心書屋叢鈔','沈氏家藏秘笈'],['六譯館叢書','重訂六譯館叢書','新訂六譯館叢書']]
def fam(c):
    c=ccore(c)
    if not c: return None
    for k,ks in enumerate(FAMS):
        if any(c.startswith(x.translate(VARIANTS)) for x in ks): return 'F%d'%k
    return 'T:'+c
BIDX={}
for p_ in glob.glob(ROOT+'/index/books/*.json'):
    for bid,b in json.load(open(p_)).items():
        if b.get('work_id'): BIDX.setdefault(b['work_id'],[]).append(b['path'])
CT={}
for p_ in glob.glob(ROOT+'/Collection/*/*/*/*.json'):
    c_=json.load(open(p_)); CT[c_['id']]=c_.get('title') or ''
def bookcols(i):
    out=set()
    for bp in BIDX.get(i,[]):
        try: b=json.load(open(ROOT+'/'+bp))
        except Exception: continue
        for ci in b.get('contained_in') or []:
            t=CT.get(ci.get('id') if isinstance(ci,dict) else ci)
            if t: out.add(ccore(t))
        e=(b.get('edition') or '').translate(VARIANTS)
        if e.endswith('本'): out.add(e[:-1])
    return out
def book_hit(a,b):
    """a 已有 Book 收在与 b 同名的叢書（或版本名为「该叢書本」）"""
    k=ccore(b['col'])
    if len(k)<2: return None
    for x in a['bcols']:
        if x==k: return k
        if len(x)>=3 and len(k)>=3:
            lo,hi=(x,k) if len(x)<=len(k) else (k,x)
            if hi.startswith(lo) and not re.match(r'[續补補外再後后]', hi[len(lo):]): return k
    return None
def jset(w):
    s=set()
    for rest,n in juan_of(w):
        if n is not None: s.add(1 if n=='不分卷' else n)
    return s
ws={}
feat_=json.load(open(S+'/feat.json'))
for g in feat_:
    for w in g['works']:
        f=full(w['id']); w['ibfull']=f.get('indexed_by') or []
        w['merged']=bool(f.get('merged_into'))
        w['sub']=bool(w['colrec'])
        w['dh']=any(k in (w['col'] or '')+(f.get('ai_note') or '') for k in DUNHUANG)
        w['bcols']=bookcols(w['id']) if not w['colrec'] else {x for x in bookcols(w['id']) if x!=ccore(w['col'])}
        ns,dy,src=names_of(w); ns={x for x in ns if x not in ('佚名','不','存疑','闕名','無名氏')}; w['ns']=ns; w['dy']=dy; w['src']=src; w['js']=jset(w)
NONZ=re.compile(r'輯|注|註|校|編|評|選|訂|補|譯|集|纂|鈔|抄|解|疏|箋|批|點|錄|述|傳本|釋|音義|考')
def pure(w):
    """责任方式全为撰／著（无辑注校编等），撰人不同才可判分立"""
    for a in w['authors']:
        if a[1] and NONZ.search(a[1]): return False
    for ti,ai,sec,sm in w['ib']:
        if ai and NONZ.search(ai): return False
    if w['src']=='col': return False
    return True
def dyn_ok(a,b):
    if not a['dy'] or not b['dy']: return True
    return bool(set(a['dy'])&set(b['dy'])) or any(x in y or y in x for x in a['dy'] for y in b['dy'])
def jrel(a,b):
    if not a['js'] or not b['js']: return '缺'
    if a['js']&b['js']: return '同'
    return '矛盾'
# 人读：著录混了多部书或层次不明的 Work，本单元不并
MIX={'d59fy10fz3ls':'著录混鬻子與公孫龍子等多書','d59f27v1ri0x':'著录混多部龜經','d59fy1x6n6rk':'著录混國老談苑等多書',
     'd59f24m60jk1':'王仁俊輯本對唐宋叢書本，輯本層次不明','d59fy11fve2o':'文房圖贊與續、十友圖贊合著錄','d59fy110w000':'小兒語與續小兒語合著錄',
     'd59fy121erk0':'聲律發蒙增補本，層次不明','d59f2puvkdmq':'周髀與周髀算經音義層次不明','d59f990cos96':'周髀與周髀算經音義層次不明','d59fy03e2ebl':'撰人李聯琇／劉壽曾歸屬不明'}
rows=[]; edges=[]
for gi,g in enumerate(feat_):
    gen = g['key'] in GEN or len(g['key'])<=1
    for a,b in itertools.combinations(g['works'],2):
        if a['merged'] or b['merged']: continue
        if frozenset((a['id'],b['id'])) in YI: lv,why='YI','子目-乙判定表已有（子目-乙-并在跑）'
        elif a['dh'] or b['dh']: lv,why='D','敦煌遗书不碰'
        elif a['id'] in MIX or b['id'] in MIX: lv,why='D',MIX.get(a['id']) or MIX.get(b['id'])
        else:
            jr=jrel(a,b); hx=lists_col(a,b) or lists_col(b,a)
            na,nb=set(a['ns']),set(b['ns'])
            if na and nb:
                if na==nb or (na&nb and (na<=nb or nb<=na)):
                    if not dyn_ok(a,b): lv,why='C','撰人同名而朝代不合'
                    elif jr=='矛盾': lv,why='D','同撰人（%s）卷数不合'%'/'.join(sorted(na&nb))
                    elif na!=nb: lv,why='B','撰人一侧多出別號或注校者（%s / %s），人读核为同书'%('/'.join(sorted(na)),'/'.join(sorted(nb)))
                    else:
                        src='（獨撰类继承丛书撰人）' if 'col' in (a['src'],b['src']) else ''
                        lv,why='A','同撰人%s%s；卷数%s%s'%('/'.join(sorted(na)),src,jr,'；总目互见「%s本」'%hx if hx else '')
                elif na&nb: lv,why='D','撰人部分相同而各有他人（%s / %s），注本／校本层次待核'%('/'.join(sorted(na)),'/'.join(sorted(nb)))
                elif {x[0] for x in na}&{x[0] for x in nb}: lv,why='D','撰人同姓异名（%s / %s），或为字號異寫，待核'%('/'.join(sorted(na)),'/'.join(sorted(nb)))
                elif not (pure(a) and pure(b)): lv,why='D','撰人不同但一侧为辑／注／校／编等责任，层次待核（%s / %s）'%('/'.join(sorted(na)),'/'.join(sorted(nb)))
                elif not dyn_ok(a,b): lv,why='C','撰人不同且朝代不同（%s / %s）'%('/'.join(sorted(na)),'/'.join(sorted(nb)))
                else: lv,why='C','撰人异姓（%s / %s）'%('/'.join(sorted(na)),'/'.join(sorted(nb)))
            else:
                if gen: lv,why='D','泛称题名，一侧或两侧缺撰人'
                elif hx and jr!='矛盾': lv,why='B','一侧缺撰人；总目单书著录列「%s本」，卷数%s'%(hx,jr)
                elif jr!='矛盾' and (book_hit(a,b) or book_hit(b,a)): lv,why='B','一侧缺撰人；单书 Work 已挂「%s」叢書本 Book，卷数%s'%(book_hit(a,b) or book_hit(b,a),jr)
                elif jr!='矛盾' and a['sub'] and b['sub'] and fam(a['col'])==fam(b['col']): lv,why='B','缺撰人；两叢書同名或同出一系（%s／%s），卷数%s'%(ccore(a['col']),ccore(b['col']),jr)
                elif jr=='矛盾': lv,why='D','缺撰人且卷数不合'
                else: lv,why='D','缺撰人、同题%s，无总目互见／同叢書 Book／同系叢書证据'%('同卷' if jr=='同' else '卷缺')
        rows.append(dict(g=gi,key=g['key'],a=a['id'],b=b['id'],lv=lv,why=why,cola=a['col'],colb=b['col'],
            na='/'.join(sorted(a['ns'])),nb='/'.join(sorted(b['ns'])),ja='|'.join(map(str,sorted(a['js']))),jb='|'.join(map(str,sorted(b['js'])))))
with open(S+'/pairs_zi.tsv','w') as f:
    cols=['g','key','a','b','lv','why','cola','colb','na','nb','ja','jb']
    f.write('\t'.join(cols)+'\n')
    for r in rows: f.write('\t'.join(str(r[c]) for c in cols)+'\n')
print(collections.Counter(r['lv'] for r in rows))
