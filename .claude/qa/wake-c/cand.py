import json,re,collections,sys
H=json.load(open('harvest.json')); B=json.load(open('books.json'))
def y(i):
    m=re.match(r'\d{4}',i['date']); return int(m.group()) if m else None
out={}
for w,v in H.items():
    seen={}
    for i in v['items']:
        if i['place']!='JP': continue
        yy=y(i)
        if yy and yy>1911: continue
        k=(re.sub(r'\s','',i['t']),i['pub'],i['date'])
        seen.setdefault(k,[]).append(i['id'])
    ex=[(b['edition'],b['year']) for b in B.get(w,[])]
    out[w]=(v['title'],v['authors'],ex,seen)
    print('##',w,v['title'],v['authors'],'| 現有:',[(e or '')[:22]+str(yr) for e,yr in ex][:8])
    for k,ids in sorted(seen.items(),key=lambda x:x[0][2]): print('   ',k,ids[0],len(ids))
