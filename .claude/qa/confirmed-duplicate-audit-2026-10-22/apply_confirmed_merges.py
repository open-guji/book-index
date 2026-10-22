#!/usr/bin/env python3
"""Apply the reviewed duplicate manifest. Dry-run by default; guards reject changed sources.
Only typed live references are redirected. Original records and conflict decisions
are retained in merge-before.json and merge-plan.json beside this script.
"""
import argparse,copy,hashlib,json,pathlib,subprocess,sys,collections,gzip
def read_snapshot(path):
 if path.exists():return json.loads(path.read_text())
 return json.loads(gzip.decompress(path.with_name(path.name+'.gz').read_bytes()))

HERE=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--root',type=pathlib.Path,required=True);ap.add_argument('--apply',action='store_true');args=ap.parse_args();R=args.root.resolve()
sys.path.insert(0,str(R/'build'));import v2common as V
plan=read_snapshot(HERE/'merge-plan.json');refpaths=read_snapshot(HERE/'merge-reference-files.json')
M={i:p['keeper'] for p in plan for i in p['losers']};P={i:p for p in plan for i in [p['keeper']]+p['losers']};paths={i:n for p in plan for i,n in p['paths'].items()}
DATE='2026-10-22';STAMP='2026-10-22T00:00:00Z';BY='Codex';RULE='confirmed-duplicate-audit-2026-10-22'
cache={};original={};fmt={};events=[]
def load(n):
 if n not in cache:
  raw=(R/n).read_text();d=json.loads(raw);cache[n]=d;original[n]=copy.deepcopy(d);fmt[n]=V.detect_format(raw,d)
 return cache[n]
def record(i,typ='Work'):
 if i not in paths:
  matches=list((R/typ/i[-3]/i[-2]/i[-1]).glob(i+'-*.json'))
  if len(matches)!=1:raise ValueError(('record resolution',i,matches))
  paths[i]=str(matches[0].relative_to(R))
 return load(paths[i])
def unique(xs):
 out=[]
 for x in xs:
  if x not in out:out.append(copy.deepcopy(x))
 return out

def addnote(d,n):
 old=d.get('ai_note','')
 if n and n not in old:d['ai_note']=(old+'\n\n'+n).strip()
def next_revision(d,major=False):
 a,b,c=map(int,d.get('revision','1.0.0').split('.'));return f'{a+1}.0.0' if major else f'{a}.{b+1}.0'
def bump(d):d['revision']=next_revision(d,d.get('type')=='book');d['revised_at']=DATE
# Abort before any write if a reviewed source has changed.
for p in plan:
 for i,n in p['paths'].items():
  assert hashlib.sha256((R/n).read_bytes()).hexdigest()==p['sha256'][i],('stale source',i)
  assert not load(n).get('merged_into'),('already merged',i)
# All source bytes are loaded before mutation; original provides a rollback/comparison view.
for p in plan:
 k=p['keeper'];d=record(k,p['type']);decision=p['decision'];typ=p['type']
 for i in p['losers']:
  src=copy.deepcopy(original[p['paths'][i]])
  for field,val in src.items():
   if field in {'id','type','schema_version','revision','revised_at','updated_at','merged_into','primary_name','title','work_id','authors','description','ai_note','alt_names'}:continue
   if typ=='Entity':
    if field not in {'merged_in','merge_history','sources','suppressed_fields'}:continue
   if typ=='Work' and decision and field not in {'indexed_by','emendated_by','resources','contained_in','related_works','additional_titles','merged_in','merged_from'}:continue
   if field=='resources' and k=='988g4v5jid':continue
   if field not in d:d[field]=copy.deepcopy(val)
   elif isinstance(val,list) and isinstance(d[field],list):
    if field in {'indexed_by','emendated_by'} and typ=='Work' and decision:d[field].extend(copy.deepcopy(val))
    else:d[field]=unique(d[field]+val)
  if typ!='Entity' and src.get('title')!=d.get('title'):
   if i!='988g85ghdx':d['additional_titles']=unique(d.get('additional_titles',[])+[src['title']])
  if typ=='Book' and not d.get('authors') and src.get('authors'):d['authors']=copy.deepcopy(src['authors'])
  if src.get('ai_note') and src['ai_note']!=d.get('ai_note'):addnote(d,f"被併條 {i} 原處理記錄：\n"+src['ai_note'])
  if typ=='Book':
   old=d.get('merged_from',[]);old=[old] if isinstance(old,str) else old;d['merged_from']=unique(old+[i])
  else:
   label='primary_name' if typ=='Entity' else 'title'
   why=decision.get('why') or decision.get('evidence') or decision.get('append_ai_note') or '業務欄位一致，且原始來源記錄識別碼相同；詳本批merge-plan.json。'
   if isinstance(why,list):why=' '.join(why)
   d.setdefault('merged_in',[]).append({'id':i,label:src.get(label,''),'at':STAMP,'by':BY,'rule':RULE,'why':why})
  tomb={key:src[key] for key in ('id','type','schema_version','subtype','primary_name','title','work_id') if key in src and (key not in ('subtype',) or typ=='Entity')}
  tomb.update(merged_into=k,revision=next_revision(src,typ=='Book'),revised_at=DATE)
  cache[p['paths'][i]]=tomb
 if typ=='Entity':
  d.update(copy.deepcopy(decision['field_overrides']))
  for f in decision.get('field_delete',[]):d.pop(f,None)
 elif typ=='Work':
  updates=decision.get('set_fields') or decision.get('resolved_fields_from_audit_baseline') or {}
  for f,val in updates.items():
   if f=='additional_titles':d[f]=unique(d.get(f,[])+val)
   else:d[f]=copy.deepcopy(val)
  for f in decision.get('remove_fields',[]):d.pop(f,None)
  if decision.get('add_additional_titles'):d['additional_titles']=unique(d.get('additional_titles',[])+decision['add_additional_titles'])
  if decision.get('remove_related_work_ids'):d['related_works']=[x for x in d.get('related_works',[]) if x.get('id') not in decision['remove_related_work_ids']]
  if decision.get('add_related_works'):d['related_works']=unique(d.get('related_works',[])+decision['add_related_works'])
  if decision.get('append_ai_note'):addnote(d,decision['append_ai_note'])
 else:
  wr=decision['work_resolution']
  if wr.get('work_id'):d['work_id']=wr['work_id']
  d['work_id']=M.get(d['work_id'],d['work_id'])
  for f,pol in (decision.get('manual_field_policy') or {}).get('fields',{}).items():
   if pol.get('action') in {'keeper','keeper_superset'}:
    if f in original[paths[k]]:d[f]=copy.deepcopy(original[paths[k]][f])
   if pol.get('action')=='union_with':d[f]=unique(d.get(f,[])+pol['value'])
  sd=p.get('semantic_decision',{})
  for f,pol in sd.get('field_decisions',{}).items():
   if 'value' in pol:d[f]=copy.deepcopy(pol['value'])
 addnote(d,f'{DATE} {RULE}：合併已核定重複條 {"、".join(p["losers"])}；原記錄、保留ID與衝突欄位裁決見 .claude/qa/{RULE}/。')
 bump(d)
# Book tombstones retain a valid canonical Work, including the 111 missing-old-Work cases.
for p in plan:
 if p['type']=='Book':
  for i in p['losers']:cache[paths[i]]['work_id']=cache[paths[p['keeper']]]['work_id']
# The global inventory of exact loser-ID occurrences contains only these typed
# locations (plus record identity and historical ledgers). Reject any new pattern.
LIVE={('authors','[]','entity_id'),('work_id',),('related_works','[]','id'),('merged_into',)}
HISTORY={'merged_in','merged_from','merge_history'}
refcounts=collections.Counter()
def redirect(x,where=()):
 if isinstance(x,dict):
  for key,val in list(x.items()):
   if key in HISTORY:continue
   loc=where+(key,)
   if isinstance(val,str) and val in M:
    if loc==('id',):continue
    if loc not in LIVE:raise ValueError(('unreviewed reference',loc,val))
    x[key]=M[val];refcounts['.'.join(loc)]+=1
   else:redirect(val,loc)
 elif isinstance(x,list):
  for val in x:redirect(val,where+('[]',))
# Include keepers newly holding unioned references, plus all source matches.
for n in sorted(set(refpaths)|set(cache)):
 if n.startswith('classification/'):
  d=load(n);rows=d.get('members',[])
  for row in rows:
   if row[0] in M:row[0]=M[row[0]];refcounts['classification.members']+=1
  byid={}
  for row in rows:
   if row[0] not in byid:byid[row[0]]=copy.deepcopy(row)
   elif row!=byid[row[0]]:
    assert len(row)==2 and len(byid[row[0]])==2,('member shape',row)
    byid[row[0]][1]='；'.join(dict.fromkeys([byid[row[0]][1],row[1]]))
  d['members']=sorted(byid.values(),key=lambda row:row[0])
 else:redirect(load(n))
# Name corrections are intentionally restricted to reviewed structural author rows.
for p in plan:
 if p['type']!='Entity':continue
 for fix in p['decision'].get('author_name_fixes',[]):
  match=fix['match'];entityids={M.get(i,i) for i in match['entity_id_in']}
  for n,d in list(cache.items()):
   if n.split('/')[0] not in fix['scope'] or d.get('merged_into'):continue
   for au in d.get('authors',[]):
    if au.get('entity_id') in entityids and au.get('name')==match['name']:
     old=copy.deepcopy(au)
     for f,val in fix['set'].items():
      if f=='role' and au.get('role') not in fix.get('only_change_role_when_old_role',[au.get('role')]):continue
      au[f]=val
     if fix.get('preserve_previous_name_as'):au[fix['preserve_previous_name_as']]=old['name']
     for f in ('name_basis','role_basis'):
      if fix.get(f+'_append'):au[f]=(au.get(f,'')+' '+fix[f+'_append']).strip()
     if n not in {paths[x['keeper']] for x in plan}:bump(d)
     events.append({'path':n,'author_before':old,'author_after':copy.deepcopy(au)})
# Canonicalize affected relationship endpoints after redirecting; keep differing notes.
for n,d in list(cache.items()):
 if not n.startswith('Work/') or d.get('merged_into') or not d.get('related_works'):continue
 rows=[]
 for edge in d['related_works']:
  dst=edge.get('id');src=d['id']
  if dst==src:events.append({'path':n,'removed_self_relation':edge});continue
  a,b,rel=V.canon_edge(src,dst,edge['relation'])
  e=copy.deepcopy(edge);e['id']=b;e['relation']=rel
  if a==src:rows.append(e)
  else:
   target=record(a);e['id']=src
   if 'title' in e:e['title']=d.get('title','')
   target['related_works']=unique(target.get('related_works',[])+[e])
  if a==src and 'title' in e:e['title']=record(dst).get('title',e['title'])
 d['related_works']=unique(rows)
 if not rows:d.pop('related_works',None)
# Classification is exclusive: never choose a class silently.
classes=collections.defaultdict(list)
work_keepers={p['keeper'] for p in plan if p['type']=='Work'}
for n in (R/'classification').glob('*/members/*.json'):
 rel=str(n.relative_to(R));d=cache.get(rel) or json.loads(n.read_text())
 for row in d['members']:
  if row[0] in work_keepers:classes[row[0]].append((rel,row))
# Apply explicit reviewed choices for mutually exclusive classification nodes.
choices={}
for cf in ('merge_classification_early.json','merge_classification_late.json'):
 if (HERE/cf).exists():
  cd=json.loads((HERE/cf).read_text())
  if 'decisions' in cd:
   choices.update({d['keeper']:{'node':d['selected_node'],'reason':d['reason'],'member_source':d['selected_member_row'][1]} for d in cd['decisions']})
  else:choices.update(cd)
for i,rows in classes.items():
 if len(rows)>1 and i in choices:
  keep=choices[i]['node']
  for rel,row in rows:
   if pathlib.Path(rel).stem!=keep:
    obj=load(rel);obj['members']=[x for x in obj['members'] if x[0]!=i]
    events.append({'classification_removed':rel,'row':row,'reason':choices[i]['reason']})
  classes[i]=[(rel,row) for rel,row in rows if pathlib.Path(rel).stem==keep]
  if not classes[i]:
   rel=f'classification/zongmu/members/{keep}.json';obj=load(rel);row=[i,choices[i].get('member_source',choices[i].get('source'))];obj['members'].append(row);obj['members'].sort(key=lambda x:x[0]);classes[i]=[(rel,row)]
   events.append({'classification_added':rel,'row':row,'reason':choices[i]['reason']})
conflicts={i:rows for i,rows in classes.items() if len(rows)>1}
if conflicts:(HERE/'classification-conflicts.json').write_text(json.dumps(conflicts,ensure_ascii=False,indent=2)+'\n');raise ValueError(('classification conflicts',len(conflicts)))
changed={n:d for n,d in cache.items() if d!=original[n]}
for p in plan:
 for i in p['losers']:assert cache[paths[i]]['merged_into']==p['keeper'] and not cache[paths[p['keeper']]].get('merged_into')
report={'groups':dict(collections.Counter(p['type'] for p in plan)),'tombstones':len(M),'changed_files':len(changed),'typed_reference_updates':dict(refcounts),'events':events,'paths':sorted(changed)}
(HERE/'merge-dry-run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(HERE/'merge-after.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n')
(HERE/'changed-before.json').write_text(json.dumps({n:original[n] for n in changed},ensure_ascii=False,indent=2)+'\n')
(HERE/'merge-changed-paths.txt').write_text('\n'.join(sorted(changed))+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('paths','events')},ensure_ascii=False),flush=True)
if args.apply:
 # Store original Git blobs before writing; parent trees were fetched with blob filtering.
 subprocess.run(['git','hash-object','-w','--stdin-paths'],input=''.join(n+'\n' for n in changed).encode(),cwd=R,stdout=subprocess.DEVNULL,check=True)
 for n,d in changed.items():
  p=R/n;tmp=p.with_suffix('.json.tmp')
  if n.startswith('classification/'):
   body='{\n  \"node\": '+json.dumps(d['node'],ensure_ascii=False)+',\n  \"members\": [\n'+',\n'.join('    '+json.dumps(row,ensure_ascii=False) for row in d['members'])+'\n  ]\n}\n'
  else:body=V.dump(d,fmt[n])
  tmp.write_text(body);tmp.replace(p)
 print('APPLIED',len(changed),flush=True)
