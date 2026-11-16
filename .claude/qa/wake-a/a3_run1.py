# -*- coding: utf-8 -*-
import sys; sys.path.insert(0,'/tmp/wa3')
from a3_resolve import *
from a3_clusters import clusters
Q=['周易','易經','尚書','書經','書集傳','詩經','毛詩','詩集傳','韓詩外傳','古文尚書','易程傳','伊川易傳','周易程傳','周易本義','易傳','書傳','詩傳','詩緝','詩序','禹貢','洪範','周易傳義','程朱傳義']
HRE=r'^(周易|易經|易程傳|伊川易傳|古周易|易學啟蒙|易傳|尚書|書經|書集傳|書傳|古文尚書|禹貢|洪範|詩經|毛詩|詩集傳|詩傳|詩緝|詩序|韓詩|詩本義|詩總聞)'
cl=clusters(Q,HRE)
res=collections.defaultdict(list)
for k,v in cl.items():
    x=v[0]
    w,why=resolve(k[0],x.get('dc:creator',''),x['title'])
    res[(k[0],w,why)].append((k,v))
out=[]
for (h,w,why),lst in sorted(res.items(),key=lambda kv:(kv[0][0],str(kv[0][1]),kv[0][2])):
    out.append('%s\t%s\t%s\t%d clusters\t%s'%(h,w,why,len(lst),lst[0][1][0].get('dc:creator','')[:30]))
open('/tmp/wa3/run1.txt','w').write('\n'.join(out))
print(len(cl),len(res))
