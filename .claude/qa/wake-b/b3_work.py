# -*- coding: utf-8 -*-
import json,subprocess,sys
P={}
for p in open('/tmp/wb_workpaths.txt').read().split('\n'):
    if p: P[p.split('/')[-1].split('-')[0]]=p
def works(ids):
    inp=''.join('origin/main:%s\n'%P[i] for i in ids).encode()
    raw=subprocess.run(['git','-c','core.quotepath=false','-C','/tmp/wk-wake-b3','cat-file','--batch'],capture_output=True,input=inp).stdout
    res={};i=0;k=0
    while i<len(raw):
        j=raw.index(b'\n',i);h=raw[i:j].split();n=int(h[2]);body=raw[j+1:j+1+n];i=j+1+n+1
        res[ids[k]]=json.loads(body);k+=1
    return res
def show(ids):
    for i,w in works(ids).items():
        au=[(a.get('name'),a.get('role')) for a in (w.get('authors') or [])][:3]
        d=w.get('dating') or {}
        print(i,w['title'],au,d.get('era'),d.get('year'),'|',(w.get('description') or {}).get('text','')[:70].replace('\n',' '))
if __name__=='__main__': show(sys.argv[1:])
