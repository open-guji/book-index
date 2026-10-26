import json,glob,collections
BI='/home/user/book-index'
P=json.load(open('pairs.json')); B=json.load(open('books.json'))
def W(i): return json.load(open(glob.glob(f'{BI}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0],encoding='utf-8'))
def cut(s,n): s=(s or '').replace('\n',' '); return s if len(s)<=n else s[:n]+'…'
def desc(i):
    w=W(i); L=[f"  id {i}｜题名《{w.get('title')}》"+(f"｜又名 {w.get('alt_titles') or w.get('other_titles')}" if (w.get('alt_titles') or w.get('other_titles')) else '')]
    L.append('  著者：'+('；'.join(f"{a.get('name')}（{a.get('role','')}，{a.get('dynasty','')}，entity={a.get('entity_id','')}）" for a in w.get('authors') or []) or '无'))
    L.append(f"  卷数 {w.get('juan_count')}｜朝代 {w.get('dynasty') or w.get('period') or ''}")
    for x in (w.get('indexed_by') or [])[:6]:
        L.append(f"  著录〔{x.get('source')}〕"+cut(' '.join(str(x.get(k)) for k in ('title','juan','author_info','version','summary') if x.get(k)),260))
    if w.get('description'): L.append('  描述：'+cut(w['description'].get('text') if isinstance(w['description'],dict) else w['description'],200))
    rs=collections.Counter(r.get('id') or r.get('site') for r in w.get('resources') or [])
    if rs: L.append('  资源：'+'，'.join(f'{k}×{v}' for k,v in rs.items()))
    bs=B.get(i,[])
    if bs: L.append(f'  Book {len(bs)} 个：'+'；'.join(cut(f"{b[0]}·{b[1]}",50) for b in bs[:8]))
    if w.get('related_works'): L.append(f"  related_works {len(w['related_works'])}")
    if w.get('ai_note'): L.append('  ai_note：'+cut(w['ai_note'],220))
    return '\n'.join(L)
segs=[[] for _ in range(5)]
for n,(a,b,recs) in enumerate(P,1):
    t=f"### 对 {n:03d}\n台湾国图藏本："+'；'.join(f"{r[0]}《{r[1]}》{r[2]}〔{r[3]}〕" for r in recs[:3])+f"\nWork 甲\n{desc(a)}\nWork 乙\n{desc(b)}\n"
    segs[(n-1)*5//len(P)].append(t)
for k,s in enumerate(segs,1):
    open(f'段{k}.md','w',encoding='utf-8').write('\n'.join(s)); print(k,len(s),sum(map(len,s)))
