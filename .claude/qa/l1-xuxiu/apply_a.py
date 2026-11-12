#!/usr/bin/env python3
"""A 档：给唯一同题的 Work 追加 indexed_by（source=續修四庫全書總目提要）。
用法：apply_a.py [--apply] [--limit N]   （--root 默认 /home/user/book-index；rows_t.pkl 由 tier.py 产出）"""
import json,pickle,re,sys,argparse,glob,os,collections
ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); ap.add_argument('--limit',type=int,default=0)
ap.add_argument('--root',default='/home/user/book-index'); ap.add_argument('--tiers',default='A'); a=ap.parse_args()
SRC='續修四庫全書總目提要'; BID='d59f2ogb4bgi'; TODAY='2026-11-12'
import os
rows=pickle.load(open(os.environ.get('ROWS','rows_t.pkl'),'rb'))
paths={}
for p in glob.iglob(a.root+'/Work/*/*/*/*.json'):
    paths[os.path.basename(p).split('-')[0]]=p
by=collections.defaultdict(list)
for r in rows:
    if r['tier'] in a.tiers.split(','): by[r.get('pick') or r['cands'][0]].append(r)
def entry(r):
    e={'source':SRC,'source_bid':BID,'title_info':r['name'].strip(),'section':r['sort']}
    m=re.match(r'^(\d+)-+(\d+)$',r['page'].strip())
    if m: e['volume']=f'第{int(m.group(1))}冊'; e['page']=str(int(m.group(2)))
    else: e['note']=f'提要頁碼原文：{r["page"]}'
    return e
n=0; skipped=collections.Counter(); multi=0
for wid,rs in sorted(by.items()):
    p=paths.get(wid)
    if not p: skipped['no-path']+=1; continue
    s=open(p,encoding='utf-8').read(); d=json.loads(s)
    if json.dumps(d,ensure_ascii=False,indent=2)+'\n'!=s: skipped['not-roundtrip']+=1; continue
    if d.get('merged_into'): skipped['tomb']+=1; continue
    ib=d.setdefault('indexed_by',[])
    if any(e.get('source')==SRC for e in ib): skipped['already']+=1; continue
    for r in rs: ib.append(entry(r))
    if len(rs)>1: multi+=1
    HOW={'A':'題名唯一同題','A2':'同題多候選中朝代、卷數、部類唯一相合','A3':'題名唯一同題且別集類年代類目與 Work 時代相合','A4':'題名為「撰人名＋已有題名」'}
    how='；'.join(sorted({HOW[x['tier']] for x in rs}))
    note=f'{TODAY} L1：據《續修四庫全書總目提要》（東方文化事業總委員會稿本）{how}，補 indexed_by（匹配檔 {rs[0]["tier"]}；書名未帶作者，以朝代、卷數、部類複核）。'
    d['ai_note']=(d['ai_note']+'\n\n'+note) if d.get('ai_note') else note
    v=d.get('revision','1.0.0').split('.'); d['revision']=f'{v[0]}.{int(v[1])+1}.0'; d['revised_at']=TODAY
    n+=1
    if a.apply: open(p,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    if a.limit and n>=a.limit: break
print('works',n,'multi',multi,dict(skipped))
