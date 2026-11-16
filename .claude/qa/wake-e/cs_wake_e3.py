# CiNii Books 檢索（wake-e 第三輪專用）：返回 [(ncid,title,author,publisher,year,libs)]
import urllib.request,urllib.parse,re,os,time,hashlib,col
C='/tmp/ndlc'
def search(q,page=1,count=200,year_to=1911,sort=2):
    u='https://ci.nii.ac.jp/books/search?'+urllib.parse.urlencode(dict(q=q,count=count,page=page,sortorder=sort,year_to=year_to))
    f=C+'/cs_'+hashlib.md5(u.encode()).hexdigest()+'.html'
    if not os.path.exists(f):
        for i in range(6):
            w=2.2-(time.time()-col._last[0])
            if w>0: time.sleep(w)
            col._last[0]=time.time()
            try:
                r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read();open(f,'wb').write(r);break
            except Exception as e: time.sleep(min(60,5*2**i))
        else: return None
    s=open(f,encoding='utf-8',errors='ignore').read()
    tot=re.search(r'([\d,]+)\s*件',re.sub(r'<[^>]+>',' ',s[s.find('listHeading')-3000:s.find('listHeading')+3000])) 
    out=[]
    for m in re.finditer(r'<li class="(?:odd|even)line">(.*?)</li>',s,flags=re.S):
        b=m.group(1)
        g=lambda p:(re.search(p,b,flags=re.S) or [None,''])[1]
        ncid=g(r'/ncid/(\w+)'); t=re.sub(r'<[^>]+>','',g(r'class="taggedlink">(.*?)</a>')).strip()
        au=re.sub(r'<[^>]+>','',g(r'item_authordata">(.*?)</p>')).strip()
        pb=re.sub(r'<[^>]+>','',g(r'class="pblc">(.*?)</span>')).strip()
        yr=re.sub(r'<[^>]+>','',g(r'class="pblcdt">(.*?)</span>')).strip()
        lib=g(r'所蔵館(\d+)館')
        ser=re.sub(r'<[^>]+>','',g(r'class="ptblt-nmetc">(.*?)</span>')).strip()
        out.append((ncid,t,au,pb,yr,lib,ser))
    return out,(tot.group(1) if tot else '?')
if __name__=='__main__':
    import sys
    q=sys.argv[1]; pg=int(sys.argv[2]) if len(sys.argv)>2 else 1
    r=search(q,pg)
    print(r[1]); 
    for x in r[0]: print('\t'.join(x))
