#!/usr/bin/env python3
"""C 档（无同题、无近似≥0.8）新建 Work。用法：new_works.py [--apply] [--limit N] [--root book-index]
读 rows_t.pkl、c1_ks.pkl（由 tier.py／near.py 产出）；id 用 mintid lane l1xuxiu(2015)。"""
import json,pickle,re,sys,argparse,collections,os,time
ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); ap.add_argument('--limit',type=int,default=0)
ap.add_argument('--root',default='/home/user/book-index'); ap.add_argument('--ks',default='c1_ks.pkl'); a=ap.parse_args()
sys.path.insert(0,a.root+'/.claude/qa'); os.chdir(a.root)
import mintid
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from build_idx import norm_t
SRC='續修四庫全書總目提要'; BID='d59f2ogb4bgi'; TODAY='2026-11-12'
rows=pickle.load(open('/home/user/lane/l1/rows_t.pkl','rb')); ks=pickle.load(open('/home/user/lane/l1/'+a.ks,'rb'))
sel=[rows[k] for k in ks if '敦煌' not in rows[k]['name']]
grp=collections.OrderedDict()
for r in sel: grp.setdefault(norm_t(r['main']),[]).append(r)
def entry(r):
    e={'source':SRC,'source_bid':BID,'title_info':r['name'].strip(),'section':r['sort']}
    m=re.match(r'^(\d+)-+(\d+)$',r['page'].strip())
    if m: e['volume']=f'第{int(m.group(1))}冊'; e['page']=str(int(m.group(2)))
    else: e['note']=f'提要頁碼原文：{r["page"]}'
    return e
PER={'清初期':('清','qing'),'清中期':('清','qing'),'清後期':('清','qing'),'民國':('民國','modern'),'明':('明','ming')}
groups=list(grp.values())
if a.limit: groups=groups[:a.limit]
ids=mintid.mint('Work','l1xuxiu',len(groups))
out=[]
for gid,rs in zip(ids,groups):
    r=rs[0]; title=r['main'].strip()
    d={'schema_version':1,'id':gid,'type':'work','title':title}
    ms=re.search(r'(不分卷|[零〇一二三四五六七八九十百千萬兩]+卷)',r['name'])
    if r['juan'] is not None:
        d['measures']=[{'number':r['juan'],'unit':'卷'}]
        d['measure_info']=ms.group(1) if ms else ''
        if not d['measure_info']: del d['measure_info']
    sec=r['sort'].split('/')
    if len(sec)>=3 and sec[1]=='別集類':
        k=sec[2].replace('之屬','')
        if k in PER:
            dyn,per=PER[k]; d['dynasty']=dyn; d['dynasty_basis']=f'catalog_section：續修四庫全書總目提要類目「{r["sort"]}」'
            d['period']=per; d['period_basis']=f'據續修四庫全書總目提要類目「{r["sort"]}」'
    d['indexed_by']=[entry(x) for x in rs]
    d['ai_note']=f'{TODAY} L1：據《續修四庫全書總目提要》著錄新建（全庫無同題 Work，近似題名相似度＜0.8）；源目錄未著撰人，責任者待補。同題而異書者將來可拆，同書而異題者將來可並。'
    d['revision']='1.0.0'; d['revised_at']=TODAY
    p=mintid.path_for(gid,title,'Work')
    out.append((p,d))
    if a.apply:
        os.makedirs(os.path.dirname(p),exist_ok=True)
        open(p,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('new works',len(out),'from rows',sum(len(g) for g in groups))
