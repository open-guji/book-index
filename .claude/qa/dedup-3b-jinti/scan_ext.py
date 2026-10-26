import json,collections,re,glob,os,sys,itertools,importlib.util
ROOT='.'
sys.path.insert(0,'.claude/qa')
spec=importlib.util.spec_from_file_location('dc','scripts/dedup-census.py'); dc=importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)
bul=dc.bulei_of_nodes(ROOT); mem=collections.defaultdict(set)
for p in glob.glob('classification/zongmu/members/*.json'):
    for row in dc.load_json(p).get('members') or []:
        if row: mem[row[0]].add(bul.get(os.path.basename(p)[:-5]))
def bl(w): return next((b for b in dc.BULEI if b in mem.get(w,())),'未分类')
judged=set()
for f in glob.glob('.claude/qa/dedup-judged/*.tsv')+['/tmp/claude-0/s/j.tsv','/tmp/claude-0/s2/j.tsv','.claude/qa/dedup-3a2yi/判定.tsv']:
    for l in open(f):
        x=l.split('\t')
        if len(x)>2 and not l.startswith('#'): judged.add(frozenset(x[:2]))
PRE=re.compile(r'^(新刊|新刻|新鐫|重刊|重刻|重訂|重校|重修|增補|增訂|增廣|校正|校刻|新校|新編|新鍥|御製|御纂|欽定|精刻|評點|批點|詳註|詳注|箋註|音註|京本|監本|古本)+')
SUF=re.compile(r'(全集|文集|詩集|集|稿|全書|彙編|合刻|合編|選|鈔|抄|錄)$')
DYN=re.compile(r'^(皇明|大明|明|宋|唐|元|漢|晉|魏|梁|陳|隋|金|遼|國朝|皇清|清)')
SER=re.compile(r'^(寶顏堂訂正|陳眉公訂正|眉公訂正|寶顏堂)')
out=[];c=collections.Counter()
for l in open('/tmp/claude-0/s2/scan.jsonl'):
    d=json.loads(l)
    if d['kind']!='近题': continue
    a,b=d['title'].split('｜')
    s,t=(a,b) if len(a)<len(b) else (b,a)
    i=t.find(s); pre=t[:i]; suf=t[i+len(s):]
    core=lambda x:PRE.sub('',x)
    if PRE.sub('',t)==s or PRE.sub('',s)==PRE.sub('',t): k='前缀'
    elif SUF.sub('',core(t))==SUF.sub('',core(s)): k='后缀'
    elif not suf and SER.fullmatch(pre): k='丛书刻名前缀'
    elif not suf and DYN.fullmatch(pre) and len(s)>=3: k='朝代前缀'
    elif not pre and suf in ('集','書'): k='后缀'+suf
    else: continue
    ids_s=[i for i in d['ids'] if dc.norm(W) if False] if False else None
    out.append((k,d['entity'],a,b,d['ids']))
json.dump(out,open('/tmp/claude-0/s2/ext_groups.json','w'),ensure_ascii=False)
print(collections.Counter(o[0] for o in out))
# expand
need={i for o in out for i in o[4]}
W={}
for p in glob.glob('Work/*/*/*/*.json'):
    i=os.path.basename(p)[:12]
    if i in need: W[i]=json.load(open(p))
pairs=[];cc=collections.Counter()
for k,e,a,b,ids in out:
    A=[i for i in ids if dc.norm(W[i].get('title') or '')==a]; B=[i for i in ids if dc.norm(W[i].get('title') or '')==b]
    for x,y in itertools.product(A,B):
        if W[x].get('merged_into') or W[y].get('merged_into'): cc['墓碑']+=1; continue
        if frozenset((x,y)) in judged: cc['已判']+=1; continue
        bb=min(bl(x),bl(y),key=lambda z:(dc.BULEI+('未分类',)).index(z))
        if k.startswith('后缀') and bb=='集部': cc['集部后缀归乙']+=1; continue
        if k=='后缀' and bb!='集部': pass
        t=W[x]['title']+W[y]['title']
        if '志' in t and ('[' in t or '縣' in t or '府' in t or '州' in t): cc['方志']+=1; continue
        pairs.append((bb,k,x,W[x]['title'],y,W[y]['title'],e)); cc[k]+=1
print(cc)
open('/tmp/claude-0/s2/new2.tsv','w').write(''.join('\t'.join(p)+'\n' for p in pairs))
