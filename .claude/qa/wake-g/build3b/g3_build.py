#!/usr/bin/env python3
import sys,re,json,os,collections
sys.path.insert(0,'/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3')
from g3_nc import info
from g3_cl import nz
from g3_plan import REIGN,jpby,book_years
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/'
OWN=str.maketrans('国学図総属蔵駒沢関広経済芸医薬団斎礼会読点遠辺竜条桜渓両県覧鉄','國學圖總屬藏駒澤關廣經濟藝醫藥團齋禮會讀點遠邊龍條櫻溪兩縣覽鐵')
RT=str.maketrans('寛宝禄応暦徳万','寬寶祿應曆德萬')
def inst(o): return re.sub(r'[\s　]+','',o).translate(OWN)
KJ='〇一二三四五六七八九'
def kanji(n):
    if n==1: return '元'
    if n<10: return KJ[n]
    s=('' if n//10==1 else KJ[n//10])+'十'
    return s+(KJ[n%10] if n%10 else '')
def parse_date(pd):
    for p in pd:
        m=re.match(r'^\s*(%s)\s*(\d+|元)\s*(?:\(|\[|\.|年|\s|$)'%'|'.join(REIGN),p)
        y=re.search(r'[\[\(](\d{4})[\]\)\.]',p)
        if m and y and not re.search(r'推|頃',p):
            nn=1 if m.group(2)=='元' else int(m.group(2))
            if abs(REIGN[m.group(1)]+nn-1-int(y.group(1)))>1: continue
            return m.group(1).translate(RT),(1 if m.group(2)=='元' else int(m.group(2))),int(y.group(1)),p
    return None
def clean_title(t):
    t=re.split(r'[,，:：]',t)[0]
    t=re.sub(r'\s*\(存.*$','',t)
    t=re.sub(r'\s*[0-9０-９]+[卷巻冊].*$','',t)
    t=re.sub(r'[\s　]+','',t)
    return nz(t).translate(str.maketrans('寳真','寶眞'))
GEN=re.compile(r'^(.{0,3}書林|.{0,3}書肆|.{0,3}書坊|銅駝坊|.{1,3}[華花]書林)$')
def split_pub(p):
    out=[]
    for x in re.split(r'[:：;；,，、]|ほか',p):
        x=x.strip().strip('[]').strip()
        if x and '不明' not in x and '書写' not in x and not GEN.match(x): out.append(x)
    return out
def build_one(work,o,titleov=None):
    recs=[i for i in (info(nc) for nc in o['ncids']) if i]
    if not recs: return None,['no recs']
    ds=[parse_date(r['pd']) for r in recs]; ok=[d for d in ds if d]
    if not ok: return None,['無明確年號紀年']
    if len({d[2] for d in ok})>1: return None,['年不一']
    reign,nth,y,pdtxt=ok[0]
    if o.get('y') and o['y']!=y: return None,['書誌頁年與檢索列表年不一 %s/%s'%(o['y'],y)]
    pc=collections.Counter(); first=[]
    for r in recs:
        ps=[x for p in r['pub'] for x in split_pub(p)]
        if not first and ps: first=ps
        for x in ps: pc[x]+=1
    if not pc: return None,['無出版者']
    probs=[]
    if any(re.search(r'推定|刊年不明',' '.join(r['notes'])) for r in recs): probs.append('notes推定')
    if recs[0]['pub'] and '[' in recs[0]['pub'][0]: return None,['出版者為編目推補']
    pubs_show=[nz(x).translate(str.maketrans('荘','莊')) for x in first[:3]]
    ed='日本%s%s年%s刊本'%(reign,kanji(nth),'、'.join(pubs_show))
    colo=[n for r in recs for n in r['notes'] if re.search(r'刊記|奥付|奧付|見返|牌記',n)]
    kath=any(re.search(r'活字',' '.join(r['notes'])) for r in recs)
    title=titleov or clean_title(recs[0]['title'])
    return dict(work=work,title=title,reign=reign,nth=nth,year=y,pubs_show=pubs_show,allpubs=sorted(pc),ed=ed,colo=colo[:2],kath=kath,recs=recs,creator=recs[0]['creator'],ext=collections.Counter(r['extent'] for r in recs),probs=probs,pdtxt=pdtxt),probs
def dupcheck(b):
    return [x['id']+':'+x['edition'][:20] for x in jpby.get(b['work'],[]) if b['year'] in book_years(x)]
def book_json(b,bid,lane,round_note):
    d={'schema_version':1,'id':bid,'type':'book','title':b['title'],'work_id':b['work'],'edition':b['ed']}
    if b['reign']=='明治':
        if any(re.search(r'活版|活字',' '.join(r['notes'])) for r in b['recs']): d['edition_type']='活字本'
        elif any(re.search(r'木版|整版',' '.join(r['notes'])) for r in b['recs']): d['edition_type']='刻本'
    else: d['edition_type']='活字本' if b['kath'] else '刻本'
    d['dating']={'era':'日本','reign':b['reign'],'year':b['year'],'certainty':'attested','source':'catalog','basis':'CiNii Books 書誌著錄「%s」%s'%(b['pdtxt'].strip(),('；'+b['colo'][0][:60]) if b['colo'] else '')}
    pi={'place':'日本','publisher':'、'.join(b['pubs_show'])}
    d['publication_info']=pi
    if len(b['ext'])==1:
        m=re.match(r'^(\d+)(冊|巻|卷)$',list(b['ext'])[0])
        if m: d['measures']=[{'number':int(m.group(1)),'unit':'冊' if m.group(2)=='冊' else '卷'}]
    prov={}
    for r in b['recs']:
        for o in r['owners']:
            k=inst(o)
            prov.setdefault(k,[]).append(r['ncid'])
    provs=[]; urls=[]
    for k,ns in prov.items():
        src=' '.join('CiNii Books https://ci.nii.ac.jp/ncid/%s'%n for n in ns[:3])
        provs.append({'institution':k,'source':src})
        for n in ns[:3]:
            u='https://ci.nii.ac.jp/ncid/%s'%n
            if u not in urls: urls.append(u)
    for r in b['recs']:
        u='https://ci.nii.ac.jp/ncid/%s'%r['ncid']
        if u not in urls and len(urls)<12: urls.append(u)
    d['provenance']=provs
    d['description']={'text':'%s（%s）；刊者據 CiNii Books 書誌著錄。'%(b['creator'][:120],b['ed']),'sources':sorted(urls)}
    d['sources']=[{'id':'wake%s3-%d'%(lane,i),'name':'CiNii Books','type':'url','details':u} for i,u in enumerate(sorted(urls))]
    others=[p for p in b['allpubs'] if p not in b['pubs_show']]
    note='和刻本日本馆藏专项第三輪（2026-11-16，車道 wake-%s，通名大 Work 穷尽）：據 CiNii Books 書誌新建（刊年、刊者、館藏據書誌頁；未核原書）。本庫該 Work 原無此刊年之日本刊本；與庫內其他版本不硬並，同年他書肆之本另立。'%lane
    note+='\n依據 NCID：'+'、'.join(r['ncid'] for r in b['recs'][:12])+('等%d條' % len(b['recs']) if len(b['recs'])>12 else '')
    if round_note: note+='\n'+round_note
    if b['colo']: note+='\n書誌記：'+b['colo'][0][:100]
    if others: note+='\n書誌所列其他書肆：'+'、'.join(others[:8])+'（或為同版之合刻／後印書肆，未判）'
    d['ai_note']=note
    d['revision']='1.0.0'; d['revised_at']='2026-11-16'
    return d
