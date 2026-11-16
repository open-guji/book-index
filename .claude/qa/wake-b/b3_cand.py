# -*- coding: utf-8 -*-
"""讀緩存中的 NCID 詳情，按 (題名,年,書肆) 聚成版本候選。僅讀緩存，不發請求。"""
import sys,json,re,os,hashlib,collections;sys.path.insert(0,'.')
import b3_an as a,b3_cinii as c
def cached(n):
    url='https://ci.nii.ac.jp/ncid/%s.json'%n
    f=os.path.join(c.CD,hashlib.md5(url.encode()).hexdigest()+'.json')
    if not os.path.exists(f): return None
    # reuse parsing from c.ncid via monkeypatch of get
    return c.ncid(n)
KY=str.maketrans({'衛':'衞','寛':'寬','宝':'寶','暦':'曆','応':'應','万':'萬','禄':'祿','徳':'德','斎':'齋','沢':'澤','広':'廣','国':'國','学':'學','蔵':'藏','関':'關','対':'對','続':'續','覚':'覺','両':'兩','来':'來','為':'爲','兵':'兵'})
def ky(s): return (s or '').translate(KY)
def pubdate_info(d):
    pd=[p for p in (d.get('pubdate') or []) if p]
    return pd
if __name__=='__main__':
    g=a.clusters()
    m=collections.OrderedDict()
    for (t,y,p),l in g.items():
        if y>=1868: continue
        for x in l: m.setdefault((t,y),[]).append(x)
    n=0
    for (t,y),l in m.items():
        for x in l:
            d=cached(x['ncid'])
            if d: n+=1
    print(n)
