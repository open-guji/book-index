import json,collections,glob,re
G=json.load(open('/tmp/claude-0/s/g5b.json'))
def ld(i): return json.load(open(glob.glob(f'Book/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0],encoding='utf-8'))
def jc(j):
    x=j.get('juan_count'); return (x or {}).get('number') if isinstance(x,dict) else x
def nt(t): return re.sub(r'^\[.*?\]|[\s（）()]','',t or '')
res=collections.Counter(); keep=[]; reg=[]
for g in G:
    if g['cls']!='dated': continue
    js=[ld(i) for i in g['ids']]
    why=None
    if any('分立依據' in (j.get('ai_note') or '') for j in js): why='分立依據'
    elif len({jc(j) for j in js if jc(j) is not None})>1: why='卷數不同'
    elif len({(j.get('measure_info') or '') for j in js if j.get('measure_info')})>1: why='measure_info不同'
    elif len({j.get('edition_type') for j in js if j.get('edition_type')})>1: why='版本類型不同'
    elif len({nt(j.get('title')) for j in js})>1: why='題名不同'
    elif len({json.dumps(j.get('authors'),sort_keys=True,ensure_ascii=False) for j in js if j.get('authors')})>1: why='責任者不同'
    elif any(j.get('physical_description') for j in js) and len({json.dumps(j.get('physical_description'),sort_keys=True,ensure_ascii=False) for j in js if j.get('physical_description')})>1: why='物理描述不同'
    res[why or '候選']+=1
    (reg if why else keep).append({**g,'why':why,'n':len(js)})
print(res, 'books in candidates',sum(g['n'] for g in keep))
json.dump({'keep':keep,'reg':reg},open('/tmp/claude-0/s/tier5b.json','w'),ensure_ascii=False)
