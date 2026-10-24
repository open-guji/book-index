#!/usr/bin/env python3
"""Apply the reviewed Feng Person batch with all-or-nothing preflight hash checks.
Dry-run by default; --apply writes only the 3 listed files. Historical IDs stay intact.
"""
import argparse,hashlib,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);a=p.parse_args()
ledger=json.loads(pathlib.Path(__file__).with_name('merges.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.root,text=True).strip()==ledger['base'], 'checkout must equal the audited immutable base'
for record in ledger['records']:
 path=a.root/record['path'];data=path.read_bytes()
 assert hashlib.sha256(data).hexdigest()==record['sha256'], 'source drift: '+record['path']
 assert json.loads(data)==record['before']
for repo in ['book-index','book-index-draft','book-text']:
 scan=json.loads(pathlib.Path(__file__).with_name('reference-scans').joinpath(repo+'.json').read_text())
 assert scan['complete'],repo+' scan incomplete'
 if repo=='book-index':assert scan['ref']==ledger['base']
if a.apply:
 for record in ledger['records']:
  path=a.root/record['path'];tmp=path.with_suffix('.json.tmp')
  tmp.write_text(json.dumps(record['after'],ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
print(json.dumps({'applied':a.apply,'groups':len(ledger['merges']),'files':len(ledger['records'])}))
