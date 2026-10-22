#!/usr/bin/env python3
"""Read fixed-current SQLite; write research artifacts only beneath this directory."""
import json,sqlite3,hashlib,pathlib,copy,subprocess
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[4]
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
DB='/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite'
c=sqlite3.connect('file:'+DB+'?mode=ro',uri=True)
manifest=json.loads(c.execute('select value from metadata where key="manifest"').fetchone()[0]);assert manifest['base']==BASE and not manifest['errors']
def save(n,v): (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def rec(i):
 r=c.execute('select id,type,name,path,blob_sha,sha256,data from records where id=?',(i,)).fetchone(); assert r
 d=dict(zip(['id','type','name','path','blob_sha','sha256','raw'],r)); b=d['raw'].encode();assert hashlib.sha256(b).hexdigest()==d['sha256']; assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==d['blob_sha'];d['data']=json.loads(d['raw']);return d
specs=[
 ('任希古／任敬臣','hixhd2h9bkd1','hixhindxb7k0','confirmed',['d59f28nhlvr9','d59f2q6ql0qp','d59f2q7wetc0'], '《經義考》卷十四直接引計敏夫稱任希古字敬臣、棣州人、弘文館學士、太子舍人；《唐詩紀事》原文再證。任希古名下新唐志／宋志集十卷，任敬臣名下宋志集亦十卷，姓名橋接與文集領域相合。', '本名與字在後世條目有倒置說；此案不新定生卒，不以宋史收錄即判宋人。人物同一不自動合併五卷／十卷的Work。'),
 ('倪思／倪正甫','hixhd2h9be75','hixhd2h9bowd','confirmed',['d59f2hs16uio','d59f2q89is5d','d59f9ttxu329'], '《班馬異同》總目明言思字正甫、湖州歸安、乾道二年進士；直齋連書條明署歸安倪思正父，《兼山論著》三十卷；宋志倪正甫《兼山小集》三十卷與同一集部著述環境相應。歸安縣志卷二十亦連錄兩題。', '人物可確認，兼山論著／小集只是相應旁證，兩Work題名同一性仍另審；keeper生卒1147–1220為現行值保留，未重驗。'),
 ('凌稚隆／凌以棟','hixhd2h9bgeo','hixhd2h9bkio','confirmed',['d59f2nifjx8h','d59f2niid24k','d59f2nfmq9z4'], '《春秋左傳評注測義》總目直接稱明淩稚隆字以棟、烏程人；《五車韻瑞》明志署淩以棟一百六十卷，總目署淩稚隆同題同卷，跨著錄且朝代、著述領域一致。', 'keeper已有淩稚隆的merged_in須保留；五車韻瑞分裂源於舊字面作者不匹配，其Work合併另案處理。'),
 ('馮時行／馮當可','hixhd2h9bfe9','hixhd2h9bun9','confirmed',['d59f2heaqy2o','d59f2hsjx341'], '《經義考》卷二十五同一《易論》三卷條引程逈稱蜀人馮時行字當可、號縉雲，又明錄朱子／陳氏名與字倒置異說。總目《縉雲文集》稱馮時行字當可、壁山人、紹興間官歷。是同一人名／字次序異說，不是兩作者。', '選作最完整執行候選。保留《易論》作者簽名馮當可及全部name_basis；不校改原文朱子說、不重定生卒或縉雲集與文集Work同一性。'),
 ('高翥／高九萬','hixhd2h9bffm','hixhd2h9bm7o','confirmed',['d59f2hpscdtu','d59f2hjy9o8y','d59f6epzoq2r'], '總目明稱宋高翥字九萬、號菊磵、餘姚人；宋史藝文志補及千頃堂均以高九萬署菊磵／菊礀小集，與高翥的集名及時代一致。外查千頃堂卷二十九明有高九萬菊磵小集一卷。', '兩Entity上圖URI不同（各記錄自己的姓名形式），尚不能證URI等價；應保存兩來源URL並人工驗證，不盲覆蓋。keeper CBDB match ambiguous_2且floruit1137未重驗；疏寮小集Work現誤掛高翥而提要屬高似孫，是既有污染須另修。因此身份confirmed但不選本組立即實施。'),
 ('劉清之／劉子澄','hixhd2h9beq7','hixhd2h9bhp0','separate',['d59f2hrrihoi','d59f2hm6hnuq','d59f6emgbwg0'], '劉清之確字子澄，但另一Entity所著是玉淵文稿。《養吾齋集》卷二十六〈跋劉玉淵道州九嶷山虞帝廟碑藁後〉明言玉淵先生劉公諱子澄字清叔，且記甲午入東京及乙丑紹陵登極赦事，連到十三世紀官歷；與清之靜春、戒子通錄不同人。', '同姓加字不是身份證據。劉清之Entity籍貫廬陵與總目臨江、提要紹興二年進士與生年1134亦有元數據問題，不在本案修；不能反以這些舊矛盾抹去玉淵原文。'),
 ('劉兆／劉延世','hixhd2h9bhy0','hixhd2h9bp38','separate',['d59f27ygfrib','d59f2prri6f5','d59f2q505k3l'], '劉兆確字延世，為晉代經學者；候選另一Entity名下談圃三卷為宋臨江劉延世錄孫升之語。四庫孫公談圃提要說元祐中孫升任中書舍人、紹聖初謫汀州，延世父知長汀，時代相隔數百年、著述領域與籍貫亦不合。', '不以另一Entity朝代空白推定晉代；談圃應保留宋人劉延世作者。'),
 ('黃雲／黃應龍','hixhd2h9bi6z','hixhd2h9bnp2','separate',['d59f2ndsv7cz','d59f6emqxyx1','d59f2hlf0s1s'], '丹岩集之明黃雲字應龍、崑山人、弘治中瑞州訓導；候選黃應龍名下璧林文集十四卷。《千頃堂書目》卷二十九獨立明標黃應龍璧林先生文集十四卷嘉熙間人，與明弘治人非同一。', '黃雲keeper另混入咸寧、字叔卿、生1508的CBDB信息，與丹岩著錄不符；須另立污染修復，不能用該錯配支持本名／字合併。清黃雲hixi8u5qhgso不在此組。')
]
cases=[]; sourceids=set(); selectedids=set()
queue=json.loads((OUT.parent/'broad-20261022/candidate-queue.json').read_text())
for n,(label,k,l,status,ws,reason,caution) in enumerate(specs,1):
 matches=[x for x in queue if set(x['ids'])=={k,l}];assert len(matches)==1 and not matches[0]['old_case_ids']; selectedids.update([k,l]); sourceids.update(ws)
 cases.append({'case_id':f'PNA-2000-{n:03d}','label':label,'status':status,'ids':[k,l],'supersedes_case_id':None,'native_merge_groups':0,'suggested_keeper':k if status=='confirmed' else None,'suggested_losers':[l] if status=='confirmed' else [],'decision':reason,'cautions':caution,'work_evidence_ids':ws,'discovery_rules':matches[0]['rules'],'research_only':True})
# Snapshot every Work associated with the selected 16 people, not just favourable evidence.
related=[]; exact_refs=[]; literal_hits=[]
loser='hixhd2h9bun9';keeper='hixhd2h9bfe9'
def walk(v,p=''):
 if isinstance(v,dict):
  for k,z in v.items(): yield from walk(z,p+'/'+k.replace('~','~0').replace('/','~1'))
 elif isinstance(v,list):
  for k,z in enumerate(v): yield from walk(z,p+'/'+str(k))
 else: yield p,v
for rid,typ,name,path,data in c.execute('select id,type,name,path,data from records'):
 d=json.loads(data)
 if typ=='Work' and any(a.get('entity_id') in selectedids for a in d.get('authors',[])):
  sourceids.add(rid);related.append({'id':rid,'name':name,'authors':d.get('authors',[])})
 if loser in data:
  for ptr,v in walk(d):
   if v==loser: exact_refs.append({'id':rid,'type':typ,'path':path,'pointer':ptr,'before':v,'after':keeper,'action':'do_not_rewrite_own_id' if ptr=='/id' else 'review_exact_reference'})
   elif isinstance(v,str) and loser in v:literal_hits.append({'id':rid,'path':path,'pointer':ptr,'value':v,'action':'preserve_historical_or_textual_content'})
sourceids.update(selectedids)
snapshots={i:rec(i) for i in sorted(sourceids)}
for case in cases:
 case['entity_snapshots']=[{k:snapshots[i][k] for k in ['id','path','blob_sha','sha256']} for i in case['ids']]
 case['catalogue_pointers']=[{'work_id':i,'path':snapshots[i]['path'],'pointer':'/indexed_by','values':snapshots[i]['data'].get('indexed_by',[])} for i in case['work_evidence_ids']]
 for s in [z for z in snapshots.values() if z['type']=='Work' and any(a.get('entity_id') in case['ids'] for a in z['data'].get('authors',[]))]: pass
save('cases.json',cases);save('source-snapshots.json',{'base':BASE,'manifest':manifest,'records':snapshots});save('related-works.json',related)
scope={'base':BASE,'scanned_types':['Entity','Work'],'table_records':c.execute('select count(*) from records').fetchone()[0],'exact_value_occurrences':exact_refs,'substring_occurrences':literal_hits,'limitations':['SQLite contains Entity and Work only; Book/Collection/classification/promotions/draft/book-text NOT covered.','Own /id is identity, not a reference to rewrite.','This is NOT full cross-repository R/D/P clearance.']};save('reference-review.json',scope)
K=copy.deepcopy(snapshots[keeper]['data']);L=copy.deepcopy(snapshots[loser]['data']);W=copy.deepcopy(snapshots['d59f2heaqy2o']['data']);newK=copy.deepcopy(K)
newK.setdefault('alt_names',[]).append({'name':'馮當可','type':'別稱'})
newK.setdefault('merged_in',[]).append({'id':loser,'primary_name':L['primary_name'],'at':'2026-10-22','by':'Codex PNA-2000 research candidate','rule':'E','why':cases[3]['decision']})
newK['revised_at']='2026-10-22'
newL={k:copy.deepcopy(L[k]) for k in ['schema_version','id','type','subtype','primary_name','revision']};newL.update({'revised_at':'2026-10-22','merged_into':keeper})
newW=copy.deepcopy(W);assert newW['authors'][0]['entity_id']==loser;newW['authors'][0]['entity_id']=keeper;newW['revised_at']='2026-10-22'
proposed={keeper:newK,loser:newL,'d59f2heaqy2o':newW}
rows=[]
for i,before,after in [(keeper,K,newK),(loser,L,newL),('d59f2heaqy2o',W,newW)]:
 for key in sorted(set(before)|set(after)):
  same=key in before and key in after and before[key]==after[key]
  rows.append({'id':i,'pointer':'/'+key,'before_present':key in before,'before':before.get(key),'after_present':key in after,'after':after.get(key),'disposition':'unchanged' if same else ('full_original_retained_in_ledger' if key not in after else 'explicit_candidate_change'),'original_owner':i})
assert set(newL)==set(['schema_version','id','type','subtype','primary_name','revision','revised_at','merged_into'])
assert newK['ai_note']==K['ai_note'] and newK['description']==K['description'] and newK['external_ids']==K['external_ids']
assert newW['authors'][0]['name']==W['authors'][0]['name'] and newW['indexed_by']==W['indexed_by']
assert not any(k in newK for k in ['works','_works'])
pre=[{k:snapshots[i][k] for k in ['id','path','blob_sha','sha256']} for i in proposed]
ledger={'main_sha':BASE,'plan_only':True,'apply_enabled':False,'native_mutations':0,'merges':[{'cluster_id':'PNA-2000-004','type':'people','keeper':keeper,'losers':[loser],'evidence':cases[3]['decision'],'preconditions':pre,'original_records':{i:snapshots[i]['data'] for i in proposed},'proposed_records':proposed,'field_ledger':'field-ledger.json','known_reference_changes':[r for r in exact_refs if r['pointer']=='/authors/0/entity_id'],'unresolved_gates':['Refresh main and hashes','Full formal/draft/text reference search','T/L/P/R/D audit','Changed-path JSON schema/check_v2','Classification check','Official builder with --text-index --write-index then --check-only'],'notes':['Candidate date/by must be refreshed at execution.','Full loser period_basis, ai_note, updated_at and other removed values retained by original owner in this ledger.','Existing entity_merge.py does not add loser primary_name automatically; explicit 馮當可/別稱 insertion required.','No external ID, description, date or locality is overwritten.','revision retained as existing; refresh under execution policy.']} ]}
save('candidate-ledger.json',ledger);save('candidate-records.json',{'main_sha':BASE,'plan_only':True,'records':proposed});save('field-ledger.json',rows)
rulepath='.claude/qa/正式库并条审查规则.md'
rules=subprocess.check_output(['git','show',BASE+':'+rulepath],cwd=ROOT)
(OUT/'merge-rules.snapshot.md').write_bytes(rules)
save('validation.json',{'base':BASE,'native_merge_groups':0,'cases':len(cases),'counts':{s:sum(x['status']==s for x in cases) for s in ['confirmed','separate','open']},'source_records':len(snapshots),'verified_original_sha256_and_git_blob_sha1':len(snapshots),'field_rows':len(rows),'no_prior_reviewed_candidate_pairs':True,'rule_snapshot_sha256':hashlib.sha256(rules).hexdigest(),'limited_candidate_assertions':'passed','NOT_RUN':['full schema','check_v2','T/L/P/R/D','classification','builder','full crossrepo refs']})
print(json.dumps({'cases':len(cases),'snapshots':len(snapshots),'field_rows':len(rows),'exact_refs':exact_refs},ensure_ascii=False))
