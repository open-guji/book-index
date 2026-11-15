import sys,time,urllib.parse,urllib.request,xml.etree.ElementTree as ET,json,os
CACHE=os.environ.get('QC','./qcache.json')
C=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
NS={'dc':'http://purl.org/dc/elements/1.1/','dcterms':'http://purl.org/dc/terms/','dcndl':'http://ndl.go.jp/dcndl/terms/','rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
def q(title,creator='',cnt=50,extra=''):
    k='%s|%s|%d|%s'%(title,creator,cnt,extra)
    if k in C: return C[k]
    u='https://ndlsearch.ndl.go.jp/api/opensearch?title=%s&cnt=%d'%(urllib.parse.quote(title),cnt)
    if creator: u+='&creator='+urllib.parse.quote(creator)
    u+=extra
    r=None
    for i in range(8):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research)'}),timeout=40).read().decode()
        except Exception as e:
            time.sleep(6*(i+1)); r=None; continue
        if '<error>' in r: time.sleep(8*(i+1)); r=None; continue
        break
    if r is None: return None
    out=[]
    for it in ET.fromstring(r).iter('item'):
        g=lambda t:[e.text for e in it.findall(t,NS) if e.text]
        out.append({'title':g('title'),'creator':g('dc:creator'),'pub':g('dc:publisher'),'date':g('dc:date')+g('dcterms:issued'),'vol':g('dc:extent')+g('dcndl:volume'),'link':g('link'),'desc':g('dc:description')})
    C[k]=out; json.dump(C,open(CACHE,'w'),ensure_ascii=False)
    time.sleep(2.2)
    return out
if __name__=='__main__':
    for x in q(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '',50,sys.argv[3] if len(sys.argv)>3 else ''):
        print(x['title'][:1],x['creator'][:2],x['pub'],x['date'][:2],x['vol'][:1],x['link'][0].split('/')[-1])
