# -*- coding: utf-8 -*-
import sys,json,re,collections,subprocess
sys.path.insert(0,'/tmp/wa3')
from a3_analyze import *
from a3_clusters import head
from a3_lib_idx import rows as LIB
WI=json.load(open('/tmp/wa3/works_idx.json')); IDX=WI['idx']; PATHS=WI['paths']
_cache={}
def load_works(ids):
    need=[i for i in ids if i not in _cache]
    if need:
        inp=''.join('origin/main:%s\n'%PATHS[i] for i in need)
        r=subprocess.run(['git','cat-file','--batch'],input=inp.encode(),capture_output=True,cwd='/home/user/book-index').stdout
        k=0;n_i=0
        while k<len(r):
            j=r.index(b'\n',k); h=r[k:j].split()
            if len(h)<3: break
            n=int(h[2]); d=json.loads(r[j+1:j+1+n]); k=j+1+n+1
            _cache[d['id']]=d
    return [_cache[i] for i in ids if i in _cache]
OVR=json.load(open('/tmp/wa3/overrides.json')) if __import__('os').path.exists('/tmp/wa3/overrides.json') else []
def resolve(h,creator,title):
    creator=re.sub(r'[\[\]\(\)（）\s]','',creator)
    # overrides: list of [head_re, creator_re, creator_not_re, wid, note]
    for hre,cre,nre,wid,note in OVR:
        if re.search(hre,nz(h)) and re.search(cre,creator) and not (nre and re.search(nre,creator)):
            return wid,'ovr:'+note
    ids=IDX.get(nz(h))
    if not ids: return None,'noWork'
    ws=load_works(ids)
    hit=[]
    for w in ws:
        names=[(a.get('name') if isinstance(a,dict) else str(a)) for a in (w.get('authors') or [])]
        names=[re.sub(r'\s','',n) for n in names if n]
        if names and any(n in creator or n[-2:] in creator for n in names): hit.append(w['id'])
    if len(hit)==1: return hit[0],'auth'
    if len(hit)>1: return None,'ambig-auth'
    return None,'noauthmatch(%d)'%len(ws)
