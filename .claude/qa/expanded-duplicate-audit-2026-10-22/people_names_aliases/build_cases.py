from pathlib import Path
import json,copy,collections,hashlib
D=Path(__file__).parent
E=json.loads((D/'entity-snapshots.json').read_text());R=json.loads((D/'references.json').read_text());W=json.loads((D/'work-snapshots.json').read_text()); names={v['record']['primary_name']:k for k,v in E.items()}
def source(name,url,finding):return {'name':name,'url':url,'finding':finding,'accessed':'2026-10-22'}
configs=[
 ('吳任臣',['吳志伊'],'志伊','字',['d59f2nv2ckjk','d59f2nbcu5tt'],'《經義考》原文「任臣字志伊仁和人」；《續字彙補》同條兩種著錄分別題吳志伊、吳任臣。',source('CiNii 呉任臣著者標目','https://ge.nii.ac.jp/author/DA07941710','同一著者標目收吳任臣著作以及署呉志伊註的山海經。')),
 ('金人瑞',['金聖嘆','金聖歎'],None,None,['d59fsigaskjk','d59fs7r49hj5','d59f2mxz6znl'],'三條均為清初唱經堂、貫華堂文評家；兩側《西廂記》評點以及詩文集相合。',source('CiNii 金聖嘆著者標目','https://ge.nii.ac.jp/author/DA00811615','著者異名列金人瑞；第六才子書責任者金人瑞歸此標目。')),
 ('李寶嘉',['李伯元'],'伯元','字',['d59f2mpqys5c','d59frypt41e0','d59fryr8m70n'],'《文明小史》原始書目直載「寶嘉字伯元」；別條所繫庚子國變彈詞及醒世緣為晚清李伯元作品。',source('教育部重編國語辭典修訂本 李寶嘉','https://pedia.cloud.edu.tw/Entry/Detail?title=%E6%9D%8E%E5%AF%B6%E5%98%89','李寶嘉字伯元，號南亭亭長；生卒1867–1906。')),
 ('范梈',['范德機'],'德機','字',['d59f2gkorj0h','d59f2goc6fpc'],'《木天禁語》提要直載「德機，范梈字也」；同條為舊題，合人不改作品真偽判斷。',source('CiNii 范徳機詩集','https://ci.nii.ac.jp/ncid/BA56525272','范徳機詩集作者作元范梈。')),
 ('劉知幾',['劉子玄'],'子玄','字',['d59f28jau9du','d59f28kqnnk3','d59fxt06migw'],'《史通》提要直載「子玄本名知幾，避明皇嫌名，以字行」；劉子玄條繫唐詩及文集，非近世同名人物。',source('臺北孔廟 歷代儒者 劉知幾','https://www.tctcc.taipei/zh-tw/C/sage/confucian/10%7C0/89.htm?22=','劉知幾字子玄，避李隆基名諱後以字行。')),
 ('李攀龍',['李于鱗'],'于鱗','字',['d59f6efsaepu','d59f2nfvgwzm','d59f6endf210'],'《千頃堂書目》李攀龍滄溟集原文「字于鱗」；李于鱗的古今詩刪、唐詩選與李攀龍名下著錄相合。',source('濟寧市自然資源和規劃局 微山湖古詩詞集錦','https://nrp.jining.gov.cn/art/2018/12/20/art_60670_2559180.html','李攀龍字于鱗，號滄溟，歷城人。')),
 ('惲格',['惲壽平'],None,None,['d59fs7ui01dv','d59fsggapxq8'],'《南田詩鈔》同條分別著錄惲格、惲壽平；故宮人物詞條明載又名格，南田畫跋與南田詩稿相合。',source('故宮博物院 惲壽平','https://www.dpm.org.cn/lemmas/240428.html','惲壽平又名格，字正叔，號南田，1633–1690，武進人。')),
 ('程大約',['程君房'],'君房','字',['d59f2nk8sikj','d59f6etv7sw5'],'《程氏墨苑》同條已記兩稱與「字幼博，又字君房」；此是人物重出非另一位制墨家。',source('故宮博物院 程大約','https://www.dpm.org.cn/lemmas/244028.html','程大約字幼博，別字君房；現條君房類型號應改字。')),
 ('夏侯尚玄',['夏侯文卿'],'文卿','字',['d59f2gctnabk','d59f2gezom4i','d59f2glnq3uo'],'《經義考》原孟條「元華亭夏侯尚&KR0975;文卿撰别字石嵓」；元史藝文志文卿名下原孟與中庸管見、華亭籍貫吻合，Entity亦有文卿字。',None),
]
cases=[]
for i,(kn,lns,alias,alias_type,proof,why,ext) in enumerate(configs,1):
 k=names[kn];ls=[names[n] for n in lns];members=[k]+ls;kd=E[k]['record'];fields={key:copy.deepcopy(val) for key,val in kd.items() if key not in {'id','type','schema_version','subtype','revision','revised_at','updated_at','ai_note','merged_in','merge_history'}}
 alt=fields.setdefault('alt_names',[])
 if alias:
  for a in alt:
   if isinstance(a,dict) and a.get('name')==alias:a['type']=alias_type
 for ln in lns:
  if not any(isinstance(a,dict) and a.get('name')==ln for a in alt):alt.append({'name':ln,'type':'別稱','note':('姓連字之著錄稱呼；字為'+alias) if alias else '同一人物的通行稱呼或異體著錄；見本次核驗依據。'})
 if kn=='李寶嘉':
  for a in alt:
   if a.get('name')=='南亭亭長':a['type']='號'
 desc=fields.setdefault('description',{});sources=desc.setdefault('sources',[])
 for l in ls:
  for s in E[l]['record'].get('description',{}).get('sources',[]):
   if s not in sources:sources.append(copy.deepcopy(s))
 if ext:
  s={'name':ext['name'],'type':'url','details':ext['url']}
  if s not in sources:sources.append(s)
 if not desc:fields.pop('description',None)
 ids=sorted(set(v for m in members for v in R[m]));losskeys=sorted(set().union(*(E[l]['record'].keys() for l in ls)))
 policy=[]
 for key in losskeys:
  if key in ['id','type','schema_version','subtype','primary_name','revision','revised_at','updated_at']:how='identity/tombstone or revision handled by merge engine; original snapshot retained'
  elif key in ['ai_note','merged_in','merge_history','sources','suppressed_fields']:how='union/preserve with original owner attribution, never overwrite history'
  elif key=='description':how='union description.sources into keeper; preserve keeper text; loser snapshots retained'
  elif key=='review':how='keep existing keeper review status; loser unreviewed is not an approval and must not become human-reviewed'
  elif key=='external_ids':how='retain keeper verified-existing identifiers; loser cbdb_match=none markers do not override keeper'
  else:how='retain keeper field including basis; loser full original archived; no conflicting new biographical value imported'
  policy.append({'field':key,'decision':how})
 c={'case_id':f'PNA-R{i:03}','status':'confirmed','type':'Entity','label':' / '.join([kn]+lns),'keeper':k,'losers':ls,'paths':{m:E[m]['path'] for m in members},'sha256':{m:E[m]['sha256'] for m in members},'why':why,'evidence_refs':[{'work_id':wid,'path':W[wid]['path'],'sha256':W[wid]['sha256'],'indexed_by':W[wid]['record'].get('indexed_by',[])} for wid in proof],'external_evidence':[] if ext is None else [ext],'related_record_ids':ids,'related_counts':dict(collections.Counter(W[x]['record']['type'] for x in ids)),'machine_decision':{'field_overrides':fields,'field_delete':[]},'field_decisions':policy,'reference_policy':'Redirect every live authors[].entity_id in Work/Book/Collection; retain author name and role unless separately adjudicated. Never globally replace historical IDs or source prose. Keep loser tombstones and complete history.','caveats':[]}
 if kn=='金人瑞':c['caveats'].append('現有生年1610與部分外部來源1608不同；本輪僅判同一人，不借合併重裁生年。聖嘆是字/法號/筆名的細分有異說，保留既有分類，新增全稱作別稱。')
 if kn=='惲格':c['caveats'].append('保留原 keeper 的既有大量別名，並不表示本輪逐項證實；本輪只新增全稱惲壽平同人關係。')
 if kn=='范梈':c['caveats'].append('木天禁語與詩學禁臠著錄為舊題；現 authors.role=撰 精度不足，另記角色清理，不把托名當作異人，也不把同人當作同書證明。')
 if kn=='程大約':c['caveats'].append('d59fy11btb0h 附中山狼傳舊題謝枋得，導致 work 目前 period=song；這是合輯角色/斷代問題，不是另一個程大約。d59f2nk8sikj 已同時列兩稱，改繫後需在保留來源的前提下消除同人同役重複 authors。')
 cases.append(c)
cs=['蔡卞','蔡元度'];members=[names[n] for n in cs]
cases.append({'case_id':'PNA-R010','status':'open','type':'Entity','label':' / '.join(cs),'keeper':members[0],'losers':[members[1]],'paths':{m:E[m]['path'] for m in members},'sha256':{m:E[m]['sha256'] for m in members},'why':'名與字關係已證明；但 keeper《毛詩名物解》d59f2hrbldz4 宋史著錄 summary 尾連董逌。須先對照宋史藝文志原段，判定只是下一條尾文或確有混書，避免將污染打包。','evidence_refs':[{'work_id':'d59f2hrbldz4','path':W['d59f2hrbldz4']['path'],'indexed_by':W['d59f2hrbldz4']['record']['indexed_by']}],'apply_blocker':'先釐清《宋史藝文志》董逌尾文與作品範圍。','related_record_ids':sorted(set(v for m in members for v in R[m]))})
(D/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
counts=collections.Counter(x['status'] for x in cases);counts['confirmed_losers']=sum(len(x['losers']) for x in cases if x['status']=='confirmed');counts['referenced_records']=len(W)
(D/'stats.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n')
lines=['# 人物本名、字與號恢復核查（2026-10-22）','','基線：bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca。重新讀取原生 JSON、索引著錄與權威公開資料；未使用丟失報告作證據。原生資料與 Git 未改。','','本批確認 9 組、10 個被併 ID；另 1 組待核。21 條 Entity、148 條真正 authors 引用已保存完整快照及 SHA256（其中同一條可被兩 Entity 同時引用）。','','| 編號 | 人物組 | 判定 | 引用數 |','|---|---|---|---|']
for c in cases:lines.append('| '+c['case_id']+' | '+c['label']+' | '+c['status']+' | '+str(len(c['related_record_ids']))+' |')
lines+=['','## 執行要點','','- 用 cases.json 的 machine_decision.field_overrides；其他逐欄取捨見 field_decisions。不要用通用「空值補入」覆蓋人工策略。','- 李寶嘉的伯元改為字、南亭亭長改為號；劉知幾的子玄改為字；程大約的君房由號改為字。姓連字的完整稱呼使用別稱，避免把姓混入表字。','- 所有被併者保留墓碑；來源、舊 ai_note 與 merged_in 必須保留。所有 Work、Book、Collection 的真實作者引用都需重指，不能只處理 Work。','- 范梈的托名作品不得因此判真；程氏墨苑混合附錄角色及重複 authors、金人瑞生年異說另記 caveats，不能靜默消失。','- 蔡卞／蔡元度只確認人物關係，暫不執行整體合併，待核董逌尾文。','','## 檔案','','- entity-snapshots.json：21 條實體原始快照。','- work-snapshots.json：真實作者引用的 Work/Book/Collection 原始快照，檔名沿用 work 但 type 以記錄為準。','- references.json：entity_id 到實際引用記錄 ID。','- cases.json：逐案證據、來源連結、ID、hash、字段覆寫及待核理由。','- candidate-queue.json：新掃出的相近稱呼候選，僅為候選，並非合併清單。']
(D/'report.md').write_text('\n'.join(lines)+'\n')
print(counts)
