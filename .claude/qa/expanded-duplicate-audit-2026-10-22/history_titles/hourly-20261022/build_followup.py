import json, pathlib, hashlib, gzip, datetime
root=pathlib.Path(__file__).resolve().parents[5]
out=pathlib.Path(__file__).resolve().parent
lane=out.parent
old=json.loads((lane/'cases.json').read_text())
by={c['case_id']:c for c in old}
def readmembers(cid):
 result=[]
 for m in by[cid]['members']:
  p=root/m['path']; raw=p.read_bytes(); r=json.loads(raw)
  assert hashlib.sha256(raw).hexdigest()==m['sha256'], str(p)
  result.append({'id':r['id'],'path':m['path'],'sha256':m['sha256'],'record':r})
 return result
specs=[
 ('H-H001','H-X112','confirmed','國語補音：宋史條的林概為跨條斷行污染，非另一作者',
  '《古今圖書集成·經籍典》卷180明引宋志，將宋庠《國語補音》三卷與林概《辨國語》三卷分列。現行維基文庫宋史卷202的清單每行尾綴下一條作者；本庫抄錄《國語補音》三卷林概，恰切掉前行尾宋庠。四庫提要、直齋及總目均繫宋庠，另一條明列宋宋庠補葺、文淵閣四庫全書子目，無不同著作證據。文獻身份確認，執行前仍須污染修復和跨庫檢查。'),
 ('H-H002','H-X110','open','後渠雜識／後渠漫記：同叢書分列，別名括注不足消除範圍疑點',
  '重新取到東洋文庫搜尋摘要：說郛續第三卷著錄後渠漫記，第一三卷著錄後渠雜識；官網開頁轉維護通知。本庫雜識明記五朝小說子目且附別名漫記，漫記屬說郛續子目。這可能涉及摘編異文或混用別名，尚無兩篇正文起訖核對，維持open，不把搜索摘要當原本書影。'),
 ('H-H003','H-C042','open','正德大同府志／大同府志：嘉靖增修範圍與描述污染待辨',
  '兩條確指張欽十八卷，並有正德年號互證；但大同府志條記明正德刻嘉靖增修本，而另一條依四庫提要記正德癸酉所作四十門。尚未比較增修內容是否僅補刻，不能只按作者和卷數合併。另keeper description稱佚文見通典、水經注與本書目賴四庫以存，實際提要只是批評張欽未採古書地理記載，屬明確生成誤讀，合併前應另修。'),
 ('H-H004','H-C002','open','南鄭縣志／續修南鄭縣志：同年同修者但缺首卷與版本核對',
  '故宮來源條記郭鳳洲修、七卷、民國辛酉十年刊本；總目條記郭鳳洲柴守愚修劉定鐸等纂、七卷首一卷、民國十年刻本。同年同修者使其為強候選，但另有Book著錄民國十年鉛印本，現有著錄不明省題與首卷缺載機制。須核故宮故志003925-003931卷首及序跋，未憑簡題硬併。')]
cases=[]; snapshots={}
for caseid,cid,status,title,reason in specs:
 ms=readmembers(cid)
 for m in ms:snapshots[m['path']]=m['record']
 c={'case_id':caseid,'supersedes_case_id':cid,'type':'Work','status':status,'verdict':status,'review_depth':'source_fields_and_local_references_compared','title':title,'reason':reason,'members':ms,'implemented':False,'machine_decision':None,'next_steps':[]}
 if caseid=='H-H001':
  c.update(keeper='d59f2hswekua',losers=['d59fyfefz9c0'],merge_eligible=False)
  c['evidence']=[{'kind':'primary_compilation_transcription','url':'https://zh.wikisource.org/zh-hant/欽定古今圖書集成/理學彙編/經籍典/第180卷','locator':'行1415–1423（本次web抽取）','quote':'宋庠「《國語補音》三卷。」見宋志。……林概《辨國語》三卷。','retrieved_on':'2026-10-22'}, {'kind':'faulty_online_segmentation','url':'https://zh.wikisource.org/wiki/宋史/卷202','locator':'行745–748（本次web抽取）','quote':'《春秋文權》五卷魯有開／《春秋指微》十卷《國語音義》一卷宋庠／《國語補音》三卷林概／《辨國語》三卷崔表','assessment':'連續列尾為下一條作者，不能按單行末尾作者歸屬。'}]
  c['field_decisions']={'indexed_by':'全部原始著錄保留，不靜默改寫林概舊引文；在該條note寫明跨條斷行與正確歸屬，並添加可追溯的集成/直齋證據。','authors':'保留宋庠entity_id；role以四庫提要補葺為可核依據，不能將唐人舊音與宋庠補音視為同一層著作。','description':'重新撰短描述，區分唐人舊音基礎與宋庠增補三卷；不複製先前過長機械摘要。','Book':'只更新work_id，版本不合；先核993fzgxdkw異常刊印串接。','emendated_by':'本次AI判斷不是考證書，不冒充emendated_by；依schema使用note/ai_note及來源。'}
  c['apply_prerequisites']=['保持原索引引文，補充有據錯行說明及來源。','完成全部引用及book-text正文/整理本/輯佚檔核查。','核查Book 993fzgxdkw元至元杭州大普寧寺刻/影印微波榭叢書本的明顯跨版本串接。','重驗當前源hash、保留墓碑與來源歷史、重建官方索引、比較基線。']
  c['next_steps']=c['apply_prerequisites']
 elif caseid=='H-H002':
  c['evidence']=[{'kind':'official_catalog_search_snippet_only','url':'https://www.toyo-bunko.org/open/KansekiQueryResult10.php?ORDERBY1=&UNIT=20&andor=1&iPage=2363&iTotal=80860&navizonestart=237&searchtype=keyword&sw1=','quote':'V-5-A-12 説郛一百二十卷續四十六卷續𢎥第一三 後渠雜識 明崔銑','availability':'開頁轉maintenance.html，未取得原著錄頁；不可據此確定篇目內容。'},{'kind':'official_catalog_search_snippet_only','url':'https://www.lib.niigata-u.ac.jp/Kanseki/KansekiCat.html','quote':'後渠漫記 一卷 明崔銑撰','availability':'搜尋摘要可見，開頁抽取未成功定位該字串；作後續線索。'}]
  c['next_steps']=['取得說郛續第三、十三卷對應書影，逐條比對起訖文及條目覆蓋。','核五朝小說所收到底是漫記同本、選本或混題；著錄清崔銑的朝代錯誤另記，不據此創造清代同名人。']
 elif caseid=='H-H003':c['next_steps']=['比對正德本與嘉靖增修本目錄、序跋、正文增補。','修正四庫提要被轉述為佚文/存目唯一證據的description污染；保存原文快照。']
 else:c['next_steps']=['取故宮故志003925-003931書目原頁/卷首，核定是否續修南鄭縣志省題及首卷。','保留郭鳳洲、柴守愚、劉定鐸不同責任角色，分開刻本與鉛印本。']
 cases.append(c)
refs=[]
for fn in (out/'reference-paths.txt').read_text().splitlines():
 p=root/fn; raw=p.read_bytes(); r=json.loads(raw); snapshots[fn]=r
 refs.append({'path':fn,'sha256':hashlib.sha256(raw).hexdigest(),'id':r.get('id'),'type':r.get('type'),'work_id':r.get('work_id'),'title':r.get('title')})
for c in cases:
 ids={m['id'] for m in c['members']}
 c['book_references']=[r for r in refs if r['path'].startswith('Book/') and r['work_id'] in ids]
(out/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
with gzip.open(out/'original-and-reference-snapshots.json.gz','wt',encoding='utf-8') as f:json.dump(snapshots,f,ensure_ascii=False)
(out/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n')
checks=[]
for c in old:
 if c['status']=='confirmed':
  for id,path in c['paths'].items():
   actual=hashlib.sha256((root/path).read_bytes()).hexdigest();checks.append({'case_id':c['case_id'],'id':id,'matched':actual==c['sha256'][id]})
assert all(c['matched'] for c in checks)
(out/'validation.json').write_text(json.dumps({'checked_on':'2026-10-22','new_cases':4,'promoted_from_open_to_confirmed':1,'remaining_open_reviewed':3,'new_separate':0,'new_losers_proposed':1,'native_records_modified':0,'confirmed_not_execution_ready':1,'source_records_hash_checked':8,'existing_confirmed_hash_checks':checks,'reference_file_count':len(refs),'book_reference_count':sum(r['path'].startswith('Book/') for r in refs),'scope':'本次核验限定源hash与所列引用；未做全库schema或跨仓正文验证。'},ensure_ascii=False,indent=2)+'\n')
print('wrote',len(cases),'cases',len(refs),'references')
