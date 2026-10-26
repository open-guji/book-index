import pickle,re,collections,glob,itertools,json
groups,info=pickle.load(open('feat.pkl','rb'))
J={}
for f in glob.glob('/home/user/book-index/.claude/qa/dedup-judged/*.tsv'):
    for l in open(f):
        if l.startswith('#'): continue
        p=l.rstrip('\n').split('\t')
        if len(p)>=2 and p[0].startswith('d') and p[1].startswith('d'):
            J[frozenset(p[:2])]=f.split('/')[-1]
DY=['先秦','周','秦','漢','三國','晉','南北朝','隋','唐','五代','宋','遼','金','元','明','清','民國']
def dyi(d):
    if not d: return None
    for i,x in enumerate(DY):
        if x in d: return i
    return None
def isfz(w): return any('方志' in s or '地理類/都會郡縣' in s for s in w['sec']) or bool(re.match(r'^[\[（(【]',w['t'] or '') and re.search(r'(志|乘|圖經|志略|志稿)$',w['ct']))
def ispu(w): return any('譜牒' in s or '家譜' in s or '族譜' in s for s in w['sec']) or bool(re.search(r'(族譜|家譜|宗譜|支譜|家乘|族志|世譜)',w['t'] or ''))
import opencc
cc=opencc.OpenCC('t2s')
NONE={'佚名','阙名','不著撰人','无名氏','不著撰者','缺名','不详'}
def an(w):
    out=set()
    for x in w['au']:
        n=cc.convert(re.sub(r'[\(（\[［].*?[\)）\]］]','',x[0] or '')); n=re.sub(r'^(释|僧)','',n)
        if n and n not in NONE: out.add(n)
        if x[3]: out.add(x[3])
    return out
def cls(a,b):
    if frozenset((a['id'],b['id'])) in J: return 'X已判',J[frozenset((a['id'],b['id']))]
    if b['id'] in a['rel'] or a['id'] in b['rel']: return 'X已互链',''
    if isfz(a) or isfz(b): return 'Z方志',''
    if ispu(a) or ispu(b): return 'Z谱',''
    T=bool(a['core']&b['core'])
    aa,ba=a['a1'],b['a1']
    if aa in NONE: aa=''
    if ba in NONE: ba=''
    if aa and ba:
        if aa==ba or (a['e1'] and a['e1']==b['e1']): A='同'
        elif aa in ba or ba in aa: A='含'
        elif (an(a)&an(b)): A='交'
        else: A='异'
    else: A='缺'
    ja,jb=[(x.get('number') or None) if isinstance(x,dict) else x for x in (a['juan'],b['juan'])]
    Jok= ja is None or jb is None or abs(ja-jb)<=1
    da,db=dyi(a['dyn']),dyi(b['dyn'])
    Dok= da is None or db is None or abs(da-db)<=1
    return ('T' if T else 't')+A+('' if Jok else '·卷异')+('' if Dok else '·代异'),''
pairs=[]
for k,g in groups.items():
    for x,y in itertools.combinations(g['ws'],2):
        c,why=cls(info[x],info[y]); pairs.append((k,x,y,c,why))
pickle.dump(pairs,open('pairs.pkl','wb'))
C=collections.Counter(p[3] for p in pairs)
for k,v in C.most_common(): print(v,k)
# groups count by best class
