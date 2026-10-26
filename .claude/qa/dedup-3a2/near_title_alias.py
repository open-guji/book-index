import os
import sys, re, collections, importlib.util, json
ROOT=os.environ.get('BOOK_INDEX','../book-index')
sys.path.insert(0, ROOT+'/.claude/qa')
spec=importlib.util.spec_from_file_location('dc', ROOT+'/scripts/dedup-census.py'); dc=importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)
import backrefs, glob, os
W={}
for t,p,d in backrefs.iter_records(ROOT):
    if t=='Work' and not d.get('merged_into') and '敦煌遺書' not in (d.get('ai_note') or ''): W[d['id']]=d
# bulei
bul=dc.bulei_of_nodes(ROOT); mem=collections.defaultdict(set)
for p in glob.glob(ROOT+'/classification/zongmu/members/*.json'):
    for row in dc.load_json(p).get('members') or []:
        if row: mem[row[0]].add(bul.get(os.path.basename(p)[:-5]))
def bl(w): return next((b for b in dc.BULEI if b in mem.get(w,())),'未分类')
PRE=re.compile(r'^(新刊|新刻|新鐫|重刊|重刻|重訂|重校|重修|增補|增訂|增廣|校正|校刻|新校|新編|新鍥|御製|御纂|欽定|精刻|評點|批點|詳註|詳注|箋註|音註|京本|監本|古本)+')
SUF=re.compile(r'(全集|文集|詩集|集|稿|全書|彙編|合刻|合編|選|鈔|抄|錄)$')
def core(t): 
    t=PRE.sub('',t); return t
byauth=collections.defaultdict(list)
for w,d in W.items():
    a=[x for x in d.get('authors') or [] if isinstance(x,dict)][:1]
    if not a: continue
    n=dc.norm_name(a[0].get('name'))
    if n in dc.ANONYMOUS: continue
    k=a[0].get('entity_id') or ('n:'+n)
    byauth[k].append((w,dc.norm(d.get('title'))))
C=collections.Counter(); pairs=[]
for k,ws in byauth.items():
    if len(ws)<2 or len(ws)>400: continue
    for i in range(len(ws)):
        for j in range(i+1,len(ws)):
            (w1,t1),(w2,t2)=ws[i],ws[j]
            if not t1 or not t2 or t1==t2: continue
            kind=None
            if core(t1)==core(t2): kind='前缀'
            elif SUF.sub('',core(t1))==SUF.sub('',core(t2)) and len(SUF.sub('',core(t1)))>=2: kind='后缀'
            elif len(t1)>=4 and len(t1)==len(t2) and sum(a!=b for a,b in zip(t1,t2))==1: kind='差一字'
            if kind:
                b=min(bl(w1),bl(w2),key=lambda x:(dc.BULEI+('未分类',)).index(x))
                C[kind]+=1; C[b+'·'+kind]+=1; pairs.append((b,kind,w1,t1,w2,t2,k))
for k,v in sorted(C.items()): print(k,v)
open(sys.argv[1],'w').write('\n'.join('\t'.join(p) for p in pairs))
# 一名又名
R=re.compile(r'(一名|又名|一作|亦名|即|蓋即|原名|又題|一題)[《「]?([^，。；、《》「」（）\s]{2,20})')
title_idx=collections.defaultdict(set)
for w,d in W.items(): title_idx[dc.norm(d.get('title'))].add(w)
hit=collections.Counter(); hp=[]
for w,d in W.items():
    txt=' '.join((ib.get('summary') or '')+' '+(ib.get('title_info') or '') for ib in d.get('indexed_by') or [] if isinstance(ib,dict))
    for m in R.finditer(txt):
        t=dc.norm(re.sub(r'[一二三四五六七八九十百千]+卷.*$','',m.group(2)))
        for w2 in title_idx.get(t,()):
            if w2!=w:
                hit[bl(w)]+=1; hp.append((bl(w),w,dc.norm(d.get('title')),m.group(1),t,w2))
print('别名命中对',sum(hit.values()),dict(hit))
open(sys.argv[2],'w').write('\n'.join('\t'.join(p) for p in hp))
