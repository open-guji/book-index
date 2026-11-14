import json,glob,collections,re,opencc,sys
sys.path.insert(0,'/tmp/claude-0/-home-user/e59db2b9-8fd4-5ed9-a492-942f4a225576/scratchpad/r10')
from meas import compat
cc=opencc.OpenCC('t2s')
S='/tmp/claude-0/-home-user/e59db2b9-8fd4-5ed9-a492-942f4a225576/scratchpad/r10'
g=json.load(open(S+'/groups2.json'))
cnt=json.load(open(S+'/provcnt.json'))
ct={}
for cid in {x['key'][1] for x in g}:
    f=glob.glob(f'Collection/{cid[-3]}/{cid[-2]}/{cid[-1]}/{cid}-*.json')[0]
    ct[cid]=json.load(open(f))['title']
BAD=re.compile('節錄|節選|摘鈔|摘抄|殘|節本|選錄|存')
R=collections.Counter(); ok=[]; rej=collections.defaultdict(list)
def num(m):
    return m
for x in g:
    cid=x['key'][1]; bs=x['books']; T=ct[cid]
    def why():
        if cid=='8rlcsybg2hhk': return 'zaizao'
        if re.search('說郛|稗海',T): return 'shuofu'
        if any(BAD.search((b['title'] or '')+(b['measure_info'] or '')+(b['edition'] or '')) for b in bs): return 'jielu'
        ms={b['measure_info'] for b in bs if b['measure_info']}
        if len(ms)>1:
            lg,mw=compat(ms)
            if lg is None: return 'measure-'+mw
            x['mlong']=lg
        if x['ni']>1: return 'two-indep'
        prints=[]
        for b in bs:
            e=(b['edition'] or '').split(';')[-1]
            ps=[p.get('source') for p in b['provenance'] or []]
            ind=bool(ps) and any(cnt[cid].get(s,0)<2 for s in ps)
            if not e: continue
            if e.endswith('本'):
                stem=re.sub('^影印|^民國.*?影印|本$','',e)
                if e.startswith('影印') or (stem and cc.convert(stem) in cc.convert(T)) or cc.convert(stem[:4]) in cc.convert(T): continue
                return 'cb-other'
            else:
                if ind: return 'print-indep'
                prints.append(e)
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
