import urllib.parse,urllib.request,re,time,os,hashlib,json,xml.etree.ElementTree as ET
C='/tmp/ndlc';_last=[0]
NS={'dc':'http://purl.org/dc/elements/1.1/','dcterms':'http://purl.org/dc/terms/','dcndl':'http://ndl.go.jp/dcndl/terms/'}
def fetch(params):
    u='https://ndlsearch.ndl.go.jp/api/opensearch?'+'&'.join('%s=%s'%(k,urllib.parse.quote(str(v))) for k,v in params)
    f=C+'/'+hashlib.md5(u.encode()).hexdigest()+'.xml'
    if os.path.exists(f): return open(f,'rb').read()
    for i in range(7):
        w=2.2-(time.time()-_last[0])
        if w>0: time.sleep(w)
        _last[0]=time.time()
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read()
            open(f,'wb').write(r);return r
        except Exception as e:
            time.sleep(min(60,5*2**i))
    return None
def parse(r):
    out=[]
    if not r: return out
    try: root=ET.fromstring(r)
    except Exception: return out
    for it in root.iter('item'):
        g=lambda t:(it.findtext(t,namespaces=NS) or '').strip()
        desc=it.findtext('description') or ''
        pre=re.sub(r'<[^>]+>','|',desc.split('タイトル')[0]).strip('| ')
        out.append(dict(place=g('dcndl:publicationPlace'),nii=next((x.text for x in it.findall('dc:identifier',NS) if x.get('{http://www.w3.org/2001/XMLSchema-instance}type','').endswith('NIIBibID')),''),date=g('dc:date'),pubr=g('dc:publisher'),descs=[x.text or '' for x in it.findall('dc:description',NS) if x.text][:20],id=(it.findtext('link') or '').split('/')[-1],t=g('dc:title'),a=g('dc:creator'),pub=g('dc:publisher'),iss=g('dcterms:issued'),ext=g('dc:extent'),pre=pre,cat=[c.text for c in it.findall('category')],note=' / '.join(x.text or '' for x in it.findall('dc:description',NS))[:200]))
    return out
def q(title,author=''):
    res={}
    for params in ([('any',title+' 和古書'),('cnt',100)],[('title',title),('from',1450),('until',1911),('cnt',100)]+([('creator',author)] if author else [])):
        for r in parse(fetch(params)): res[r['id']]=r
    return res
