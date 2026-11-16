# -*- coding: utf-8 -*-
import sys,json,re,collections;sys.path.insert(0,'.')
import b3_map as m, b3_strong as s
rows=m.rows
built={17,23,315,39,48,49,64,98,265,126,127,128,130,131,161,173,179,183,206,228,229,234,241,247,248,284,261,262,263,266,267,269,272,275,278,279,283,294,295,296,310,4,5}
# 269 兩種署名之第二組為 idx 270? 以題名年份判定
out=[]
for x in rows:
    if x['i'] in built: continue
    if x['t']=='礼記' and x['y']==1843 and any(h in ''.join(x['shops']) for h in ('吉野屋仁兵衞','升屋勘兵衞')): 
        continue
    d=x['det'][0]
    fl=x['flags'];why=[]
    for f in fl:
        if f.startswith('EX:'): why.append('庫內已有同年同題版本（%s），未能證明異版，未建（可作補挂）'%f[3:])
        elif f=='NOSHOP': why.append('書肆不明')
        elif f=='WEAK': why.append('刊年為推定')
        elif f=='CHN': why.append('疑清刻或中國刊本被日本館藏')
        elif f=='NOJP': why.append('無和古書／明治前漢籍標記，未確認日本刊')
    if not fl:
        w=m.auto(x['t'])
        if not w: why.append('庫內無對應 Work（日本人著作／衍生書），不硬挂')
        elif not s.strong(x): why.append('證據不足（僅單條著錄且出版者為括弧補記或無刊記說明），不建')
        else: why.append('待核')
    out.append((x['t'],x['y'],'/'.join(x['shops'][:3]),','.join(x['ncids'][:4]),'；'.join(why)))
out.sort()
open('TODO3.tsv','w',encoding='utf-8').write('題名(規範化)\t刊年\t書肆\tNCID\t未建原因\n'+'\n'.join('\t'.join(map(str,r)) for r in out)+'\n'
 +'(全組)\t1868-1911\t(明治期)\t(略)\t明治期刊本（左傳輯釋、春秋左氏傳校本明治諸本、禮記後藤點明治諸本等）本輪未逐條核版式，按第二輪口徑不建\n'
 +'(全組)\t-\t(漢籍注疏)\t(略)\t附釋音周禮／禮記／春秋左傳注疏、監本附音公羊／穀梁注疏等 CiNii 條目皆為清阮刻、點石齋、脈望仙館等中國刊本，非日本刊，未建\n')
print(len(out))
c=collections.Counter(r[4][:14] for r in out);print(c.most_common(12))
