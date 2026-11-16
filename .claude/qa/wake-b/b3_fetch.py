# -*- coding: utf-8 -*-
import sys,json,re,collections;sys.path.insert(0,'.')
import b3_an as a,b3_cinii as c
g=a.clusters()
NOISE=re.compile(r'辨志堂|嫏嬛館|金陵書局|王儒行|點石|校經山房|天工書局|上海|粤東|南昌府學|崇徳堂|嘉業堂|清章邱|李元|坂東|茶之湯|興歌|英米|祇園|西国|奉納|春秋社|世説|毛詩稽古|経伝釈詞|纂文|漆雕子|礼緯|石渠|礼論|礼記馬氏|礼記孫氏|礼記新義|礼記熊氏|周礼徐氏|春秋成長|春秋大伝|春秋緯|春秋穀梁伝注義|春秋左氏長経|春秋左伝義疏|春秋規過|春秋左氏伝解誼|周礼鄭|学春秋|左伝紀事|左伝会箋|左氏会箋')
m=collections.OrderedDict()
for (t,y,p),l in g.items():
    if NOISE.search(t) or y>=1868: continue
    m.setdefault((t,y),[]).extend(l)
out={}
n=0
for (t,y),l in m.items():
    seen=set()
    for x in sorted(l,key=lambda x:-x['own']):
        k=a.pk(x)[:14]
        if k in seen and len(seen)>=1 and sum(1 for z in out if False)>=0 and len([1 for s in seen if s==k])>=1: 
            continue
        seen.add(k)
        d=c.ncid(x['ncid']);n+=1
        if d: out[x['ncid']]=d
    print(n,t,y,flush=True)
json.dump(out,open('/tmp/wb3_ncid.json','w'),ensure_ascii=False)
