#!/usr/bin/env python3
import sys,time,urllib.parse,urllib.request,re,xml.etree.ElementTree as ET,json,os
CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'ndl_cache.json')
C=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def q(title,creator='',cnt=20):
    k=title+'|'+creator
    if k in C: return C[k]
    u='https://ndlsearch.ndl.go.jp/api/opensearch?title=%s&cnt=%d'%(urllib.parse.quote(title),cnt)
    if creator: u+='&creator='+urllib.parse.quote(creator)
    for i in range(8):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research)'}),timeout=30).read().decode()
        except Exception as e:
            time.sleep(5*(i+1)); continue
        if '<error>' in r: time.sleep(6*(i+1)); continue
        break
    else: return None
    ns={'dc':'http://purl.org/dc/elements/1.1/','dcterms':'http://purl.org/dc/terms/','dcndl':'http://ndl.go.jp/dcndl/terms/','rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
    out=[]
    for it in ET.fromstring(r).iter('item'):
        g=lambda t:[e.text for e in it.findall(t,ns) if e.text]
        out.append({'title':g('title'),'creator':g('dc:creator'),'pub':g('dc:publisher'),'date':g('dc:date')+g('dcterms:issued'),'vol':g('dc:extent')+g('dcndl:volume'),'link':g('link'),'type':[e.text for e in it.findall('dc:type',ns)],'id':[ (e.get('{http://www.w3.org/2001/XMLSchema-instance}type'),e.text) for e in it.findall('dc:identifier',ns)]})
    C[k]=out; json.dump(C,open(CACHE,'w'),ensure_ascii=False)
    time.sleep(2)
    return out
if __name__=='__main__':
    for x in q(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else ''):
        print(x['title'],x['creator'],x['pub'],x['date'],x['vol'],x['link'][:1],[i[1] for i in x['id']][:3])
