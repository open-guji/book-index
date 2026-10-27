import json,sys,re,itertools,collections
exec(open('/tmp/claude-0/s/tier.py').read().split("D=json.load")[0])
PO={'pre-qin':0,'qin-han':1,'three-kingdoms':2,'jin':3,'nanbeichao':4,'sui-tang':5,'five-dynasties':6,'song':7,'liao-jin-yuan':8,'ming':9,'qing':10,'modern':11}
DY={'清':10,'明':9,'晉':3,'元':8,'唐':5,'宋':7,'東漢':1,'北宋':7,'趙宋':7,'南朝梁':4,'南宋':7,'西晉':3,'金':8,'隋':5,'北魏':4,'東晉':3,'漢':1,'三國魏':2,'西漢':1,'北周':4,'南朝宋':4,'三國吳':2,'戰國':0,'三國':2,'南朝陳':4,'五代':6,'宋末元初':8,'南朝齊':4,'南唐':6,'後秦':3,'三國蜀':2,'北齊':4,'陳':4,'南北朝':4,'北涼':3,'遼':8,'民國':11,'吳':2,'東魏':4,'後唐':6,'梁':4,'西夏':8,'上古':0}
def per(w):
    a=(w.get('authors') or [{}])[0]
    if a.get('dyn') in DY: return DY[a['dyn']]
    if w.get('period') in PO: return PO[w['period']]
    e=a.get('ent') or {}
    if e.get('period') in PO: return PO[e['period']]
    return None
G=[json.loads(l) for l in []]
D=json.load(open('/tmp/claude-0/w/manual.json'))+json.load(open('/tmp/claude-0/w/auto.json'))
D.sort(key=lambda g:g['gi'])
def srcs(w): return {s.get('source') for s in w.get('src',[])}
res=[];cnt=collections.Counter()
for g in D:
    ws=g['works']; flags=set(g['why'])
    pairs=[]
    allsafe=True
    for a,b in itertools.combinations(ws,2):
        A=(a.get('authors') or [{}])[0];B=(b.get('authors') or [{}])[0]
        pa,pb=per(a),per(b)
        why=None
        ja,jb=a.get('juan'),b.get('juan')
        if pa is not None and pb is not None and abs(pa-pb)>=2: why='朝代悬隔'
        elif ja and jb and abs(ja-jb)>1: why='卷数悬殊'
        elif not flags and A.get('eid') and B.get('eid') and A['eid']!=B['eid']:
            ja,jb=a.get('juan'),b.get('juan')
            if ja and jb and abs(ja-jb)>1: why='异人且卷数异'
            elif srcs(a)=={'中國古籍總目'} and srcs(b)=={'中國古籍總目'}: why='异人·均总目著录'
        pairs.append((a['id'],b['id'],why))
        if not why: allsafe=False
    g['pairs']=pairs; g['safe']=allsafe
    cnt['safe' if allsafe else 'manual']+=1
print(cnt)
json.dump(D,open('/tmp/claude-0/w/tiered.json','w'),ensure_ascii=False)
