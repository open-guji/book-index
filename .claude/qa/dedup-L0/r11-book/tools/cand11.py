import json,glob,collections,re,opencc,sys
S='/tmp/claude-0/-home-user/e59db2b9-8fd4-5ed9-a492-942f4a225576/scratchpad/r11'
sys.path.insert(0,S)
from meas import compat,norm
from shared_key import K
cc=opencc.OpenCC('t2s')
g0=json.load(open(S+'/groups2.json'))
cnt=json.load(open(S+'/provcnt.json'))
def indep(cid,b):
    ps=[K(p) for p in b['provenance'] or []]
    return bool(ps) and any(cnt[cid].get(s,0)<2 for s in ps)
# split groups whose measures are incompatible into same-measure subclusters
g=[]; nsplit=0
for x in g0:
    ms={b['measure_info'] for b in x['books'] if b['measure_info']}
    if len(ms)>1 and compat(ms)[0] is None:
        nsplit+=1
        sub=collections.defaultdict(list)
        for b in x['books']:
            if b['measure_info']: sub[re.sub('^不分卷','一卷',norm(b['measure_info']))].append(b)
        for k,bs in sub.items():
            if len(bs)>1:
                cid=x['key'][1]
                g.append({'key':x['key'],'books':bs,'ni':sum(indep(cid,b) for b in bs),'ns':0,'split':1})
    else: g.append(x)
print('split groups',nsplit,'subclusters',sum(1 for x in g if x.get('split')))
ct={}
for cid in {x['key'][1] for x in g}:
    f=glob.glob(f'Collection/{cid[-3]}/{cid[-2]}/{cid[-1]}/{cid}-*.json')[0]
    ct[cid]=json.load(open(f))['title']
BAD=re.compile('節錄|節選|摘鈔|摘抄|殘|節本|選錄|存')
PRINTMARK=re.compile('刻|印|抄|鈔|寫|景|影|拓|局')
R=collections.Counter(); ok=[]; rej=collections.defaultdict(list)
for x in g:
    cid=x['key'][1]; bs=x['books']; T=ct[cid]
    def why():
        if cid=='8rlcsybg2hhk': return 'zaizao'
        if re.search('說郛|稗海',T): return 'shuofu'
        if any(BAD.search((b['title'] or '')+(b['measure_info'] or '')+(b['edition'] or '')) for b in bs): return 'jielu'
        au=[{a.get('name') for a in (b['authors'] or []) if a.get('name')} for b in bs]
        au=[a for a in au if a]
        if len(au)>1 and any(not(a&b2) for i,a in enumerate(au) for b2 in au[i+1:]): return 'author'
        ms={b['measure_info'] for b in bs if b['measure_info']}
        if len(ms)>1:
            lg,mw=compat(ms)
            if lg is None: return 'measure-'+mw
            x['mlong']=lg
        if x['ni']>1: return 'two-indep'
        prints=[]; other=[]; other_all=[]
        for b in bs:
            e=(b['edition'] or '').split(';')[-1]
            ind=indep(cid,b)
            if not e: continue
            if e.endswith('本'):
                if e.startswith('影印') or e.startswith('民國'): other_all.append(e)
                stem=re.sub('^影印|^民國.*?影印|本$','',e)
                if e.startswith('影印') or (stem and cc.convert(stem) in cc.convert(T)) or cc.convert(stem[:4]) in cc.convert(T): continue
                if not PRINTMARK.search(e): return 'cb-other-name'
                if ind: return 'cb-indep'
                other.append(e)
            else:
                if ind: return 'print-indep'
                prints.append(e)
        if len(set(other))>1 or len(set(other+other_all))>1: return 'cb-other-two'
        if other and prints: return 'cb-print-mix'
        if len(set(prints))>1: return 'print-conflict'
        if len({b['title'] for b in bs})>1:
            if not(len(ms)==1 and all(b['measure_info'] for b in bs)): return 'title'+('-m' if len(ms)>1 else '')
            x['tdiff']=1
        return None
    w=why()
    R[w]+=1
    if w: rej[w].append(x)
    else: ok.append(x)
print(R)
json.dump(ok,open(S+'/ok.json','w'),ensure_ascii=False)
json.dump(rej,open(S+'/rej.json','w'),ensure_ascii=False)
