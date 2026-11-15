import sys,time,json,os,re,urllib.parse,urllib.request,hashlib
import xml.etree.ElementTree as ET
CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache'); os.makedirs(CACHE,exist_ok=True)
UA='Mozilla/5.0 (compatible; book-index-research)'
def get(url,tries=6):
    f=os.path.join(CACHE,hashlib.md5(url.encode()).hexdigest())
    if os.path.exists(f): return open(f,encoding='utf-8').read()
    for i in range(tries):
        time.sleep(1.5)
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=40)
            t=r.read().decode('utf-8','replace')
            if '<code>429' in t: raise Exception('429')
            open(f,'w',encoding='utf-8').write(t); return t
        except Exception as e:
            time.sleep(5*(i+1))
    return None
NS={'dc':'http://purl.org/dc/elements/1.1/','dcndl':'http://ndl.go.jp/dcndl/terms/'}
def ndl(title,creator='',cnt=20):
    q='title=%s&cnt=%d'%(urllib.parse.quote(title),cnt)
    if creator: q+='&creator='+urllib.parse.quote(creator)
    t=get('https://ndlsearch.ndl.go.jp/api/opensearch?'+q)
    if not t: return None
    root=ET.fromstring(t); out=[]
    for it in root.iter('item'):
        g=lambda p:[e.text for e in it.findall(p,NS) if e.text]
        out.append({'title':g('title'),'creator':g('dc:creator'),'pub':g('dc:publisher'),'date':g('dc:date'),'link':g('link'),'cat':[e.text for e in it.findall('category')]})
    return out
