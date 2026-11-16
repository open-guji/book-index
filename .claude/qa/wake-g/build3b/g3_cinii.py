import sys,re,subprocess,html,json,os,time,hashlib,urllib.parse
C='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/cache/'
os.makedirs(C,exist_ok=True)
UA='Mozilla/5.0 (X11; Linux x86_64) research-script'
def get(u,delay=1.2):
    f=C+hashlib.md5(u.encode()).hexdigest()
    if os.path.exists(f): return open(f,encoding='utf8').read()
    for k in range(4):
        time.sleep(delay*(k+1))
        r=subprocess.run(['curl','-sS','-m','40','-A',UA,u],capture_output=True)
        t=r.stdout.decode('utf8','ignore')
        if len(t)>2000 and '429' not in t[:300]:
            open(f,'w',encoding='utf8').write(t); return t
    return ''
def search(q,page=1,count=200,year_to=1911,extra=''):
    u='https://ci.nii.ac.jp/books/search?q=%s&count=%d&p=%d&year_to=%d%s'%(urllib.parse.quote(q),count,page,year_to,extra)
    h=get(u)
    m=re.search(r'検索結果[^0-9]*?([\d,]+)\s*件',h)
    tot=m.group(1) if m else None
    items=[]
    for blk in re.split(r'<li class="(?:odd|even)line">',h)[1:]:
        n=re.search(r'href="/ncid/([A-Z0-9]+)"[^>]*>(.*?)</a>',blk,re.S)
        if not n: continue
        def sp(c):
            x=re.search(r'class="%s"[^>]*>(.*?)</span>'%c,blk,re.S); return html.unescape(re.sub('<[^>]+>','',x.group(1))).strip() if x else ''
        au=re.search(r'item_authordata">(.*?)</p>',blk,re.S)
        lib=re.search(r'所蔵館(\d+)館',blk)
        items.append(dict(ncid=n.group(1),title=html.unescape(re.sub('<[^>]+>','',n.group(2))).strip(),au=html.unescape(re.sub('<[^>]+>','',au.group(1))).strip() if au else '',pub=sp('pblc'),yr=sp('pblcdt'),vol=sp('vlsr'),libs=int(lib.group(1)) if lib else 0))
    return tot,items
if __name__=='__main__':
    t,it=search(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 1)
    print(t,len(it))
    for i in it[:int(sys.argv[3]) if len(sys.argv)>3 else 30]: print(i)
