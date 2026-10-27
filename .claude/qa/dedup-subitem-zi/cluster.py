"""由 pairs_zi.tsv 的 A／B 边连簇；簇内若有 C／D 对则整簇降为待核。输出 clusters.json 与统计。"""
import csv, json, os, collections
S=os.environ.get('OUT','/tmp/zi')
R=list(csv.DictReader(open(S+'/pairs_zi.tsv'),delimiter='\t'))
lv={frozenset((r['a'],r['b'])):r for r in R}
par={}
def f(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
for r in R:
    f(r['a']); f(r['b'])
    if r['lv'] in ('A','B'): par[f(r['a'])]=f(r['b'])
comp=collections.defaultdict(set)
for x in list(par): comp[f(x)].add(x)
out=[]; st=collections.Counter()
for ms in comp.values():
    if len(ms)<2: continue
    bad=[lv[frozenset((x,y))] for x in ms for y in ms if x<y and frozenset((x,y)) in lv and lv[frozenset((x,y))]['lv'] in ('C','D','YI') and not lv[frozenset((x,y))]['why'].startswith(('缺撰人、同题','泛称题名'))]
    key=next(r['key'] for r in R if r['a'] in ms)
    levels=sorted({lv[frozenset((x,y))]['lv'] for x in ms for y in ms if x<y and frozenset((x,y)) in lv})
    out.append(dict(key=key,ids=sorted(ms),conflict=[(r['a'],r['b'],r['lv'],r['why']) for r in bad],levels=levels))
    st['冲突簇' if bad else '净簇']+=1
    st['冲突簇条' if bad else '净簇条']+=len(ms)
json.dump(out,open(S+'/clusters.json','w'),ensure_ascii=False,indent=1)
print(st)
