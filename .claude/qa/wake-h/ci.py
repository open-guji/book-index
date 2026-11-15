import urllib.request,urllib.parse,re,html,json,os,time
CC='./cicache.json'
K=json.load(open(CC)) if os.path.exists(CC) else {}
def f(u):
    for i in range(5):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research)'}),timeout=60).read().decode('utf-8','replace')
        except Exception: time.sleep(4*(i+1))
def txt(t):
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S); return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',t)))
def search(q):
    k='s:'+q
    if k in K: return K[k]
    t=f('https://ci.nii.ac.jp/books/search?q='+urllib.parse.quote(q)+'&count=20')
    if t is None: return None
    ids=list(dict.fromkeys(re.findall(r'/ncid/([A-Z0-9]+)',t)))
    s=txt(t); a=s.find('件中'); res=s[a-10:a+3000]
    K[k]={'ids':ids,'text':res}; json.dump(K,open(CC,'w'),ensure_ascii=False); time.sleep(2); return K[k]
def ncid(n):
    k='n:'+n
    if k in K: return K[k]
    t=f('https://ci.nii.ac.jp/ncid/'+n)
    if t is None: return None
    s=txt(t); a=s.find('書誌詳細'); 
    K[k]=s[:6000]; json.dump(K,open(CC,'w'),ensure_ascii=False); time.sleep(2); return K[k]
if __name__=='__main__':
    import sys
    if sys.argv[1]=='s': r=search(sys.argv[2]); print(r['ids']); print(r['text'][:1800])
    else: print(ncid(sys.argv[2])[:3500])

def info(n):
    s=ncid(n)
    if not s: return None
    a=s.find('書誌事項'); b=s.find('大学図書館所蔵'); c=s.find('該当する所蔵館はありません'); d=s.find('この図書・雑誌をさがす')
    e=s.find('注記',d)
    return {'bib':s[a:b][:400],'hold':s[b:min(x for x in (c,d) if x>0) if (c>0 or d>0) else b+600][:700],'note':s[e:e+500]}
