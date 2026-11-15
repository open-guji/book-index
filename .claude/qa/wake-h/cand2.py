import json,re,sys
W=json.load(open('works.json'));bw=json.load(open('bw.json'))
C=json.load(open('qcache.json')); C.update(json.load(open('qcache_rev.json')))
def norm(s): 
    s=re.sub(r'[\s　]','',s); s=re.sub(r'[０-９0-9]+(巻|卷)?(首[0-9]*巻)?|存.*$|\(.*?\)|（.*?）','',s)
    return s.replace('羣','群').replace('卷','巻').replace('薮','藪')
def yr(x):
    for d in x['date']:
        m=re.match(r'(\d{4})',d)
        if m: return int(m.group(1))
out=[]
for w,v in W.items():
    au=[a[0] for a in v['authors'] if a[0]]
    cr=au[0] if au and v['title'] not in ('周易','孟子','大學') else ''
    rs=None
    for k in (C.get('%s|%s|50|&until=1912'%(v['title'],cr)),):
        rs=k
    if rs is None: continue
    wt=norm(v['title'])
    for x in rs:
        if not x['title']: continue
        t=norm(x['title'][0])
        y=yr(x)
        if t!=wt or not y or y>1868: continue
        pub=(x['pub'] or [''])[0]
        out.append((w,v['title'],x['title'][0],','.join(x['creator'][:2]),pub,y,x['link'][0].split('/')[-1]))
json.dump(out,open('cand2.json','w'),ensure_ascii=False)
for o in out: print('\t'.join(map(str,o)))
