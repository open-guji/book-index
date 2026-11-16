#!/usr/bin/env python3
# wake-g 第四輪：明治期刊本（集部字書及其它）新建。用法 g4_build.py [--apply]
import sys,re,json,os,collections
sys.path.insert(0,'/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g4')
from g3_build import build_one,inst,kanji,dupcheck
from g3_nc import info
APPLY='--apply' in sys.argv
W_ZHEN='d59f6ejgbshu'; W_WZ='d59f2hqcy1oj'; W_HM='d59f2q6wtrsw'; W_NS='d59f28lkb75v'; W_SZ='d59f2pymq4u8'; W_3='d59fxu2sxo1s'
CAT='https://ci.nii.ac.jp/ncid/'
SPEC=[
 dict(k='zhenbao1870',work=W_ZHEN,title='古文眞寶',nc='BC18799551 BB24117910 BB1712959X BC07482258 BB08090846',pubs=['勝村屋治右衛門','吉野屋仁兵衛','菱屋孫兵衛'],
      note='前集三卷後集二卷合刻；見返「明治三庚午歳晩夏校正新刻」「三書房藏」；後集跋題「重刋古文眞寶」。東大總合（BC07482258）、京大吉田南（BB08090846）兩館僅著錄後集；部分書誌另列書肆風月堂庄左衛門（同為八行十七字訓點本，併為一版）。'),
 dict(k='jiaoben1876',work=W_ZHEN,title='校本古文眞寶',nc='BB25891739 BB25934376',pubs=['勝村治右衛門'],
      note='鈴木善教校；前集（BB25891739）、後集（BB25934376，存一卷，版心下有「文德堂梓」）各一書誌，併為一版；前後集是否同時刊行未逐冊核。'),
 dict(k='pl1870',work=W_WZ,title='正文章軌範評林註釋',nc='BB08069114',pubs=['群玉堂'],
      note='題簽「明治再刻文章軌範評林」；僅正編七卷；藍田東龜年補訂（寬政三年序）之重刻。'),
 dict(k='pl1872',work=W_WZ,title='正續文章軌範評林註釋',nc='BB24629606 BA76735391',pubs=['鹿兒嶋縣'],
      note='見返「明治五壬申歳新鐫」「鹿兒嶋縣刊行」；正編七卷續編七卷；題簽「明治新鐫正文章軌範評林」。'),
 dict(k='pl1876',work=W_WZ,title='正續文章軌範評林註釋',nc='BB0573165X BB02382281 BA54828240 BA54945266',pubs=['高橋種香','田中九兵衛'],
      note='刊記「版權免許 明治九年五月十四日 出版人 高橋種香 製本所 田中九兵衛 賣弘所 田中九兵衛」；版心「鹿兒島縣刊行」；首書本，訓點附；BA54945266 為續編（缺卷一二）。'),
 dict(k='pl1878',work=W_WZ,title='正續文章軌範評林註釋',nc='BB17400503 BA69367968 BA54837219 BA54956499',pubs=['岡田茂兵衛','山內五郎助'],
      note='見返「群玉堂梓行」；書誌注「明治8刊の再版」；BA54956499 為續編（缺卷一至四）；首書本，訓點附。'),
 dict(k='pl1886',work=W_WZ,title='正續文章軌範評林註釋',nc='BA55172814 BB22797450 BA55293229',pubs=['林斧介'],
      note='福井掬補輯；磊落堂藏版；首書本，訓點附；正編（BA55172814）與續編（BB22797450、BA55293229）合刻。'),
 dict(k='zp1878',work=W_WZ,title='文章軌範纂評',nc='BB01057365',pubs=['佐々木惣四郎','大谷仁兵衛','新惣三郎','田中太右衛門'],
      note='安藤太郎纂評（凡例嘉永六年）；奧付記「明治9年5月版權免許、同11年5月再版改式御屆、同11年8月出板」；見返「合書房藏梓」。'),
 dict(k='hm1869',work=W_HM,title='倭名類聚鈔',nc='BB02290627 BA69227062 BB20285323',pubs=['寶文堂大野木市兵衛'],
      note='貞享五年大坂澁川清右衛門刊本之明治二年補刻後印（那波道圓校）；見返「明治二補刻」「大坂書肆 寳文堂發兌」；BB20285323 另列秋田屋市兵衛、阪本屋大二郎、堺屋仁兵衛、森屋治兵衛、山城屋佐兵衛、須原屋茂兵衛等及大垣、桑名、兵庫、姬路、岡山各地書肆（相合發兌），併為一版。'),
 dict(k='sd1870',work=W_NS,title='日本書紀神代',nc='BB1099408X',pubs=['出雲寺文治郎','石田和助','稻田佐兵衛'],
      note='神代二卷（清原國賢校、清原宣通重校）；書誌注「享保14年跋刊の後印」；另列華井卯助。僅神代卷，非全書。'),
 dict(k='sd1873a',work=W_NS,title='神代巻正訓',nc='BB11123546 BB05851866',pubs=['出雲寺文治郎','大谷仁兵衛','永田調兵衛'],
      note='神代二卷，中山茂樹（繁樹）訓點；刊記「延寶四年丙辰八月原版／明治六年四月二刻」；另列澤田友五郎。僅神代卷，非全書。'),
 dict(k='sd1873b',work=W_NS,title='説教必携神代卷',nc='BB11105759 BB11105216 BA54782820',pubs=['文榮堂'],
      note='見返「明治六年七月補刻」「文榮堂梓」；BB11105216／BA54782820 著錄出版者為前川源七郎，見返同為文榮堂，視為同版換肆（前川源七郎）。僅神代卷，非全書。'),
 dict(k='kana1875',work=W_NS,title='假名日本紀',nc='BB11024588',pubs=['東崖堂'],
      note='清原國賢校；見返「東崖書屋藏梓」，奧付「山岸氏藏版」；為日本書紀神代卷之假名本，非全書。'),
 dict(k='sn1869',work=W_SZ,title='續日本紀',nc='BD1276054X',pubs=['綿屋喜兵衛','加嶋屋清助','敦賀屋彦七'],
      note='書誌注「明暦3年跋刊の後印」（立野春節校）；二十冊；書肆多家相合（森屋治兵衛、丁子屋平兵衛、和泉屋市兵衛、山城屋佐兵衛、菊屋七郎兵衛、菱屋弥兵衛、吉野屋勘兵衛、平野屋茂兵衛等）。'),
 dict(k='sz1876',work=W_3,title='三字經',nc='BD06597353',pubs=['淺倉屋吉田久兵衛'],
      note='見返「王伯厚先生纂／東都 文淵堂梓」；奧付「眀治九年五月十八日版權免許／讓受人 淺倉屋 吉田久兵衛／出版人兼發賣 山城屋 稲田佐兵衛」；訓點送假名付。'),
]
OUT=[]
import g3_build
_orig=g3_build.info
def _clean(nc):
    r=_orig(nc)
    if r and nc in ('BB01057365',): r=dict(r,pub=[re.sub(r'\s*\[ほか\]','',p) for p in r['pub']])
    return r
g3_build.info=_clean
for sp in SPEC:
    b,pr=build_one(sp['work'],{'ncids':sp['nc'].split()},sp['title'])
    if not b: print('REJ',sp['k'],pr); continue
    b['pubs_show']=sp['pubs'][:3]
    b['ed']='日本%s%s年%s刊本'%(b['reign'],kanji(b['nth']),'、'.join(b['pubs_show']))
    b['sp']=sp; b['dup']=dupcheck(b)
    OUT.append(b)
    print(sp['k'],b['year'],b['ed'],'recs=%d'%len(b['recs']),'own=%d'%len({o for r in b['recs'] for o in r['owners']}),'DUP:'+str(b['dup']) if b['dup'] else '', 'P:'+str(b['probs']) if b['probs'] else '')
def book_json(b,bid):
    sp=b['sp']
    d={'schema_version':1,'id':bid,'type':'book','title':b['title'],'work_id':b['work'],'edition':b['ed']}
    txt=' '.join(' '.join(r['notes']) for r in b['recs'])
    if re.search(r'活版|活字印',txt): d['edition_type']='活字本'
    elif re.search(r'版心|魚尾|四周|匡郭|匡廓|版權免許|補刻|再刻|後印',txt): d['edition_type']='刻本'
    d['dating']={'era':'日本','reign':b['reign'],'year':b['year'],'certainty':'attested','source':'catalog','basis':'CiNii Books 書誌著錄「%s」%s'%(b['pdtxt'].strip(),('；'+b['colo'][0][:60]) if b['colo'] else '')}
    d['publication_info']={'place':'日本','publisher':'、'.join(b['pubs_show'])}
    if len(b['ext'])==1:
        m=re.match(r'^(\d+)(冊|巻|卷)$',list(b['ext'])[0])
        if m: d['measures']=[{'number':int(m.group(1)),'unit':'冊' if m.group(2)=='冊' else '卷'}]
    prov={}
    for r in b['recs']:
        for o in r['owners']: prov.setdefault(inst(o),[]).append(r['ncid'])
    provs=[];urls=[]
    for k,ns in prov.items():
        provs.append({'institution':k,'source':' '.join('CiNii Books '+CAT+n for n in ns[:3])})
        for n in ns[:3]:
            if CAT+n not in urls: urls.append(CAT+n)
    for r in b['recs']:
        if CAT+r['ncid'] not in urls and len(urls)<12: urls.append(CAT+r['ncid'])
    d['provenance']=provs
    d['description']={'text':'%s（%s）；刊者據 CiNii Books 書誌著錄。'%(b['creator'][:120],b['ed']),'sources':sorted(urls)}
    d['sources']=[{'id':'wakeg4-%d'%i,'name':'CiNii Books','type':'url','details':u} for i,u in enumerate(sorted(urls))]
    note='和刻本日本馆藏专项第四輪（2026-11-16，車道 wake-g，明治期刊本·集部字書及其它）：據 CiNii Books 書誌新建（刊年、刊者、館藏據書誌頁；未核原書）。本庫該 Work 原無此刊年之明治刊本；不與庫內其他版本硬並。'
    note+='\n依據 NCID：'+'、'.join(r['ncid'] for r in b['recs'])
    note+='\n版本說明：'+sp['note']
    d['ai_note']=note
    d['revision']='1.0.0'; d['revised_at']='2026-11-16'
    return d
json.dump([dict(b,recs=[r['ncid'] for r in b['recs']],ext=dict(b['ext']),sp=None) for b in OUT],open('g4_build.out.json','w'),ensure_ascii=False)
if APPLY:
    WK='/tmp/wk-g4'; sys.path.insert(0,WK+'/.claude/qa'); import mintid
    os.chdir(WK)
    sel=[b for b in OUT if not b['dup'] and any(r['owners'] for r in b['recs'])]
    ids=mintid.mint('Book','wake-g',len(sel))
    led=[];paths=[]
    for b,bid in zip(sel,ids):
        d=book_json(b,bid)
        safe=re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]','',b['ed'])[:24]
        p='Book/%s/%s/%s/%s-%s%s.json'%(bid[-3],bid[-2],bid[-1],bid,b['title'],safe)
        os.makedirs(os.path.dirname(p),exist_ok=True)
        open(p,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
        paths.append(p)
        led.append('\t'.join([bid,b['title'],'新建',b['ed'],'、'.join(x['institution'] for x in d['provenance']),' '.join(x['details'] for x in d['sources'][:3]),b['work']]))
    qa=WK+'/.claude/qa/wake-g'
    open(qa+'/ledger4.tsv','w',encoding='utf-8').write('\n'.join(led)+'\n')
    open(qa+'/changed_paths4.txt','w').write('\n'.join(paths)+'\n')
    print('APPLIED',len(sel))
