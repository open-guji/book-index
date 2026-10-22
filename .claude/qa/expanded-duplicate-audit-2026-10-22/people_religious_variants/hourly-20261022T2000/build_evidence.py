from pathlib import Path
import json,sqlite3,hashlib,subprocess,copy
OUT=Path(__file__).parent
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
c=sqlite3.connect('file:/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row
manifest=json.loads(c.execute("select value from metadata where key='manifest'").fetchone()[0]);assert manifest['base']==BASE and not manifest['errors']
def save(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def source(sid,title,url,pointer,excerpt):return dict(source_id=sid,title=title,url=url,pointer=pointer,excerpt=excerpt,accessed='2026-10-22',kind='primary_text_transcription',excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest())
sources=[
source('S01','舊唐書卷八','https://zh.wikisource.org/wiki/舊唐書/卷8','本紀第八開頭；web turn51view0 L146','玄宗至道大聖大明孝皇帝諱隆基，睿宗第三子也'),
source('S02','孝經注疏四庫提要','https://zh.wikisource.org/wiki/孝經注疏_(四庫全書本)','提要；web turn48view1 L143','唐元宗御注宋郉昺疏；趙明誠金石錄載明皇注孝經四卷'),
source('S03','仁宗睿皇帝實錄卷一','https://zh.wikisource.org/wiki/仁宗睿皇帝實錄/卷1','首段及味餘書室；web turn44view4 L114、119','仁宗受天興運敷化綏猷崇文經武孝恭勤儉端敏英哲睿皇帝，諱顒琰'),
source('S04','元史卷十八','https://zh.wikisource.org/wiki/元史/卷018','成宗本紀；web turn44view0 L126','成宗欽明廣孝皇帝，諱鐵穆耳，世祖之孫，裕宗真金第三子也'),
source('S05','晚晴簃詩匯卷一百九十五','https://zh.wikisource.org/wiki/晚晴簃詩匯/卷一百九十五','今釋小傳；web turn44view6 L158','今釋，字澹歸，杭州人，本姓金，名堡，字道隱，號衛公。'),
source('S06','長慶宗寶獨禪師語錄','https://higrid.net/show/ancient/153-366.html','卷第一署名；web turn50view0 L34–35','長慶宗寶獨禪師語錄卷第一；丹霞法孫　今釋　重編'),
source('S07','梁高僧傳卷七','https://zh.wikisource.org/wiki/梁高僧傳/卷七','宋京師東安寺釋慧嚴；web turn48view0 L182','釋慧嚴，姓范，豫州人。'),
source('S08','古今圖書集成經籍典432','https://zh.wikisource.org/wiki/欽定古今圖書集成/理學彙編/經籍典/第432卷','隋書經籍志道家及唐書藝文志；web turn48view3 L180、247','《老子道德經》二卷，釋惠嚴注'),
source('S09','宋高僧傳卷二','https://zh.wikisource.org/wiki/宋高僧傳/卷02','唐洛京大遍空寺實叉難陀傳；web turn44view5 L193','釋實叉難陀，一雲施乞叉難陀，華言學喜，蔥嶺北于闐人也。'),
source('S10','百千印陀羅尼經','https://zh.wikisource.org/wiki/百千印陀羅尼經_(版本一)','T1369a 卷首；web turn48view2 L111–113','百千印陀羅尼經一卷；大周三藏實叉難陀奉制譯'),
source('S11','寶髻經四法憂波提舍','https://zh.wikisource.org/wiki/寶髻經四法憂波提舍','翻譯記及卷首；web turn44view1 L124、129–131','天親菩薩造；元魏烏萇國三藏毘目智仙譯'),
source('S12','開元釋教錄卷十二下','https://zh.wikisource.org/wiki/開元釋教録_(四庫全書本)/卷12下','三具足經論及轉法輪經論；web turn50view2 L310–311','諸録皆云菩提留支譯者誤也今依序記為正'),
source('S13','古今圖書集成經籍典321','https://zh.wikisource.org/wiki/欽定古今圖書集成/理學彙編/經籍典/第321卷','經義考列目；web turn50view1 L1472、turn51view1 L1179','高拱《大學直講》一卷；高拱《中庸直講》一卷'),
source('S14','四庫總目日進直講提要原頁轉錄','https://zh.wikisource.org/wiki/Page:文淵閣四庫全書_0001冊.djvu/803','日進直講五卷；web turn19search3/turn44view3','明高拱撰；嘉靖三十一年拱以翰林編修與檢討陳以勤同爲裕王講官')]
# These are short extraction excerpts; ellipsis/semicolon separate noncontinuous clauses. No claim of whole-web-page archival.
specs=[
('001','李隆基／明皇',['PRV-B-C0309'],'confirmed',['S01','S02'],'原典以玄宗諱隆基、孝經御注與明皇注互證；僅存作者明皇的一條Work題名與之相合。','原生寫入前完成全型別/草稿/promotions/book-text引用查核及實際寫後驗證。'),
('002','清仁宗／愛新覺羅·顒琰',['PRV-B-C12534'],'confirmed',['S03'],'實錄直接記仁宗諱顒琰；十二個所繫Work包括仁宗御製詩、味餘書室詩文，與生平記載相容。','保留keeper兩條既有merged_in；原諡號受天興敷化漏運字，另作有來源的訛名/校正，不能默默覆蓋。'),
('003','成宗／鐵穆耳',['PRV-B-C12705'],'open',['S04'],'元成宗確為鐵穆耳，但成宗Entity源自題名成宗實録錯切為作者；已修正Work的ai_note明示此條失引用。這是壞作者殘條，非一般帝王雙條。','核原始千頃堂書目頁、舊Work墓碑與歷史merge_history；完整入邊排查後決定retired而非自動merged_into，不能恢復成宗為作者。'),
('004','金堡／明清兩釋今釋',['PRV-B-C2987','PRV-B-C2988'],'confirmed',['S05','S06'],'小傳明言今釋俗姓名堡並載遍行堂集；明標記條建檔所據長慶宗寶禪師語錄原署丹霞法孫今釋重編，與同一丹霞僧吻合；明清跨代本身不構成異人。','原生前逐字段保留兩loser朝代依據、CBDB未匹配狀態、ai_note及上圖來源；明清period不能僅機械覆蓋。keeper卒年1679與後續年譜線索有出入，未由本輪原典定年，不順手改。'),
('005','釋惠嚴／釋慧嚴',['PRV-B-C12162'],'open',['S07','S08'],'早期目錄確有惠嚴老子注，梁傳確有劉宋豫州范氏慧嚴；但現惠嚴Entity帶金谿籍貫、文惠大師號及CBDB53643，不能在未辨污染前全量傳遞給南本涅槃經編者。','查CBDB53643原紀錄與文惠大師來源；用經錄/高僧傳明確連接老子注與南本涅槃經治定者；先定污染字段與保留歸檔位置，再決定並條。'),
('006','釋學喜／釋實叉難陀',['PRV-B-C12197'],'confirmed',['S09','S10'],'宋高僧傳直接列華言學喜；現keeper華嚴經譯者與loser建檔百千印陀羅尼經原署實叉難陀一致。','native_place吐蕃諸部與原傳于闐不一致；外部ID與籍貫需單獨審查，不能將機讀值當已核實。保留兩條來源/未匹配歷史，任何校正署源。'),
('007','毗目智仙／釋毘目智仙',['PRV-B-C12761'],'confirmed',['S11','S12'],'寶髻經翻譯記與開元錄在同一興和三年鄴城金華寺譯事列毗/毘目智仙；三具足、寶髻、轉法輪均在該譯事譜系，支持異體同人。','北魏標記出自補魏書概括，興和三年實為東魏；三Work責任role撰與天親造/智仙譯衝突，另作歸屬修正。開元錄明指菩提留支舊錄誤題，不把此人、瞿曇流支、魏菩提留支或唐菩提流志混併。'),
('008','高拱／髙拱',['PRV-B-C4927'],'confirmed',['S13','S14'],'異體候選非僅字形：髙拱實際作者邊三書，其中大學直講、中庸直講被原典目錄明確署高拱；四庫日進直講提要定位裕王講官。','保留loser period_basis及完整建檔ai_note；keeper生年1510與所繫Work說明1513衝突，另核生年，不將歷史說明改為一致。')]
candidates=json.loads((OUT.parent/'broad-20261022/candidates.json').read_text());bycid={v['candidate_id']:v for v in candidates}
allids=set();cases=[]
for num,label,cids,status,ss,decision,gate in specs:
 cs=[bycid[k] for k in cids];assert all(not v['prior_case_ids'] for v in cs)
 ids=sorted(set(i for v in cs for i in v['ids']));allids.update(ids)
 cases.append(dict(case_id='PRV-H2000-'+num,group=label,type='people',status=status,new_case=True,candidate_ids=cids,ids=ids,source_ids=ss,decision=decision,remaining_gates=[gate,'Fresh-main hash preconditions; complete native types and promotions plus draft and full nonempty 16-shard book-text; lossless person field ledger; actual changed-path schema/check_v2/classification/builder and independent audit.'],native_merge_count=0))
# Only read Entity/Work coverage represented by this manifest. Exact JSON string pointers separate active references from text/history.
rows={};refs=[]
def walk(o,targets,p=''):
 if isinstance(o,dict):
  for k,v in o.items():yield from walk(v,targets,p+'/'+k)
 elif isinstance(o,list):
  for j,v in enumerate(o):yield from walk(v,targets,p+'/'+str(j))
 elif isinstance(o,str):
  if o in targets:yield(p,o,'exact')
  else:
   for i in targets:
    if i in o:yield(p,i,'embedded_text')
for i in allids:
 r=c.execute('select * from records where id=?',(i,)).fetchone();rows[i]=dict(r)
# one SQL read only scan, no statement about other repository types
for r in c.execute("select * from records where type='Work'"):
 if any(i in r['data'] for i in allids):
  d=json.loads(r['data']);hits=list(walk(d,allids));refs.append(dict(id=r['id'],name=r['name'],path=r['path'],inactive=bool(d.get('merged_into') or d.get('retired')),hits=[dict(pointer=p,target=i,match=m) for p,i,m in hits]));rows[r['id']]=dict(r)
validation=[]
for r in rows.values():
 raw=r['data'].encode();sha=hashlib.sha256(raw).hexdigest();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert sha==r['sha256'] and blob==r['blob_sha'],r['id']
 tree=subprocess.run(['git','ls-tree',BASE,'--',r['path']],check=True,capture_output=True,text=True).stdout.split()[2];assert tree==blob
 r['data']=json.loads(r['data']);validation.append(dict(id=r['id'],blob_matches_fixed_main=True,sha256_matches=True))
for ca in cases:
 ca['records']=[{k:rows[i][k] for k in ['id','name','path','blob_sha','sha256']} for i in ca['ids']]
 ca['known_work_refs']=[v for v in refs if any(h['target'] in ca['ids'] for h in v['hits'])]
save('cases.json',cases);save('sources.json',sources);save('source-snapshots.json',{'base':BASE,'source_manifest':manifest,'records':list(rows.values())});save('known-references.json',{'scope':'Read-only broad-current.sqlite Work records only; exact pointers and embedded text distinguished; NOT cross-repository validation','references':refs})
rules=[]
for p in ['schema/common.md','schema/entity/_common.md','.claude/qa/entity_merge.py','scripts/audit-merge-ledger.py']:
 raw=subprocess.run(['git','show',BASE+':'+p],check=True,capture_output=True).stdout
 rules.append(dict(path=p,sha256=hashlib.sha256(raw).hexdigest(),blob_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()))
save('validation.json',dict(base=BASE,new_groups=len(cases),confirmed=sum(v['status']=='confirmed' for v in cases),separate=0,open=sum(v['status']=='open' for v in cases),native_merge_count=0,source_snapshots_verified=validation,rules=rules,full_crossrepo_validation=False,official_native_write_checks='not_run_no_native_changes'))
# Safest future candidate: original keeper fields all retained byte-for-value except knowledge event/source additions.
kid='hixhd2f8wam8';lid='hixhd2h9bn9s';k=copy.deepcopy(rows[kid]['data']);l=rows[lid]['data'];after=copy.deepcopy(k)
for s in sources[:2]:after['description']['sources'].append(dict(name=s['title'],type='url',details=s['url']))
after['ai_note']+='\n\n2026-10-22 研究候選（未執行）：據《舊唐書》卷八與《孝經注疏》四庫提要，明皇所繫《孝經明皇注》之責任者即玄宗李隆基。本段僅供未來執行另定日期；舊建檔數字及既有並條史完整保留。'
after['merged_in'].append(dict(id=lid,primary_name=l['primary_name'],at='EXECUTION_DATE_REQUIRED',by='EXECUTOR_REQUIRED',rule='帝王別稱與所繫孝經注原典互證',why='PRV-H2000-001；S01/S02；身份確認不等於全庫門檻已完成'))
after['revision']='1.1.0';after['revised_at']='EXECUTION_DATE_REQUIRED'
tomb={q:l[q] for q in ['schema_version','id','type','subtype','primary_name']};tomb.update(merged_into=kid,revision='1.1.0',revised_at='EXECUTION_DATE_REQUIRED')
ledger=[]
for owner,before,proposal in [(kid,k,after),(lid,l,tomb)]:
 for field,val in before.items():
  disposition='preserved_exact' if proposal.get(field)==val else ('versioned_management_value_archived' if field in ['revision','revised_at','updated_at'] else 'appended_without_overwrite')
  ledger.append(dict(entity_id=owner,field=field,before=val,after=proposal.get(field),disposition=disposition,archive='source-snapshots.json'))
assert all(after.get(f)==v for f,v in k.items() if f not in ['description','ai_note','merged_in','revision','revised_at'])
assert after['ai_note'].startswith(k['ai_note']) and after['merged_in'][:len(k['merged_in'])]==k['merged_in']
assert set(tomb)==set(['schema_version','id','type','subtype','primary_name','merged_into','revision','revised_at'])
save('field-retention-proposal.json',dict(base=BASE,case_id='PRV-H2000-001',executable=False,reason='No native write; execution date/executor placeholders intentionally invalid until preflight; not a ready-to-apply ledger',keeper=kid,losers=[lid],preconditions=[{k:rows[i][k] for k in ['id','path','blob_sha','sha256']} for i in [kid,lid]],keeper_candidate=after,loser_candidate=tomb,field_ledger=ledger,known_reference_edit=dict(work_id='d59f28n1djid',pointer='/authors/0/entity_id',before=lid,after=kid,preserve_fields=['name','role','source','dynasty','name_basis']),unresolved_gates=cases[0]['remaining_gates']))
print(json.dumps({'groups':len(cases),'confirmed':sum(v['status']=='confirmed' for v in cases),'open':sum(v['status']=='open' for v in cases),'snapshots':len(rows),'references':len(refs),'field_ledger_rows':len(ledger)},ensure_ascii=False))
