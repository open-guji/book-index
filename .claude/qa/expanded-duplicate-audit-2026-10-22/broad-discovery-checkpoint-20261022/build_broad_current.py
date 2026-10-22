import pathlib, subprocess, hashlib, json, sqlite3, collections, time, argparse

ROOT=pathlib.Path('/workspace/scratch/0bc7226fa660')
parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=pathlib.Path,default=ROOT/'book-index-current')
parser.add_argument('--base',default='c6dd8356d613fc5614beb88f0a61a3d04cfb069e')
parser.add_argument('--out',type=pathlib.Path,default=ROOT/'audit/broad-current.sqlite')
args=parser.parse_args();REPO=args.repo;BASE=args.base;OUT=args.out
OUT.parent.mkdir(parents=True,exist_ok=True)
t=time.time()
tree=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','-z',BASE])
paths={}
for entry in tree.split(b'\0'):
    if not entry: continue
    meta,p=entry.split(b'\t',1)
    p=p.decode()
    if p.startswith(('Work/','Entity/','classification/')) and p.endswith('.json'):
        paths[p]=meta.split()[2].decode()
tmp=OUT.with_suffix('.building.sqlite')
if tmp.exists():tmp.unlink()
db=sqlite3.connect(tmp)
db.executescript('PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; CREATE TABLE records(id TEXT PRIMARY KEY,type TEXT,name TEXT,path TEXT,blob_sha TEXT,sha256 TEXT,data TEXT); CREATE TABLE membership(work_id TEXT,division TEXT,node TEXT); CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);')
stats=collections.Counter(); classes={}; mismatches=[]; errors=[]
for i,(p,sha) in enumerate(paths.items()):
    raw=(REPO/p).read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if actual!=sha:
        raw=subprocess.check_output(['git','-C',str(REPO),'cat-file','blob',sha])
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==sha
        mismatches.append(p)
    try:o=json.loads(raw)
    except Exception as e:errors.append([p,str(e)]);continue
    if p.startswith('classification/'):
        classes[p]=o;continue
    typ=p.split('/')[0];stats[typ+'_files']+=1
    if not isinstance(o,dict) or not o.get('id'):
        errors.append([p,'missing record id']);continue
    if o.get('merged_into') or o.get('retired'):
        stats[typ+'_inactive']+=1;continue
    db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?)',(o['id'],typ,o.get('title',o.get('primary_name','')),p,sha,hashlib.sha256(raw).hexdigest(),raw.decode()))
    stats[typ+'_active']+=1
    if i%25000==0:
        db.commit(); print(i,dict(stats),round(time.time()-t,1),flush=True)
nodes={n['id']:n for n in classes['classification/zongmu/tree.json']['nodes']}
for p,o in classes.items():
    if '/members/' not in p:continue
    node=pathlib.Path(p).stem
    n=nodes[node]
    while n.get('parent'):n=nodes[n['parent']]
    members=o if isinstance(o,list) else o.get('members',o.get('work_ids',[]))
    for member in members:
        wid=member if isinstance(member,str) else member[0] if isinstance(member,list) else member.get('work_id',member.get('id'))
        if wid:db.execute('INSERT INTO membership VALUES(?,?,?)',(wid,n['label'],node))
db.executescript('CREATE INDEX rec_type ON records(type); CREATE INDEX rec_name ON records(name); CREATE INDEX member_work ON membership(work_id); CREATE INDEX member_division ON membership(division);')
stats['membership_rows']=db.execute('SELECT COUNT(*) FROM membership').fetchone()[0]
summary={'base':BASE,'tree_sha256':hashlib.sha256(tree).hexdigest(),'stats':dict(stats),'local_changes_read_from_main_instead':mismatches,'errors':errors,'elapsed_seconds':round(time.time()-t,2)}
assert not errors,errors
db.execute('INSERT INTO metadata VALUES(?,?)',('manifest',json.dumps(summary,ensure_ascii=False)))
db.commit();db.close();tmp.rename(OUT)
OUT.with_name(OUT.stem+'-manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False),flush=True)
