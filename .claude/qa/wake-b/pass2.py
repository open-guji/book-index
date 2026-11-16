import json,re,sys
sys.path.insert(0,'.')
import ndl,eras
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
shard=json.load(open(S+'shard1.json'))
def q(title,y,cnt=100):
    d=ndl.fetch({'title':ndl.jp(title),'from':y,'until':y,'cnt':cnt})
    try: root=ET.fromstring(d)
    except Exception: return []
    out=[]
    for it in root.iter('item'):
        g=lambda t:(it.findtext(t,namespaces=ndl.NS) or '').strip()
        out.append((it.findtext('link').split('/')[-1],g('dc:title'),g('dc:creator'),g('dc:publisher'),g('dc:date'),g('dcndl:volume'),g('dc:extent'),'/'.join(c.text for c in it.findall('category'))))
    return out
jobs=[]
for x in shard:
    y,_=eras.era_year(x['edition'])
    if y and y<1912+1 and ('日本' in x['edition'] or x['jp'] or '寬' in x['edition'] or '寛' in x['edition']): jobs.append((x,y))
def run(j):
    x,y=j
    t=x['title']
    # 核心題名：去標點
    res=q(t,y)
    core=ndl.jp(t)
    keep=[r for r in res if core[:3] in ndl.jp(r[1]) or ndl.jp(r[1])[:3] in core]
    return x,y,keep
with ThreadPoolExecutor(5) as ex:
    out=list(ex.map(run,jobs))
json.dump([(x['id'],y,k) for x,y,k in out],open('/tmp/wb_pass2.json','w'),ensure_ascii=False)
print(len(out))
