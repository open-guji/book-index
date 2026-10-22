import json,pathlib,copy,gzip,hashlib
O=pathlib.Path(__file__).parent; A=json.loads((O/'prefix-records.json').read_text())
rows=json.loads((O/'prefix_specs.json').read_text());S={};specs=[]
for cid,k,ls,status,url,why in rows:
 S[cid]={'url':url,'title':A[k]['record']['primary_name']+' 人物與著錄佐證','support':why,'retrieved_at':'2026-10-22'}
 specs.append((cid,k,ls,status,cid,why))
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
  out[f]=selected;fd[f]={'action':policy,'selected':selected,'original_values':vals,'reason':'字段原值全部保存在 prefix-records.json；非衝突資訊保留到 canonical；衝突不擅自聲稱外部權威ID等價。'}
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
 if cid in ['PRV-P001','PRV-P013']:
  targets={'優曇'} if cid=='PRV-P001' else {'月川','空印'}
  for x in alts:
   if isinstance(x,dict) and x.get('name') in targets:
    original_type=x.get('type');x['type']='別名';x['note']='原type='+str(original_type)+'；字/號分類資料互有異說，本批不強定。'+why
 out['alt_names']=alts
 note='2026-10-22 expanded duplicate audit '+cid+'：'+why+' 證據：'+S[src]['url']
 if archive:note+=' 合併前衝突原值存檔：'+json.dumps(archive,ensure_ascii=False)
 out['ai_note']=out.get('ai_note','')+'\n\n'+note
 # preserve review conservatively: no human-reviewed status is fabricated.
 if any(d.get('review',{}).get('status')=='unreviewed' for d in ds):out['review']={'status':'unreviewed'}
 # Legacy sparse entity may omit required subtype; integration must set it.
 out['subtype']='people'
 c={'case_id':cid,'cluster_id':cid,'type':'Entity','status':status,'keeper':k,'losers':ls,'why':why,'evidence':[S[src]],'records':[{'id':i,'path':A[i]['path'],'sha256':A[i]['sha256'],'primary_name':A[i]['record']['primary_name']} for i in ids],'related_work_ids':unique([w['record']['id'] for i in ids for w in A[i]['works']]),'work_review':{'coverage':'all current live Work.authors[].entity_id references scanned','count':sum(len(A[i]['works']) for i in ids),'snapshots':'prefix-records.json'},'field_decisions':fd}
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
(O/'cases-prefix.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
(O/'sources-prefix.json').write_text(json.dumps(S,ensure_ascii=False,indent=2)+'\n')
with gzip.open(O/'original-prefix-records.json.gz','wt',encoding='utf8') as f:json.dump(A,f,ensure_ascii=False)
counts={s:sum(c['status']==s for c in cases) for s in ['confirmed','open','separate']}
(O/'stats-prefix.json').write_text(json.dumps({'base':'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca','counts':counts,'confirmed_losers':sum(len(c['losers']) for c in cases if c['status']=='confirmed'),'entity_snapshots':len(A),'work_snapshots':sum(len(v['works']) for v in A.values()),'confirmed_related_works':len(set(w for c in cases if c['status']=='confirmed' for w in c['related_work_ids']))},indent=2)+'\n')
print(counts)
