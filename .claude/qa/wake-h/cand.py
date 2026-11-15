import json,re,ndl,match
d=json.load(open('shard7.json'))
def norm(s): return re.sub(r'[\s　]','',s)
out=[]
for r in d:
    res=ndl.C.get(r['title']+'|')
    y=match.year(r['edition'])
    print('==',r['id'],r['title'],'|',r['edition'][:45],'|',y,r['prov'][:1])
    if res is None: print('   (no result)'); continue
    n=0
    for x in res:
        t=norm(''.join(x['title']))
        if r['title'][:2] not in t: continue
        ds=' '.join(x['date']); 
        ok = y is not None and str(y) in ds
        if y is not None and not ok: continue
        if y is None and not any(k in ''.join(x['type']+x['pub']+x['title']) or True for k in ['']): continue
        print('  ',t[:30],'|',x['creator'][:1],'|',x['pub'][:1],'|',ds[:25],'|',x['link'][0][-38:] if x['link'] else '')
        n+=1
        if n>=6: break
