import json,re
H=json.load(open('harvest.json')); B=json.load(open('books.json'))
def y(i):
    m=re.match(r'\d{4}',i['date']); return int(m.group()) if m else None
skip=set(open('reviewed.txt').read().split()) if __import__('os').path.exists('reviewed.txt') else set()
n=0
for w,v in H.items():
    if w in skip: continue
    tt=set(v['title'])
    seen={}
    for i in v['items']:
        if i['place']!='JP': continue
        yy=y(i)
        if yy and yy>1911: continue
        t=re.sub(r'\s','',i['t'])
        if len(tt&set(t))/len(tt)<0.7: continue
        k=(t[:30],i['pub'][:25],i['date'])
        seen.setdefault(k,[]).append(i['id'])
    ex=[(b['edition'] or '')[:20]+str(b['year'] or '') for b in B.get(w,[])]
    print('##',w,v['title'],v['authors'],'| 現有%d:'%len(ex),ex[:6])
    for k,ids in sorted(seen.items(),key=lambda x:x[0][2])[:14]: print('   ',k,ids[0],len(ids))
