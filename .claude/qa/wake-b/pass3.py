import json,re,sys
sys.path.insert(0,'.')
import ndl,eras
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
ws=json.load(open('/tmp/wb_works.json'))
def q(title,creator):
    p={'title':ndl.jp(title),'from':'1450','until':'1912','cnt':100}
    if creator: p['creator']=creator
    d=ndl.fetch(p)
    try: root=ET.fromstring(d)
    except Exception: return []
    out=[]
    for it in root.iter('item'):
        g=lambda t:(it.findtext(t,namespaces=ndl.NS) or '').strip()
        out.append((it.findtext('link').split('/')[-1],g('dc:title'),g('dc:creator'),g('dc:publisher'),g('dc:date'),g('dcndl:volume'),g('dc:extent'),'/'.join(c.text for c in it.findall('category'))))
    return out
def job(wid):
    w=ws[wid];t=w['title'];au=(w.get('authors') or [{}])[0].get('name')
    r=q(t,None)
    if au and au!='佚名': r+=q(t,ndl.jp(au))
    return wid,r
with ThreadPoolExecutor(5) as ex: res=list(ex.map(job,list(ws)))
json.dump(res,open('/tmp/wb_pass3.json','w'),ensure_ascii=False)
print('ok')
