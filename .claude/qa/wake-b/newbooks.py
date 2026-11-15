# -*- coding: utf-8 -*-
import json,os,re,sys
HERE=os.path.dirname(os.path.abspath(__file__));BI=os.path.abspath(os.path.join(HERE,'../../..'))
sys.path.insert(0,os.path.join(BI,'.claude/qa'));import mintid
APPLY='--apply' in sys.argv
NDL,WAS,KYU='國立國會圖書館','早稻田大學圖書館','九州大學附屬圖書館'
# (Work id, 題名, edition, 刊型, 年, 年號, 書肆, [(機構,rid)], 備註/冊數, 互鏈說明)
I=[
('d59f27x7sttv','子華子','日本寬延元年京都西村平八刊本','刻本',1748,'寬延','西村平八',[(KYU,'R100000092-I2324_428073')],'',''),
('d59f2gphdreo','唐才子傳','日本正保四年上村次郎右衞門刊本','刻本',1647,'正保','上村次郎右衞門',[(NDL,'R100000002-I000007536534'),(WAS,'R000000050-I000042549')],'NDL著錄10卷5冊；早大3冊',''),
('d59fxz2st0qo','金匱要畧方論','日本享和元年群玉堂刊本','刻本',1801,'享和','群玉堂',[(WAS,'R000000050-I000011598')],'早大2冊（卷之上中下）','庫內另有「日本影宋鈔本」等，與本條版本不同'),
('d59f28m4adxd','千金翼方','日本明和七年山本長兵衞幽松軒藏板刊本','刻本',1770,'明和','山本長兵衞',[(NDL,'R100000002-I000007559148')],'30卷15冊','NDL另著錄同年山口又一郎刊本，疑為同版後印，未能確認，另立一條'),
('d59f28m4adxd','千金翼方','日本明和七年山口又一郎刊本','刻本',1770,'明和','山口又一郎',[(NDL,'R100000002-I000007559153')],'30卷15冊','NDL另著錄同年山本長兵衞幽松軒藏板刊本，疑為同版，未能確認，另立一條'),
('d59f2ogat2wx','春秋名號歸一圖','日本享和三年須原屋孫七刊本','刻本',1803,'享和','須原屋孫七',[(WAS,'R000000050-I000072580')],'早大1冊（卷上下）','庫內另有享和元年官版刻本，版本信息不同，另立一條'),
('d59f6ejkp43r','老子翼','日本寬延四年京都勝村治右衞門刊本','刻本',1751,'寬延','勝村治右衞門',[(NDL,'R100000002-I000007620458'),(WAS,'R000000050-I000046049')],'6卷6冊；早大著錄為承應二年刊之後刷','與承應二年小嶋市郎右衞門刊本（庫內已有）為同一底本之後刷，未能確認為同版，另立一條'),
('d59f2mxztgqp','新校正孔方圖鑑','日本嘉永六年向陽樓刊本','刻本',1853,'嘉永','向陽樓',[(WAS,'R000000050-I000041784')],'早大1冊',''),
('d59gduogi8ld','老子經通考','日本寶永二年富倉太兵衞刊本','刻本',1705,'寶永','富倉太兵衞',[(WAS,'R000000050-I000018004')],'早大4冊','庫內另有「日本松本屋刊本」（無年份），未能確認是否同版，另立一條'),
('d59f2px93eo1','本朝文粹','日本正保五年上村次郎右衞門刊本','刻本',1648,'正保','上村次郎右衞門',[(WAS,'R000000050-I000075535')],'14卷目錄1卷；早大15冊','NDL另著錄同年林甚右衞門刊本，疑為同版異肆，未能確認，另立一條'),
('d59f2px93eo1','本朝文粹','日本正保五年林甚右衞門刊本','刻本',1648,'正保','林甚右衞門',[(NDL,'R100000002-I000007317035')],'NDL 15冊','另有同年上村次郎右衞門刊本，疑為同版異肆，未能確認，另立一條'),
('d59f2px93eo1','本朝文粹','日本寬永六年田中長左衞門刊本','刻本',1629,'寬永','田中長左衞門',[(NDL,'R100000002-I000007317034')],'NDL 8冊','庫內另有寬永七年活字本，年份書肆均異'),
('d59fyfcszg1s','悉曇字記','日本寬文九年釋澄禪刊本','刻本',1669,'寬文','釋澄禪',[(NDL,'R100000002-I000007614153')],'1卷1冊',''),
('d59fyfcszg1s','悉曇字記','日本文政二年刊本（附攷誤一卷）','刻本',1819,'文政','',[(NDL,'R100000002-I000007613394')],'1卷附攷誤1卷1冊',''),
('d59f2q12ftaa','金匱玉函要略方論輯義','日本天保八年英大助等刊本','刻本',1837,'天保','英大助',[(NDL,'R100000002-I030026125')],'6巻10冊；NDL著錄責任者多紀元堅','庫內另有文化九年聿修堂刊本（丹波元簡著），著者與年份均異'),
('d59g10f1hinp','禪苑蒙求','日本寬永十六年田原仁左衞門刊本','刻本',1639,'寬永','田原仁左衞門',[(NDL,'R100000002-I000007616673')],'3卷1冊',''),
('d59g10f1hinp','禪苑蒙求','日本寬永十七年西村九郎兵衞刊本','刻本',1640,'寬永','西村九郎兵衞',[(NDL,'R100000002-I000007616676')],'3卷3冊（合1冊）',''),
('d59g10f0jt29','職原抄','日本延寶七年井筒屋六兵衞刊本','刻本',1679,'延寶','井筒屋六兵衞',[(WAS,'R000000050-I000039947')],'早大2冊',''),
('d59g10f0jt29','職原抄','日本正保二年小嶋市郎右衞門刊本','刻本',1645,'正保','小嶋市郎右衞門',[(NDL,'R100000002-I000007297530')],'2卷1冊',''),
]
TODAY='2026-11-15'
ids=mintid.mint('Book','wake-b',len(I)) if APPLY else ['dry%07d'%i for i in range(len(I))]
led=open(os.path.join(HERE,'ledger.tsv'),'a',encoding='utf-8');files=[]
for it,bid in zip(I,ids):
    wid,title,ed,et,y,reign,pub,hs,ext,link=it
    d={'schema_version':1,'type':'book','id':bid,'title':title,'work_id':wid,'edition':ed,'edition_type':et,
       'dating':{'era':'日本','reign':reign,'year':y,'certainty':'attested','source':'catalog','basis':'NDL Search 著錄刊年（%d）'%y}}
    if pub: d['publication_info']={'details':'刊刻者：'+pub}
    d['provenance']=[{'institution':i,'source':'NDL Search https://ndlsearch.ndl.go.jp/books/'+r} for i,r in hs]
    d['description']={'text':'《%s》，%s。%s據NDL Search著錄。'%(title,ed,(ext+'。') if ext else ''),'sources':['NDL Search '+'；'.join('https://ndlsearch.ndl.go.jp/books/'+r for _,r in hs)]}
    d['sources']=[{'id':'ndl-'+r.split('-')[-1].lower(),'name':'NDL Search','type':'url','details':'https://ndlsearch.ndl.go.jp/books/'+r} for _,r in hs]
    d['ai_note']='和刻本日本馆藏专项 wake-b（2026-11-15）新建：據NDL Search（含各館聚合記錄）著錄的題名、刊年、書肆定版本，未核原書。'+((' '+link+'。') if link else '')
    d['revision']='1.0.0';d['revised_at']=TODAY
    safe=re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]','',ed)[:24]
    f='Book/%s/%s/%s/%s-%s%s.json'%(bid[-3],bid[-2],bid[-1],bid,title,safe)
    files.append(f)
    if APPLY:
        p=os.path.join(BI,f);os.makedirs(os.path.dirname(p),exist_ok=True)
        open(p,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
        for i,r in hs: led.write('\t'.join([bid,title,'新建',i,'https://ndlsearch.ndl.go.jp/books/'+r])+'\n')
print(len(files));open('/tmp/wb_new.txt','w').write('\n'.join(files))
