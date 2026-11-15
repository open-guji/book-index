import json,ndl,re
d=json.load(open('shard7.json'))
skip=re.compile(r'昭和|大正|影印|石印|景印|鉛印|排印|銅版')
ts=[]
for r in d:
    if skip.search(r['edition']) and not re.search('明治',r['edition']): continue
    t=r['title']
    if t not in ts: ts.append(t)
print(len(ts),flush=True)
for t in ts:
    ndl.q(t); print(t,flush=True)
