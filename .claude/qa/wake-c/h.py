import urllib.parse,sys,json
from ndl import get
import xml.etree.ElementTree as ET
NS={'dc':'http://purl.org/dc/elements/1.1/','dcndl':'http://ndl.go.jp/dcndl/terms/'}
def q(**kw):
    u='https://ndlsearch.ndl.go.jp/api/opensearch?'+urllib.parse.urlencode(kw)
    t=get(u)
    if not t: return None
    r=ET.fromstring(t); out=[]
    for it in r.iter('item'):
        g=lambda p:[e.text for e in it.findall(p,NS) if e.text]
        out.append((g('title'),g('dc:creator'),g('dc:publisher'),g('dc:date'),it.find('link').text.split('/')[-1]))
    return out
if __name__=='__main__':
    for a in sys.argv[1:]:
        for kw in ({'title':a,'cnt':30,'until':1911},{'any':a+' 和古書','cnt':30}):
            print(kw); 
            for r in q(**kw) or []: print('  ',r)
