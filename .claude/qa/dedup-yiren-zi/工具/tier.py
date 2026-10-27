import json,sys,re,itertools,collections
sys.path.insert(0,'/home/user/book-index/.claude/qa')
from scan import VARIANTS
PUNCT = re.compile(r'[\s·・、，,。．.：:；;「」『』《》〈〉()（）〔〕【】\[\]]')
ANON = {'', '佚名', '闕名', '缺名', '無名氏', '不著撰人', '不著撰者', '不題撰人', '不詳', '撰者不詳', '□□'}
def nn(s): return PUNCT.sub('', (s or '').translate(VARIANTS)).strip('□') if s else ''
D=json.load(open('/tmp/claude-0/w/dossier.json'))
PH=re.compile(r'(氏|人|初|末|代|朝|某|子|居士|先生|道人|山人|太子|帝|宗|王|公|生|叟|翁|老|僧|師|館|局|會|社|院|堂|齋|軒|樓|閣|書屋|主人)$')
def names(e):
    s=set()
    for k in ('primary_name','alt_names','names','alternate_names','courtesy_name','art_name'):
        v=e.get(k)
        if isinstance(v,str): s.add(nn(v))
        elif isinstance(v,list):
            for x in v: s.add(nn(x if isinstance(x,str) else (x.get('name') if isinstance(x,dict) else '')))
    return s-{''}
auto,manual=[],[]
reasons=collections.Counter()
for gi,g in enumerate(D):
    ws=g['works']; g['gi']=gi
    fa=[(w.get('authors') or [{}])[0] for w in ws]
    why=[]
    if not all(a.get('eid') for a in fa): why.append('缺eid')
    if len({a.get('eid') for a in fa})<len(fa): why.append('同eid')
    ns=[nn(a.get('name')) for a in fa]
    for a,b in itertools.combinations(range(len(ws)),2):
        na,nb=ns[a],ns[b]
        if (len(na)==len(nb) and sum(x!=y for x,y in zip(na,nb))<=1) or (na and nb and (na in nb or nb in na)): why.append('近名'); break
    for i,j in itertools.permutations(range(len(ws)),2):
        if ns[i] and ns[i] in names(fa[j].get('ent') or {}): why.append('别名'); break
    for n in ns:
        if n and (len(n)<=1 or len(n)>=4 or PH.search(n)): why.append('疑号或占位'); break
    for w in ws:
        if '不詳' in json.dumps(w,ensure_ascii=False)[:0]: pass
    g['why']=why
    (manual if why else auto).append(g)
    for x in set(why): reasons[x]+=1
print(len(auto),len(manual),reasons)
json.dump(auto,open('/tmp/claude-0/w/auto.json','w'),ensure_ascii=False)
json.dump(manual,open('/tmp/claude-0/w/manual.json','w'),ensure_ascii=False)
