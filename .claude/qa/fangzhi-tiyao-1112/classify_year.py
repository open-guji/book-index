"""B 类（总目内重名／库内多候选）按「年号+年」在库内候选 Work 的版本摘要里找：同地（总目内同键的 sort 全相同）、有年份、恰有一个候选摘要含该「年号X年」→ 挂。
用法：classify_year.py <classified.json> <out.json>；out 里 r['d']='D2提及年号唯一' 以复用 attach.py。"""
import sys,os,json,re,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from classify import key,split,isfz
res=json.load(open(sys.argv[1]))
W={}
for r,_,fs in os.walk('Work'):
    for f in fs:
        if not f.endswith('.json'): continue
        d=json.load(open(os.path.join(r,f)))
        if d.get('merged_into'): continue
        secs=[(i.get('source'),i.get('section') or '') for i in d.get('indexed_by',[]) if isinstance(i,dict)]
        sm=' '.join((i.get('summary') or '')+(i.get('title_info') or '') for i in d.get('indexed_by',[]) if isinstance(i,dict))
        W[d['id']]=(isfz(secs),sm,os.path.join(r,f))
g=collections.defaultdict(list)
for x in res:
    if x['cls'] in('B1总目内重名','B2库内多候选'): g[key(x['bookName'])].append(x)
yre=re.compile(r'^[元二三四五六七八九十廿卅百]+年')
out=[]; st=collections.Counter()
for k,v in g.items():
    one_place=len({x['sort'] for x in v})==1
    for x in v:
        if not one_place: st['异地不处理']+=1; continue
        rg,_=split(x['bookName']); m=yre.match(x['bookName'][len(rg):])
        if not m: st['无年份']+=1; continue
        ys=rg+m.group(0)
        hits=[i for i in x['ids'] if W[i][0] and ys in W[i][1]]
        if len(hits)==1:
            x['d']='D2提及年号唯一'; x['target']=hits[0]; out.append(x); st['挂']+=1
        else: st['命中%d个'%len(hits)]+=1
print(st); json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
