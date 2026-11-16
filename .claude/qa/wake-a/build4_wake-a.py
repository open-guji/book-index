#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-a 第四輪：明治期(1868-1911)刊本·經部（孟子/大學/中庸/論語/四書集註/春秋左氏傳校本）。用法：build4_wake-a.py [--apply]"""
import json,os,re,sys,subprocess,collections
sys.path.insert(0,'/tmp/wa4')
from sel_a4 import *
APPLY='--apply' in sys.argv
BI='/tmp/wk-a4'
sys.path.insert(0,BI+'/.claude/qa'); import mintid
TODAY='2026-11-16'
CI='https://ci.nii.ac.jp/ncid/'
SHIN=str.maketrans({'学':'學','図':'圖','総':'總','属':'屬','医':'醫','経':'經','国':'國','関':'關','広':'廣','会':'會','蔵':'藏','芸':'藝','体':'體','実':'實','号':'號','当':'當','与':'與','台':'臺','画':'畫','歴':'歷','続':'續','観':'觀','・':'·','両':'兩','竜':'龍'})
def inst(n):
    n=n.replace('大学共同利用機関法人 人間文化研究機構 ','').replace('大学共同利用機関法人 ','')
    return re.sub(r'\s+','',n).translate(SHIN)
KN='〇一二三四五六七八九'
def kan(n):
    if n==1: return '元'
    s=''
    if n>=10:
        s+=('' if n//10==1 else KN[n//10])+'十'
    return s+(KN[n%10] if n%10 else '')
RISK=re.compile(r'購版|購板|後印|求版|求板|補刻|後修|再刻|三刻|四刻|再版|後刷|覆刻|重刻|改刻|修訂')
FAMT={'孟子':'孟子','大學':'大學','中庸':'中庸','論語':'論語','四書集註':'四書集註','春秋左氏傳校本':'春秋左氏傳校本'}
def leaf(i): return 'Book/%s/%s/%s'%(i[-3],i[-2],i[-1])
def jd(d): return json.dumps(d,ensure_ascii=False,indent=2)+'\n'
def pubnice(m):
    # 以擁館最多之記錄的出版者字串
    best=max(m,key=lambda it:int(it[3]['own'] or 0))[3]
    out=[]
    for p in best['pub'] or []:
        for t in re.split(r'[:：]|\[ほか\]|ほか\d*書肆?',p):
            t=re.sub(r'[\[\]\(\)（）\s]|發兌|發賣|發行|発売|発兌|賣弘|出板|專賣|専賣|等$','',t)
            if t and '不明' not in t and '製本' not in t and t not in out: out.append(t)
    return [x.translate(SHIN) for x in out]
def kunten(m):
    c=' '.join(it[3]['cre'] or '' for it in m)
    if '後藤' in c: return '後藤點'
    if '秦鼎' in c: return '秦鼎校'
    if '松岡' in c: return '松岡彦二校正訓點'
    return ''
sel=[];todo=[]
for t,y,m in sorted(groups(),key=lambda x:(x[0],x[1])):
    tk=sorted({s for it in m for s in it[4]})
    h=libhits(W[t],y,tk)
    st='NEW' if not h else ('DUP' if any(x[2] for x in h) else ('AMBIG' if not all(x[3] for x in h) else 'NEW'))
    notes=' '.join(' '.join(it[3]['note'] or [])+' '+it[3]['title'] for it in m)
    ncs=[it[2] for it in m]
    anyd=[b for b in LIB if t in (b['t'] or '') and b['w']!=W[t] and (b['y']==y or re.search('明治'+kan(y-1867)+'年|明治'+str(y-1867)+'年',b['ed'] or '')) and any(k.replace('衛','衞') in nz((b['ed'] or '')+(b['pub'] or '')+b['note']).replace('衛','衞') for k in tk)]
    if st=='NEW' and anyd: st='XDUP'; h=[(b['id'],) for b in anyd]
    if re.search(r'鼇頭|頭書|首書|標註|何氏校本|[;；]|\.',' '.join(it[3]['title'] for it in m)) and st=='NEW': st='EXCL'; h=[('標註類或合刊',)]
    if t in ('孟子','論語') and any('宝文閣' in x for x in tk) and st=='NEW': st='EXCL'; h=[('宝文閣四書集註之零冊',)]
    if st=='NEW' and all(p.strip().startswith('[') for it in m for p in (it[3]['pub'] or [])): st='BRKPUB'; h=[('出版者為方括號推定',)]
    if st!='NEW': todo.append((t,y,st,ncs,('庫內已有／排除：'+','.join(x[0] for x in h))));continue
    if RISK.search(notes) : todo.append((t,y,'RISK',ncs,'註記含後印／再刻等，印次不明'));continue
    if not tk or all(x.endswith('藩') for x in tk): todo.append((t,y,'NOPUB',ncs,'出版者不明或僅藩藏版'));continue
    sel.append((t,y,m,tk))
print('選',len(sel),'待',len(todo))
for x in todo: print('TODO',x)
nid=mintid.mint('Book','wake-a',len(sel)) if APPLY else ['dryb%06d'%i for i in range(len(sel))]
files={};ledger=[]
for (t,y,m,tk),bid in zip(sel,nid):
    its=[(it[2],it[3]) for it in m]
    rep=max(its,key=lambda x:int(x[1]['own'] or 0))[1]
    pubs=pubnice(m); kt=kunten(m)
    ed='日本明治%s年%s%s%s本'%(kan(y-1867),'、'.join(pubs[:3]),'等' if len(pubs)>3 else '','刊'+kt if kt else '刊')
    ed=ed.replace('刊刊','刊')
    prov=[];srcs=[]
    for n,v in its:
        for o in v['owners']:
            prov.append({'institution':inst(o[0]),'notes':'CiNii Books所藏館「%s」；%s；%s'%(o[0],v['title'],' : '.join(v['pub'] or [])+('；'+v['ext'] if v['ext'] else '')),'source':'CiNii Books '+CI+n})
            ledger.append((bid,t,'新建',inst(o[0]),CI+n))
        srcs.append({'id':'cinii-'+n,'name':'CiNii Books','type':'url','details':CI+n})
    alts=[]
    for n,v in its:
        for a in (v['alt'] or [])+[v['title']]:
            a=re.sub(r'\s*\d+[巻卷].*$','',a).strip()
            if a and a!=t and a not in alts and len(a)<20: alts.append(a)
    notes=' '.join(' '.join(v['note'] or []) for n,v in its)
    et='刻本' if '木版' in notes else ('鉛印本' if '活版' in notes else None)
    pds=sorted({str(x) for n,v in its for x in (v['pd'] or []) if x})
    basis='CiNii Books%s著錄：刊年%d（%s）；出版者%s'%('多館獨立' if len(its)>1 else '',y,'／'.join(pds)[:50],'・'.join(pubs)[:80])
    d={'schema_version':1,'id':bid,'type':'book','title':t,'work_id':W[t],'edition':ed}
    if et: d['edition_type']=et
    d['dating']={'era':'日本','reign':'明治','year':y,'certainty':'attested','source':'catalog','basis':basis}
    if alts[:4]: d['additional_titles']=alts[:4]
    ex=rep['ext'] or ''
    mm=re.fullmatch(r'(\d+)冊',ex.strip())
    if mm: d['measures']=[{'number':int(mm.group(1)),'unit':'冊'}]
    d['provenance']=prov
    cre=re.sub(r'\s+','',re.sub(r'[\[\]]','',rep['cre'] or '')).translate(SHIN)
    d['description']={'text':'%s《%s》，%s。'%(cre,t,ed[2:]),'sources':['CiNii Books '+CI+n for n,v in its[:3]]}
    d['sources']=srcs
    d['ai_note']='和刻本日本館藏專項第四輪（wake-a，2026-11-16）：明治期刊本，據CiNii Books書目新建（NCID %s）；刊年／書肆／冊數錄自書目，未核原書；庫內同Work同年已逐條查重，無同肆者。'%'、'.join(n for n,v in its)
    d['revision']='1.0.0';d['revised_at']=TODAY
    safe=re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]','',ed)[:24]
    files['%s/%s-%s%s.json'%(leaf(bid),bid,t,safe)]=d
print('新建',len(files))
for (t,y,m,tk),bid in zip(sel,nid): print(bid,t,y,len(m),'|'.join(tk)[:60])
if not APPLY: sys.exit(0)
subprocess.check_call(['git','sparse-checkout','add']+sorted({'/'+leaf(i)+'/' for i in nid}),cwd=BI)
Q=BI+'/.claude/qa/wake-a'
for p,d in files.items():
    os.makedirs(os.path.join(BI,os.path.dirname(p)),exist_ok=True)
    open(os.path.join(BI,p),'w',encoding='utf-8').write(jd(d))
open(Q+'/applied_paths4.txt','w').write('\n'.join(files)+'\n')
with open(Q+'/ledger4.tsv','w',encoding='utf-8') as f:
    f.write('Book id\t題名\t判定\t日本館藏\t依據URL\n')
    for r in ledger: f.write('\t'.join(r)+'\n')
with open(Q+'/TODO4.tsv','w',encoding='utf-8') as f:
    f.write('題名\t刊年\t判定\tNCID\t原因\n')
    for t,y,st,ncs,why in todo: f.write('%s\t%d\t%s\t%s\t%s\n'%(t,y,st,','.join(ncs),why))
print('已寫')
