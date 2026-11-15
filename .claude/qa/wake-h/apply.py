#!/usr/bin/env python3
import json,subprocess,os,re,sys
BI='/tmp/wk-wake-h'; TODAY='2026-11-15'
N='https://ndlsearch.ndl.go.jp/books/'; CI='https://ci.nii.ac.jp/ncid/'
NDL='國立國會圖書館'
D={ # id: (basis, [(inst, call, url)])
'988g4y9wxt':('題名、責任者（服部南郭）、刊年（寬延三年＝1750）、書肆（嵩山房小林新兵衛）一致',[(NDL,'144-3',N+'R100000002-I000007301362'),('九州大學附屬圖書館',None,N+'R100000092-I2324_430219')]),
'988g8rb3es':('題名、刊年（享和二年＝1802）、官版（昌平坂學問所）一致',[(NDL,None,N+'R100000002-I000007682089'),('西尾市岩瀨文庫',None,N+'R100000094-I213277')]),
'988fzbower':('題名、元和七年（1621）銅活字勅版一致',[('慶應義塾大學',None,N+'R100000100-Ikanseki110x_40_15_1')]),
'988g3ubjf9':('題名、責任者（鐵眼道光）、天和元年（1681）刊一致',[('三康圖書館','椎和1803-18',N+'R100000126-I40002362')]),
'9950cxjmrk':('題名、責任者（張以寧）、元祿十年（1697）刊、書肆（翠簾屋又右衛門）一致',[(NDL,None,N+'R100000002-I000007513139')]),
'988g7l6230':('題名、活字本、元和寬永間（NDL 著錄「元和・寬永年間」）一致；年份為範圍，故僅按版種對應',[(NDL,None,N+'R100000002-I000007637607')]),
'9950i39tz4':('題名、寬政十一年（1799）刊一致（NDL 著錄刊者西村源六／求古館）',[(NDL,None,N+'R100000002-I000007512638')]),
'988g3h7kle':('題名、責任者（海保漁村）、天保十一年（1840）傳經書屋刊一致',[('東京大學',None,N+'R100000102-I000240407'),('早稻田大學',None,N+'R000000050-I000066890')]),
'988g5pfk7d':('題名、弘化二年（1845）刊一致（刊者天王寺屋市郎兵衛）',[('岡山縣立圖書館','W120/69/1',N+'R100000001-I33111009810225260')]),
'993elg5c00':('題名、責任者（王謨）、明治十八年（1885）樂善堂刊一致',[(NDL,None,N+'R100000002-I000000418692')]),
'993g5zclqa':('題名、責任者（山崎闇齋）、延寶六年（1678）村上勘兵衛刊一致',[(NDL,'121-123',N+'R100000002-I000007508060'),('九州大學附屬圖書館',None,N+'R100000092-I2324_4110288')]),
'993emmllvl':('題名、責任者（鄭玄）、寬政七年（1795）刊一致；NDL 著錄發行者林伊兵衛，與「兼葭堂刻」為刻者／發行者之別，按同版處理但存此備注',[('關西大學圖書館',None,N+'R100000114-I002434130')]),
'988g06le6r':('題名、責任者（元結）、文政四年（1821）官版一致',[('京都大學附屬圖書館',None,N+'R100000105-I000003197')]),
'988g46hslt':('題名、責任者（多紀元簡）、文政二年（1819）須原屋茂兵衛（聿修堂）刊一致',[('九州大學附屬圖書館',None,N+'R100000092-I2324_4492027')]),
'988g84u0av':('題名、責任者（多紀元簡）、安政四年（1857）和泉屋金右衛門・須原屋茂兵衛刊一致',[('宮城縣圖書館',None,N+'R000000054-I040_53950')]),
'988g740077':('題名、寬文九年（1669）刊一致',[('京都大學附屬圖書館',None,N+'R100000105-I000012762')]),
'988g0kbu30':('題名、責任者（陳會）、正保二年（1645）田原仁左衛門刊一致',[('早稻田大學',None,N+'R000000050-I000067009'),('東京大學',None,N+'R100000102-I000228764')]),
'988g23ku8h':('題名、天保四年（1833）官版（昌平叢書）一致',[('西尾市岩瀨文庫',None,N+'R100000094-I213243')]),
'994xusgutc':('題名、享保二年（1717）梅村玉池堂（書肆梅村彌右衛門）刊一致',[('早稻田大學',None,N+'R000000050-I000047452'),('名古屋市鶴舞中央圖書館','河カ-26',N+'R100000138-I2755')]),
'988g07ucch':('題名、責任者（林鉞）、明和四年（1767）平安書肆和泉掾（出雲寺）刊一致',[('九州大學附屬圖書館',None,N+'R100000092-I2324_7167615'),('佛教大學附屬圖書館',None,CI+'BB00551989')]),
'993fo2rk01':('題名（書經古註音義）、明和五年（1768）江戶前川六左衛門等刊一致',[('九州大學附屬圖書館',None,N+'R100000092-I2324_428038')]),
'993ekxf3eq':('題名、寶曆十一年（1761）刊一致；NDL 摘要未載書肆，崇文堂未獨立核實',[('名古屋市鶴舞中央圖書館','河サ-85',N+'R100000138-I3263')]),
'988g4d1s0c':('題名、嘉永二年（1849）刊記（河內屋喜兵衛等）一致',[('天理大學附屬天理圖書館','791||285',CI+'BB2610513X')]),
'99je93h7vw':('題名、天明七年（1787）序、刊記「太古堂藏刻」一致',[('京都大學文學研究科圖書館','中哲文 日C||IVa||3-11',CI+'BB18355357')]),
'993j4bu801':('題名、責任者（李昉）、封面裏「光緒己丑貴陽陳氏栞于日本」一致',[('京都大學文學研究科圖書館','中哲文 D||IIIp||5-2',CI+'BB23317222')]),
'988g7xyscq':('題名（將來台州錄）、文政四年（1821）比叡山淨土院藏版一致',[('關西大學圖書館','L23||||100||6174',CI+'BA72751512')]),
'988g4i1koz':('題名（來臺州錄，與 988g7xyscq 疑重複著錄）、文政四年（1821）比叡山淨土院藏版一致',[('關西大學圖書館','L23||||100||6174',CI+'BA72751512')]),
}
def path(i):
    out=subprocess.run(['git','ls-tree','-r','origin/main','--name-only','--','Book/%s/%s/%s'%(i[-3],i[-2],i[-1])],cwd=BI,capture_output=True,text=True).stdout
    for l in out.splitlines():
        if '/'+i+'-' in l: return l.strip('"')
shard={r['id']:r for r in json.load(open(os.path.join(BI,'.claude/qa/wake-h/shard7.json')))}
rows=[]
for i,(basis,hs) in D.items():
    p=path(i)
    raw=subprocess.run(['git','ls-tree','-r','origin/main','--name-only','-z','--','Book/%s/%s/%s'%(i[-3],i[-2],i[-1])],cwd=BI,capture_output=True,text=True).stdout.split('\0')
    p=[x for x in raw if '/'+i+'-' in x][0]
    subprocess.run(['git','sparse-checkout','add','/'+p],cwd=BI,check=True)
    subprocess.run(['git','checkout'],cwd=BI,capture_output=True)
    d=json.load(open(os.path.join(BI,p),encoding='utf-8'))
    ex={q.get('institution') for q in d.get('provenance',[])}
    add=[]
    for inst,call,url in hs:
        e={'institution':inst}
        if call: e['call_number']=call
        e['source']='NDL Search '+url if 'ndlsearch' in url else 'CiNii Books '+url
        if any(q.get('source')==e['source'] for q in d.get('provenance',[])): continue
        add.append(e)
    d.setdefault('provenance',[]).extend(add)
    a,b,c=d['revision'].split('.'); d['revision']='%s.%s.%d'%(a,b,int(c)+1); d['revised_at']=TODAY
    note='2026-11-15 和刻本日本館藏專項（車道 wake-h）：補掛日本館藏%s。依據：%s。'%('、'.join(h[0] for h in hs),basis)
    old=d.get('ai_note')
    d['ai_note']=(old.rstrip()+'\n'+note) if isinstance(old,str) and old else note
    open(os.path.join(BI,p),'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    rows.append((i,shard[i]['title'],'補挂','、'.join(h[0] for h in hs),' '.join(h[2] for h in hs),basis))
open(os.path.join(BI,'.claude/qa/wake-h/applied.json'),'w').write(json.dumps(rows,ensure_ascii=False))
print(len(rows))
