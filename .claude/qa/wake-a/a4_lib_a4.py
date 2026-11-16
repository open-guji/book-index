# -*- coding: utf-8 -*-
import json,re,subprocess,unicodedata
PATHS=json.load(open('/tmp/wa4/paths.json'))
WORKS=[p for p in PATHS if p.startswith('Work/')]
BOOKS=[p for p in PATHS if p.startswith('Book/')]
_c={}
def cat(paths,ref='origin/main'):
    need=[p for p in paths if p not in _c]
    if need:
        inp=''.join('%s:%s\n'%(ref,p) for p in need)
        r=subprocess.run(['git','cat-file','--batch'],input=inp.encode(),capture_output=True,cwd='/home/user/book-index').stdout
        k=0;i=0
        while k<len(r) and i<len(need):
            j=r.index(b'\n',k); h=r[k:j].split()
            if len(h)<3: _c[need[i]]=None; k=j+1; i+=1; continue
            n=int(h[2]); 
            try: _c[need[i]]=json.loads(r[j+1:j+1+n])
            except Exception: _c[need[i]]=None
            k=j+1+n+1; i+=1
    return [_c.get(p) for p in paths]
def nm(p): 
    n=p.split('/')[-1][:-5]; i,_,t=n.partition('-'); return i,t
def works_by_title(sub):
    return [p for p in WORKS if sub in nm(p)[1]]
def books_by_title(sub):
    return [p for p in BOOKS if sub in nm(p)[1]]
