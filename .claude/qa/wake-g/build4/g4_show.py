import sys,json
sys.path.insert(0,'.')
from g3_nc import info
c=json.load(open(sys.argv[1]))
def rng(s):
    out=[]
    for x in s.split(','):
        if '-' in x: a,b=x.split('-'); out+=range(int(a),int(b)+1)
        else: out.append(int(x))
    return out
for k in rng(sys.argv[2]):
    o=c[k]; print('=== #%d %s %s %s'%(k,o['tc'],o['y'],'/'.join(o['ps'])[:50]))
    for nc in o['ncids'][:6]:
        i=info(nc)
        if not i: print('  ',nc,'FAIL'); continue
        print('  %s %s | %s | %s | %s | pub=%s | pd=%s | ext=%s | own=%d %s'%(nc,i['title'][:30],i['creator'][:50],i['date'],'/'.join(i['alt'])[:30],'; '.join(i['pub'])[:60],'/'.join(i['pd']),i['extent'],len(i['owners']),','.join(x[:8] for x in i['owners'][:5])))
        for n in i['notes'][:6]: print('       note:',n[:110])
