#!/usr/bin/env python3
"""Research-only projection; writes only beside this script, never native data."""
import copy, hashlib, json, subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
LANE=OUT.parent
ROOT=LANE.parents[2]
OLD=Path('/workspace/scratch/0bc7226fa660/book-index')
REF='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
def write(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
tree={}
for row in Path('/workspace/scratch/0bc7226fa660/audit/current-main-tree.z').read_bytes().split(b'\0'):
 if row:
  meta,p=row.split(b'\t',1);tree[p.decode()]=meta.split()[2].decode()
prior=json.loads((LANE/'astra-review-20261022/selected-current-snapshots.json').read_text())['records']
snaps={}
for p,v in prior.items():
 b=(OLD/p).read_bytes();assert blob(b)==tree[p]==v['git_blob_sha'];assert hashlib.sha256(b).hexdigest()==v['sha256']
 snaps[p]={'git_blob_sha':blob(b),'sha256':hashlib.sha256(b).hexdigest(),'record':json.loads(b),'verification':'local bytes Git blob SHA1 == fixed-main tree; SHA256 == prior checkpoint'}
extra=['Entity/i/x/i/hixhd2h9bixi-僧肇.json','Entity/f/k/4/hixhjtdcdfk4-釋僧肇.json','Work/4/o/z/d59f27vzh4oz-道行經序.json']
for p in extra:
 b=(OLD/p).read_bytes();assert blob(b)==tree[p];snaps[p]={'git_blob_sha':blob(b),'sha256':hashlib.sha256(b).hexdigest(),'record':json.loads(b),'verification':'local bytes Git blob SHA1 == fixed-main tree; separate SHA256 recorded'}
rules={}
for p in ['schema/common.md','schema/entity/_common.md','schema/json/entity.schema.json','schema/json/common.schema.json']:
 b=(OLD/p).read_bytes();assert blob(b)==tree[p];rules[p]={'git_blob_sha':blob(b),'sha256':hashlib.sha256(b).hexdigest()}
for p in ['scripts/audit-merge-ledger.py','scripts/check-duplicate-audit.py','.claude/qa/reports/duplicate-audit-2026-10-21/README.md']:
 b=subprocess.check_output(['git','show',REF+':'+p],cwd=ROOT);assert blob(b)==tree[p];rules[p]={'git_blob_sha':blob(b),'sha256':hashlib.sha256(b).hexdigest()}
write('source-snapshots.json',{'main_ref':REF,'records':snaps,'rules':rules})
byid={v['record']['id']:(p,v) for p,v in snaps.items()}
groups=json.loads((LANE/'astra-review-20261022/candidate-plan.json').read_text())['groups']
cases=[];merges=[];checks=[]
def union(a,b):
 out=copy.deepcopy(a)
 for v in b:
  if v not in out:out.append(copy.deepcopy(v))
 return out
for g in groups:
 kid=g['keeper'];lid=g['losers'][0];k=copy.deepcopy(byid[kid][1]['record']);l=copy.deepcopy(byid[lid][1]['record']);a=copy.deepcopy(k)
 label='PRV-H1900-'+g['supersedes_case_id'].removeprefix('PRV-')
 for f,v in l.items():
  if f not in a and f not in ('updated_at','revision','revised_at','id'):a[f]=copy.deepcopy(v)
 a['alt_names']=union(union(k.get('alt_names',[]),l.get('alt_names',[])),[{'name':l['primary_name'],'type':'別名','note':g['why']}])
 for f in ('dynasty_basis','period_basis'):
  if k.get(f) and l.get(f) and k[f]!=l[f]:a[f]=f"[來源 {kid}] {k[f]}\n[來源 {lid}] {l[f]}"
 notes=[f"[來源 {r['id']}] {r['ai_note']}" for r in (k,l) if r.get('ai_note')]
 src='https://www.shidianguji.com/zh/book/CADAL02036163/chapter/1lafpp28af1nv' if g['supersedes_case_id']=='PRV-P007' else 'https://authority.dila.edu.tw/person/search.php?aid=A001358'
 notes.append('2026-10-22 '+label+' 候選并條理由：'+g['why']+' 證據：'+src+'。舊說明中的著錄處數／部數為建檔當時記載，不是本輪引用掃描結果。')
 a['ai_note']='\n\n'.join(notes)
 sources=union(k.get('description',{}).get('sources',[]),l.get('description',{}).get('sources',[]))
 sources=union(sources,[{'name':'話墮集卷三（識典古籍轉錄）' if g['supersedes_case_id']=='PRV-P007' else 'DILA 人名規範 A001358','type':'url','details':src}])
 a['description']=copy.deepcopy(k.get('description',l.get('description',{})));a['description']['sources']=sources
 a['review']={'status':'unreviewed'}
 for f in ('merged_in','merge_history'):
  if k.get(f) or l.get(f):a[f]=union(k.get(f,[]),l.get(f,[]))
 a['merged_in']=union(a.get('merged_in',[]),[{'id':lid,'primary_name':l['primary_name'],'at':'2026-10-22','by':'expanded-duplicate-audit','rule':g['supersedes_case_id'],'why':g['why']}])
 a['revision']='1.1.0';a['revised_at']='2026-10-22'
 tomb={f:copy.deepcopy(l[f]) for f in ('schema_version','id','type','subtype','primary_name')};tomb.update(merged_into=kid,revision='1.1.0',revised_at='2026-10-22')
 fields=[]
 for f in sorted(set(k)|set(l)|set(a)|set(tomb)):
  if f in ('revision','revised_at','updated_at'):action='archive_original_management_values; refresh_on_execution; minor_content_bump_for_keeper_and_tombstone'
  elif f=='id':action='keeper_id_retained; loser_id_retained_in_tombstone_and_merged_in'
  elif f=='primary_name':action='retain_keeper; loser_name_in_alias_and_tombstone'
  elif f in ('ai_note','dynasty_basis','period_basis'):action='retain_all_attributed_original_text; add_research_reason_only'
  elif f=='description':action='preserve_source_objects_exactly; stable_union; append_evidence_source'
  elif f in ('alt_names','merged_in','merge_history'):action='stable_exact_object_union; preserve_historical_ids'
  else:action='retain_or_copy_nonconflicting_value; no_inferred_enrichment'
  fields.append({'field':f,'before':[{'id':r['id'],'present':f in r,**({'value':r[f]} if f in r else {})} for r in (k,l)],'keeper_after':{'present':f in a,**({'value':a[f]} if f in a else {})},'tombstone_after':{'present':f in tomb,**({'value':tomb[f]} if f in tomb else {})},'action':action,'archive':'source-snapshots.json'})
 checks.append({'case_id':label,'all_original_top_level_fields_accounted':set(k)|set(l)<=set(x['field'] for x in fields),'all_original_ai_notes_preserved':all(r.get('ai_note','') in a['ai_note'] for r in (k,l)),'all_dynasty_basis_values_preserved':all(r.get('dynasty_basis','') in a.get('dynasty_basis','') for r in (k,l)),'all_original_sources_preserved':all(s in a['description']['sources'] for r in (k,l) for s in r.get('description',{}).get('sources',[])),'minimal_tombstone':set(tomb)=={'schema_version','id','type','subtype','primary_name','merged_into','revision','revised_at'}})
 merge={'cluster_id':label,'type':'people','keeper':kid,'losers':[lid],'preconditions':[{'id':rid,'path':byid[rid][0],'sha256':byid[rid][1]['sha256'],'git_blob_sha':byid[rid][1]['git_blob_sha']} for rid in (kid,lid)],'field_ledger':fields,'projected_keeper':a,'projected_tombstone':tomb,'ready_to_apply':False,'projection_warning':'Only research artifacts. Execution date, revision, and source drift must be reevaluated; no native write occurred.'}
 merges.append(merge)
 c=copy.deepcopy(g);c.update(case_id=label,cluster_id=label,supersedes_case_id=g['case_id'],supersedes_case_ids=[g['case_id']],original_case_id=g['supersedes_case_id'],counts_as_new_case=False,main_ref=REF,execution_status='field_ledger_complete_pending_reference_and_write_gates',field_ledger_file='candidate-ledger.json',native_mutations=0)
 c.pop('candidate_field_overrides',None)
 c['pending_gates']+=['root consolidated scan must certify all native families, promotions, draft, book-text; known Work references are not full scan','Independent per-field Entity losslessness audit beyond official script L checks (which only cover work/book)','Do not reuse hardcoded 2026-10-21 checker ledger or obsolete 1876 mapping; bind exact two-group candidate ledger']
 cases.append(c)
old=next(c for c in json.loads((LANE/'cases-all.json').read_text()) if c['case_id']=='PRV-R012')
c={k:copy.deepcopy(old[k]) for k in ('keeper','losers','related_work_ids','evidence')};c.update(case_id='PRV-H1900-R012',cluster_id='PRV-H1900-R012',supersedes_case_id='PRV-R012',counts_as_new_case=False,status='open',main_ref=REF,native_mutations=0,execution_status='pollution_boundary_refined_not_ready',why='固定main仍将《道行經序》归僧肇；原目录summary残名「僧 」不能支持补字，ai_note自承归属存疑却在description和结构化authors作断言。保持open，先核丁志原页及隋目对应条再定作者；不自动改挂僧叡或道安。',records=[{'id':rid,'path':byid[rid][0],'sha256':byid[rid][1]['sha256']} for rid in [old['keeper'],old['losers'][0],'d59f27vzh4oz']],field_risks=['authors[0].name/entity_id/dynasty/dynasty_basis与description.text、ai_note、dynasty_basis、period_basis是相互依赖的污染修复范围，不能只换entity_id','loss_status=lost依描述机读；作者校正不自动证明作品亡佚或存世','历史ai_note保留并追加纠正，禁止抹除误补僧肇的原决策'],apply_blockers=['核丁國鈞《補晉書藝文志》原页残字与《隋眾經目錄》对应条','核准确候选Entity身份与全引用；不以同名序互并','原人物身份裁决与著作归属污染修复分开，不扩大二组执行映射'])
cases.append(c)
write('cases.json',cases);write('candidate-ledger.json',{'schema':'research-only-person-field-ledger-v1','main_ref':REF,'ready_to_apply':False,'native_mutations':0,'merges':merges});write('validation.json',{'main_ref':REF,'source_snapshot_count':len(snaps),'rule_snapshot_count':len(rules),'field_checks':checks,'passed':all(all(v for k,v in c.items() if k!='case_id') for c in checks),'not_run':['official audit-merge-ledger against modified native tree','schema/check_v2 on actual changes','classification','build_derived','all references (delegated to root)'],'new_cases':0,'new_identity_decisions':0,'native_merges':0})
print(json.dumps({'snapshots':len(snaps),'field_rows':[len(g['field_ledger']) for g in merges],'cases':len(cases),'native_mutations':0}))
