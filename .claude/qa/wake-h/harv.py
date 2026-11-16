# -*- coding: utf-8 -*-
import h3lib,re,sys,collections,json,os
from tri import yr
ERA='慶長|元和|寛永|寛文|寛永|延宝|天和|貞享|元禄|元祿|宝永|寶永|正徳|享保|元文|寛保|延享|寛延|宝暦|明和|安永|天明|寛政|享和|文化|文政|天保|弘化|嘉永|安政|万延|文久|元治|慶応|明治|江戸|江戶|室町|桃山|五山|古活字|正保|慶安|承応|明暦|万治|延喜|天正|文禄|永正|大永|享禄|天文'
def isjp(x,incl_meiji=True):
    s=x['year']
    if re.search(ERA,s):
        if not incl_meiji and '明治' in s: return False
        return True
    return False
def harvest(qs,pages=3,incl_meiji=True,extra='&year_to=1911'):
    seen={}
    for q in qs:
        for p in range(1,pages+1):
            r=h3lib.search(q,p,200,extra)
            if not r: break
            for x in r['recs']:
                if isjp(x,incl_meiji): seen.setdefault(x['ncid'],x)
            if len(r['recs'])<200: break
    return seen
def norm(s): return re.sub(r'[\s　\.．,，、]','',s)
def view(seen,key=None):
    rows=sorted(seen.values(),key=lambda x:(norm(x['title'])[:12],yr(x['year']) or 0))
    for x in rows:
        if key and key not in x['title']: continue
        print(x['ncid'],'|',x['title'][:40],'|',x['auth'][:20],'|',x['pub'][:24],'|',x['year'][:16],'|',x['n'])
if __name__=='__main__':
    qs=sys.argv[1].split(';'); seen=harvest(qs,int(sys.argv[2]) if len(sys.argv)>2 else 3)
    print(len(seen)); view(seen)
