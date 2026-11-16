import re,html,time,urllib.request,json,os,sys
HC=os.path.join(os.path.dirname(os.path.abspath(__file__)),'hold_cache.json')
H=json.load(open(HC)) if os.path.exists(HC) else {}
def fetch(u):
    for i in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research)'}),timeout=40).read().decode('utf-8','replace')
        except Exception as e: time.sleep(4*(i+1))
def ndlpage(rid):
    if rid in H: return H[rid]
    t=fetch('https://ndlsearch.ndl.go.jp/books/'+rid)
    if not t: return None
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S); t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(re.sub(r'\s+',' ',t))
    a=t.find('すべての資料形態'); b=t.find('書店で探す',a+10)
    # holdings section between 'すべての資料形態' and '書店で探す 日本の古本屋'
    b=t.find('日本の古本屋',a)
    H[rid]={'title':t[:60],'hold':t[a:b][:1500],'bib':t[b:b+1800]}
    json.dump(H,open(HC,'w'),ensure_ascii=False); time.sleep(2)
    return H[rid]
def cinii(ncid):
    k='cinii:'+ncid
    if k in H: return H[k]
    t=fetch('https://ci.nii.ac.jp/ncid/'+ncid)
    if not t: return None
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S); t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(re.sub(r'\s+',' ',t))
    H[k]={'text':t[:4000]}
    json.dump(H,open(HC,'w'),ensure_ascii=False); time.sleep(2)
    return H[k]
if __name__=='__main__':
    for a in sys.argv[1:]:
        r=ndlpage(a); print('==',a,r['title']); print(r['hold'][:900]); print(r['bib'][:700])
