"""Reproducible routing/diagnostics; never turns candidate edges into verdicts."""
import argparse, collections, gzip, hashlib, json, pathlib, sqlite3, subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=pathlib.Path, required=True)
parser.add_argument('--db', type=pathlib.Path, required=True)
args = parser.parse_args()
OUT = pathlib.Path(__file__).resolve().parent
AUDIT = OUT.parent
BASE = 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
source = AUDIT / 'broad-census-20261022/unclassified-candidate-pairs.json'
pairs = json.loads(source.read_text())
db = sqlite3.connect(f'file:{args.db}?mode=ro', uri=True)
manifest = json.loads(db.execute("select value from metadata where key='manifest'").fetchone()[0])
assert manifest['base'] == BASE
tree_raw = subprocess.check_output(['git', 'ls-tree', '-rz', BASE], cwd=args.repo)
tree = {}
for line in tree_raw.split(b'\0'):
    if line:
        meta, path = line.split(b'\t', 1)
        tree[path.decode()] = meta.decode().split()[2]
records = {}; snapshots = {}; hints = {}
for wid in sorted({i for p in pairs for i in p['ids']}):
    path, oid, sha, raw = db.execute('select path,blob_sha,sha256,data from records where id=?', (wid,)).fetchone()
    b = raw.encode()
    assert hashlib.sha256(b).hexdigest() == sha
    assert hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == oid == tree[path]
    o = json.loads(raw); assert not o.get('merged_into')
    assert not db.execute('select 1 from membership where work_id=?', (wid,)).fetchone()
    records[wid] = o
    snapshots[wid] = dict(path=path,blob_sha=oid,sha256=sha,raw_utf8=raw)
    h = []
    for i, row in enumerate(o.get('indexed_by', [])):
        section = row.get('section', '')
        if section.startswith(('經部/', '史部/', '子部/', '集部/')):
            h.append(dict(division=section[:2],pointer=f'/indexed_by/{i}/section',value=section))
    hints[wid] = h

def names(o):
    return sorted({a.get('name','') for a in o.get('authors',[]) if a.get('name','') not in ('','不詳','佚名','無名氏','闕名','失名','未詳','不著撰人')})
def summaries(o):
    return {(s.get('source_bid') or s.get('source'), s.get('summary','')) for s in o.get('indexed_by',[]) if s.get('summary')}

rows=[]; counts=collections.Counter(); divs=collections.Counter(); parent={}
def find(x):
    parent.setdefault(x,x)
    if parent[x]!=x:parent[x]=find(parent[x])
    return parent[x]
for i,p in enumerate(pairs):
    x,y=p['ids']; a,b=records[x],records[y]; na,nb=names(a),names(b)
    parent[find(x)]=find(y)
    shared=summaries(a)&summaries(b)
    boiler=[s for s in shared if s[1].startswith('共 ') and '個版本' in s[1]]
    conflict=bool(na and nb and not set(na)&set(nb))
    diagnostic=('different_named_responsibilities_and_shared_catalogue_wrapper' if conflict and boiler else
                'different_named_responsibilities' if conflict else
                'missing_named_responsibility' if not na or not nb else 'named_responsibility_candidate')
    ds=sorted({h['division'] for wid in [x,y] for h in hints[wid]})
    counts[diagnostic]+=1
    for d in ds:divs[d]+=1
    rows.append(dict(queue_index=i,ids=[x,y],titles=[a['title'],b['title']],names=[na,nb],
                     diagnostic=diagnostic,source_section_routing_hints=ds,
                     hint_pointers={wid:hints[wid] for wid in [x,y]},
                     shared_summary_count=len(shared),shared_generic_wrapper_count=len(boiler),
                     status='unreviewed_candidate',merge_allowed=False,
                     reason='Names/sections are source routing diagnostics, not historical identity judgments.'))
components=collections.defaultdict(list)
for wid in records:components[find(wid)].append(wid)
summary=dict(base=BASE,input_pair_count=len(pairs),unique_work_records=len(records),
             candidate_components=len(components),diagnostic_counts=dict(counts),
             routing_counts_overlapping=dict(divs),pairs_without_source_section_hint=sum(not x['source_section_routing_hints'] for x in rows),
             research_confirmations=0,research_separations=0,native_mutations=0,
             warning='Source sections are not official membership; different names can be aliases. No pair discarded or merge authorized.')
validation=dict(base=BASE,raw_records_checked=len(records),sha256_git_blob_and_main_tree_checked=True,
                source_queue_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                main_tree_listing_sha256=hashlib.sha256(tree_raw).hexdigest(),errors=[],
                not_run=['historical identity review','Book/Collection references','draft/text references','native schema/builder'])
for name,data in [('unclassified-routing.json',rows),('unclassified-summary.json',summary),('unclassified-validation.json',validation)]:
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
with (OUT/'unclassified-original-records.json.gz').open('wb') as target:
    with gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as f:
        f.write(json.dumps(snapshots,ensure_ascii=False).encode())
print(json.dumps(summary,ensure_ascii=False))
