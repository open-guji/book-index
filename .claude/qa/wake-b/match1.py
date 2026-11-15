import json,re,sys
sys.path.insert(0,'.')
import eras
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
shard=json.load(open(S+'shard1.json'))
raw={};cur=None
for l in open('/tmp/wb_ndl_raw.txt'):
    if l.startswith('##'): cur=l.split()[1];raw[cur]=[];continue
    p=[s.strip() for s in l.split('|')]
    raw[cur].append(p)
PFX={'R100000002':'NDL','R100000039':'NDL(digi)','R000000050':'早大','R100000092':'九大','R100000102':'東大','R100000105':'京大','R100000087':'駒大','R100000103':'福井','R000000054':'宮城縣圖','R100000113':'佐賀縣圖','R100000094':'岩瀬','R100000136':'CiNiiR','R100000001':'地方館'}
for x in shard:
    y,_=eras.era_year(x['edition'])
    if y is None and x['year'] and 'JP' : y=x['year']
    if not y: print('NOYEAR',x['id'],x['title'],x['edition'][:30]);continue
    c=[]
    for p in raw.get(x['work'],[]):
        m=re.match(r'(\d{4})',p[4])
        if m and abs(int(m.group(1))-y)<=0: c.append(p)
    print('\n%s %s | %s | %s'%(x['id'],x['title'],x['edition'][:50],y))
    seen=set()
    for p in c:
        k=(p[1],p[3],p[0][:11])
        if k in seen: continue
        seen.add(k);print('    %s %s | %s | %s | %s | %s'%(PFX.get(p[0].split('-')[0],p[0].split('-')[0]),p[0],p[1][:40],p[2][:12],p[3][:30],p[5][:14]))
