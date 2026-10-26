# 上图-并：对 2,422 组（现库在世）两两出特征
import pickle,json,os,re,collections,csv,opencc,sys
exec(open('load.py').read())
cc=opencc.OpenCC('t2s')
VAR={}
for r in csv.DictReader(open('/mnt/project-files/dedup-3a-2/variants-zi-ji.tsv'),delimiter='\t'):
    a,b=cc.convert(r['异体字']),cc.convert(r['正字'])
    if a and b and a!=b: VAR[a]=b
for a,b in ['抄钞','畧略','廸迪','劄札','隄堤','彚汇','彙汇','匯汇','艷艳','豔艳','菴庵','塲场','懴忏','懺忏','栢柏','崑昆','啓启','鳯凤','峯峰','鈔钞','裏里','綫线','讚赞','託托','歎叹','脩修','於于','麤粗','蹟迹','跡迹','鑑鉴','鑒鉴','鍾钟','鐘钟','註注','游遊','遊游','敘叙','説说','榖谷','穀谷','衆众','寗宁','甯宁','異异','畧略','録录']:
    VAR[cc.convert(a)]=cc.convert(b)
TR=str.maketrans(VAR)
def fold(s): return cc.convert(s or '').translate(TR)
NUM=r'一二三四五六七八九十百千〇零两兩廿卅\d'
PFX=r'^(新刊|新刻|新鐫|新鍥|重刊|重刻|重訂|欽定|御定|御纂|御製|增補|增訂|校正|精選|新編|新镌|新锲|重订|钦定|增补|增订|新编|绣像|繡像|全像|古本|足本|原本)'
def core(s):
    s=s or ''
    s=re.sub(r'\s*\[[^\]]*\]','',s).strip()
    s=re.sub(r'^(周|秦|漢|晉|宋|齊|梁|陳|隋|唐|五代|遼|金|元|明|清|民國)\s+','',s)
    s=re.sub(r'^[\(（][^\)）]{1,12}[\)）]','',s)
    s=re.sub(r'[\(（\[［【〔].*?[\)）\]］】〕]','',s)
    s=re.sub(r'(存)?['+NUM+r']+卷.*$','',s); s=re.sub(r'(不分卷|卷首|殘卷|附錄|附|首).*$','',s)
    s=re.sub(r'['+NUM+r']+[冊册種种篇回齣折]$','',s)
    s=re.sub(r'[\s・·\.。，,：:／/、;；\-—《》〈〉「」]','',s)
    s=fold(s)
    s2=re.sub(cc.convert(PFX),'',s)
    return s2 if len(s2)>=2 else s
CN={c:i for i,c in enumerate('〇一二三四五六七八九')}
def cnum(s):
    if s.isdigit(): return int(s)
    s=s.replace('兩','二').replace('两','二').replace('零','〇')
    if '百' in s:
        a,b=s.split('百',1); n=(CN.get(a,1) if a else 1)*100
        return n+(cnum(b) if b else 0)
    if '十' in s:
        a,b=s.split('十',1); return (CN.get(a,1) if a else 1)*10+(CN.get(b,0) if b else 0)
    if all(c in CN for c in s): return int(''.join(str(CN[c]) for c in s))
    return None
def juan(s):
    m=re.search('(['+NUM+r']+)卷',s or '')
    return cnum(m.group(1)) if m else None
def load(wid):
    p=R+W[wid]['path']; d=json.load(open(p))
    ib=d.get('indexed_by') or []
    sec=[x.get('section') for x in ib if x.get('section')]
    tis=[x.get('title_info') for x in ib if x.get('title_info')]
    j=d.get('juan_count') or next((juan(t) for t in tis if juan(t)),None)
    au=[(a.get('name'),a.get('dynasty'),a.get('role'),a.get('entity_id')) for a in d.get('authors') or []]
    rel=set()
    for r in d.get('related_works') or []:
        rel.add(r.get('id') or r.get('work_id') if isinstance(r,dict) else r)
    nb=0
    return dict(id=wid,t=d.get('title'),core={core(t) for t in [d.get('title')]+tis+[ (x if isinstance(x,str) else x.get('title')) for x in d.get('additional_titles') or []] if t}-{''},
        ct=core(d.get('title')),au=au,a1=re.sub(r'^(释|僧|釋)','',fold(re.sub(r'[\(（\[［].*?[\)）\]］]','',au[0][0] or ''))) if au and au[0][0] else '',
        e1=au[0][3] if au else None,dyn=d.get('dynasty') or (au[0][1] if au else None),sec=sec,bu=(sec[0].split('/')[0] if sec else '未分类'),
        juan=j,rel=rel,ci=bool(d.get('contained_in')),path=W[wid]['path'],desc=json.dumps(d.get('description') or '',ensure_ascii=False)[:300],tis=tis)
BW=collections.Counter(b['w'] for b in B.values() if not b['merged'])
FZ=re.compile(r'(志|乘|圖經|図経|志略|志稿|志料|紀略|縣誌|府誌|州誌)$')
info={}
for k,g in groups.items():
    for w in g['ws']:
        if w not in info: info[w]=load(w); info[w]['nb']=BW.get(w,0)
pickle.dump((groups,info),open('feat.pkl','wb'))
print('works',len(info))
