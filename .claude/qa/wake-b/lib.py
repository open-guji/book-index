import sys,re,os,hashlib,urllib.parse,urllib.request,time,html
CD='/tmp/wb_cache'
def sru(rid):
    url='https://ndlsearch.ndl.go.jp/api/sru?operation=searchRetrieve&query='+urllib.parse.quote('itemno="%s"'%rid)+'&recordSchema=dcndl'
    f=os.path.join(CD,'sru_'+hashlib.md5(url.encode()).hexdigest())
    if os.path.exists(f): return open(f,encoding='utf-8').read()
    for t in range(3):
        try:
            d=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; research-bot)'}),timeout=60).read().decode('utf-8');break
        except Exception: d=None;time.sleep(3)
    if d is None: return ''
    open(f,'w',encoding='utf-8').write(d);time.sleep(0.8);return d
def libs(rid):
    d=sru(rid)
    m=re.search(r'name="LIBRARY"&gt;(.*?)&lt;/lst',d,re.S)
    return re.findall(r'name="([^"]+)"',html.unescape(m.group(1))) if m else []
if __name__=='__main__':
    for r in sys.argv[1:]: print(r,libs(r))
