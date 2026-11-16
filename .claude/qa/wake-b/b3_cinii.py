# -*- coding: utf-8 -*-
"""wake-b 第三輪 CiNii Books 檢索（OpenSearch JSON + NCID JSON），緩存 /tmp/wb3_cache，串行，≥2 秒，退避。"""
import json,os,time,hashlib,urllib.parse,urllib.request,sys
CD='/tmp/wb3_cache';os.makedirs(CD,exist_ok=True)
UA={'User-Agent':'Mozilla/5.0 (compatible; research-bot)'}
_last=[0]
def get(url):
    f=os.path.join(CD,hashlib.md5(url.encode()).hexdigest()+'.json')
    if os.path.exists(f):
        try: return json.load(open(f,encoding='utf-8'))
        except Exception: pass
    for t in range(5):
        w=2.0-(time.time()-_last[0])
        if w>0: time.sleep(w)
        try:
            _last[0]=time.time()
            d=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60).read().decode('utf-8')
            j=json.loads(d);json.dump(j,open(f,'w',encoding='utf-8'),ensure_ascii=False);return j
        except Exception as e:
            time.sleep(4*(2**t))
    return None
def search(page=1,**kw):
    p={'year_from':1500,'year_to':1911,'count':200,'p':page,'format':'json'};p.update(kw)
    j=get('https://ci.nii.ac.jp/books/opensearch/search?'+urllib.parse.urlencode(p))
    if not j: return 0,[]
    c=j['@graph'][0];tot=int(c.get('opensearch:totalResults','0'));its=c.get('items',[])
    out=[]
    for i in its:
        pub=i.get('dc:publisher',[]);pub=[pub] if isinstance(pub,str) else pub
        out.append({'ncid':i['@id'].rsplit('/',1)[-1],'title':i.get('title',''),'date':i.get('dc:date',''),'pub':pub,'cr':i.get('dc:creator') or '','own':int(i.get('cinii:ownerCount','0') or 0)})
    return tot,out
def search_all(maxpages=8,**kw):
    res=[];pg=1
    while pg<=maxpages:
        tot,o=search(pg,**kw);res+=o
        if len(res)>=tot or not o: break
        pg+=1
    return res
def ncid(n):
    j=get('https://ci.nii.ac.jp/ncid/%s.json'%n)
    if not j: return None
    e=j['@graph'][0]
    def v(x):
        if isinstance(x,list): return [v(y) for y in x]
        if isinstance(x,dict): return x.get('@value',x.get('foaf:name',x))
        return x
    owners=[{'name':o.get('foaf:name'),'id':o.get('@id','').rsplit('/',1)[-1]} for o in (e.get('bibo:owner') or [])] if isinstance(e.get('bibo:owner'),list) else ([{'name':e['bibo:owner'].get('foaf:name'),'id':e['bibo:owner'].get('@id','').rsplit('/',1)[-1]}] if e.get('bibo:owner') else [])
    t=e.get('dc:title');t=t[0]['@value'] if isinstance(t,list) else (t.get('@value') if isinstance(t,dict) else t)
    return {'ncid':n,'title':t,'alt':e.get('dcterms:alternative'),'cr':e.get('dc:creator'),'pub':v(e.get('dc:publisher')),'extent':e.get('dcterms:extent'),'size':e.get('cinii:size'),'date':e.get('dc:date'),'pubdate':e.get('prism:publicationDate'),'notes':e.get('cinii:note'),'owners':owners,'parts':v(e.get('dcterms:hasPart')),'series':v(e.get('dcterms:isPartOf')),'url':'https://ci.nii.ac.jp/ncid/'+n}
if __name__=='__main__':
    r=search_all(title=sys.argv[1])
    for x in r: print(x['ncid'],x['title'],x['date'],x['pub'],x['cr'],x['own'])
