# -*- coding: utf-8 -*-
import sys,json,re,collections,hashlib,os,glob
sys.path.insert(0,'/tmp/wa3')
import a3lib
from a3norm import nz,era_year
JP=re.compile(r'(衛門|兵衛|衞門|兵衞|右衛|左衛|エ門|ヱ門|[一-龥]助|[一-龥]郎|[一-龥]屋|書肆|藩|學問所|学問所|昌平|官版|林氏|天王寺|書林|閣|館|庵|房|軒)')
CN2=re.compile(r'(通志堂|汲古|書業堂|嫏嬛|琅嬛|學海堂|粤雅|雅雨|葆璞|蜚英|點石|脈望|鴻寶|埽葉|雙梧|奎章|尊經|四友|金閶|王詒燕|三益堂|西園|六蓺|六藝|樂善堂|聚盛|慶餘|江寧|寧波|刊刻局|書院|刻局)')
CN=re.compile(r'(書局|书局|中華|商務|石印|上海|廣州|書院$|官書|刻書處|出版社|印書)')
def allitems(Q):
    seen={}
    for t in Q:
        p=1
        while True:
            f=os.path.join(a3lib.CACHE,'c_'+hashlib.md5(a3lib.q(t,p).encode()).hexdigest()+'.json')
            if not os.path.exists(f): break
            j=json.load(open(f,encoding='utf8')); its=a3lib.items(j)
            for x in its: seen[x['@id'][-10:]]=x
            if p*200>=a3lib.total(j) or p>=15: break
            p+=1
    return seen
def cand(x):
    d=x.get('dc:date','') or ''
    if not re.fullmatch(r'\d{4}',d): return None
    y=int(d)
    if y<1590 or y>1911: return None
    pub=' '.join(x.get('dc:publisher',[]) if isinstance(x.get('dc:publisher'),list) else [x.get('dc:publisher','')])
    if '不明' in pub: return None
    if CN.search(pub) or CN2.search(pub): return None
    if not JP.search(pub): return None
    return y,pub
