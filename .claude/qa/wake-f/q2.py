import json,os,re,sys,time,urllib.parse,urllib.request,hashlib
import xml.etree.ElementTree as ET
C='/tmp/wf_cache'; os.makedirs(C,exist_ok=True)
def get(url):
    f=C+'/'+hashlib.md5(url.encode()).hexdigest()
    if os.path.exists(f): return open(f,encoding='utf-8').read()
    for i in range(5):
        time.sleep(2.2*(2**i) if i else 2.2)
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research; bibliographic)'}),timeout=30)
            t=r.read().decode('utf-8','replace'); open(f,'w',encoding='utf-8').write(t); return t
        except Exception as e:
            pass
    return ''
def ndl(title,extra=''):
    u='https://ndlsearch.ndl.go.jp/api/opensearch?'+urllib.parse.urlencode({'title':title,'cnt':40})
    t=get(u); res=[]
    try: root=ET.fromstring(t)
    except Exception: return res
    for it in root.iter('item'):
        g=lambda n:[e.text for e in it if e.tag.endswith('}'+n) or e.tag==n]
        link=(g('link') or [''])[0]
        res.append({'t':(g('title') or [''])[0],'c':(g('creator') or g('author') or [''])[:2],'p':(g('publisher') or [''])[0],'d':(g('date') or g('issued') or [''])[0],'l':link,'cl':[x for x in g('type')][:1]})
    return res
if __name__=='__main__':
    for r in ndl(sys.argv[1]): print(r)
