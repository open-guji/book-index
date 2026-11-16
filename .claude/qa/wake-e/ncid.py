import urllib.request,re,os,time,sys
import col
def get(n):
    f='/tmp/ndlc/ncid_%s.html'%n
    if not os.path.exists(f):
        w=2.2-(time.time()-col._last[0])
        if w>0:time.sleep(w)
        col._last[0]=time.time()
        for i in range(5):
            try:
                r=urllib.request.urlopen(urllib.request.Request('https://ci.nii.ac.jp/ncid/'+n,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read();open(f,'wb').write(r);break
            except Exception as e: time.sleep(5*2**i)
        else: return None
    s=open(f,encoding='utf-8',errors='ignore').read()
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S);t=re.sub(r'<[^>]+>','\n',t);t=re.sub(r'[ \t　]+',' ',t);t=re.sub(r'\n\s*\n+','\n',t)
    i=t.find('書誌事項');j=t.find('この図書・雑誌をさがす')
    k=t.find('注記',j)
    hold=t[t.find('大学図書館所蔵'):j] if '大学図書館所蔵' in t else ''
    holders=[]
    lines=[x.strip() for x in hold.split('\n') if x.strip()]
    return dict(bib=' / '.join(x.strip() for x in t[i:t.find('大学図書館所蔵')].split('\n')[1:12] if x.strip()),hold=' | '.join(lines[:30]),note=' / '.join(x.strip() for x in t[k:k+900].split('\n')[1:12] if x.strip()))
if __name__=='__main__':
    for n in sys.argv[1:]:
        d=get(n);print('==',n);print(d['bib']);print('HOLD:',d['hold'][:400]);print('NOTE:',d['note'][:400])
