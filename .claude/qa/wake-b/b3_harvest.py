# -*- coding: utf-8 -*-
import json,sys;sys.path.insert(0,'.')
import b3_cinii as c
Q=['周禮','周礼','周官','考工記','考工记','儀禮','儀礼','禮記','礼記','礼记','大戴禮','大戴礼','三禮','三礼','曲禮','月令','檀弓','春秋','左傳','左伝','左氏','公羊','穀梁','谷梁','榖梁','三傳','三伝','四傳','四伝','經傳集解','経伝集解','左傳博議','左氏博議','春秋胡傳','春秋集傳']
out={}
for q in Q:
    r=c.search_all(maxpages=25,title=q)
    print(q,len(r),flush=True)
    for x in r: out.setdefault(x['ncid'],x)
json.dump(out,open('/tmp/wb3_harvest.json','w'),ensure_ascii=False)
print(len(out))
