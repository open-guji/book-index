import h3lib,re,sys
def yr(s):
    m=re.search(r'\b([12][0-9]{3})\b',s)
    if m: return int(m.group(1))
    if re.search(r'江戸|江戶|寛永|明暦|慶長|元和|天正|室町|桃山',s): return 1700
    return None
def tri(q,pages=1,maxy=1911,miny=0,show=True,extra='&year_to=1911'):
    out=[];tot=None
    for p in range(1,pages+1):
        r=h3lib.search(q,p,200,extra)
        if not r: break
        tot=r['tot']
        for x in r['recs']:
            y=yr(x['year'])
            if y is None or (miny<=y<=maxy): out.append(x)
        if len(r['recs'])<200: break
    if show:
        print('##',q,'total',tot,'kept',len(out))
        for x in out: print(x['ncid'],'|',x['title'][:34],'|',x['auth'][:22],'|',x['pub'][:26],'|',x['year'][:18],'|',x['n'])
    return out
if __name__=='__main__':
    tri(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 1)
