# -*- coding: utf-8 -*-
import json,re,collections,sys
from clus_a4 import *
CNERA=re.compile(r'同治|光緒|宣統|道光|咸豐|乾隆|嘉慶|康熙|民國|民国')
JPN=re.compile(r'和装|袋綴|訓点|訓點|付訓|返り点|返点|頭注|頭註|首書|送り仮名|送仮名|木版|活版|銅版|石版|見返|題簽|題箋|藏版|蔵版|刊記|奥付')
def info(k,v):
    pdl=[str(x) for x in (v['pd'] or []) if x]
    pdt=' '.join(pdl)
    if CNERA.search(pdt): return None
    cre=v['cre'] or ''; notes=' '.join(v['note'] or [])
    jp= v['lang']=='jpn' or JPN.search(notes) or '日本' in cre or re.search(r'點|訓',cre)
    year=None;flag=''
    e=eraY(v)
    if e:
        year=e[1]; jp=True
        if not e[2]: flag='era-mismatch'
    else:
        for s in pdl:
            m=re.fullmatch(r'(\d{4})(?:\.\d+)?(?:-\d{4}(?:\.\d+)?)?',s.strip())
            if m: year=int(m.group(1)); break
        if year is None:
            for s in pdl:
                if re.search(r'\[|\(',s): flag='bracket-'+s[:20]
    if year is None: return dict(skip='noyear',flag=flag)
    if not(1868<=year<=1911): return dict(skip='range',flag=flag)
    if str(v['date'])!=str(year): flag+=' date-conflict(%s)'%v['date']
    if not jp: return dict(skip='notjp',flag=flag)
    return dict(year=year,flag=flag.strip(),jp=True)
def cluster():
    cl=collections.defaultdict(list)
    skipc=collections.Counter()
    for k,v in d.items():
        if not v: continue
        i=info(k,v)
        if not i: skipc['cn']+=1; continue
        if 'skip' in i: skipc[i['skip']]+=1; continue
        t=nz(v['title'].split(' ')[0].split(',')[0])
        pub=nz((v['pub'] or [''])[0])
        pub=re.sub(r'\(.*?\)|ほか|等','',pub)
        cl[(t,i['year'])].append((k,v,i))
    return cl,skipc
if __name__=='__main__':
    cl,sc=cluster(); print(sc,len(cl), sum(len(x) for x in cl.values()))
