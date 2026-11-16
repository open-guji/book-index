# -*- coding: utf-8 -*-
"""和刻本專項第三輪 wake-b（主題組B：周禮、儀禮、禮記、春秋三傳）：新建日本刊本 Book。
用法：python3 build3.py [--apply]；僅依 CiNii Books 書誌（OpenSearch／NCID JSON，緩存 /tmp/wb3_cache）。"""
import json,os,re,sys
HERE=os.path.dirname(os.path.abspath(__file__));BI=os.path.abspath(os.path.join(HERE,'../../..'))
sys.path.insert(0,os.path.join(BI,'.claude/qa'));import mintid
sys.path.insert(0,HERE)
import b3_cinii as c, ndl
APPLY='--apply' in sys.argv
TODAY='2026-11-16'
CN='https://ci.nii.ac.jp/ncid/'
INV={v:chr(k) for k,v in ndl.M.items()}
EXTRA={'関':'關','広':'廣','国':'國','対':'對','続':'續','両':'兩','属':'屬','総':'總','附属':'附屬','図書館':'圖書館','大学':'大學','経':'經','済':'濟','学':'學','蔵':'藏','覚':'覺','応':'應','万':'萬','党':'黨','団':'團','会':'會','区':'區','県':'縣','医':'醫','薬':'藥','芸':'藝','礼':'禮','辺':'邊','斎':'齋','沢':'澤','気':'氣','竜':'龍','徳':'德','駒':'駒','峰':'峯','歴':'歷','図':'圖','専':'專','門':'門','国立':'國立','東洋文化研究所':'東洋文化研究所','文学部':'文學部','人文社会系研究科':'人文社會系研究科','教育学部':'教育學部','附属図書館':'附屬圖書館'}
def lib(n):
    n=re.sub(r'\s+','',n or '')
    out=''
    for ch in n: out+=EXTRA.get(ch,INV.get(ch,ch))
    return out
def owners(ncids,year):
    res=[];seen=set()
    for n in ncids:
        d=c.ncid(n)
        if not d: continue
        for o in d['owners']:
            k=lib(o['name'])
            if k in seen: continue
            seen.add(k);res.append({'institution':k,'source':'CiNii Books '+CN+n})
    return res
def ext(ncids,year):
    vals=set()
    for n in ncids:
        dd=c.ncid(n)
        if not dd or not dd.get('extent') or re.search(r'存|残|殘',str(dd.get('title'))): continue
        m=re.match(r'^(\d+)冊$',dd['extent'].strip())
        if m: vals.add(int(m.group(1)))
    return [{'number':vals.pop(),'unit':'冊'}] if len(vals)==1 else None
# 條目：work, title, edition, reign, year, certainty, shops, ncids(主NCID在前；歸併者附後), basis, desc, note
E=[]
def add(**k): E.append(k)
exec(open(os.path.join(HERE,'b3_entries.py'),encoding='utf-8').read())
def jd(d): return json.dumps(d,ensure_ascii=False,indent=2)+'\n'
ids=mintid.mint('Book','wake-b',len(E)) if APPLY else ['dry%07d'%i for i in range(len(E))]
LEDGER=[];changed=[]
for e,bid in zip(E,ids):
    ncids=e['ncids']
    prov=owners(ncids,e['year'])
    if not prov:
        print('!! 無館藏',e['title'],e['year']);continue
    d={'schema_version':1,'id':bid,'type':'book','title':e['title'],'work_id':e['work'],'edition':e['edition'],'edition_type':'刻本',
       'dating':{'era':'日本','reign':e['reign'],'year':e['year'],'certainty':e['certainty'],'source':'catalog','basis':e['basis']}}
    pi={'place':'日本'}
    if e.get('pub'): pi['publisher']=e['pub']
    d['publication_info']=pi
    m=ext(ncids,e['year'])
    if m: d['measures']=m
    d['provenance']=prov
    urls=[CN+n for n in ncids]
    d['description']={'text':e['desc'],'sources':['CiNii Books '+u for u in urls]}
    d['sources']=[{'id':'wakeb3-%d'%i,'name':'CiNii Books','type':'url','details':u} for i,u in enumerate(urls)]
    d['ai_note']=('和刻本日本馆藏专项第三輪（2026-11-16，車道 wake-b，主題組B：禮與春秋）：據 CiNii Books 書誌（NCID JSON：刊記／奧付、所藏館）新建；刊年、書肆、館藏據該頁，未核原書。'
                  +('\n'+e['note'] if e.get('note') else ''))
    d['revision']='1.0.0';d['revised_at']=TODAY
    safe=re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]','',e['edition'])[:24]
    path='Book/%s/%s/%s/%s-%s%s.json'%(bid[-3],bid[-2],bid[-1],bid,e['title'],safe)
    changed.append((path,d))
    LEDGER.append((bid,e['title'],'新建',e['edition'],'、'.join(p['institution'] for p in prov),' '.join(urls)))
print(len(changed),'新建')
if APPLY:
    for p,d in changed:
        fp=os.path.join(BI,p);os.makedirs(os.path.dirname(fp),exist_ok=True);open(fp,'w',encoding='utf-8').write(jd(d))
    open(os.path.join(HERE,'ledger3.tsv'),'w',encoding='utf-8').write('Book id\t題名\t判定\tedition\t日本館藏\t依據URL\n'+'\n'.join('\t'.join(r) for r in LEDGER)+'\n')
    open(os.path.join(HERE,'changed_paths3.txt'),'w').write('\n'.join(p for p,_ in changed)+'\n')
