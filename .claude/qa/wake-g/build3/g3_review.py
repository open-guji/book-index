import sys,re,json
sys.path.insert(0,'.')
from g3_group import groups
from g3_nc import info
def short(i):
    ks=[n for n in i['notes'] if re.search(r'見返|奥付|奧付|刊記|蔵版|藏版|書肆|刊行|印行|訓点|訓點|活字|写本|寫本|推定|刊年|刊期|改刻|後印|覆刻|重刻|求版|版元|序|跋',n)]
    return ' / '.join(k[:70] for k in ks[:4])
if __name__=='__main__':
    scan=sys.argv[1]; rx=re.compile(sys.argv[2]); ex=re.compile(sys.argv[3]) if len(sys.argv)>3 and sys.argv[3] else None
    G=groups(scan)
    for k,g in sorted(G.items(),key=lambda kv:(kv[0][0],kv[0][2] or 0)):
        if not rx.search(k[0]) or (ex and ex.search(k[0])): continue
        print('=== %s | %s | %s | n=%d'%(k[0],k[1],k[2],len(g['items'])))
        for it in g['items']:
            i=info(it['ncid'])
            if not i: print('  ',it['ncid'],'FETCHFAIL'); continue
            print('  %s %s | %s | %s | %s | %s | %s'%(i['ncid'],i['title'][:30],'; '.join(i['pub'])[:50],'/'.join(i['pd']),i['extent'],','.join(o.replace(' 附属図書館','').replace('大学','大')[:12] for o in i['owners']),short(i)))
