import re,html,time,urllib.request,json,os,sys
PC='./pgcache.json'
P=json.load(open(PC)) if os.path.exists(PC) else {}
def fetch(u):
    for i in range(6):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research)'}),timeout=40).read().decode('utf-8','replace')
        except Exception: time.sleep(4*(i+1))
def page(rid):
    if rid in P: return P[rid]
    t=fetch('https://ndlsearch.ndl.go.jp/books/'+rid)
    if not t: return None
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S); t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(re.sub(r'\s+',' ',t))
    P[rid]=t; json.dump(P,open(PC,'w'),ensure_ascii=False); time.sleep(2)
    return t
if __name__=='__main__':
    for a in sys.argv[1:]:
        t=page(a); i=t.find('タイトル'); print('==',a); print(t[:2500])
