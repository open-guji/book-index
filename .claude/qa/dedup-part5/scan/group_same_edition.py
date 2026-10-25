import json,collections,re
B=[json.loads(l) for l in open('/tmp/claude-0/s/books2.jsonl')]
byw=collections.defaultdict(list)
for b in B: byw[b['w']].append(b)
def ne(e):
    e=(e or '').strip()
    for a,b in [('彙','匯'),('註','注')]: e=e.replace(a,b)
    return re.sub(r'[\s　]','',e)
MS=re.compile(r'抄|鈔|稿|寫本|批|校本|跋本|題識|拓|手札|寫')
YEAR=re.compile(r'(元年|[一二三四五六七八九十廿]+年|\d+年)')
def cls(e):
    if MS.search(e): return 'ms'
    if YEAR.search(e): return 'dated'
    if re.search(r'叢書本|本$',e) and len(e)>4 and not re.fullmatch(r'(清|明|元|宋|民國|日本|朝鮮)?(刻|刊|活字印|石印|鉛印|木活字印)本',e): return 'named'
    return 'generic'
c=collections.Counter();cb=collections.Counter();ex=collections.defaultdict(list)
groups=[]
for w,v in byw.items():
    d=collections.defaultdict(list)
    for b in v:
        if ne(b['ed']): d[ne(b['ed'])].append(b)
    for e,x in d.items():
        if len(x)<2: continue
        k=cls(e)
        ci_same=len({tuple(sorted(b['ci'])) for b in x})==1
        kk=k+('' if ci_same else '/ci-diff')
        c[kk]+=1; cb[kk]+=len(x); ex[kk].append(e)
        groups.append({'w':w,'ed':e,'cls':kk,'ids':[b['id'] for b in x]})
print(c);print(cb)
import random;random.seed(1)
for k,v in ex.items(): print(k,random.sample(v,min(12,len(v))))
json.dump(groups,open('/tmp/claude-0/s/g5b.json','w'),ensure_ascii=False)
