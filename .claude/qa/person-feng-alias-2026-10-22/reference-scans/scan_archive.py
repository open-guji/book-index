#!/usr/bin/env python3
"""Scan every regular archive member at an immutable Git ref for selected IDs.
Read-only: preserves exact matching bytes and coverage; never applies merges.
"""
import argparse, collections, hashlib, json, pathlib, tarfile, time, urllib.request
P=argparse.ArgumentParser();P.add_argument('repo');P.add_argument('sha');P.add_argument('--out',required=True);P.add_argument('--extract');P.add_argument('--ids',nargs='+',required=True);a=P.parse_args()
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
ids=a.ids
patterns=[x.encode() for x in ids]; counts=collections.Counter(); hits=[]; path_hits=[]; started=time.time()
def walk(x,p=''):
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,p+'/'+k.replace('~','~0').replace('/','~1'))
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
 elif isinstance(x,str):
  for id in ids:
   if id in x:yield {'pointer':p,'id':id,'exact':x==id,'value':x}
url=f'https://codeload.github.com/open-guji/{a.repo}/tar.gz/{a.sha}'
try:
 with urllib.request.urlopen(url,timeout=120) as response,tarfile.open(fileobj=response,mode='r|gz') as arc:
  for m in arc:
   if not m.isfile():continue
   parts=pathlib.PurePosixPath(m.name).parts[1:]
   if not parts or '..' in parts:raise ValueError('unsafe archive path')
   path='/'.join(parts);path_hits.extend({'path':path,'id':id} for id in ids if id in path);data=arc.extractfile(m).read();counts['files']+=1;counts['bytes']+=len(data)
   if a.extract:
    dest=pathlib.Path(a.extract)/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
   found=[id for id,pat in zip(ids,patterns) if pat in data]
   if found:
    dest=out/'matches'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    hit={'path':path,'ids':found,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    try:hit['json_occurrences']=list(walk(json.loads(data)))
    except (ValueError,UnicodeDecodeError):hit['json_occurrences']=None
    hits.append(hit)
   if counts['files']%50000==0:print(json.dumps(dict(counts)),flush=True)
 result={'repo':a.repo,'ref':a.sha,'complete':True,'targets':ids,'counts':dict(counts),'hits':hits,'path_hits':path_hits,'elapsed_seconds':round(time.time()-started,1),'url':url}
except Exception as e:
 result={'repo':a.repo,'ref':a.sha,'complete':False,'targets':ids,'counts':dict(counts),'hits':hits,'error':str(e)}
(out/'scan.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='hits'},ensure_ascii=False),flush=True)
raise SystemExit(0 if result['complete'] else 1)
