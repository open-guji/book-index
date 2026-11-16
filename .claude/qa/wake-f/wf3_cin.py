import re,sys,json,time,os,hashlib,urllib.parse,urllib.request
C='/tmp/wf_cache'; os.makedirs(C,exist_ok=True)
def get(url):
    f=C+'/'+hashlib.md5(url.encode()).hexdigest()
    if os.path.exists(f):
        t=open(f,encoding='utf-8').read()
        if t: return t
    for i in range(5):
        time.sleep(2.2*(2**i) if i else 2.2)
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research; bibliographic)'}),timeout=40)
            t=r.read().decode('utf-8','replace'); open(f,'w',encoding='utf-8').write(t); return t
        except Exception as e: pass
    return ''
JP='慶長 元和 寛永 寬永 正保 慶安 慶應 承応 承應 明暦 明曆 万治 萬治 寛文 寬文 延宝 延寶 天和 貞享 元禄 元祿 宝永 寶永 正徳 享保 元文 寛保 寬保 延享 寛延 寬延 宝暦 寶曆 寶暦 明和 安永 天明 寛政 寬政 享和 文化 文政 天保 弘化 嘉永 安政 万延 萬延 文久 元治 慶応 明治 文禄 天正 永禄 天文 大永 延徳 應仁 応仁 明応 寛正 元亀 天承'.split()
def isjp(d): return any(e in d for e in JP)
def clean(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',s)).strip()
def search(q,maxpages=5,yto=1911):
    out=[];seen=set()
    for pg in range(1,maxpages+1):
        u='https://ci.nii.ac.jp/books/search?'+urllib.parse.urlencode({'q':q,'count':200,'year_to':yto,'p':pg,'sortorder':3})
        t=get(u)
        items=re.findall(r'<li class="(?:odd|even)line">(.*?)</li>',t,re.S)
        if not items: break
        n=0
        for it in items:
            m=re.search(r'href="/ncid/([A-Z0-9]+)"[^>]*>(.*?)</a>',it,re.S)
            if not m: continue
            nc=m.group(1)
            if nc in seen: continue
            seen.add(nc); n+=1
            g=lambda c:(lambda x:clean(x.group(1)) if x else '')(re.search(r'class="%s">(.*?)</(?:span|p)>'%c,it,re.S))
            lib=re.search(r'所蔵館(\d+)館',it)
            out.append({'ncid':nc,'title':clean(m.group(2)),'au':g('item_subData item_authordata'),'pub':g('pblc'),'date':g('pblcdt'),'ser':g('ptblt-nmetc'),'vol':g('vlsr')[:100],'lib':int(lib.group(1)) if lib else 0})
        if len(items)<200: break
    return out
if __name__=='__main__':
    q=sys.argv[1]; mp=int(sys.argv[2]) if len(sys.argv)>2 else 3
    r=search(q,mp)
    print(len(r),'total;')
    for x in r:
        if isjp(x['date']): print(x['ncid'],x['title'][:40],'|',x['au'][:25],'|',x['pub'][:20],'|',x['date'][:22],'|',x['vol'][:30],'|',x['lib'])
