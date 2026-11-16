import json,re,sys,collections
sys.path.insert(0,'.')
jp=json.load(open('jpbooks.json'))
dbn=set(open('ncids_in_db.txt').read().split())
byyear=collections.defaultdict(list)
for b in jp:
    d=b.get('dating') or {}
    y=d.get('year') if isinstance(d,dict) else None
    if y: byyear[y].append(b)
def yr(s):
    m=re.search(r'\[(\d{4})',s) or re.search(r'\((\d{4})',s)
    return int(m.group(1)) if m else None
def norm(t):
    t=re.sub(r'[\s　]|[0-9０-９]+[巻卷册冊]?|\(存.*?\)|\[.*?\]|[、,:：;；。,]','',t)
    t=t.translate(str.maketrans('経伝論説証図礼発国楽観読点斎様歴辞辺広会関医処剣対沢画県体両児覚寿尽恵応仮戦旧栄歓気竜寛変称随単断済蔵県県','經傳論說證圖禮發國樂觀讀點齋樣歷辭邊廣會關醫處劍對澤畫縣體兩兒覺壽盡惠應假戰舊榮歡氣龍寬變稱隨單斷濟藏縣縣'))
    return t
def pub1(p):
    p=re.split(r'[,:，：;；\[\(（]',p)[0].strip()
    return p
def groups(scanfile,qs=None):
    r=json.load(open(scanfile)); G={}
    for q,v in r.items():
        if qs and q not in qs: continue
        for i in v['jp']:
            k=(norm(i['title'])[:14],pub1(i['pub']),yr(i['yr']))
            g=G.setdefault(k,dict(items=[],qs=set()))
            if i['ncid'] not in [x['ncid'] for x in g['items']]: g['items'].append(i)
            g['qs'].add(q)
    return G
if __name__=='__main__':
    G=groups(sys.argv[1])
    out=[]
    for k,g in sorted(G.items(),key=lambda kv:(kv[0][0],kv[0][2] or 0)):
        indb=[i['ncid'] for i in g['items'] if i['ncid'] in dbn]
        y=k[2]
        near=[b['id']+':'+b['title'][:8] for b in byyear.get(y,[]) if y and k[0][:2] in norm(b['title'])] if y else []
        print('%s|%s|%s|n=%d|db=%s|near=%s|%s'%(k[0],k[1],y,len(g['items']),','.join(indb) or '-',','.join(near[:3]) or '-',g['items'][0]['ncid']))
