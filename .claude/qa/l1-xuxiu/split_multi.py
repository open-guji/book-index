#!/usr/bin/env python3
"""拆开 L1 车道新建 Work 中挂了「卷数不同」多则续修四库提要的：每个不同 title_info 另立 Work（首组留原条）。--apply 写盘。"""
import json,glob,os,sys,re,collections,copy
sys.path.insert(0,'.claude/qa'); import mintid
ap=sys.argv
apply='--apply' in ap
SRC='續修四庫全書總目提要'; TODAY='2026-11-12'
cands=[]
for p in glob.iglob('Work/*/*/*/d59gc4i*.json'):   # 本车道 lane 2015 的 id 段
    d=json.load(open(p))
    if d.get('merged_into'): continue
    if 'L1：據《續修四庫全書總目提要》著錄新建' not in (d.get('ai_note') or ''): continue
    ib=[e for e in d.get('indexed_by',[]) if e.get('source')==SRC]
    ti=collections.OrderedDict()
    for e in ib: ti.setdefault(e['title_info'].strip(),[]).append(e)
    if len(ti)>1: cands.append((p,d,ti))
print('待拆',len(cands),'组→新增',sum(len(t)-1 for _,_,t in cands))
ids=mintid.mint('Work','l1xuxiu',sum(len(t)-1 for _,_,t in cands)) if cands else []
it=iter(ids)
def measure(ti):
    m=re.search(r'(不分卷|[零〇一二三四五六七八九十百千萬兩]+卷)',ti); return m.group(1) if m else None
NUM={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
def juan(ti):
    m=measure(ti)
    if not m: return None
    if m=='不分卷': return 0
    s=m[:-1].replace('兩','二'); v=0;cur=0
    if '百' in s or '千' in s or '萬' in s: return None
    for c in s:
        if c=='十': v+=(cur or 1)*10; cur=0
        else: cur=NUM.get(c,0)
    return v+cur
n=0
for p,d,ti in cands:
    keys=list(ti)
    keep=keys[0]
    others=[e for e in d['indexed_by'] if e.get('source')!=SRC]
    d['indexed_by']=others+ti[keep]
    j=juan(keep)
    if j is not None: d['measures']=[{'number':j,'unit':'卷'}]; 
    if measure(keep): d['measure_info']=measure(keep)
    d['ai_note']+=f'\n\n{TODAY} L1：原條曾並掛卷數不同的另 {len(keys)-1} 則提要（{"、".join(keys[1:])}），按同題而卷數不同視為異書，已拆出另立（L0 提示）。'
    v=d['revision'].split('.'); d['revision']=f'{v[0]}.{int(v[1])+1}.0'; d['revised_at']=TODAY
    newrecs=[]
    for k in keys[1:]:
        gid=next(it)
        nd={'schema_version':1,'id':gid,'type':'work','title':d['title'],'indexed_by':ti[k]}
        jj=juan(k)
        if jj is not None: nd['measures']=[{'number':jj,'unit':'卷'}]
        if measure(k): nd['measure_info']=measure(k)
        nd['ai_note']=f'{TODAY} L1：自 {d["id"]}《{d["title"]}》拆出（同題而卷數不同的續修四庫提要著錄）；源目錄未著撰人，責任者待補。將來可核是否同書。'
        nd['revision']='1.0.0'; nd['revised_at']=TODAY
        newrecs.append((mintid.path_for(gid,d['title'],'Work'),nd))
    if apply:
        open(p,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
        for np_,nd in newrecs:
            os.makedirs(os.path.dirname(np_),exist_ok=True)
            open(np_,'w',encoding='utf-8').write(json.dumps(nd,ensure_ascii=False,indent=2)+'\n')
    n+=len(newrecs)
print('新建',n)
