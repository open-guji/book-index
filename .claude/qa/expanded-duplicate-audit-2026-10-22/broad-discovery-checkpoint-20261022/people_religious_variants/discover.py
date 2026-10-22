"""Read-only full current Entity discovery. Candidate edges are NOT identity judgments."""
import sqlite3,json,re,collections,itertools,pathlib,unicodedata
ROOT=pathlib.Path('/workspace/scratch/0bc7226fa660')
HERE=pathlib.Path(__file__).resolve().parent
AUDIT=HERE.parent.parent
DB=ROOT/'audit/broad-current.sqlite'
con=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
manifest=json.loads(con.execute("select value from metadata where key='manifest'").fetchone()[0])
people={}
for row in con.execute("select id,name,path,blob_sha,sha256,data from records where type='Entity'"):
 d=json.loads(row[5])
 if d.get('subtype')=='people':people[row[0]]={'id':row[0],'name':row[1],'path':row[2],'blob_sha':row[3],'sha256':row[4],'record':d}
religion=re.compile(r'釋|禪師|禅师|法師|法师|沙門|沙门|比丘|道士|真人|僧人|僧侣|僧侶|高僧|禪僧|禅僧|詩僧|诗僧|佛教|天師|天师|道教|道號|道号|法號|法号|法名|僧名|帝王|皇帝|廟號|庙号|諡號|谥号|太祖|高祖|太宗|世祖|世宗|仁宗|高宗|玄宗|徽宗|神宗|武帝|文帝|明帝|哀帝')
scope={i for i,x in people.items() if religion.search(x['name']) or re.search(r'禪師|法師|沙門|比丘|道士|真人|僧|佛教|天師|道教|帝王|皇帝|廟號|諡號',json.dumps({k:x['record'].get(k) for k in ['description','alt_names']},ensure_ascii=False))}
# Deliberately finite character equivalences; these only retrieve candidates.
trans=str.maketrans({'释':'釋','禅':'禪','昙':'曇','净':'淨','觉':'覺','观':'觀','圆':'圓','义':'義','昇':'升','恵':'惠','慧':'惠','叡':'睿','峯':'峰','隠':'隱','隠':'隱','澂':'澄','毗':'毘','镕':'鎔','眞':'真','鑒':'鑑','祐':'佑','竺':'竺','髙':'高'})
prefix=re.compile(r'^(?:(?:後秦|姚秦|北魏|南宋|北宋|東晉|西晉|後唐|後漢|後周|南唐|大唐|大宋|大明|大清|唐|宋|元|明|清|隋|晉|梁|陳|周|漢))?(?:釋|沙門|僧)')
suffix=re.compile(r'(?:禪師|法師|大師|上人|道人|和尚|比丘|真人)$')
def norm(s):
 s=unicodedata.normalize('NFKC',s);s=re.sub(r'[\s·・（）()\[\]〔〕]','',s).translate(trans)
 s=prefix.sub('',s);s=suffix.sub('',s)
 return s
keys=collections.defaultdict(list)
for i,x in people.items():
 names=[(x['name'],'primary')]+[(a.get('name',''),'alias') for a in x['record'].get('alt_names',[]) if isinstance(a,dict)]
 for s,kind in names:
  k=norm(s)
  if 2<=len(k)<=16:keys[k].append((i,s,kind))
edges={}
for k,items in keys.items():
 ids={a[0] for a in items}
 if len(ids)<2 or not(ids&scope):continue
 for a,b in itertools.combinations(sorted(ids),2):
  if a not in scope and b not in scope:continue
  e=edges.setdefault((a,b),{'ids':[a,b],'signals':[]})
  sig={'kind':'name_or_alias_normalization','key':k,'forms':[[i,s,t] for i,s,t in items if i in [a,b]]}
  if sig not in e['signals']:e['signals'].append(sig)
# Shared external authorities: exclude editorial status/source fields and null values.
auth=collections.defaultdict(set)
for i,x in people.items():
 for k,v in x['record'].get('external_ids',{}).items():
  if isinstance(v,(str,int)) and v and not any(s in k for s in ['match','source','note']) and str(v).lower() not in ['none','null','unknown','0']:
   auth[(k,str(v))].add(i)
for (k,v),ids in auth.items():
 if len(ids)<2 or not(ids&scope):continue
 for a,b in itertools.combinations(sorted(ids),2):
  if a not in scope and b not in scope:continue
  edges.setdefault((a,b),{'ids':[a,b],'signals':[]})['signals'].append({'kind':'shared_external_id','field':k,'value':v})
old=collections.defaultdict(set)
for p in AUDIT.glob('*/**/cases*.json'):
 if 'broad-20261022' in p.parts:continue
 try:cases=json.load(open(p))
 except:continue
 if isinstance(cases,dict):cases=cases.get('cases',[])
 if not isinstance(cases,list):continue
 for c in cases:
  if not isinstance(c,dict) or not c.get('case_id'):continue
  ids=set(c.get('losers',[])); keeper=c.get('keeper')
  if isinstance(keeper,str):ids.add(keeper)
  for r in c.get('records',[]):
   if isinstance(r,dict) and r.get('id') in people:ids.add(r['id'])
  for a,b in itertools.combinations(sorted(ids&people.keys()),2):old[(a,b)].add(c['case_id'])
rows=[]
for n,(pair,e) in enumerate(sorted(edges.items()),1):
 e['candidate_id']=f'PRV-B-C{n:04d}';e['tier']='primary_or_authority' if any(s['kind']=='shared_external_id' or any(f[2]=='primary' for f in s.get('forms',[])) for s in e['signals']) else 'alias_only_collision';e['prior_case_ids']=sorted(old.get(pair,[]));e['status']='candidate_unreviewed'
 e['records']=[{k:v for k,v in people[i].items() if k!='record'}|{'dynasty':people[i]['record'].get('dynasty'),'alt_names':people[i]['record'].get('alt_names',[]),'external_ids':people[i]['record'].get('external_ids',{})} for i in pair]
 rows.append(e)
# All Work author incoming edges, scanned once in shared SQLite, not native files.
wanted={i for e in rows for i in e['ids']};works=collections.defaultdict(list)
for row in con.execute("select id,name,path,blob_sha,sha256,data from records where type='Work'"):
 d=json.loads(row[5])
 for i in {a.get('entity_id') for a in d.get('authors',[]) if isinstance(a,dict)}&wanted:
  works[i].append({'id':row[0],'title':row[1],'path':row[2],'blob_sha':row[3],'sha256':row[4],'record':d})
for e in rows:e['work_counts']={i:len(works[i]) for i in e['ids']}
stats={'base':manifest['base'],'source_manifest':manifest,'active_people_scanned':len(people),'scope_matched_people':len(scope),'normalization_buckets':len(keys),'unique_candidate_pairs':len(rows),'candidate_pairs_with_prior_cases':sum(bool(e['prior_case_ids']) for e in rows),'new_candidate_pairs':sum(not e['prior_case_ids'] for e in rows),'unique_candidate_entities':len(wanted),'work_author_edges':sum(map(len,works.values())),'tiers':dict(collections.Counter(e['tier'] for e in rows)),'automatic_confirmed':0,'scope':'All active subtype=people Entities; candidates require religious/imperial lexical scope in at least one endpoint. Primary/alias finite normalization and shared external IDs; not exhaustive semantic historical identity discovery.'}
for filename,data in [('candidates.json',rows),('discovery-stats.json',stats),('candidate-snapshots.json',{i:people[i]|{'works':works[i]} for i in sorted(wanted)})]:
 (HERE/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False,indent=2))
