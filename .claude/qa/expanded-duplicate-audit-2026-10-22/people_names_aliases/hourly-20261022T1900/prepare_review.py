"""Read-only native-data review. Writes candidates/ledger only alongside this script."""
from pathlib import Path
import ast,copy,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
P=OUT.parent
OLD=ROOT.parent/'book-index'
SHA='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
DATE='2026-10-22'
def write(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def source(path): return subprocess.check_output(['git','-c','gc.auto=0','show',SHA+':'+path],cwd=ROOT)
oldcases=json.loads((P/'astra-review-20261022/cases.json').read_text())
plans=json.loads((P/'astra-review-20261022/candidate-merge-plan.json').read_text())['cases']
li=next(x for x in json.loads((P/'cases.json').read_text()) if x['case_id']=='PNA-R015')
paths={p for c in oldcases+[li] for p in c['paths'].values()}
paths.update(op['path'] for p in plans for op in p['known_typed_reference_operations'])
paths.update(x['path'] for x in li['evidence_refs'])
tree_raw=subprocess.check_output(['git','ls-tree','-r','-z',SHA,'--',*sorted(paths)],cwd=ROOT)
tree={p.decode():meta.decode().split()[2] for row in tree_raw.split(b'\0') if row for meta,p in [row.split(b'\t',1)]}
snapshots={};checks=[]
for path in sorted(paths):
 raw=(OLD/path).read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 assert blob==tree[path], 'main drift: '+path
 rec=json.loads(raw);snapshots[path]={'record':rec,'sha256':hashlib.sha256(raw).hexdigest(),'git_blob':blob}
 checks.append({'path':path,'git_blob':blob,'main_git_blob':tree[path],'sha256':snapshots[path]['sha256'],'main_verified':True})
ledger=[];candidates={};fields=[];cases=[];index_checks=[]
# Execute precisely the main builder's Entity projection (no full repository build).
module=ast.parse(source('build/build_derived.py'))
fn=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='index_entry')
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<main:index_entry>','exec'),ns)
for n,(c,plan) in enumerate(zip(oldcases,plans),1):
 cid=f'PNA-1900-00{n}';kid=c['keeper'];lid=c['losers'][0]
 kp,lp=c['paths'][kid],c['paths'][lid];k=snapshots[kp]['record'];l=snapshots[lp]['record']
 newk=copy.deepcopy(k)
 alias=copy.deepcopy(plan['entity_actions'][0]['value']);alias['note']=alias['note'].replace(c['case_id'],cid)
 assert alias['name'] not in {a.get('name') for a in k.get('alt_names',[])}
 newk.setdefault('alt_names',[]).append(alias)
 newk.setdefault('merged_in',[]).append({'id':lid,'primary_name':l['primary_name'],'at':DATE,'by':'expanded-duplicate-audit/people_names_aliases','rule':'本名與字之同人；獨立文獻及著作領域互證','why':c['identity_evidence']})
 newk['revised_at']=DATE
 tomb={f:l[f] for f in ['schema_version','id','type','subtype','primary_name','revision']}
 tomb.update(merged_into=kid,revised_at=DATE)
 candidates[kp]=newk;candidates[lp]=tomb
 field_rows=[]
 for owner,old,new in [(kid,k,newk),(lid,l,tomb)]:
  for f in sorted(set(old)|set(new)):
   if owner==kid:
    policy={'alt_names':'append verified surname+style alias; preserve existing values/order','merged_in':'append owner-tagged merge history; no rewrite of earlier history','revised_at':'set actual execution date; proposal date must refresh if later'}.get(f,'preserve byte-equivalent JSON value; no recertification')
   else: policy='retain in schema-minimal tombstone' if f in tomb else 'remove from tombstone; preserve exact old value with original owner in ledger.original_records'
   field_rows.append({'owner_id':owner,'field':f,'before_present':f in old,'before':old.get(f),'after_present':f in new,'after':new.get(f),'policy':policy})
 operations=copy.deepcopy(plan['known_typed_reference_operations'])
 for op in operations:
  rec=copy.deepcopy(snapshots[op['path']]['record']);assert snapshots[op['path']]['sha256']==op['pre_sha256']
  pos=int(op['json_pointer'].split('/')[2]);assert rec['authors'][pos]['entity_id']==op['old']
  rec['authors'][pos]['entity_id']=op['new'];candidates[op['path']]=rec
 pre=[{'id':i,'path':c['paths'][i],'sha256':snapshots[c['paths'][i]]['sha256']} for i in [kid,lid]]
 ledger.append({'cluster_id':cid,'type':'people','keeper':kid,'losers':[lid],'evidence':c['identity_evidence'],'preconditions':pre,'original_records':{kid:k,lid:l},'field_ledger':field_rows,'known_reference_operations':operations,'apply_enabled':False,'full_reference_scan_complete':False})
 fields.extend(field_rows)
 for path,before,after in [(kp,k,newk),(lp,l,tomb)]:
  b=ns['index_entry'](before,'Entity',path);a=ns['index_entry'](after,'Entity',path)
  assert a==b
  index_checks.append({'path':path,'before_projection':b,'after_projection':a,'index_entry_changed':False})
 case=copy.deepcopy(c);case.update(case_id=cid,supersedes_case_id=c['case_id'],review_kind='exact field/tombstone/index execution-candidate review; no native mutation',execution_status='plan_only_pending_central_reference_scan_and_post_write_gates',ledger_path=str((OUT/'candidate-ledger.json').relative_to(ROOT)),apply_enabled=False)
 cases.append(case)
# An open case is advanced by excluding a tempting but invalid source bridge.
lc=copy.deepcopy(li);lc.update(case_id='PNA-1900-003',supersedes_case_id='PNA-R015',main_sha=SHA,status='open',why='柳宗直字正夫與孤立柳正夫《西漢蒙求》的責任者橋接仍未證。新查張栻《西漢蒙求跋》先舉宗直《西漢文類》，後轉東平侯彦明編書；前者是比興先例，不可當成宗直作《西漢蒙求》的證據。',execution_status='open_identity_bridge_missing',new_identity_confirmations=0,native_mutations=0)
lc['external_evidence']=[{'url':'https://www.shidianguji.com/zh/book/CADAL01024476/chapter/1l3f0fa2xfkss','title':'張南軒先生文集卷六：西漢蒙求跋','accessed':DATE,'source_ref':'turn30view0','lines':'284-304','finding':'開篇回顧柳宗直所輯《西漢文類》，接著以東平侯彦明取班史故事及雅訓語為新書敘述主體；不是柳宗直／柳正夫互見。搜尋摘要截取題名與首句易造成假橋接。','short_quotes':['柳宗直輯西漢文類','東平侯彦明取班史故事及雅訓語']}]
lc['next_step']='優先核《西漢蒙求》柳正夫條原刻與注本，尋本名、籍貫或官歷；張栻跋只可作異作者線索，不能據此改繫侯彦明。保留兩Entity及兩Work原字段。'
cases.append(lc)
write('cases.json',cases)
write('candidate-ledger.json',{'main_sha':SHA,'plan_only':True,'apply_enabled':False,'native_mutations':0,'merges':ledger})
write('candidate-records.json',{'main_sha':SHA,'not_applied':True,'known_reference_scope_only':True,'records':candidates})
write('field-ledger.json',fields)
write('source-snapshots.json',snapshots)
write('source-validation.json',{'main_sha':SHA,'method':'fixed-main tree Git blob SHA1 versus exact old-checkout bytes plus SHA256','checks':checks,'native_mutations':0})
write('index-review.json',{'main_sha':SHA,'official_function':'build/build_derived.py:index_entry','entity_checks':index_checks,'known_work_changes':'only authors[].entity_id; unchanged authors[].name, dynasty, role means official Work index projection is unchanged','expected_repository_index_delta':0,'must_run_official_builder':True,'do_not_delete_tombstone_index_entries':True,'not_a_whole_repo_build':True})
# Structural assertions use exact main schema definitions; full schema checker is a post-write gate.
schema=json.loads(source('schema/json/entity.schema.json'))
for path,rec in candidates.items():
 if not path.startswith('Entity/'): continue
 assert set(schema['required']) <= set(rec)
 assert not (set(rec)-set(schema['properties']))
 for alt in rec.get('alt_names',[]): assert alt['type'] in schema['$defs']['AltName']['properties']['type']['enum']
 for h in rec.get('merged_in',[]): assert set(h) <= set(schema['$defs']['EntityMergedInItem']['properties'])
write('validation.json',{'main_sha':SHA,'source_paths_verified':len(checks),'candidate_entities_structural_assertions':4,'full_json_schema_validation':'not run: jsonschema unavailable in system and primary runtime; exact schema required-key/property/alias/history checks passed','candidate_records':len(candidates),'field_ledger_rows':len(fields),'entity_index_projection_changes':0,'full_live_reference_scan':'delegated to root; not claimed here','official_post_write_checks':'not run; no native writes','effective_count_delta':{'confirmed':0,'separate':0,'open':0},'native_mutations':0})
print(json.dumps({'source_verified':len(checks),'candidate_records':len(candidates),'field_rows':len(fields),'structural_assertions':'passed'},ensure_ascii=False))
