from pathlib import Path
from collections import defaultdict,Counter
import json,hashlib,re,os,time
R=Path(__file__).resolve().parents[4]
O=Path(__file__).resolve().parent
by=defaultdict(list); rows={}; n=0
for root,_,fs in os.walk(R/'Work'):
 for fn in fs:
  if not fn.endswith('.json'):continue
  p=Path(root)/fn; b=p.read_bytes(); d=json.loads(b)
  if d.get('merged_into'):continue
  n+=1
  if not any('子部/' in x.get('section','') for x in d.get('indexed_by',[])):continue
  rows[d['id']]={'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'record':d}
  idx=d.get('indexed_by',[])
  if idx:by[(d.get('title'),json.dumps(idx,ensure_ascii=False,sort_keys=True))].append(d['id'])
groups=[v for v in by.values() if len(v)>1]
(O/'candidate-snapshots.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(O/'candidate-identical-index.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2))
print('active works',n,'masters source rows',len(rows),'identical index groups',len(groups))
for ids in groups:
 rs=[rows[i]['record'] for i in ids]; keys=set().union(*(r.keys() for r in rs)); diff=[k for k in keys if len({json.dumps(r.get(k),ensure_ascii=False,sort_keys=True) for r in rs})>1]
 print(ids,rs[0]['title'],'DIFF',diff)
