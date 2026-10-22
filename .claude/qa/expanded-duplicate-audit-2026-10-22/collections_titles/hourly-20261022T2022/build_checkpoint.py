import hashlib,json,sqlite3,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
AUDIT=HERE.parents[1]
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
DB=Path('/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite')
TREE=Path('/workspace/scratch/0bc7226fa660/audit/current-main-tree.z')
def write(name,obj): (HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
gates=[
 'Revalidate current origin/main before implementation; preserve this fixed research baseline.',
 'Inventory and adjudicate every Book and edition, Collection containment, authors, resources, indexed_by, description, ai_note and prior merge history; retain all unique values in keeper or field ledger.',
 'Scan and rewrite typed Work/Book/Collection/Entity references, classification membership and promotions production_id; preserve historical merge-ledger IDs.',
 'Audit draft repository work_id/merged_into/related_works/classification references and prepare its separate PR when needed.',
 'Record book-text HEAD and manifest and inspect affected text/links; do not infer absent text from this Work/Entity-only census.',
 'Prepare reproducible merge script, exact keeper/loser precondition SHA256 ledger and minimal tombstones; no execution map is supplied by this research checkpoint.',
 'After actual writes run T/L/P/R audit-merge-ledger, schema/check_v2 on real changed paths, classification, official indexes and builder baseline comparison; no hypothetical green checks.',
 'Rebase/revalidate before small-batch PR; do not auto-merge.']
rows=[
('001',['d59f2hfub6rm','d59f2hsp84ch'],'格齋／格齋四六','confirmed',
 '两条均指王子俊现存一卷102首四六；格齋一条的题名从《格齋》四六分裂抽取，书前提要及正文卷题明作格齋四六。不是把已佚三松类稿全集并入现存残编。',
 ['S01','S02'],['/title','/indexed_by/0/title_info','/indexed_by/0/summary','/authors/0/entity_id','/juan_count'],
 ['保留格齋与格齋三松集原名及出处；不得把三松類稿作为无条件全集同义名。','核四种Book范围和contained_in，才制定可执行映射。'],
 {'identity':'王子俊，字材臣/才臣；两Work共用hixhd2h9bn3s；字号差异不是新作者。','scope':'现存一卷102首四六','excluded':'已佚史論、師友緒言及三松類稿全体'}),
('002',['d59f2nj89r7l','d59f2njfrg8x'],'青溪漫稿／清谿漫稿','confirmed',
 '总目卷170作清谿漫稿，四库书前与二十四卷目录作青谿漫稿；同署倪岳、字舜咨，并以奏议59篇及同批具体奏题对应。清/青是该书传题差异，不能概括成一般简繁转换。',
 ['S03','S04'],['/title','/additional_titles','/indexed_by/1/note','/indexed_by/2/title_info','/authors/0/entity_id','/juan_count'],
 ['修订既有note把青/清误称简繁转换的解释，原值留台账。','保留24卷主集与补遗1卷的版本/附属范围，不把补遗抹平；查Book是否记录附件。'],
 {'identity':'倪岳/倪嶽均为字舜咨、倪谦之子，现共用hixhd2h9bjyw；不是其父謙齋文錄。','scope':'倪岳二十四卷主集；补遗作为附属范围另保留','excluded':'未确认所有抄刻本逐篇完全相同'}),
('003',['d59f2gnyfzsw','d59f2hrydpmo'],'佩韋齋文集／佩韋齋集','separate',
 '短题Work唯一indexed_by对应宋百家诗存一卷选诗；全集为诗七卷文九卷，辑闻四卷另书。宋百家诗存原序明确选录，卷38用短题且仅列诗。不能因全集目录也称佩韋齋集便把该选本并入全集。短题Work顶层20卷与唯一来源1卷冲突，须先厘清误混字段。',
 ['S05','S06','S07','S08'],['/juan_count','/measures','/measure_info','/indexed_by/0/title_info','/indexed_by/0/summary','/additional_titles'],
 ['核短题Work历史和所挂Book，把20卷字段的来源与一卷曹庭栋选本分开，不直接删除。','明确建立/保留选本与原集关系；俞庸辑全集与曹庭栋选诗的责任层次应分别表达。','不得借本案吞并佩韋齋輯聞四卷。'],
 {'identity':'俞德鄰同一作者hixhd2h9bi1h；俞庸裒辑、曹庭栋选录为不同编纂层次。','scope':'separate针对宋百家诗存一卷选本与16卷诗文全集；并非否认全集短题','record_scope_conflict':True,'excluded':'20卷顶层字段尚待历史复核；各Book归属未判'}),
('004',['d59f2gotyyo1','d59f2gpw1wxs'],'剡源文集／剡源集','open',
 '同一四库页面提要题剡源集而目录题剡源文集，三十卷题名同一确证；但文集Work同时聚合五卷清抄本。八千卷楼书目将三十卷集、五卷文集、四卷文钞并列，且四库提要区分旧28卷、重辑30卷、黄宗羲选四卷，不能整条并。',
 ['S09','S10'],['/indexed_by/0/title_info','/indexed_by/1/title_info','/indexed_by/2/title_info','/indexed_by/2/summary','/juan_count','/additional_titles'],
 ['读上图/南图五卷抄本目录、序跋、首末，确认是甲乙丙丁戊选文系统还是完整30卷重分卷，不能以检索摘要代替。','先按来源拆清30卷与5卷范围，保留28卷历史版本和4卷选本边界，再重审合并。'],
 {'identity':'戴表元字帥初/曾伯，两条共用hixhd2h9bfhv，未见作者冲突。','scope':'30卷题名同一，5卷抄本范围未决','excluded':'4卷黄宗羲选本及28卷旧编不能自动等价'}),
('005',['d59f2nkla0ht','d59fsejqvr46'],'半軒集／王半軒先生文集','open',
 '同作者王行、字止仲可核，但6卷旧钞本已有傅斯年图书馆条码165211独立著录；四库正文目录及书前为12卷兼补遗，现Work顶层却14卷。八千卷楼目录并列14卷和12卷补遗2卷，提示附卷计数层次，但不足证明6卷本重分卷同内容。',
 ['S10','S11','S12'],['/title','/indexed_by/0/title_info','/indexed_by/1/title_info','/indexed_by/3/title_info','/juan_count','/merged_in','/additional_titles'],
 ['查傅斯年165211六卷旧钞与天一阁本篇目，比较四库12卷及补遗；数字化状态不等于已阅影像。','保留现merged_in的d59f6eigqqkg历史；14/12/6卷逐来源建账，不盲改主卷数。'],
 {'identity':'王行字止仲，两条共用hixhd2h9bfku；半軒是题名组成，不能仅凭先生称谓判全范围。','scope':'6卷旧钞与12卷主集+补遗的关系未决','excluded':'未读取傅斯年六卷影像；WorldCat链接只返回空壳'})]
cases=[]
for num,ids,label,status,reason,sources,pointers,steps,scope in rows:
 cases.append({'case_id':'COL-2022-'+num,'type':'Work','status':status,'applied':False,'native_mutations':0,'execution_hold':True,'research_ref':BASE,'ids':ids,'label':label,'reason':reason,'scope':scope,'external_sources':['COL-2022-'+s for s in sources],'field_review_pointers':pointers,'next_steps':steps,'execution_gates':gates,'supersedes_case_id':None,'candidate_source':'collections_titles/broad-20261022/review-pool.json','execution_mapping':None})
c=sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True)
manifest=json.loads(c.execute("select value from metadata where key='manifest'").fetchone()[0]);assert manifest['base']==BASE
traw=TREE.read_bytes();assert hashlib.sha256(traw).hexdigest()==manifest['tree_sha256']
tree={}
for row in traw.split(b'\0'):
 if row:
  meta,path=row.split(b'\t',1);tree[path.decode()]=meta.split()[2].decode()
workids={i for x in cases for i in x['ids']};ids=set(workids)
for i in workids:
 d=json.loads(c.execute('select data from records where id=?',(i,)).fetchone()[0]);ids.update(a['entity_id'] for a in d.get('authors',[]) if a.get('entity_id'))
records={};checks=[]
for rid in sorted(ids):
 ty,path,blob,sha,s=c.execute('select type,path,blob_sha,sha256,data from records where id=?',(rid,)).fetchone();raw=s.encode();d=json.loads(s)
 assert hashlib.sha256(raw).hexdigest()==sha
 oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert oid==blob==tree[path]
 assert not d.get('merged_into')
 records[rid]={'path':path,'sha256':sha,'blob_sha':blob,'type':ty,'record':d}
 checks.append({'id':rid,'path':path,'sha256':sha,'blob_sha':blob,'exact_main_bytes':True})
for x in cases:
 x['records']=[{'id':i,**{k:records[i][k] for k in ['path','sha256','blob_sha']},'title':records[i]['record']['title']} for i in x['ids']]
 x['main_verification']={'reference':'verification.json','all_work_bytes_match_main':True,'tombstones':0}
write('cases.json',cases);write('original-records.json',records)
raw=subprocess.check_output(['git','show',BASE+':.claude/qa/正式库并条审查规则.md'],cwd=ROOT);(HERE/'formal-rules-main.md').write_bytes(raw)
write('verification.json',{'research_ref':BASE,'sqlite_manifest':manifest,'method':'Readonly SQLite original UTF-8 bytes SHA256 and Git blob SHA1 checked against metadata and complete fixed-main tree; tree SHA256 checked against census manifest.','checked_records':len(checks),'work_records':len(workids),'entity_records':len(ids)-len(workids),'byte_identical':len(checks),'drift':0,'tombstones':0,'checks':checks,'rules_sha256':hashlib.sha256(raw).hexdigest(),'native_mutations':0,'not_checked':gates})
overlap=[]
for f in AUDIT.rglob('cases.json'):
 if f==HERE/'cases.json':continue
 try: old=json.loads(f.read_text())
 except Exception:continue
 if not isinstance(old,list):continue
 for o in old:
  if not isinstance(o,dict):continue
  s=json.dumps(o)
  for x in cases:
   hits=[i for i in x['ids'] if i in s]
   if hits:overlap.append({'new_case':x['case_id'],'existing_file':str(f.relative_to(AUDIT)),'existing_case':o.get('case_id'),'ids':hits,'action':'review overlap before root rollup; no automatic supersession'})
write('overlap-check.json',overlap)
hashes=[]
for f in sorted((HERE/'evidence').glob('*.json')):hashes.append({'path':str(f.relative_to(HERE)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'kind':'web tool response snapshot, not raw page/PDF bytes'})
write('evidence-manifest.json',hashes)
write('stats.json',{'new_work_case_groups':5,'new_research_families':5,'new_work_records':10,'confirmed':2,'separate':1,'open':2,'supersedes':[],'native_merges':0,'redundant_work_count_confirmed':2,'execution_ready':0})
write('validation.json',{'passed':['5 new case IDs and 10 unique Work IDs','15 original records byte-identical to fixed main','all source snapshots hashed','all cases execution_hold with explicit gates','no execution mapping/native changes'], 'case_counts':{'confirmed':2,'separate':1,'open':2},'overlap_hits':len(overlap),'limits':'Research-only; all implementation and cross-repository validation gates remain unrun.'})
ledger=[]
def pointer_get(obj,pointer):
 for part in pointer.lstrip('/').split('/'):
  obj=obj[int(part)] if isinstance(obj,list) else obj[part]
 return obj
for x in cases:
 for rid in x['ids']:
  obj=records[rid]['record']
  for p in x['field_review_pointers']:
   try:value=pointer_get(obj,p)
   except (KeyError,IndexError,ValueError):continue
   ledger.append({'case_id':x['case_id'],'record_id':rid,'record_path':records[rid]['path'],'pointer':p,'original_value':value,'proposed_value':None,'action':'research-only; retain original until source/scope and execution review','record_sha256':records[rid]['sha256']})
write('field-ledger.json',ledger)
refs=json.loads((HERE/'references.json').read_text()); refids={r['source_id'] for r in refs}
assert len(refids)==len(refs)==12
assert len({x['case_id'] for x in cases})==len(cases)==5
assert all(set(x['external_sources'])<=refids for x in cases)
assert all((HERE/r['snapshot']).is_file() for r in refs)
write('source-validation.json',{'reference_count':12,'all_case_source_ids_resolve':True,'all_reference_snapshots_exist':True,'evidence_snapshots_hashed':len(hashes),'field_ledger_valid_pointers':len(ledger),'primary_images_or_pdf_read':0,'scope':'Only primary-text transcriptions and institutional catalogue pages actually opened; search-only leads not decision evidence.'})
write('artifact-manifest.json',[{'path':str(f.relative_to(HERE)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(HERE.rglob('*')) if f.is_file() and f.name!='artifact-manifest.json'])
print(json.dumps({'cases':len(cases),'records':len(records),'overlap_hits':len(overlap),'confirmed':2,'separate':1,'open':2,'native_mutations':0}))
