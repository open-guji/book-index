import json,pathlib,copy,gzip,hashlib
O=pathlib.Path(__file__).parent; A=json.loads((O/'records.json').read_text())
S={
 'sengrui':{'url':'https://authority.dila.edu.tw/person/search.php?aid=A001599','title':'DILA 人名規範 A001599 僧叡','support':'羅什弟子；釋僧叡傳；《智論》《十二門論》《中論》等序，與大小品及法華、維摩諸經序。'},
 'sengzhao':{'url':'https://authority.dila.edu.tw/person/search.php?aid=A001598','title':'DILA 人名規範 A001598 僧肇','support':'釋僧肇列為別名；東晉、後秦；物不遷、般若無知、不真空與注維摩詰等著述。'},
 'zhidun':{'url':'https://authority.dila.edu.tw/person/search.php?aid=A002205','title':'DILA 人名規範 A002205 支遁','support':'東晉；字道林；支道林為別名；注莊子逍遙遊。'},
 'qisong':{'url':'https://authority.dila.edu.tw/person/search.php?aid=A000821','title':'DILA 人名規範 A000821 契嵩','support':'北宋，字仲靈，自號潛子；輔教編、傳法正宗記、鐔津文集同屬此人。'},
 'zongle':{'url':'https://authority.dila.edu.tw/person/search.php?aid=A000581','title':'DILA 人名規範 A000581 宗泐','support':'季潭、全室；臨海；全室集及心經、金剛經注解。生卒數字內部存在1390/1391異文，本輪不據之改動原 dates。'},
 'jiaoran':{'url':'https://authority.dila.edu.tw/person/search.php?aid=A008833','title':'DILA 人名規範 A008833 皎然','support':'釋皎然、清晝等別名；唐，長城，詩式作者。'},
 'zhuhong':{'url':'https://authority.dila.edu.tw/person/search.php?aid=A001394','title':'DILA 人名規範 A001394 袾宏','support':'袾宏與雲棲祩宏、蓮池祩宏異寫；字佛慧號蓮池；1535—1615；往生集、禪關策進、阿彌陀經疏鈔、菩薩戒經義疏發隱等。'},
 'yijing':{'url':'https://heritage.bnf.fr/france-chine/zh-hans/yijing-635-713','title':'法國國家圖書館：义净 (635-713)','support':'大唐西域求法高僧傳、南海寄歸內法傳作者；金光明最勝王經譯者。籍貫此文用范陽，現行欄用齊州；本次保留原欄、另列待核。'},
 'xu':{'url':'https://www.cnxxk.com.cn/list_24/1115.html','title':'江陰市徐霞客研究會：比较不同版本的徐霞客传（陳錫良）','support':'比較墓誌、縣志與宗譜之弘祖/宏祖；振之為字，霞客為別號；江陰人；並說明清代弘字避諱。'},
 'chen':{'url':'https://www.shidianguji.com/zh/book/DZ0091/chapter/1k1uvbg7bfxu2','title':'《太上洞玄靈寶無量度人上品妙經注》卷上','support':'卷端署上陽子陳觀吾注；站點作者索引為元陳致虛；與庫內四庫提要致虛字觀吾、自號上陽子相互印證。'},
 'zhang':{'url':'https://zh.wikisource.org/wiki/明史/卷299','title':'《明史》卷二百九十九 張三丰傳','support':'名全一，一名君寶，三丰為號；遼東懿州人。僅確認人物異稱，非為所題著作真偽背書。'},
 'qiujun':{'url':'https://www.mem.gov.cn/jjz/xcjy/201712/t20171218_168566.shtml','title':'丘濬：可继堂中承德泽','support':'丘濬古籍亦作邱濬，明代瓊山人，字仲深。此證只支持明代兩名，不支持合入宋人著作。'},
 'mudan':{'url':'https://da.adm.thers.ac.jp/item/n004-20230901-06655','title':'名古屋大學藏《牡丹榮辱志》','support':'著者列宋丘璿；宋邱濬條可能另有形訛問題，絕不與明丘濬直接合併。'},
 'daoxing':{'url':'https://www.ss.ncu.edu.tw/~calin/scripture/t55/T55n2146.pdf','title':'《大隋眾經目錄》T2146','support':'檢索可見《道行經序》一卷釋僧叡，與本庫僧肇名下殘名「僧 」之抽取衝突，須回查原著錄。'}
}
for x in S.values():x['retrieved_at']='2026-10-22'
# id, keeper, losers, status, proof, notes
specs=[
('PRV-R001','hixhd2h9bhwb',['hixhjtdgfim8','hixhd2h9bksm'],'confirmed','sengrui','同一羅什譯場僧叡；姚秦是政權前綴、釋是僧人稱謂。hixhjtdgfim8 的大智論、中論等疑為原序文條誤抽正文標題；角色問題留獨立清單，不把僧叡改成龍樹。'),
('PRV-R002','hixhd2h9bhv5',['hixhd2h9bty4'],'confirmed','zhidun','釋支遁兩部書都題支道林；本名與字相合。晉人諸注與文集全部保留分別的 Work。'),
('PRV-R003','hixhd2h9bfbi',['hixhd2h9blnp','hixhd2h9boxu'],'confirmed','qisong','本名契嵩冠釋、僧產生三條；五個關聯 Work 的著錄與規範庫著述相符。'),
('PRV-R004','hixhd2h9btx1',['hixhd2h9bkiz'],'confirmed','zongle','全室、季潭同人；全室外集及西遊集與心經金剛經注均吻合。保留原 dates，不混淆作品全集與節選。'),
('PRV-R005','hixhd2h9bsrm',['hixhd2h9btzv'],'confirmed','yijing','唐義淨/釋義淨，求法高僧傳、南海寄歸內法傳與金光明最勝王經構成一致的著述集合；保持撰與譯不同角色。'),
('PRV-R006','hixhd2h9bg93',['hixhd2h9bnng'],'confirmed','jiaoran','唐詩僧釋皎然即皎然，詩集及尋陸鴻漸不遇與杼山集、詩式等相合。'),
('PRV-R007','hixhd2h9bej6',['hixhd2h9bqle'],'confirmed','xu','徐弘祖與徐宏祖為避諱異寫；字振之、號霞客、江陰籍及遊記一致。外部 CBDB 有兩 ID，不據 ID 一致判同人。'),
('PRV-R008','hixhd2h9bf92',['hixhd2h9buc4'],'confirmed','chen','陳觀吾為姓加字；四庫提要明言致虛字觀吾，自號上陽子；度人經卷端同署上陽子陳觀吾注。'),
('PRV-R009','hixi5fivkq3j',['hixhd2h9bkj6','hixhgyrw4xtf','hixi8us1ybhp'],'confirmed','zhuhong','袾/祩字異寫及釋前綴；庫內千頃堂書目明言字佛慧、別號蓮池；全組30部作品的作者著錄一致。保留 CBDB 34791 基線，700411記為待核外部重號，非新確認其映射。'),
('PRV-R010','hixhgyrw4vmm',['hixhd2h9bgnz'],'confirmed','zhang','張全一與張三丰為本名及號；明史藝文志金丹直指條本就署張三丰，與同列金丹祕旨互證。兩個 CBDB/Wikidata ID 衝突不作同人依據，保留 keeper 映射、其他原值入合併備註待外部消歧。'),
('PRV-R011','hixhd2h9be7k',['hixhd2h9be1h'],'open','qiujun','明代兩名本可相合，但 keeper 混入三條宋丘濬太乙書；另《邱海二公文集合編》作者標清。先分清著作作者/編者及宋人掛接，再落地合併。'),
('PRV-R012','hixhd2h9bixi',['hixhjtdcdfk4'],'open','sengzhao','人物異稱證據充分；但 keeper 名下 d59f27vzh4oz《道行經序》只剩原名「僧 」且隋目作僧叡，先核此錯掛，避免把污染延續到新主條。'),
('PRV-R013','hixhd2h9be7k',['hixi8us1ybgl'],'separate','mudan','宋代《牡丹榮辱志》責任者不能與明代文莊公相合；宋條可能是丘璿等形訛，另案核正。共享上海圖書館人物 URI 不足為同人證。')]
ignore={'id','schema_version','type','subtype','revision','updated_at','revised_at','merged_into'}
union={'alt_names','merged_in','merge_history','sources','suppressed_fields','todo'}
def unique(xs):
 out=[]
 for x in xs:
  if x not in out:out.append(x)
 return out
cases=[]
for cid,k,ls,status,src,why in specs:
 ids=[k]+ls;ds=[A[i]['record'] for i in ids];keeper=ds[0];out={};fd={};archive=[]
 for f in sorted(set().union(*(d.keys() for d in ds))-ignore):
  vals=[{'id':i,'value':copy.deepcopy(d[f])} for i,d in zip(ids,ds) if f in d];u=unique([x['value'] for x in vals]);selected=copy.deepcopy(keeper.get(f,u[0]));policy='retain_keeper' if f in keeper else 'copy_nonconflicting_loser'
  if f in union:
   selected=unique([x for v in u for x in (v if isinstance(v,list) else [v])]);policy='stable_union'
  elif f=='ai_note':selected='\n\n'.join('[來源 '+i+'] '+d[f] for i,d in zip(ids,ds) if d.get(f));policy='preserve_attributed_notes'
  elif f.endswith('_basis'):
   selected='\n'.join(str(x) for x in u);policy='preserve_attributed_basis_values'
  elif f=='description':
   selected={};texts=unique([v.get('text','') for v in u if isinstance(v,dict) and v.get('text')]);sources=unique([z for v in u if isinstance(v,dict) for z in v.get('sources',[])])
   if texts:selected['text']='\n'.join(texts)
   if sources:selected['sources']=sources
   policy='union_description_and_sources'
  elif len(u)>1:
   archive.append({'field':f,'values':vals,'selected':selected});policy='retain_keeper_and_archive_all_alternatives'
  out[f]=selected;fd[f]={'action':policy,'selected':selected,'original_values':vals,'reason':'字段原值全部保存在 records.json；非衝突資訊保留到 canonical；衝突不擅自聲稱外部權威ID等價。'}
 # Extra names only classify what the evidence establishes; all original alt names retained.
 alts=out.get('alt_names',[])
 for i in ls:
  nm=A[i]['record']['primary_name']
  if nm!=keeper['primary_name'] and not any(isinstance(x,dict) and x.get('name')==nm for x in alts):alts.append({'name':nm,'type':'避諱' if cid=='PRV-R007' else '別名','note':why})
 if cid=='PRV-R009':
  for n,t in [('佛慧','字'),('蓮池','號')]:
   if not any(isinstance(x,dict) and x.get('name')==n for x in alts):alts.append({'name':n,'type':t,'note':'DILA A001394；千頃堂書目竹窗隨筆條。'})
 if cid=='PRV-R010':
  for x in alts:
   if isinstance(x,dict) and x.get('name')=='全一':x['type']='別名';x['note']='《明史》卷299作名全一；原紀錄「字」類型不沿用。'
 out['alt_names']=alts
 note='2026-10-22 expanded duplicate audit '+cid+'：'+why+' 證據：'+S[src]['url']
 if archive:note+=' 合併前衝突原值存檔：'+json.dumps(archive,ensure_ascii=False)
 out['ai_note']=out.get('ai_note','')+'\n\n'+note
 # preserve review conservatively: no human-reviewed status is fabricated.
 if any(d.get('review',{}).get('status')=='unreviewed' for d in ds):out['review']={'status':'unreviewed'}
 # Legacy sparse entity may omit required subtype; integration must set it.
 out['subtype']='people'
 c={'case_id':cid,'cluster_id':cid,'type':'Entity','status':status,'keeper':k,'losers':ls,'why':why,'evidence':[S[src]],'records':[{'id':i,'path':A[i]['path'],'sha256':A[i]['sha256'],'primary_name':A[i]['record']['primary_name']} for i in ids],'related_work_ids':unique([w['record']['id'] for i in ids for w in A[i]['works']]),'work_review':{'coverage':'all current live Work.authors[].entity_id references scanned','count':sum(len(A[i]['works']) for i in ids),'snapshots':'records.json'},'field_decisions':fd}
 if status=='confirmed':
  # Integration appends fresh tombstones after stable history union; never overwrite those additions.
  for managed in ['merged_in','merge_history','sources','suppressed_fields']:out.pop(managed,None)
  for field,value in out.items():
   fd.setdefault(field,{'action':'explicit_evidence_addition','original_values':[],'reason':why})['selected']=value
  c['machine_decision']={'field_overrides':out,'field_delete':[],'why':why}
 else:c['apply_blockers']=[why]
 if cid=='PRV-R007':c['metadata_caveats']=['birth=1586 是兩條相同既有值，西曆1587/農曆1586換算未在此輪重校。','cbdb_id 129892/62822 不同；保留 keeper 基線並把 loser 值記入 ai_note，不把外部ID相等作證。']
 if cid=='PRV-R004':c['metadata_caveats']=['DILA 卒年欄與引文內有1390/1391差異，原dates=1391原樣保留待考。']
 if cid=='PRV-R005':c['metadata_caveats']=['籍貫原值齊州與BNF范陽不同，此輪未更動原有齊州及其CBDB依據。']
 cases.append(c)
(O/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
(O/'sources.json').write_text(json.dumps(S,ensure_ascii=False,indent=2)+'\n')
with gzip.open(O/'original-records.json.gz','wt',encoding='utf8') as f:json.dump(A,f,ensure_ascii=False)
counts={s:sum(c['status']==s for c in cases) for s in ['confirmed','open','separate']}
(O/'stats.json').write_text(json.dumps({'base':'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca','counts':counts,'confirmed_losers':sum(len(c['losers']) for c in cases if c['status']=='confirmed'),'entity_snapshots':len(A),'work_snapshots':sum(len(v['works']) for v in A.values()),'confirmed_related_works':len(set(w for c in cases if c['status']=='confirmed' for w in c['related_work_ids']))},indent=2)+'\n')
print(counts)
