import pickle,re,collections,sys,json
sys.path.insert(0,'/home/user/ai-team/domain/专名/工具/异体折叠')
from fold import fold
ent=pickle.load(open('/tmp/ppl.pkl','rb')); W=pickle.load(open('/tmp/works.pkl','rb'))
live={i:d for i,d in ent.items() if not d.get('merged_into')}
sfx={i[-6:]:i for i in ent}
PRE=re.compile(r'^(釋|释|僧|沙門)')
def core(n): return fold(PRE.sub('',n))
def alts(d): return [a['name'] for a in d.get('alt_names') or [] if isinstance(a,dict)]
ANC=('春秋','戰國','先秦','上古')
def dy(d):
    x=d.get('dynasty')
    if not x: return None
    for k in ('宋','唐','明','清','元','晉','隋','魏','漢','梁','陳','齊','周','金','遼','秦'):
        if x.startswith(k) or x.endswith(k): return k
    return x
def cbdb(d): return (d.get('external_ids') or {}).get('cbdb_id')
def ok(a,b):
    da,db=dy(a),dy(b)
    if da and db and da!=db: return False
    ca,cb=cbdb(a),cbdb(b)
    if ca and cb and ca!=cb: return False
    A,B=a.get('dates') or {},b.get('dates') or {}
    for k in('birth','death'):
        if A.get(k) and B.get(k) and abs(A[k]-B[k])>3: return False
    return True
res=pickle.load(open('/tmp/mres.pkl','rb'))
pairs=[];defer=[]
DEFER_IDS={'5ywvjj','5xcoso','rw4xtc','h9bgof','h9bnv0'}   # 元宏/元弘、景隆
for m,j,c,o in res['prim']:
    a,b=live[m],live[j]
    if not o: defer.append((m,j,'朝代/CBDB/生卒冲突')); continue
    if m[-6:] in DEFER_IDS or j[-6:] in DEFER_IDS: defer.append((m,j,'异字或多人同名，存疑')); continue
    if any((x.get('dynasty') or '').startswith(ANC) for x in (a,b)): defer.append((m,j,'古代人物同名')); continue
    pa,pb=bool(PRE.match(a['primary_name'])),bool(PRE.match(b['primary_name']))
    da,db=dy(a),dy(b)
    if da and db: pairs.append((m,j,'同名(去釋/僧/沙門前缀)＋同代')); continue
    if pa and pb: pairs.append((m,j,'釋/僧/沙門前缀异写，朝代一侧缺')); continue
    defer.append((m,j,'一侧朝代缺且另一侧无僧前缀'))
cur=[('b88rzi','h9bu0q','靈徹/靈澈异写，僧'),('h9boya','h9bo40','慧能/惠能异写'),
 ('h9btzb','h9bf8q','釋玄惲：釋道世字玄惲'),('h9blm9','h9bf8q','僧玄憚：釋道世字玄惲之异写'),
 ('h9bq38','h9btx5','寒山子/寒山'),('h9bjym','h9bu0v','齊已為齊己訛名'),('dcdfk3','h9bhv5','支道林＝支遁'),
 ('h9bn0m','h9bmlv','釋無盡＝傳燈別稱'),('h9bv21','h9btzo','遍照金剛＝空海'),('whzuvx','h9bd7u','釋南潛＝董說'),
 # 女性
 ('h9bj33','','rename'),]
for a,b,w in cur:
    if b: pairs.append((sfx[a],sfx[b],w))
# 閨秀
for s,t in [('h9bj34','unrksj'),('h9bj92','h9bryt'),('h9bj2b','h9bdjf'),('h9bjeh','h9bdj8'),('h9bjef','up0iyr'),('h9bjdb','8gbgkh')]:
    pairs.append((sfx[s],sfx[t],'閨秀前缀为著录标注，本名条同代'))
# 妻/室
fem=[('郝懿行妻王照圓','h9bhwl'),('郝懿行室王照圓','h9bhwl'),('陳之遴室徐燦','徐燦清4'),('高其倬室蔡琬','蔡琬'),('許宗彥室梁德繩','梁德繩'),('孫原湘室席佩蘭','席佩蘭'),('陳裴之室汪端','8gbgkh')]
idx=collections.defaultdict(list)
for i,d in live.items(): idx[d['primary_name']].append(i)
def one(n,dyn='清'):
    c=[i for i in idx[n] if live[i].get('dynasty')==dyn]; assert len(c)>=1,n
    return c
for ln,kn in fem:
    l=idx[ln][0]
    if kn.startswith('h9bhwl') or kn=='8gbgkh': k=sfx[kn] if kn in sfx else None
    elif kn=='徐燦清4': k=[i for i in idx['徐燦'] if live[i].get('dynasty')=='清' and len(W.get(i,[]))==4][0]
    else:
        k=one(kn)[0]
    pairs.append((l,k,'「某妻／某室＋本名」与本名条同人，同为清人，夫姓前缀作別名'))
# union
par={}
def f(x):
    while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
    return x
why={}
for a,b,w in pairs:
    par[f(a)]=f(b); why[(a,b)]=w
cl=collections.defaultdict(set)
for a,b,w in pairs: cl[f(a)].update([a,b])
out=[]
for r,mem in cl.items():
    mem=sorted(mem)
    bad=[(x,y) for x in mem for y in mem if x<y and not ok(live[x],live[y]) and live[x].get('dynasty') and live[y].get('dynasty')]
    out.append((mem,bad))
print('clusters',len(out),'with conflicts',sum(1 for m,b in out if b))
for m,b in out:
    if b: print([live[x]['primary_name'] for x in m],b[:2])
pickle.dump((pairs,why,out,defer),open('/tmp/w/plan.pkl','wb'))
print(len(pairs),len(defer))
