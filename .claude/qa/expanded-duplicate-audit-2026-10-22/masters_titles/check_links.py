from pathlib import Path
import json,os,re,gzip,collections,hashlib
O=Path(__file__).resolve().parent;R=O.parents[3];C=json.loads((O/'cases.json').read_text());ids={i for c in C if c['status']=='confirmed' and c['type']=='Work' for i in [c['keeper']]+c['losers']};pat=re.compile('|'.join(ids).encode());found=[];counts=collections.Counter();n=0
for root,_,fs in os.walk(R/'Book'):
 for fn in fs:
  if not fn.endswith('.json'):continue
  n+=1;p=Path(root)/fn;b=p.read_bytes()
  if not pat.search(b):continue
  d=json.loads(b)
  if d.get('merged_into') or d.get('work_id') not in ids:continue
  found.append({'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'record':d});counts[d['work_id']]+=1
with gzip.open(O/'related-books-before.json.gz','wt',encoding='utf-8') as f:json.dump(found,f,ensure_ascii=False)
assets={};T=R.parent/'book-text-ref/index/texts'
for p in T.glob('*.json'):
 for i,v in json.loads(p.read_text()).items():
  if i in ids:assets[i]=v
(O/'related-books-summary.json').write_text(json.dumps({'files_scanned':n,'active_related':len(found),'by_work':dict(counts),'book_text_own_assets':assets},ensure_ascii=False,indent=2))
for c in C:
 if c['status']=='confirmed' and c['type']=='Work':
  c['related_book_ids']=[x['record']['id'] for x in found if x['record']['work_id'] in [c['keeper']]+c['losers']]
  c['own_text_assets']={i:assets[i] for i in [c['keeper']]+c['losers'] if i in assets}
(O/'cases.json').write_text(json.dumps(C,ensure_ascii=False,indent=2)+'\n')
print('Book files',n,'related',len(found),'own text assets',list(assets))
for c in C:
 if c['status']=='confirmed' and c['type']=='Work':
  rel=[x['record'] for x in found if x['record']['work_id'] in [c['keeper']]+c['losers']]
  print(c['case_id'],c['title'],len(rel),'titles',sorted(set(x['title'] for x in rel)))
