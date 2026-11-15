# -*- coding: utf-8 -*-
import json,os,re,subprocess,sys
BI=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
NDL,WAS,KYU,KYO,SAGA='國立國會圖書館','早稻田大學圖書館','九州大學附屬圖書館','京都大學',''
ISH,MYG,NGY,IWA='石川縣立圖書館','宮城縣圖書館','名古屋市鶴舞中央圖書館','西尾市岩瀬文庫'
KYT,AKI,OKI='京都府立京都學・歷彩館','秋田縣立圖書館','沖繩縣立圖書館'
P={
'995123eb5s':[(NDL,'R100000002-I031716419'),(ISH,'R100000133-IorgnB001384129')],
'988g36li4y':[(NDL,'R100000002-I000011104045'),(KYO,'R100000105-I000014524')],
'9950fo6mf5':[(NDL,'R100000002-I000007513009'),(KYO,'R100000105-I000002946'),(IWA,'R100000094-I213256')],
'995212lmgx':[(NDL,'R100000002-I000007507334'),(KYO,'R100000105-I000002934'),(KYU,'R100000092-I2324_420327'),(NGY,'R100000138-I104249')],
'988g70vmrl':[(KYU,'R100000092-I2324_431949')],
'988fz2y974':[(NDL,'R100000002-I000007291958'),(KYO,'R100000105-I000011891')],
'994zk15o8w':[(NDL,'R100000002-I000007535910')],
'993d0gehhc':[(NGY,'R100000138-I104529')],
'996jcalhe8':[(KYO,'R100000105-I000002813')],
'9979895f5y':[(NDL,'R100000002-I034217489'),(KYO,'R100000105-I000003007'),(OKI,'R100000001-I47111106047810')],
'9951217ncx':[(NDL,'R100000002-I024220684')],
'988g505c74':[(NDL,'R100000002-I000007296720'),(WAS,'R000000050-I000064866'),(KYU,'R100000092-I2324_419583'),(KYO,'R100000105-I000012517')],
'988g5rxgjo':[(NDL,'R100000002-I000007327624'),(KYU,'R100000092-I2324_4706094')],
'988g2pfg92':[(IWA,'R100000094-I200609')],
'988g2pfg9g':[(WAS,'R000000050-I000058100')],
'988g2d9729':[(NDL,'R100000002-I000007295524'),(WAS,'R000000050-I000022889'),(KYU,'R100000092-I2324_419601')],
'995269w0e8':[(KYU,'R100000092-I2324_420976')],
'988g1uiygz':[(KYU,'R100000092-I2324_4706131'),(KYO,'R100000105-I000014321')],
'99jidudamc':[(NDL,'R100000002-I000007620455')],
'994yk9jri8':[(ISH,'R100000133-IorgnB001503361')],
'988g5bp4b4':[(MYG,'R000000054-I040_55010'),(KYO,'R100000105-I000024869')],
'988fzuf4zv':[(NDL,'R100000002-I028392845')],
'988g6qw1dv':[(KYT,'R100000001-I2612110925153')],
'988g5hbe2u':[(AKI,'R100000001-I05111009710035068')],
'988g8ji5u2':[(MYG,'R000000054-I040_54352')],
}
books={b['id']:b for b in json.load(open('/tmp/wb_books.json'))}
led=open(os.path.join(os.path.dirname(__file__),'ledger.tsv'),'a',encoding='utf-8')
changed=[]
for bid,hs in P.items():
    b=books[bid]; f=b.pop('_f'); f=f.split(':',1)[-1]
    have=[p.get('institution','') for p in b.get('provenance',[])]
    add=[]
    for inst,rid in hs:
        if inst==NDL and any('國會' in h or '国会' in h for h in have): continue
        if inst in have: continue
        add.append((inst,rid))
    if not add:
        led.write('\t'.join([bid,b['title'],'已有','—','—'])+'\n'); continue
    for inst,rid in add:
        b.setdefault('provenance',[]).append({'institution':inst,'source':'NDL Search https://ndlsearch.ndl.go.jp/books/'+rid})
    v=b.get('revision','1.0.0').split('.'); v[2]=str(int(v[2])+1); b['revision']='.'.join(v); b['revised_at']='2026-11-15'
    note='和刻本日本馆藏专项 wake-b（2026-11-15）：據NDL Search（含各館聚合記錄）按題名＋刊年(＋書肆)比對，補掛日本館藏：%s；未核原書。'%'、'.join(i for i,_ in add)
    b['ai_note']=(b['ai_note']+'\n' if b.get('ai_note') else '')+note
    p=os.path.join(BI,f); os.makedirs(os.path.dirname(p),exist_ok=True)
    open(p,'w',encoding='utf-8').write(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
    changed.append(p)
    for inst,rid in add: led.write('\t'.join([bid,b['title'],'補掛',inst,'https://ndlsearch.ndl.go.jp/books/'+rid])+'\n')
open('/tmp/wb_changed.txt','a').write('\n'.join(changed)+'\n')
print(len(changed))
