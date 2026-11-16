# -*- coding: utf-8 -*-
import sys,json,re,collections;sys.path.insert(0,'.')
import b3_an as a,b3_group as bg
from b3_group import shops,kanki,weak,japan
v=json.load(open('/tmp/wb3_versions.json'))
ex=collections.defaultdict(list)
for b in a.jb: ex[a.nt(b['title'])].append(b)
CHNS=re.compile(r'辨志堂|和衷堂|李光明|白炤|聯墨|藏書堂|雄風館|粤東|崇徳|金陵|點石|校經|天工|貞固堂|有慶堂')
def shopex(t,shs):
    r=[]
    for et,bl in ex.items():
        if et==t or (len(t)>=3 and len(et)>=3 and (t in et or et in t)):
            for b in bl:
                for sh in shs:
                    k=re.sub(r'(屋|堂|院|館|軒|齋)$','',sh)
                    if len(sh)>=3 and sh in b.get('edition','') : r.append(b['id']+'~'+sh)
    return r
def exm(t,y):
    r=[]
    for et,bl in ex.items():
        if et==t or (len(t)>=3 and len(et)>=3 and (t in et or et in t)):
            for b in bl:
                if a.ey(b)==y: r.append(b['id'])
    return r
rows=[]
for i,x in enumerate(sorted(v,key=lambda x:(x['t'],x['y'],x['shops']))):
    d=x['det'][0]
    jp=any(japan(d) for d in x['det'])
    flags=[]
    if not x['shops']: flags.append('NOSHOP')
    if any(weak(d) for d in x['det']): flags.append('WEAK')
    if CHNS.search(''.join(x['shops'])): flags.append('CHN')
    if not jp: flags.append('NOJP')
    e=exm(x['t'],x['y'])+shopex(x['t'],x['shops'])
    if e: flags.append('EX:'+','.join(e))
    x['flags']=flags;x['i']=i
    rows.append(x)
json.dump(rows,open('/tmp/wb3_pre.json','w'),ensure_ascii=False)
for x in rows:
    d=x['det'][0]
    print(x['i'],x['t'],x['y'],'/'.join(x['shops'][:3]),'n%d'%len(x['ncids']),(d['cr'] or '')[:22],'|',' '.join(x['flags']))
