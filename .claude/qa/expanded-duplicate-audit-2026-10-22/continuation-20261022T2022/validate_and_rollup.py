"""Validate this continuation against its frozen case baseline and main tree."""
import argparse, collections, gzip, hashlib, itertools, json, pathlib, sqlite3, subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=pathlib.Path,required=True)
parser.add_argument('--db',type=pathlib.Path,required=True)
args=parser.parse_args()
OUT=pathlib.Path(__file__).resolve().parent; ROOT=OUT.parent
baseline=json.loads((OUT/'prior-case-baseline.json').read_text()); BASE=baseline['base']
LANES=['classics_titles','history_titles','masters_titles','collections_titles','people_names_aliases','people_religious_variants']
def ids(c):
    items=c.get('ids') or c.get('members') or ([c.get('keeper')]+c.get('losers',[]))
    return sorted({v if isinstance(v,str) else v['id'] for v in items if isinstance(v,str) or isinstance(v,dict) and 'id' in v})
oldpairs={}
for c in baseline['historical_cases']:
    for p in itertools.combinations(c['ids'],2):oldpairs.setdefault(p,[]).append(c['case_id'])
effective={c['case_id']:c for c in baseline['prior_effective_cases']}
newpairs={}; cases=[]; files={};errors=[]
for lane in LANES:
    folder=ROOT/lane/'hourly-20261022T2022'
    assert (folder/'report.md').is_file()
    data=json.loads((folder/'cases.json').read_text())
    assert isinstance(data,list)
    for c in data:
        cid=c['case_id']; members=ids(c); state=c['status']
        if len(members)<2 or state not in ['confirmed','open','separate']:errors.append([cid,'invalid case'])
        if cid in effective:errors.append([cid,'duplicate case ID'])
        supersedes=c.get('supersedes_case_id') or c.get('supersedes')
        if supersedes:
            if supersedes not in effective:errors.append([cid,'unknown superseded case'])
            else:effective.pop(supersedes)
        item=dict(case_id=cid,lane=lane,ids=members,status=state)
        cases.append(item);effective[cid]=item
        for pair in itertools.combinations(members,2):
            if pair in oldpairs and not supersedes:errors.append([cid,'previously reviewed pair',oldpairs[pair]])
            if pair in newpairs:errors.append([cid,'cross-lane repeated pair',newpairs[pair]])
            newpairs[pair]=cid
    for f in sorted(folder.rglob('*')):
        if f.is_file() and '__pycache__' not in f.parts:
            files[str(f.relative_to(ROOT))]=dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size)
db=sqlite3.connect(f'file:{args.db}?mode=ro',uri=True)
assert json.loads(db.execute("select value from metadata where key='manifest'").fetchone()[0])['base']==BASE
tree_raw=subprocess.check_output(['git','ls-tree','-rz',BASE],cwd=args.repo)
tree={}
for line in tree_raw.split(b'\0'):
    if line:
        meta,p=line.split(b'\t',1);tree[p.decode()]=meta.decode().split()[2]
snapshots={}
for wid in sorted({i for c in cases for i in c['ids']}):
    path,oid,sha,raw=db.execute('select path,blob_sha,sha256,data from records where id=?',(wid,)).fetchone()
    b=raw.encode();o=json.loads(raw)
    if hashlib.sha256(b).hexdigest()!=sha:errors.append([wid,'sha256 mismatch'])
    if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=oid or tree[path]!=oid:errors.append([wid,'main blob mismatch'])
    if o.get('merged_into'):errors.append([wid,'already merged'])
    snapshots[wid]=dict(path=path,blob_sha=oid,sha256=sha,raw_utf8=raw)
counts=collections.Counter(c['status'] for c in cases)
rollup=dict(base=BASE,prior_effective_case_count=len(baseline['prior_effective_cases']),
            this_round_cases=len(cases),this_round_counts=dict(counts),
            effective_case_count=len(effective),effective_counts=dict(collections.Counter(c['status'] for c in effective.values())),
            lanes={lane:dict(collections.Counter(c['status'] for c in cases if c['lane']==lane)) for lane in LANES},
            native_merge_groups_this_round=0,scope='Historical identity research only; no native apply or execution approval',
            model='gpt-6-astra',reasoning_effort='high',fork_turns='none')
validation=dict(base=BASE,case_count=len(cases),member_records_checked=len(snapshots),
                unique_member_pairs=len(newpairs),old_and_cross_lane_pairs_checked=True,
                byte_sha256_and_git_blob_against_fixed_main_tree_checked=True,errors=errors,
                not_run=['all-type reference migration','draft/promotions/text asset migration','native writes','native schema/classification/builder audits'],
                lane_files=files,cases=cases)
for name,d in [('current-rollup.json',rollup),('validation.json',validation)]:
    (OUT/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
with (OUT/'selected-main-records.json.gz').open('wb') as target:
    with gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as f:f.write(json.dumps(snapshots,ensure_ascii=False).encode())
print(json.dumps(rollup,ensure_ascii=False));print('errors',errors)
raise SystemExit(bool(errors))
