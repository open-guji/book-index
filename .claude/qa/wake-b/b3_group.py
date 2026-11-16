# -*- coding: utf-8 -*-
"""把 NCID 詳情聚成版本候選（僅讀緩存）。輸出 /tmp/wb3_versions.json"""
import sys,json,re,collections;sys.path.insert(0,'.')
import b3_an as a,b3_cinii as c,b3_cand as cd
from b3_cand import ky
def shops(d):
    out=[]
    for p in d.get('pub') or []:
        if isinstance(p,dict): p=p.get('@value','')
        p=re.sub(r'\[?ほか\]?|\(發賣\)|\(發兌\)|\(発売\)|\(販賣\)|\(專賣\)|\(賣捌\)|（.*?）|\(.*?\)|\[|\]','',str(p))
        for s in re.split(r'[:：;；/／、,，\s]+',p):
            s=ky(s.strip())
            if s and '不明' not in s and len(s)>=2: out.append(s)
    return out
def kanki(d):
    return [n for n in (d.get('notes') or []) if re.search(r'刊記|奥付|奧付|見返',n)]
def weak(d):
    pd=' '.join(p for p in (d.get('pubdate') or []) if p)
    return bool(re.search(r'頃|推定|間\b|\?|？|\d-|\[.*\?\]',pd))
def japan(d):
    n=' '.join(d.get('notes') or [])
    return bool(re.search(r'和漢古書|明治より前に刊行された漢籍|和古書',n))
def build():
    g=a.clusters();cl=collections.defaultdict(list)
    for (t,y,p),l in g.items():
        if y>=1868: continue
        for x in l: cl[(t,y)].append(x)
    vers=[]
    for (t,y),l in cl.items():
        det=[]
        for x in l:
            d=cd.cached(x['ncid'])
            if d: det.append((x,d))
        # 以書肆集合聚
        groups=[]
        for x,d in det:
            sh=set(shops(d))
            for gr in groups:
                if gr['shops']&sh and sh: gr['items'].append((x,d));gr['shops']|=sh;break
            else:
                groups.append({'shops':set(sh),'items':[(x,d)]})
        for gr in groups:
            vers.append({'t':t,'y':y,'shops':sorted(gr['shops']),'ncids':[x['ncid'] for x,d in gr['items']],'det':[d for x,d in gr['items']]})
    return vers
if __name__=='__main__':
    v=build();json.dump(v,open('/tmp/wb3_versions.json','w'),ensure_ascii=False);print(len(v))
