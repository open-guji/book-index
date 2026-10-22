import hashlib,json,sqlite3,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
DB=Path('/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite')
TREE=Path('/workspace/scratch/0bc7226fa660/audit/current-main-tree.z')
def write(n,v): (HERE/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
c=sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True)
manifest=json.loads(c.execute("select value from metadata where key='manifest'").fetchone()[0]);assert manifest['base']==BASE
traw=TREE.read_bytes();assert hashlib.sha256(traw).hexdigest()==manifest['tree_sha256']
tree={}
for row in traw.split(b'\0'):
 if row:
  meta,path=row.split(b'\t',1);tree[path.decode()]=meta.split()[2].decode()
cases=json.loads((HERE/'cases.json').read_text());workids={i for x in cases for i in x['ids']};ids=set(workids)
for i in workids:
 d=json.loads(c.execute('select data from records where id=?',(i,)).fetchone()[0])
 ids.update(a['entity_id'] for a in d.get('authors',[]) if a.get('entity_id'))
records={};checks=[]
for rid in sorted(ids):
 r=c.execute('select type,path,blob_sha,sha256,data from records where id=?',(rid,)).fetchone();assert r,rid
 ty,path,blob,sha,s=r;raw=s.encode();d=json.loads(s)
 assert hashlib.sha256(raw).hexdigest()==sha,rid
 oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert oid==blob==tree[path],rid
 assert not d.get('merged_into'),rid
 records[rid]={'path':path,'sha256':sha,'blob_sha':blob,'type':ty,'record':d}
 checks.append({'id':rid,'path':path,'sha256':sha,'blob_sha':blob,'exact_main_bytes':True})
for x in cases:
 x['records']=[{'id':i,**{k:records[i][k] for k in ['path','sha256','blob_sha']},'title':records[i]['record']['title']} for i in x['ids']]
 x['main_verification']={'reference':'verification.json','all_work_bytes_match_main':True,'tombstones':0}
write('cases.json',cases);write('original-records.json',records)
rulepath='.claude/qa/正式库并条审查规则.md';raw=subprocess.check_output(['git','show',BASE+':'+rulepath],cwd=ROOT);(HERE/'formal-rules-main.md').write_bytes(raw)
write('verification.json',{'research_ref':BASE,'sqlite_manifest':manifest,'method':'Read-only SQLite data UTF-8 bytes SHA256 and Git blob SHA1 match metadata and fixed-main complete tree; tree fingerprint matches manifest. No historical checkout used.','checked_records':len(checks),'work_records':len(workids),'entity_records':len(ids)-len(workids),'byte_identical':len(checks),'drift':0,'tombstones':0,'checks':checks,'rules_sha256':hashlib.sha256(raw).hexdigest(),'native_mutations':0,'not_checked':['Book records/attachments','full typed references','promotions','draft repository','book-text HEAD/manifest/text','merge audit/schema/classification/builder execution']})
# Scan existing case files for pair-level overlap; relation-only mentions do not replace an Entity case.
overlap=[]
for f in HERE.parents[1].rglob('cases.json'):
 if f==HERE/'cases.json':continue
 try: old=json.loads(f.read_text())
 except Exception:continue
 if not isinstance(old,list):continue
 for oldcase in old:
  if not isinstance(oldcase,dict):continue
  s=json.dumps(oldcase)
  for x in cases:
   hits=[i for i in x['ids'] if i in s]
   if hits:overlap.append({'new_case':x['case_id'],'existing_file':str(f.relative_to(HERE.parents[1])),'existing_case':oldcase.get('case_id'),'existing_type':oldcase.get('type') or ('Entity' if oldcase.get('ids') and all(i.startswith('hix') for i in oldcase['ids']) else 'unknown'),'ids':hits,'action':'cross-reference only; existing decision retained, not superseded'})
write('overlap-check.json',overlap)
hashes=[]
for f in sorted((HERE/'evidence').glob('*.json')):hashes.append({'path':str(f.relative_to(HERE)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'kind':'saved web tool response snapshot, not raw webpage/PDF bytes'})
write('evidence-manifest.json',hashes)
write('stats.json',{'new_work_case_groups':9,'new_research_families':8,'new_work_records':17,'confirmed':0,'separate':3,'open':6,'supersedes':[],'related_existing_entity_cases':['PRV-R011','PRV-R013','PNA-2000-005'],'native_merges':0,'redundant_work_count_confirmed':0})
print('Verified',len(checks),'records;',len(cases),'cases; 0 confirmed,3 separate,6 open; native merges 0')
