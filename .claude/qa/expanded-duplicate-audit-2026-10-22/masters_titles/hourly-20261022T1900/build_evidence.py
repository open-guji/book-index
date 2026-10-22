"""Read bounded candidates; verify all saved records against pinned main; no native writes."""
import gzip, hashlib, json, subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[4]
BASE=REPO.parent
MAIN='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
tree_bytes=(BASE/'audit/current-main-tree.z').read_bytes()
tree={}
for row in tree_bytes.split(b'\0'):
    if row:
        meta,p=row.decode().split('\t'); tree[p]=meta.split()[2]
def hashes(b):
    return {'sha256':hashlib.sha256(b).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
def checked(p,b,method):
    h=hashes(b)
    assert h['git_blob']==tree[p],p
    return {'path':p,**h,'main_blob':tree[p],'verified_equal':True,'read_method':method,'record':json.loads(b)}
def read(p):
    f=BASE/'book-index'/p
    if f.exists() and hashes(f.read_bytes())['git_blob']==tree[p]:return checked(p,f.read_bytes(),'local bytes, exact pinned-main Git blob equality')
    return checked(p,subprocess.check_output(['git','show',MAIN+':'+p],cwd=REPO,timeout=30),'git show pinned main')
def save(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
work=[]
for r in json.load(gzip.open(OUT.parent/'astra-review-20261022/current-source-snapshots.json.gz','rt')):
    if r['record']['id'] in ['d59fxziflw5e','d59fxunlrzeo','d59f2q7zj6yp','d59fxwylng8x']:
        b=(json.dumps(r['record'],ensure_ascii=False,indent=2)+'\n').encode()
        assert hashes(b)['sha256']==r['sha256']
        work.append(checked(r['path'],b,'reconstructed snapshot; stored SHA256 + pinned-main Git blob equality'))
work.append(read('Work/7/9/d/d59fxuzex79d-沈注金匱要畧.json'))
save('work-records.json',work)
ledger=read('.claude/qa/reports/duplicate-audit-2026-10-21/merges.json')
save('WORK-0187-ledger-extract.json',{k:v for k,v in ledger.items() if k!='record'}|{'record':next(x for x in ledger['record']['merges'] if x['cluster_id']=='WORK-0187'),'extract_only':True})
books=[]; candidates=[]
for p in tree:
    if p.startswith('Book/') and '夢溪' in p:
        f=BASE/'book-index'/p
        if not f.exists(): candidates.append({'path':p,'state':'local_missing_not_examined'}); continue
        b=f.read_bytes(); h=hashes(b); x=json.loads(b)
        candidates.append({'path':p,'matches_main':h['git_blob']==tree[p]})
        if x.get('work_id')=='d59fxwylng8x': books.append(read(p))
save('mengxi-book-records.json',books)
collections=[]
for p in tree:
    if p.startswith('Collection/') and any(i in p for i in ['8rldot389yx0','8rldo9qhnwua']):collections.append(read(p))
save('mengxi-collection-records.json',collections)
save('bounded-book-scan.json',{'scope':'Only current-main Book paths containing 夢溪; not full-reference scan','candidates':candidates,'matched_work_books':len(books),'one_juan_books':[r['record']['id'] for r in books if r['record'].get('measure_info')=='一卷'],'lin_sijin_mentions':[r['record']['id'] for r in books if '林思進' in json.dumps(r['record'],ensure_ascii=False)]})
save('validation.json',{'main':MAIN,'tree_sha256':hashlib.sha256(tree_bytes).hexdigest(),'work_records_verified':len(work),'book_records_verified':len(books),'collection_records_verified':len(collections),'ledger_full_source_verified':True,'native_changes':0,'data_merges':0,'full_reference_scan':False,'schema_classification_builder_run':False})
print(json.dumps({'work':len(work),'books':len(books),'collections':len(collections),'all_saved_records_match_pinned_main':True}))
