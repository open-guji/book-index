import json,gzip,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
snap=json.load(open(OUT/'work-snapshots.json')); by={x['id']:x for x in snap}
books=json.load(gzip.open(OUT/'related-books.json.gz','rt'))
specs=[
('MR-H001','confirmed','辨中邊論頌 / 辯中邊論頌',['d59fxwbvtqtc','d59fyky6ark0'],'兩條原始總目均明載彌勒菩薩說、玄奘譯、一卷；keeper原始著錄已同時收辨/辯兩題，非僅依字形相似。8個Book著錄皆同一卷頌本，沒有世親釋文或其他譯者。','保留d59fxwbvtqtc及其舊merged_in，另一條的天竺署地資訊補入彌勒責任者；原書所稱「題」仍保留在author_info，不將托名判為歷史事實。',['https://cbetaonline.dila.edu.tw/T1601','https://cbetaonline.dila.edu.tw/en/T55n2148'],'zm0525'),
('MR-H002','open','佛說無畏授所問大乘經',['d59fy9elowld','d59fydyml4hs'],'雖題名與施護譯者相同，原始總目及Book確實分載三卷與二卷；二卷條jn374dand65ylyck未載版次館藏，無法判斷缺卷、另分卷或節本。additional_titles單字「問」是校字誤抽，不能當作獨立別名。','核jn374dand65ylyck原始catalog/書影與正文起訖；二卷Record與三卷T0331對讀。不要改Book二卷為三卷，也不要以正字處理掩蓋卷數疑點。',['https://cbetaonline.dila.edu.tw/T0331'],None),
('MR-H003','open','指南針 / 道書十二種',['d59fxyybfaww','d59fxx2sf4e9'],'總目括注指南針像別名，但實際館藏目錄證明該題也用作合編內部子組封面。CiNii BD04685234把指南針著錄為道書十二種第13冊，內含陰符經、敲爻歌、百字碑等；BB21525160亦明載只有其中一段封面題指南針。不能把括注全視為全書別名。','核遼寧嘉慶本8q7tt4nuyefddbyt與護國庵1819本pqc24ajtz8lzqmmj的總目/分冊，判定前者是子組還是整套；在此之前保留兩Work與兩Book。',['https://ci.nii.ac.jp/ncid/BD04685234','https://ci.nii.ac.jp/ncid/BB21525160'],None),
('MR-H004','confirmed','幼科醫學指南 / 幼科指南',['d59fxycg6txd','d59fxycjmfwh'],'總目四卷條明列幼科指南為別題，兩側原始責任者同為周震，並非只由標準化作者字段推定。5個Book沒有新增注者/編者/節本詞。裸題Book卷數未載應仍留空，不能據合人補成四卷。','保留四卷全題為主題；Book 993h9q8idc的contMap與題名行朝代不一致註記原樣保留。此案確認著作身份，不確認該本分卷/完帙。',['https://ctext.org/wiki.pl?if=gb&remap=gb&res=7338741'],'zm0389'),
('MR-H005','confirmed','叢桂堂集驗良方 / 叢桂山房集驗良方',['d59fxyr0wr28','d59fxyr0liip'],'原始總目明列兩題互名，兩側署同一叢桂堂居士輯。6個Book均同一方書，敏芝堂醫書四種是載體；本案不把整個醫書四種與該子書合併。裸題條的叢編分類是載體分類，不能據此生成另一著作。','保留叢桂堂集驗良方主題與別題；Book 993ho6wcg2保留one_side_empty責任者差異註記。無source.details的既有作者source原樣存檔，整合時依schema檢查，不能刪除來源。',['https://sxzygj.cn/sys-nd/42.html'],'zm0390')]
cases=[]
for cid,status,title,ids,reason,nextstep,urls,node in specs:
 recs=[by[i] for i in ids]
 c={'case_id':cid,'type':'Work','status':status,'title':title,'ids':ids,'reason':reason,'records':[{k:r[k] for k in ['id','path','sha256']} for r in recs],'evidence':[{'id':r['id'],'indexed_by':r['record'].get('indexed_by',[]),'ai_note':r['record'].get('ai_note','')} for r in recs],'related_book_ids':[b['id'] for b in books if b['record']['work_id'] in ids],'external_sources':urls,'next_step':nextstep,'applied':False}
 if status=='confirmed':
  c.update(keeper=ids[0],losers=ids[1:],apply_prerequisites=['重新校驗本案全部Work及Book原檔雜湊；禁止套用到已變更基線。','跨庫book-text整理本/輯佚檔引用尚未完成；檢查與必要遷移後才執行。','全部原始indexed_by與來源、歷史、ai_note保留；Book只改work_id，不合版本。','重寫所有有效引用，保留墓碑，統一分類後重建官方派生索引。'])
  mergedauthors=recs[0]['record']['authors']
  if cid=='MR-H001':mergedauthors=recs[1]['record']['authors']
  c['machine_decision']={'set_fields':({'authors':mergedauthors} if cid=='MR-H001' else {}),'remove_fields':[]}
  c['classification_decision']={'node':node,'reason':'依作品內容沿用keeper專門類，原來源的不同section仍全部保存。'}
  actions={}
  for key in set().union(*(r['record'].keys() for r in recs)):
   if key in ['indexed_by','emendated_by']:act='append_preserve_order'
   elif key in ['merged_in','merge_history','additional_titles','sources','resources','contained_in']:act='union_preserve_payload'
   elif key=='ai_note':act='preserve_with_original_id'
   elif key in ['revision','revised_at']:act='bump_by_schema'
   elif key=='authors' and cid=='MR-H001':act='explicit_override_preserve_source_details'
   elif key in ['id','title']:act='retain_keeper'
   elif all(r['record'].get(key)==recs[0]['record'].get(key) for r in recs):act='equal_keep'
   else:act='review_required_before_apply'
   actions[key]={'action':act,'selected':mergedauthors if key=='authors' and cid=='MR-H001' else recs[0]['record'].get(key)}
  c['field_decisions']=actions
 cases.append(c)
(OUT/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
# Only new work and book records were inspected; full cross-repository checks remain parent-owned.
old=json.load(open(OUT.parent/'cases.json')); mismatch=[];n=0
for c in old:
 for r in c.get('records',[]):
  n+=1;p=ROOT/r['path']
  if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:mismatch.append(r['path'])
newbad=[r['path'] for r in snap+books if hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()!=r['sha256']]
oldids={i for c in old for i in c.get('ids',[])+c.get('losers',[])+([c['keeper']] if 'keeper' in c else [])}
assert not oldids.intersection(by),'new cases overlap previous adjudications'
assert not mismatch and not newbad,(mismatch,newbad)
stats={'reviewed_groups':5,'confirmed':3,'open':2,'separate':0,'confirmed_loser_work_ids':3,'work_snapshots':len(snap),'book_files_scanned':381716,'related_book_snapshots':len(books),'confirmed_related_books':sum(1 for b in books if b['record']['work_id'] in {i for c in cases if c['status']=='confirmed' for i in c['ids']}),'old_records_hash_checked':n,'old_hash_mismatches':mismatch,'new_hash_mismatches':newbad,'previous_case_overlap':[],'native_data_modified':False,'cross_repository_validation':'not_done','pr_created_by_lane':False}
(OUT/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False))
