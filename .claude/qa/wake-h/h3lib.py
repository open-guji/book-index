import urllib.request,urllib.parse,re,html,json,os,time,sys
D=os.path.dirname(os.path.abspath(__file__))
CC=os.path.join(D,'h3cache.json')
def _ld():
    try: return json.load(open(CC,encoding='utf-8'))
    except Exception: return {}
K=_ld()
def save():
    tmp=CC+'.tmp'
    json.dump(K,open(tmp,'w',encoding='utf-8'),ensure_ascii=False); os.replace(tmp,CC)
def get(u):
    for i in range(6):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research)'}),timeout=60).read().decode('utf-8','replace')
        except Exception as e: time.sleep(4*(i+1))
def clean(s): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s))).strip()
def search(q,page=1,count=200,extra=''):
    k='s:%s|%d|%d|%s'%(q,page,count,extra)
    if k in K: return K[k]
    t=get('https://ci.nii.ac.jp/books/search?q=%s&count=%d&p=%d%s'%(urllib.parse.quote(q),count,page,extra))
    if t is None: return None
    m=re.search(r'(\d+)件中',clean(t)); tot=int(m.group(1)) if m else None
    recs=[]
    for li in re.findall(r'<li class="(?:odd|even)line">(.*?)</li>',t,flags=re.S):
        nc=re.search(r'name="ncid"[^>]*value="([A-Z0-9]+)"',li)
        if not nc: continue
        g=lambda c:(lambda m:clean(m.group(1)) if m else '')(re.search(r'class="%s[^"]*"[^>]*>(.*?)</(?:p|dt)>'%c,li,flags=re.S))
        recs.append(dict(ncid=nc.group(1),title=g('item_mainTitle'),auth=g('item_subData'),pub=clean(' '.join(re.findall(r'class="pblc"[^>]*>(.*?)</span>',li,flags=re.S))),year=clean(' '.join(re.findall(r'class="pblcdt"[^>]*>(.*?)</span>',li,flags=re.S))),vol=g('item_bbldata-other'),n=(re.search(r'所蔵館(\d+)館',li) or [0,0])[1]))
    K[k]={'tot':tot,'recs':recs}; save(); time.sleep(2); return K[k]
def ncid(n):
    k='n:'+n
    if k in K: return K[k]
    t=get('https://ci.nii.ac.jp/ncid/'+n)
    if t is None: return None
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    s=clean(t); a=s.find('書誌事項'); b=s.find('大学図書館所蔵'); d=s.find('この図書・雑誌をさがす')
    r={'bib':s[a:b][:600],'hold':s[b:(d if d>b else b+900)][:700],'note':''}
    K[k]=r; save(); time.sleep(2); return r
if __name__=='__main__':
    if sys.argv[1]=='s':
        pg=int(sys.argv[3]) if len(sys.argv)>3 else 1
        r=search(sys.argv[2],pg); print('total',r['tot'])
        for x in r['recs']: print(x['ncid'],x['title'][:40],'|',x['auth'][:25],'|',x['pub'][:25],'|',x['year'],'|',x['vol'][:30],'|',x['n'])
    else:
        r=ncid(sys.argv[2]); print(r['bib']); print(r['hold']); print(r['note'])

def _v(x):
    if isinstance(x,list): return [_v(i) for i in x]
    if isinstance(x,dict): return x.get('@value',x.get('foaf:name',x))
    return x
def nj(n):
    """NCID json -> compact dict"""
    k='j:'+n
    if k in K: return K[k]
    t=get('https://ci.nii.ac.jp/ncid/%s.json'%n)
    if t is None: return None
    try: g=json.loads(t)['@graph'][0]
    except Exception: return None
    own=[]
    for o in g.get('bibo:owner',[]) if isinstance(g.get('bibo:owner',[]),list) else [g.get('bibo:owner')]:
        own.append(o.get('foaf:name') if isinstance(o,dict) else o)
    r=dict(ncid=n,title=_v(g.get('dc:title')),creator=_v(g.get('dc:creator')),pub=_v(g.get('dc:publisher')),ext=_v(g.get('dcterms:extent')),date=_v(g.get('dc:date')),pdate=_v(g.get('prism:publicationDate')),note=_v(g.get('cinii:note')),owners=own,nown=g.get('cinii:ownerCount'),vol=_v(g.get('dcterms:hasPart')) if 'dcterms:hasPart' in g else None)
    K[k]=r; save(); time.sleep(1.5); return r
