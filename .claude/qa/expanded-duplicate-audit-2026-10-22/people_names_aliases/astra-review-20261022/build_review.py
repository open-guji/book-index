from pathlib import Path
import json,gzip,hashlib,subprocess,collections
ROOT=Path('/workspace/scratch/0bc7226fa660/book-index-expanded-pr')
OLD=Path('/workspace/scratch/0bc7226fa660/book-index')
P=ROOT/'.claude/qa/expanded-duplicate-audit-2026-10-22/people_names_aliases'
OUT=P/'astra-review-20261022'
SHA='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
def write(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
cs=json.loads((P/'cases.json').read_text())+json.loads((P/'hourly-20261022/cases.json').read_text())
sup={c.get('supersedes_case_id') for c in cs};cs=[c for c in cs if c['case_id'] not in sup]
snaps={}
for n in ['entity-snapshots.json','work-snapshots.json','batch2-entity-snapshots.json','batch2-work-snapshots.json']:
 snaps.update(json.loads((P/n).read_text()))
snaps.update(json.loads(gzip.decompress((P/'hourly-20261022/original-snapshots.json.gz').read_bytes())))
selected=[next(c for c in cs if c['case_id']==i) for i in ['PNA-R011','PNA-H002']]
paths={}
for c in cs:
 for i,p in c['paths'].items(): paths[p]=c.get('sha256',{}).get(i)
for c in selected:
 for i in c['related_record_ids']:
  s=snaps[i];paths[s['path']]=s['sha256']
rawtree=subprocess.check_output(['git','-c','gc.auto=0','ls-tree','-r','-z',SHA,'--',*paths],cwd=ROOT)
tree={}
for row in rawtree.split(b'\0'):
 if row:
  meta,p=row.split(b'\t',1);tree[p.decode()]=meta.decode().split()[2]
verified={};checks=[]
for p,baseline_hash in paths.items():
 raw=(OLD/p).read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 check={'path':p,'main_blob':tree.get(p),'local_blob':blob,'sha256':hashlib.sha256(raw).hexdigest(),'baseline_sha256':baseline_hash,'identical_to_main':blob==tree.get(p),'identical_to_research_baseline':hashlib.sha256(raw).hexdigest()==baseline_hash}
 checks.append(check)
 if check['identical_to_main']: verified[p]={'path':p,'sha256':check['sha256'],'git_blob':blob,'record':json.loads(raw)}
write('main-source-validation.json',{'main_sha':SHA,'method':'Compare SHA1 Git blob identity from fixed main ls-tree with exact bytes of old full checkout; only matching bytes treated as current main. No inference from old checkout age.','checked_paths':len(checks),'matching_paths':len(verified),'checks':checks})
coverage=[]
for c in cs:
 recs=[verified.get(p) for p in c['paths'].values()]
 coverage.append({'case_id':c['case_id'],'label':c['label'],'status':c['status'],'source_bytes_verified':all(recs),'merged_into':{i:verified[p]['record'].get('merged_into') for i,p in c['paths'].items() if p in verified},'applied':all(verified.get(c['paths'][l],{}).get('record',{}).get('merged_into')==c.get('keeper') for l in c.get('losers',[])) if c['status']=='confirmed' else None})
write('main-coverage.json',{'main_sha':SHA,'old_effective_counts':dict(collections.Counter(c['status'] for c in cs)),'cases':coverage,'applied_confirmed_groups':sum(c['applied'] is True for c in coverage),'not_applied_confirmed_groups':sum(c['status']=='confirmed' and c['source_bytes_verified'] and not c['applied'] for c in coverage),'new_native_merges':0})
write('selected-source-snapshots.json',{i:verified[snaps[i]['path']] for c in selected for i in [c['keeper'],*c['losers'],*c['related_record_ids']] if snaps[i]['path'] in verified})
refs=[];outcases=[];plans=[]
for j,c in enumerate(selected,1):
 all_verified=all(c['paths'][i] in verified for i in [c['keeper'],*c['losers']]) and all(snaps[i]['path'] in verified for i in c['related_record_ids'])
 if not all_verified: continue
 keeper=verified[c['paths'][c['keeper']]]['record'];loser=verified[c['paths'][c['losers'][0]]]['record']
 cr=[];ops=[]
 for i in c['related_record_ids']:
  s=verified[snaps[i]['path']];r=s['record'];a=[]
  for k,v in enumerate(r.get('authors',[])):
   if v.get('entity_id') in [c['keeper'],*c['losers']]:
    a.append({'json_pointer':f'/authors/{k}/entity_id','value':v['entity_id'],'name':v.get('name'),'role':v.get('role')})
    if v['entity_id'] in c['losers']:
     ops.append({'path':s['path'],'pre_sha256':s['sha256'],'op':'replace','json_pointer':f'/authors/{k}/entity_id','old':v['entity_id'],'new':c['keeper'],'preserve':['name','role','dynasty','name_basis','dynasty_basis']})
  cr.append({'path':s['path'],'sha256':s['sha256'],'id':i,'type':r['type'],'merged_into':r.get('merged_into'),'author_refs':a,'title':r.get('title'),'indexed_by':r.get('indexed_by',[])})
 refs+=cr
 cid=f'PNA-A00{j}'
 conflicts=[]
 for f in sorted(set(keeper)|set(loser)):
  if keeper.get(f)!=loser.get(f):conflicts.append({'field':f,'keeper':keeper.get(f),'loser':loser.get(f),'policy':'management fields follow merge engine; primary_name keeper; alt_names add surname+style; retain keeper existing biography; preserve complete loser ai_note and historical values in ledger'})
 outcases.append({'case_id':cid,'supersedes_case_id':c['case_id'],'status':'confirmed','review_kind':'current-main verification and candidate preparation; not new identity discovery','label':c['label'],'main_sha':SHA,'keeper':c['keeper'],'losers':c['losers'],'paths':c['paths'],'sha256':{i:verified[p]['sha256'] for i,p in c['paths'].items()},'identity_evidence':c['why'],'name_role':{'primary':keeper['primary_name'],'style':['希白'] if j==1 else ['子材','子才'],'alias':loser['primary_name'],'note':'姓連字全稱列別稱；字與號不混用。現有號不重新鑒定。'},'field_conflicts':conflicts,'known_current_reference_count':len(cr),'known_loser_reference_edits':len(ops),'reference_paths':[r['path'] for r in cr],'full_live_reference_scan_complete':False,'external_evidence':[{'url':'https://zh.wikisource.org/wiki/南部新書_(四庫全書本)','retrieval':'direct open unavailable; search result of public-domain Siku preface and main native indexed_by mutually support 易字希白'}] if j==1 else [{'url':'https://zh.wikisource.org/wiki/入蜀記/卷1','retrieval':'opened 2026-10-22; line 152 reads 喻子材郎中樗'}],'execution_status':'candidate plan only; cross-root/cross-repository and write-after validations remain','caveats':['No Work/Book merges authorized by this identity determination.','Prior external IDs, date and native place metadata are not independently recertified.']})
 add={'name':loser['primary_name'],'type':'別稱','note':f'姓連字之著錄稱呼；字為'+('希白' if j==1 else '子材（亦作子才）')+f'。見 {cid}。'}
 plans.append({'case_id':cid,'keeper':c['keeper'],'losers':c['losers'],'precondition_main_sha':SHA,'pre_sha256':{i:verified[p]['sha256'] for i,p in c['paths'].items()},'identity_mapping':{l:c['keeper'] for l in c['losers']},'entity_actions':[{'action':'append_alt_name_if_absent','target':c['keeper'],'value':add},{'action':'preserve_all_keeper_fields_except_merge_management_and_alt_names','target':c['keeper']},{'action':'archive_complete_originals_in_ledger','records':{c['keeper']:keeper,c['losers'][0]:loser}},{'action':'union_ai_note_description_sources_and_merge_history_with_original_owner','keeper':c['keeper'],'losers':c['losers']},{'action':'append_merged_in_and_create_schema_minimal_loser_tombstone','keeper':c['keeper'],'losers':c['losers']}],'known_typed_reference_operations':ops,'additional_reference_gate':'Before mutation, scan fixed/latest main Work, Book, Collection, Entity, classifications, promotions production_id, all other typed refs; scan draft and book-text. Known operations are not exhaustive. Historical prose and ledger IDs stay unchanged.','post_write_gates':['scripts/audit-merge-ledger.py T/L/P/R without ERROR; D linked draft PR or zero residual','check_v2.py --paths - on decoded actual changed paths','scripts/check-classification.py','build/build_derived.py --check-only'],'apply_enabled':False})
write('cases.json',outcases);write('references.json',refs);write('candidate-merge-plan.json',{'main_sha':SHA,'native_mutations':0,'plan_only':True,'cases':plans})
print(json.dumps({'checked':len(checks),'matches':len(verified),'cases':len(outcases),'groups':len(coverage),'applied':sum(c['applied'] is True for c in coverage),'drift':[c['path'] for c in checks if not c['identical_to_main']]},ensure_ascii=False),flush=True)
