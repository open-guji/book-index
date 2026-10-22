#!/usr/bin/env python3
"""Read-only current-main Work scan. Candidate signals are not identity decisions."""
import gzip,json,sqlite3,pathlib,collections,itertools,re,unicodedata
ROOT=pathlib.Path('/workspace/scratch/0bc7226fa660')
OUT=pathlib.Path(__file__).resolve().parent
DB=ROOT/'audit/broad-current.sqlite'
db=sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True)
manifest=json.loads(db.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()[0])
assert manifest['base']=='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
rows={r[0]:dict(zip(['id','type','name','path','blob_sha','sha256','data'],r)) for r in db.execute("SELECT * FROM records WHERE type='Work'")}
for r in rows.values():r['data']=json.loads(r['data'])
scope={r[0] for r in db.execute("SELECT DISTINCT work_id FROM membership WHERE division='子部'")} & rows.keys()
source_scope={i for i,r in rows.items() if any(str(x.get('section','')).startswith('子部') for x in r['data'].get('indexed_by',[]))}
scope|=source_scope
variants=str.maketrans({'畧':'略','祕':'秘','註':'注','刋':'刊','羣':'群','辯':'辨','徵':'徴','啓':'啟','録':'錄','説':'說','内':'內','叙':'敘','册':'冊'})
def norm(s):return re.sub(r'[^\w\u3400-\u9fff]','',unicodedata.normalize('NFKC',s).translate(variants))
entity_aliases=collections.defaultdict(set)
entity_alias_records={}
for eid,raw in db.execute("SELECT id,data FROM records WHERE type='Entity'"):
 e=json.loads(raw)
 if e.get('subtype')!='people':continue
 ns={e.get('primary_name','')}
 for a in e.get('alt_names',[]):
  v=a if isinstance(a,str) else a.get('name','')
  if len(v)>=2:ns.add(v)
  if isinstance(a,dict) and a.get('type') in ['字','號'] and len(v)>=2 and len(e.get('primary_name','')) in [2,3]:ns.add(e['primary_name'][0]+v)
 for n in ns:
  if len(n)>=2:entity_aliases[norm(n)].add(eid)
 entity_alias_records[eid]={'name':e.get('primary_name'),'alt_names':e.get('alt_names',[]),'dynasty':e.get('dynasty')}
def authkeys(o):
 out=set()
 for a in o.get('authors',[])[:1]:
  if not isinstance(a,dict):continue
  n=norm(a.get('name',''))
  if n in entity_aliases and len(entity_aliases[n])==1:out.add('entity-alias-candidate:'+next(iter(entity_aliases[n])))
  if n and n not in ['佚名','無名氏','不詳','闕名','失名','匿名']:out.add('name:'+n+':'+a.get('dynasty',o.get('dynasty','')))
  for k in ['id','entity_id','person_id']:
   if a.get(k):out.add('id:'+a[k])
  s=a.get('source',{})
  if isinstance(s,dict) and str(s.get('details','')).startswith('http'):out.add('uri:'+s['details'])
 return out
names=collections.defaultdict(list); authors=collections.defaultdict(list); normalized={}
for i,r in rows.items():
 n=norm(r['name']);normalized[i]=n;names[n].append(i)
 for a in authkeys(r['data']):authors[a].append(i)
pairs=collections.defaultdict(set)
def add(a,b,signal):
 if a!=b and (a in scope or b in scope):pairs[tuple(sorted([a,b]))].add(signal)
for n,ids in names.items():
 if len(ids)>1 and any(i in scope for i in ids):
  for a,b in itertools.combinations(ids,2):add(a,b,'normalized-title' if rows[a]['name']!=rows[b]['name'] else 'exact-title')
# Deliberately conservative similarity: one insertion/deletion/substitution, or containment.
def close(a,b):
 if min(len(a),len(b))<3:return False
 if a in b or b in a:return True
 if abs(len(a)-len(b))>1:return False
 if len(a)==len(b):return sum(x!=y for x,y in zip(a,b))<=1
 if len(a)>len(b):a,b=b,a
 return any(a==b[:j]+b[j+1:] for j in range(len(b)))
skipped=[]
for key,ids in authors.items():
 if not any(i in scope for i in ids) or len(ids)<2:continue
 if len(ids)>1200:skipped.append([key,len(ids)]);continue
 for a,b in itertools.combinations(ids,2):
  if normalized[a]!=normalized[b] and close(normalized[a],normalized[b]):add(a,b,'same-first-author-near-title')
# Explicit Work alternate titles only. Indexed bibliography parentheses may be parts, not aliases.
for i in scope:
 o=rows[i]['data']
 for field in ['additional_titles','aliases','alt_titles','alternative_titles','alternate_titles','other_titles','title_aliases']:
  vals=o.get(field,[]);vals=[vals] if isinstance(vals,str) else vals
  if not isinstance(vals,list):continue
  for v in vals:
   v=v if isinstance(v,str) else (v.get('title',v.get('name','')) if isinstance(v,dict) else '')
   for j in names.get(norm(v),[]):add(i,j,'explicit-alternate-title')
 for entry in o.get('indexed_by',[]):
  for v in re.findall(r'[（(]([^()（）]{3,40})[）)]',entry.get('title_info','')):
   v=re.sub(r'^[又一別原亦]名','',v);v=re.sub(r'[一二三四五六七八九十百零〇兩上下中]+卷.*$','',v)
   for j in names.get(norm(v),[]):add(i,j,'catalogue-parenthesis-needs-scope-check')
# Capture any old case pair, including superseded case evidence, across six lanes.
old=collections.defaultdict(list)
for p in OUT.parents[1].rglob('cases.json'):
 if 'broad-20261022' in str(p):continue
 try:cs=json.load(open(p))
 except Exception:continue
 if not isinstance(cs,list):continue
 for c in cs:
  ids=set(c.get('ids',[]));ids.update(c.get('losers',[]))
  if c.get('keeper'):ids.add(c['keeper'])
  for r in c.get('records',[]):
   if isinstance(r,dict) and r.get('id'):ids.add(r['id'])
  for a,b in itertools.combinations(sorted(ids & rows.keys()),2):old[(a,b)].append(c.get('case_id',str(p)))
result=[]
for (a,b),signals in sorted(pairs.items()):
 x,y=rows[a]['data'],rows[b]['data']
 result.append({'ids':[a,b],'titles':[rows[a]['name'],rows[b]['name']],'signals':sorted(signals),'old_cases':sorted(set(old.get((a,b),[]))),'first_authors':[x.get('authors',[])[:1],y.get('authors',[])[:1]],'same_first_author_keys':sorted(authkeys(x)&authkeys(y)),'indexed_by':[x.get('indexed_by',[]),y.get('indexed_by',[])]})
# Connected groups are reporting containers; never assumed to be one work.
parents={}
def find(x):
 parents.setdefault(x,x)
 if parents[x]!=x:parents[x]=find(parents[x])
 return parents[x]
for a,b in pairs:parents[find(a)]=find(b)
groups=collections.defaultdict(list)
for i in parents:groups[find(i)].append(i)
summary={'base':manifest['base'],'database_manifest':manifest,'active_work_scanned':len(rows),'masters_classification_or_source_scope':len(scope),'masters_source_section_scope':len(source_scope),'people_entities_with_alias_lookup':len(entity_alias_records),'unambiguous_name_alias_keys':sum(len(v)==1 for v in entity_aliases.values()),'unique_candidate_pairs':len(result),'unique_candidate_groups':len(groups),'old_case_repeat_pairs':sum(bool(x['old_cases']) for x in result),'new_candidate_pairs':sum(not x['old_cases'] for x in result),'signal_pair_counts':dict(collections.Counter(s for x in result for s in x['signals'])),'oversized_author_buckets_skipped':skipped,'native_data_mutated':False,'all_candidates_are_unreviewed_until_in_cases':True}
(OUT/'candidate-pairs.json.gz').write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
(OUT/'scope-work-ids.json').write_text(json.dumps(sorted(scope)))
(OUT/'candidate-groups.json').write_text(json.dumps(list(groups.values()),ensure_ascii=False,indent=2))
(OUT/'scan-stats.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(OUT/'candidate-records.json.gz').write_bytes(gzip.compress(json.dumps([rows[i] for i in sorted(parents)],ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
print(json.dumps(summary,ensure_ascii=False,indent=2))
