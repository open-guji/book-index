# -*- coding: utf-8 -*-
"""wake-b 第四輪 深掃：對掃描1中年份相合的 NCID 取書誌 JSON，全記錄（書名/出版者/注記）中找書肆字串。"""
import json,re,sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import b3_cinii as c, ndl
from build4_wake_b_scan2 import norm,key,grams
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/w4'
B=json.load(open(S+'/books.json'))
T=open(S+'/scan1.txt',encoding='utf-8').read().split('## ')[1:]
out={}
for t in T:
    L=t.strip().split('\n');h=L[0];bid=h.split()[0]
    m=re.search(r'y=(\d+)',h);y=m.group(1) if m else None
    if not y: continue
    b=B[bid]['b'];g=grams(key(b['edition']))
    hits=[]
    for l in L[1:]:
        p=l.split(' | ')
        if len(p)<4 or p[1].strip()!=y: continue
        ncid=p[0].split()[0];ti=norm(p[0][len(ncid)+1:])
        r=difflib.SequenceMatcher(None,norm(b['title']),ti[:len(b['title'])+4]).ratio()
        if r<0.6: continue
        d=c.ncid(ncid)
        if not d: continue
        txt=norm(json.dumps(d,ensure_ascii=False))
        hit=sorted(k for k in g if k in txt)
        hits.append({'ncid':ncid,'title':d['title'],'pub':d['pub'],'pubdate':d['pubdate'],'ext':d['extent'],'notes':d['notes'],'own':[o['name'] for o in d['owners']],'gram':hit,'r':round(r,2)})
    out[bid]={'grams':sorted(g),'hits':hits}
json.dump(out,open(S+'/res2.json','w'),ensure_ascii=False)
print(len(out))
