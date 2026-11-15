import json,re,sys
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
shard={x['id']:x for x in json.load(open(S+'shard1.json'))}
PFX={'R100000002':'NDL','R100000039':'NDL*','R000000050':'早大','R100000092':'九大','R100000102':'東大','R100000105':'京大','R100000087':'駒大','R100000103':'福井','R000000054':'宮城圖','R100000113':'佐賀圖','R100000094':'岩瀬','R100000136':'~Cin','R100000001':'~地方','R100000133':'石川圖','R100000138':'名古屋鶴舞','R100000143':'茨大','R100000114':'關大','R100000139':'千葉大','R100000144':'神戸大','R100000123':'同志社','R100000147':'大倉'}
for bid,y,res in json.load(open('/tmp/wb_pass2.json')):
    x=shard[bid]
    print('\n%s %s | %s | %s'%(bid,x['title'],x['edition'][:60],y))
    seen=set()
    for r in res:
        p=r[0].split('-')[0]
        t=re.sub(r'\s*[\[〔]\d+[\]〕]$|〔卷之.*?〕$','',r[1])
        k=(p,t,r[3],r[2])
        if k in seen: continue
        seen.add(k)
        print('   %-5s %s | %s | %s | %s | %s'%(PFX.get(p,p),r[0],t[:36],r[2][:12],r[3][:28],r[6][:14]))
