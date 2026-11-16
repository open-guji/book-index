# -*- coding: utf-8 -*-
import json,re,collections,sys
sys.path.insert(0,'.')
import ndl,eras
h=json.load(open('/tmp/wb3_harvest.json'))
jb=json.load(open('/tmp/wb3_jpbooks.json'))
def N(s):
    s=ndl.jp(s)
    for x,y in [('註','注'),('辯','弁'),('辨','弁'),('觽','觿'),('竒','奇'),('觧','解'),('礼','礼'),('傅','傅'),('榖','穀'),('谷梁','穀梁'),('歴','曆'),('暦','曆'),('寳','宝'),('麁','粗'),('両','兩')]: s=s.replace(x,y)
    return re.sub(r'[\s　,，、]','',s)
def nt(t): return N(re.sub(r'\s*\d+[巻卷册冊].*$|\s*[\[〔(（].*$','',t))
JP=re.compile(r'衛門|兵衞|兵衛|衞門|右衞|左衞|屋|書林|藏版|蔵版|[ぁ-ゟ゠-ヿ]|昌平|學問所|学問所|官版|官板|館|堂|軒|齋|斎|社$|書院|書房|大學|大学|藩|寮|[ほ]か')
FAM=re.compile(r'周礼|周官|考工記|儀礼|礼記|大戴礼|三礼|曲礼|月令|檀弓|春秋|左伝|左氏|公羊|穀梁|谷梁|榖梁|三伝|四伝|経伝集解|博議')
EXC=re.compile(r'呂氏春秋|晏子春秋|呉越春秋|十六国春秋|十国春秋|昔昔|皇清経解|昭代叢書|漢魏叢書|通志堂|繁露|史記|越春秋|春秋時代|春秋社|春秋戦国|神仙|医|月令博物|林園月令|経典釈文|読書雑志|明史|国語|社日|諸子|百家|十三経|五経|四書|叢書|全書|新書')
def ey(b):
    y,_=eras.era_year(b.get('edition',''))
    d=b.get('dating',{})
    return y or d.get('year')
def run():
    C=[]
    for n,x in h.items():
        t=nt(x['title'])
        if not FAM.search(t) or EXC.search(t): continue
        pub=' '.join(x['pub'])
        if not x['date'] or not re.match(r'^\d{4}$',x['date']): 
            pass
        C.append((t,x))
    return C
if __name__=='__main__':
    C=run();print(len(C))
    g=collections.defaultdict(list)
    for t,x in C: g[t].append(x)
    for t,l in sorted(g.items(),key=lambda a:-len(a[1]))[:80]:
        print(len(l),t)

def cands(minown=1):
    C=run();rows=[]
    ex=collections.defaultdict(list)
    for b in jb: ex[nt(b['title'])].append(b)
    for t,x in C:
        pub=' '.join(x['pub'])
        if not JP.search(pub): continue
        if not re.match(r'^\d{4}$',x['date'] or ''): continue
        y=int(x['date'])
        if y<1500: continue
        match=[]
        for et,bl in ex.items():
            if et==t or (len(t)>=3 and (t in et or et in t) and len(et)>=3):
                for b in bl:
                    if ey(b)==y: match.append(b['id']+':'+b['title'])
        rows.append((t,y,pub,x,match))
    return rows

JP2=re.compile(r'衛門|兵衞|兵衛|衞門|右衞|左衞|[ぁ-ゟ゠-ヿ]|官版|官板|學問所|学問所|昌平|書林|屋[^敷]|助$|郎|藩|館|[ほ]か')
CHN=re.compile(r'點石齋|脈望仙館|商務|中華|掃葉|上海|廣雅|江南|金閶|同文|石印|局$|嘉業堂|文瑞|醉六|鴻寶|積山|蜚英|鴻文|宏文|圖書集成|五桂樓|崇正堂|敦化堂|崇道堂|經元堂|致和堂|三多齋|刊本')
def jpish(x):
    pub=' '.join(x['pub']);cr=x['cr'] or ''
    if re.search(r'日本|點|点|訓|訓点|句読|句讀|校定|道春|惺窩|闇齋|闇斎|羅山|芝山',cr): return True
    if CHN.search(pub) and not re.search(r'衛門|兵衞|兵衛|衞門',pub): return False
    return bool(re.search(r'衛門|兵衞|兵衛|衞門|右衞|左衞|[ぁ-ゟ゠-ヿ]|官版|官板|學問所|学問所|昌平|書林|屋[^敷]|ほか',pub))
def pk(x):
    p=''.join(x['pub']);p=re.sub(r'[\s\[\]　:：;；,，、()（）\-]','',p);p=p.replace('衞','衛').replace('發賣','').replace('發兌','')
    return p
def clusters():
    C=run();g=collections.OrderedDict()
    for t,x in C:
        if not jpish(x): continue
        if not re.match(r'^\d{4}$',x['date'] or ''): continue
        y=int(x['date'])
        if y<1500: continue
        g.setdefault((t,y,pk(x)[:14]),[]).append(x)
    return g
