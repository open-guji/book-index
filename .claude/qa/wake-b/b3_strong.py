# -*- coding: utf-8 -*-
import sys,json,re,collections;sys.path.insert(0,'.')
import b3_map as m
from b3_group import kanki,shops
def rec_strong(d):
    pubs=[p if isinstance(p,str) else str(p) for p in (d.get('pub') or [])]
    if not pubs or any('[' in p and '[ほか]' not in p and 'ほか' not in p for p in pubs): 
        # 括號=推定
        return False
    if any('不明' in p for p in pubs): return False
    pd=' '.join(p for p in (d.get('pubdate') or []) if p)
    if re.match(r'^\[',pd) or re.search(r'頃|推定|\?',pd): return False
    return True
def strong(x):
    good=[d for d in x['det'] if rec_strong(d)]
    if not good: return False
    kk=any(kanki(d) for d in good)
    return kk or len(good)>=2
rows=m.rows
inc=[x for x in rows if not x['flags'] and m.auto(x['t'])]
S=[x for x in inc if strong(x)]
if __name__=='__main__':
    print(len(inc),len(S))
    for x in S: print(x['i'],x['t'],x['y'],'/'.join(x['shops'][:3]),len(x['ncids']))
