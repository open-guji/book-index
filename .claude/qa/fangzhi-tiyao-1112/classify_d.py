"""D 类（同题异朝／库内无年号）细分：库内无年号 Work 的版本摘要提及该年号且唯一 → 挂；全是他年号 → 新修次。用法：classify_d.py <classified.json> <out.json>"""
import sys,json,os,collections,re
sys.path.insert(0,'.claude/qa/fangzhi-tiyao-1112')
from classify import key,isfz,split
from norm import REIGN
res=json.load(open(sys.argv[1]))
cnt=collections.Counter(key(r['bookName']) for r in res)
D=[r for r in res if r['cls'].startswith('D')]
# load works with summaries
W={}
idx2=collections.defaultdict(list)
for r,_,fs in os.walk('Work'):
    for f in fs:
        if not f.endswith('.json'):continue
        d=json.load(open(os.path.join(r,f)))
        if d.get('merged_into'):continue
        secs=[(i.get('source'),i.get('section') or '') for i in d.get('indexed_by',[]) if isinstance(i,dict)]
        sm=' '.join((i.get('summary') or '')+(i.get('title_info') or '') for i in d.get('indexed_by',[]) if isinstance(i,dict))
        rg,b=key(d.get('title',''))
        W[d['id']]=(d['title'],d.get('dynasty',''),isfz(secs),sm,rg,os.path.join(r,f))
        idx2[b].append(d['id'])
out=[]
st=collections.Counter()
for x in D:
    rg,b=key(x['bookName'])
    if cnt[(rg,b)]>1: x['d']='D6总目内重名'; st[x['d']]+=1; out.append(x); continue
    cands=[W[i] for i in idx2[b] if W[i][2]]
    cands_all=[(i,W[i]) for i in idx2[b]]
    cf=[(i,W[i]) for i in idx2[b] if W[i][2]]
    if not cf: x['d']='D0同题非方志类'; st[x['d']]+=1; out.append(x); continue
    # any cand mentions reign
    ment=[i for i,w in cf if rg in w[3] or rg==w[4]]
    other_reign_only=all(w[4]!='' and w[4]!=rg for i,w in cf)
    noreign=[i for i,w in cf if w[4]=='']
    if other_reign_only: x['d']='D1新修次'; 
    elif len(ment)==1: x['d']='D2提及年号唯一' if W[ment[0]][4]=='' else 'D2b目标带他年号'; x['target']=ment[0]; x['target_path']=W[ment[0]][5]
    elif len(ment)>1: x['d']='D3提及多个'
    else:
        # no-reign cands never mention reign: do summaries name other reigns?
        namedother=all(any(r_ in w[3] for r_ in REIGN if r_!=rg) for i,w in cf if w[4]=='')
        x['d']='D4无年号且摘要有他年号→新修次' if namedother else 'D5无从判别'
    st[x['d']]+=1; out.append(x)
print(st)
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
