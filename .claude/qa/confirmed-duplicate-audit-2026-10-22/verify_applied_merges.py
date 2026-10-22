#!/usr/bin/env python3
"""Verify the reviewed merge manifest against source files, independent of the writer."""
import json,pathlib,subprocess,collections,sys,gzip,argparse
def read_snapshot(path):
 if path.exists():return json.loads(path.read_text())
 return json.loads(gzip.decompress(path.with_name(path.name+'.gz').read_bytes()))

A=pathlib.Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=pathlib.Path);R=ap.parse_args().root.resolve();plan=read_snapshot(A/'merge-plan.json');before=read_snapshot(A/'merge-before.json');M=read_snapshot(A/'merge-map.json');after=read_snapshot(A/'merge-after.json')
errors=[];counts=collections.Counter();allpaths={i:n for p in plan for i,n in p['paths'].items()}
for n,d in after.items():
 if json.loads((R/n).read_text())!=d:errors.append(['write does not match reviewed projection',n])
for p in plan:
 typ=p['type'];keeper=json.loads((R/p['paths'][p['keeper']]).read_text());assert not keeper.get('merged_into')
 for i in p['losers']:
  d=json.loads((R/p['paths'][i]).read_text());allowed={'id','type','schema_version','title','merged_into','revision','revised_at'}
  if typ=='Entity':allowed.remove('title');allowed|={'primary_name','subtype'}
  if typ=='Book':allowed.add('work_id')
  if set(d)!=allowed:errors.append(['tombstone shape',i,set(d)^allowed])
  if d['merged_into']!=p['keeper']:errors.append(['tombstone target',i])
  if typ=='Book' and d['work_id']!=keeper['work_id']:errors.append(['tombstone work',i])
  if typ=='Book':history=keeper.get('merged_from',[])
  else:history=[x.get('id') if isinstance(x,dict) else x for x in keeper.get('merged_in',[])]
  if i not in history:errors.append(['history missing',i])
  if d['revision']==before[i]['record']['revision']:errors.append(['revision unchanged',i])
  counts[typ]+=1
# Independent exhaustive literal-ID search, including curation and root catalog files.
roots=['Entity','Work','Book','Collection','classification','curation','recommended.json','index.json','resource.json','resource-site.json','resource-collection.json','resource-catalog.json']
r=subprocess.run(['rg','-l','-F','-f',str(A/'merge-ids.txt'),*roots],cwd=R,capture_output=True,text=True);assert r.returncode in (0,1)
residual=collections.Counter();historical={'merged_in','merged_from','merge_history'}
def scan(x,n,path=()):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in M:errors.append(['loser used as live key',n,path,k])
   if k in historical:continue
   scan(v,n,path+(k,))
 elif isinstance(x,list):
  for v in x:scan(v,n,path+('[]',))
 elif isinstance(x,str) and x in M:
  if path==('id',):residual['tombstone identity']+=1
  else:errors.append(['stale live ID',n,path,x])
for n in r.stdout.splitlines():
 if n.endswith('.json'):scan(json.loads((R/n).read_text()),n)
report={'new_tombstones':dict(counts),'groups':dict(collections.Counter(p['type'] for p in plan)),'reviewed_projection_matches':len(after),'residual_exact_ids':dict(residual),'errors':errors}
(A/'verification-applied.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=list)+'\n');print(json.dumps(report,ensure_ascii=False,default=list));assert not errors
