import json, sys, time, re
sys.path.insert(0,'.')
import ndl
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad'
d=json.load(open(S+'/shard3.json')); W=json.load(open(S+'/d_works.json'))
qs={}
for x in d:
    if '無求備齋' not in x['edition'] and re.search(r'昭和|大正|民國|光緒三十一年|排印|影印|景印|石印',x['edition']): continue
    au=(W[x['work']]['au'] or [''])[0]
    au=re.sub(r'^(日本|魏|晉|唐|宋|元|明|清|釋)','',au) if au.startswith('日本') else au
    qs[(x['title'],au)]=1
cache={}
try: cache=json.load(open('cache_d.json'))
except: pass
for (t,a) in qs:
    k=t+'|'+a
    if k in cache: continue
    try:
        n=ndl.ndl(t,a); time.sleep(0.6)
        c=ndl.cinii(t+' '+a); time.sleep(0.6)
        cache[k]={'ndl':n,'cinii':c}
    except Exception as e:
        cache[k]={'err':str(e)}
    json.dump(cache,open('cache_d.json','w'),ensure_ascii=False)
print('done',len(cache))
