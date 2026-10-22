"""Read-only full 集部 candidate discovery against shared, main-verified SQLite."""
import sqlite3,json,pathlib,re,itertools,collections,difflib,hashlib,sys
OUT=pathlib.Path(__file__).resolve().parent
AUDIT=OUT.parents[1]
DB=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite')
db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
def norm(s):
 return re.sub(r'[\s·•《》〈〉（）()\[\]【】「」『』，,。:：－—\-]','',str(s or '')).translate(str.maketrans('﨑峯羣峝菴窻淩鳬静啓脩槀刋','崎峰群洞庵窗凌鳧靜啟修稿刊'))
def first(d):
 a=d.get('authors') or []
 return a[0] if a else {}
def variants(d):
 vals=[d.get('title','')]
 for a in d.get('additional_titles',[]):
  vals.append(a if isinstance(a,str) else a.get('title',a.get('name','')))
 return set(filter(None,map(norm,vals)))
classified={r[0] for r in db.execute("SELECT DISTINCT work_id FROM membership WHERE division='集部'")}
W={}; meta={}; source_only=0
for rid,path,sha,h,data in db.execute("SELECT id,path,blob_sha,sha256,data FROM records WHERE type='Work' AND (id IN (SELECT work_id FROM membership WHERE division='集部') OR data LIKE '%集部%')"):
 d=json.loads(data)
 section=any(str(x.get('section','')).startswith('集部') for x in d.get('indexed_by',[]))
 if rid not in classified and not section:continue
 W[rid]=d;meta[rid]={'id':rid,'path':path,'blob_sha':sha,'sha256':h}
 if rid not in classified:source_only+=1
oldpairs=set(); oldids=set();oldcases={}
for f in AUDIT.glob('*/**/cases.json'):
 if OUT in f.parents:continue
 try:cs=json.loads(f.read_text())
 except Exception:continue
 if not isinstance(cs,list):continue
 for c in cs:
  if not isinstance(c,dict):continue
  ids=set()
  for key in ['records','evidence','works']:
   for e in c.get(key,[]) if isinstance(c.get(key,[]),list) else []:
    if isinstance(e,dict) and e.get('id') in W:ids.add(e['id'])
    elif isinstance(e,str) and e in W:ids.add(e)
  for v in [c.get('keeper')]+c.get('losers',[]):
   if isinstance(v,str) and v in W:ids.add(v)
  oldids.update(ids)
  for p in itertools.combinations(sorted(ids),2):oldpairs.add(p);oldcases.setdefault(p,set()).add(c.get('case_id'))
old_candidate_pairs=set()
for c in json.loads((OUT.parent/"same-source-summary-candidates.json").read_text()):
 for p in itertools.combinations(sorted(m["id"] for m in c["members"]),2):old_candidate_pairs.add(p)
pairs=collections.defaultdict(set)
def add(a,b,why):
 if a!=b:pairs[tuple(sorted((a,b)))].add(why)
# 1. Explicit alias equality, regardless of author. Exact title alone requires same author.
titlemap=collections.defaultdict(set);authors=collections.defaultdict(set);summaries=collections.defaultdict(set)
for rid,d in W.items():
 for v in variants(d):titlemap[v].add(rid)
 a=first(d)
 if a.get('name') in ['佚名','不著撰人','不詳','無名氏','闕名']:a={}
 if a.get('entity_id'):authors['id:'+a['entity_id']].add(rid)
 if a.get('name'):authors['name:'+norm(a['name'])].add(rid)
 for src in d.get('indexed_by',[]):
  s=norm(src.get('summary',''))
  if len(s)>=100:summaries[(src.get('source_bid',src.get('source','')),s)].add(rid)
for title,ids in titlemap.items():
 for a,b in itertools.combinations(sorted(ids),2):
  if norm(W[a].get('title'))!=title or norm(W[b].get('title'))!=title:add(a,b,'explicit_alias_equal')
for key,ids in summaries.items():
 if len(ids)<=25:
  for a,b in itertools.combinations(sorted(ids),2):add(a,b,'same_source_long_summary')
examined=set()
for aid,ids in authors.items():
 for a,b in itertools.combinations(sorted(ids),2):
  if (a,b) in examined:continue
  examined.add((a,b));x=norm(W[a].get('title'));y=norm(W[b].get('title'))
  if x==y:add(a,b,'same_title_first_author')
  elif len(x)>=2 and len(y)>=2:
   ratio=difflib.SequenceMatcher(None,x,y).ratio()
   if ratio>=.72 or ((x in y or y in x) and min(len(x),len(y))>=3):add(a,b,'same_author_title_similar')
   xx=re.sub(r'(先生|居士|文忠公|文公|公|詩文|詩|文|全集|別集|集|稿|鈔|抄|選|續|前|後|外|遺|初|二|三|四)','',x)
   yy=re.sub(r'(先生|居士|文忠公|文公|公|詩文|詩|文|全集|別集|集|稿|鈔|抄|選|續|前|後|外|遺|初|二|三|四)','',y)
   if xx==yy and len(xx)>=2:add(a,b,'same_author_core_scope_variants')
   ja=W[a].get('juan_count',{});jb=W[b].get('juan_count',{})
   if isinstance(ja,dict) and isinstance(jb,dict) and ja.get('number')==jb.get('number') and isinstance(ja.get('number'),(int,float)) and ja['number']>=2 and re.search(r'[集稿鈔詩文]$',x) and re.search(r'[集稿鈔詩文]$',y):add(a,b,'same_author_equal_extent_different_title')
# Connected components are discovery groups, never merge components.
parent={}
def find(x):
 parent.setdefault(x,x)
 if parent[x]!=x:parent[x]=find(parent[x])
 return parent[x]
def union(a,b):parent[find(a)]=find(b)
rows=[]
for p,why in pairs.items():
 a,b=p;union(a,b)
 rows.append({'ids':list(p),'titles':[W[x].get('title') for x in p],'authors':[first(W[x]) for x in p],'channels':sorted(why),'old_pair':p in oldpairs,'previously_discovered_pair':p in old_candidate_pairs,'old_cases':sorted(oldcases.get(p,[])),'old_record_overlap':any(x in oldids for x in p)})
groups=collections.defaultdict(list)
for rid in parent:groups[find(rid)].append(rid)
rows.sort(key=lambda r:(r['old_pair'],-int('explicit_alias_equal' in r['channels']),-int('same_source_long_summary' in r['channels']),-int('same_title_first_author' in r['channels']),r['titles']))
counts=collections.Counter(ch for r in rows for ch in r['channels'])
stats={'base':json.loads(db.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()[0]),'scope':{'classification_members':len(classified),'active_collection_works':len(W),'source_section_only':source_only,'author_pair_comparisons':len(examined),'author_buckets':len(authors)},'candidate_unique_pairs':len(rows),'candidate_unique_groups':len(groups),'old_pair_repeats':sum(r['old_pair'] for r in rows),'new_candidate_pairs':sum(not r['old_pair'] for r in rows),'previous_candidate_repeats':sum(r['previously_discovered_pair'] for r in rows),'discovery_new_pairs':sum(not r['old_pair'] and not r['previously_discovered_pair'] for r in rows),'pairs_overlapping_old_record':sum(r['old_record_overlap'] for r in rows),'channels_nonadditive':dict(counts),'candidate_is_not_confirmation':True}
for name,obj in [('candidates.json',rows),('candidate-groups.json',[sorted(v) for v in groups.values()]),('scan-stats.json',stats),('scan-records.json',meta)]:
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in stats.items() if k!='base'},ensure_ascii=False,indent=2))
for r in rows[:100]:print(r['ids'],r['titles'],r['channels'])
