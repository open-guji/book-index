import urllib.parse,sys,json,re
from ndl import get
import xml.etree.ElementTree as ET
NS={'dc':'http://purl.org/dc/elements/1.1/','dcndl':'http://ndl.go.jp/dcndl/terms/','dcterms':'http://purl.org/dc/terms/'}
def q(**kw):
    t=get('https://ndlsearch.ndl.go.jp/api/opensearch?'+urllib.parse.urlencode(kw))
    if not t: return None
    try: r=ET.fromstring(t)
    except Exception: return None
    out=[]
    for it in r.iter('item'):
        g=lambda p:[e.text for e in it.findall(p,NS) if e.text]
        out.append({'t':(g('dc:title') or [''])[0],'cr':g('dc:creator'),'pub':(g('dc:publisher') or [''])[0],'date':(g('dc:date') or [''])[0],'iss':(g('dcterms:issued') or [''])[0],'place':(g('dcndl:publicationPlace') or [''])[0],'ext':(g('dc:extent') or [''])[0],'id':it.find('link').text.split('/')[-1],'cat':[c.text for c in it.findall('category')]})
    return out
if __name__=='__main__':
    works=json.load(open('/tmp/wk-wake-c/.claude/qa/wake-c/works.json'))
    res={}
    for w,v in works.items():
        title=v['title']; items=[]
        for idx in (1,31,61):
            r=q(title=title,cnt=30,until=1911,idx=idx)
            if r is None: break
            items+=r
            if len(r)<30: break
        res[w]={'title':title,'authors':v['authors'],'items':items}
        print(w,title,len(items),sum(1 for i in items if i['place']=='JP'),flush=True)
        json.dump(res,open('harvest.json','w'),ensure_ascii=False)
