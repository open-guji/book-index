import sys,re,json,collections
sys.path.insert(0,'/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3')
from g3_nc import info
from g3_scan import isjp
VAR=str.maketrans('衞荘莊点経伝説証図礼発国楽読斎歴辞広会関医処対画体両児覚寿尽恵応仮戦旧栄気竜寛変称随単断済蔵県権学氏栄徳拝薬釈訳訳覧蘭両縁條条鉄隠亀壱弐賛観総巻円鶴霊欠曽黒鬧鬪',
                  '衛莊莊點經傳說證圖禮發國樂讀齋歷辭廣會關醫處對畫體兩兒覺壽盡惠應假戰舊榮氣龍寬變稱隨單斷濟藏縣權學氏榮德拜藥釋譯譯覽蘭兩緣條條鐵隱龜壹貳讚觀總卷圓鶴靈缺曾黑鬧鬪')
def nz(s): return re.sub(r'[\s　]','',s).translate(VAR)
def tcore(t):
    t=nz(t)
    t=re.sub(r'\(存.*?\)|\[.*?\]|[:：].*$','',t)
    t=re.sub(r'(序目錄?|目錄|首|目|附錄|[0-9０-９]+卷.*|[0-9０-９]+冊.*|上|下)$','',t)
    t=re.sub(r'[0-9０-９]+','',t)
    return t
def pubs(plist):
    out=[]
    for p in plist:
        for x in re.split(r'[:：;；,，、・\[\]\(\)（）]|ほか|他',nz(p)):
            x=x.strip()
            if x and x not in ('出版者不明',): out.append(x)
    return out
def yearof(i):
    m=None
    for s in i['pd']+[i['date']]:
        m=re.search(r'\[?(1[0-9]{3})',s)
        if m: return int(m.group(1))
def cluster(scanfiles,title_rx,excl_rx=None,qs=None):
    items={}
    for sf in scanfiles:
        r=json.load(open(sf))
        for q,v in r.items():
            if qs and q not in qs: continue
            for i in v['jp']:
                if title_rx.search(nz(i['title'])) and not (excl_rx and excl_rx.search(nz(i['title']))): items[i['ncid']]=i
    # fetch
    recs=[]
    for nc in items:
        inf=info(nc)
        if inf: recs.append(inf)
    cl=[]
    for r in recs:
        tc=tcore(r['title']); y=yearof(r); ps=set(pubs(r['pub']))
        for c in cl:
            if c['tc']==tc and c['y']==y and (c['ps']&ps or (not ps and not c['ps'])):
                c['recs'].append(r); c['ps']|=ps; break
        else: cl.append(dict(tc=tc,y=y,ps=set(ps),recs=[r]))
    # second pass merge
    ch=True
    while ch:
        ch=False
        for a in range(len(cl)):
            for b in range(a+1,len(cl)):
                A,B=cl[a],cl[b]
                if A['tc']==B['tc'] and A['y']==B['y'] and (A['ps']&B['ps']):
                    A['recs']+=B['recs'];A['ps']|=B['ps'];del cl[b];ch=True;break
            if ch:break
    return sorted(cl,key=lambda c:(c['tc'],c['y'] or 0))
def colo(r):
    return [n for n in r['notes'] if re.search(r'刊記|奥付|奧付|見返|牌記|識語|跋',n)]
def pdinfer(r):
    return not any(re.match(r'^\s*[^\[\]\d]*\d+(\s|\(|\[|年|\.)',p) and '[' in p for p in r['pd']) 
if __name__=='__main__':
    rx=re.compile(sys.argv[1]); ex=re.compile(sys.argv[2]) if len(sys.argv)>2 and sys.argv[2] else None
    cl=cluster(sys.argv[3].split(','),rx,ex)
    for n,c in enumerate(cl):
        recs=c['recs']; own=sorted({o for r in recs for o in r['owners']})
        cs={nz(x)[:60] for r in recs for x in colo(r)[:1]}
        print('#%d %s | %s | %s | ncid=%d own=%d | %s'%(n,c['tc'],c['y'],'/'.join(sorted(c['ps']))[:60],len(recs),len(own),recs[0]['ncid']))
        print('     ',recs[0]['title'][:30],'|',recs[0]['creator'][:60],'|',recs[0]['extent'],'|',(' // '.join(colo(recs[0])))[:160])
