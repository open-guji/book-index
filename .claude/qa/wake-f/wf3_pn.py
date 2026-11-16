import re,sys,json
from wf3_cin import get
def flat(t):
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    s=re.sub(r'<[^>]+>','|',t); s=re.sub(r'&emsp;|&nbsp;',' ',s); s=re.sub(r'\s+',' ',s); return re.sub(r'(\| ?)+','|',s)
def parse(nc):
    s=flat(get('https://ci.nii.ac.jp/ncid/'+nc))
    d={'ncid':nc}
    i=s.find('書誌事項|'); j=s.find('|タイトル別名',i) 
    k=s.find('|大学図書館所蔵',i)
    seg=s[i+5:(k if k>0 else i+800)]
    parts=seg.split('|')
    d['title']=parts[0]; d['resp']=parts[1] if len(parts)>1 else ''; d['imprint']=parts[2] if len(parts)>2 else ''
    d['vols']=[p for p in parts[3:] if not p.startswith('タイトル')][:12]
    a=s.find('タイトル別名|'); 
    if a>0 and (k<0 or a<k): d['alt']=s[a+8:(k if k>0 else a+200)].split('|タイトル読み')[0].split('|')
    # holders
    h=[]
    if k>0:
        e=s.find('|OPAC|',k); e2=s.find('該当する所蔵館はありません',k)
        hs=s[k:e if e>0 else k+800]
        m=re.search(r'全\|(\d+)\|件\|(.*)',hs)
        if m:
            body=m.group(2)
            # institution names precede '|図|' or '|書|'
            for tok in body.split('|'):
                tok=tok.strip()
                if re.search(r'大学|大學|図書館|文庫|博物館|研究所|資料館|学校|学院|史料|センター|研究会|会館|宮内庁|書陵部|協会|病院|医学館|医院|室|所',tok) and not re.match(r'^[\d第巻卷]',tok) and tok not in h: h.append(tok)
            d['hold_raw']=body[:240]
    d['holders']=h
    nn=s.find('|Tweet'); n=s.rfind('|注記|',0,nn)
    d['notes']=s[n+4:nn].split('|') if n>0 else []
    def fld(name):
        m=re.search(r'\|'+name+r'\|([^|]*)',s); return m.group(1) if m else ''
    d['place']=fld('出版地'); d['extent']=fld('ページ数/冊数'); d['size']=fld('大きさ')
    return d
if __name__=='__main__':
    for nc in sys.argv[1:]:
        d=parse(nc); print(json.dumps(d,ensure_ascii=False))
