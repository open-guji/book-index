"""故宫善本 Book 挂接不一致（A3-20261026，349 条）出卷宗：每条列馆方著录、Book 现况、现挂 Work、匹配 Work 与其余同题候选。
用法：P4WORK=<目录，含 load.py 的 cache.pkl> python3 mkreview_npm.py <挂接不一致.tsv> [批数]"""
import os,sys,csv,json,pickle,collections,re
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)+'/../../../../scripts'))
from importlib import import_module
cen=import_module('dedup-census'); norm=cen.norm
P=os.environ.get('P4WORK','/tmp/p4'); TSV=sys.argv[1]; N=int(sys.argv[2]) if len(sys.argv)>2 else 5
W,B,C=pickle.load(open(P+'/cache.pkl','rb')); print('载入',len(W),len(B)); assert W and B
books_of=collections.defaultdict(list)
for b in B.values():
    if b.get('work_id'): books_of[b['work_id']].append(b)
bytitle=collections.defaultdict(set)
for k,w in W.items(): bytitle[norm(w.get('title') or '')].add(k)
def wb(k,mark=''):
    w=W.get(k)
    if not w: return f"  {mark}{k} （不在／已并）"
    au=';'.join('/'.join(x for x in (a.get('dynasty') or '',a.get('name') or '',a.get('role') or '')) for a in w.get('authors') or [] if isinstance(a,dict))
    ai=' '.join(i.get('author_info') or '' for i in w.get('indexed_by') or [])[:70]
    j=w.get('juan_count'); j=j.get('number') if isinstance(j,dict) else None
    sec=[i.get('section') for i in w.get('indexed_by') or [] if i.get('section')][:1]
    eds=[(x.get('edition') or '')[:24] for x in books_of.get(k,[])][:6]
    cs=' 叢書子目' if '叢書子目' in (w.get('ai_note') or '') else ''
    return f"  {mark}{k} 《{w.get('title')}》 著者[{au}] 总目著者[{ai}] 卷{j} 本{len(books_of.get(k,[]))}{cs} 分类{sec} 版本{eds}"
rows=list(csv.DictReader(open(TSV,encoding='utf-8'),delimiter='\t')); print('行',len(rows))
grp=collections.OrderedDict()
for r in rows: grp.setdefault(r['book_id'],[]).append(r)
out=[]
for bid,rs in grp.items():
    b=B.get(bid)
    L=[f"== {bid} 〔{'；'.join(sorted({r['类别'] for r in rs}))}〕"+(f" 本 Book 对应故宫 {len(rs)} 条记录（合刻／叢書一册）" if len(rs)>1 else '')]
    for r in rs: L.append(f"故宫：{r['holding_id']}「{r['lib_title']}」 {r['lib_author']} ｜ {r['lib_version']} → 匹配 {r['match_work（现 keeper）']}")
    if not b: L.append('  Book 已并或不存在'); out.append(('\n'.join(L),rs)); continue
    cols=[]
    for c in b.get('contained_in') or []:
        cid=c.get('id') if isinstance(c,dict) else c
        if cid in C: cols.append(C[cid].get('title'))
    L.append(f"Book：《{b.get('title')}》 版本「{b.get('edition') or ''}」 收入叢書{cols} ai_note「{(b.get('ai_note') or '')[:120]}」")
    cur=b.get('work_id'); ms=[]
    for r in rs:
        if r['match_work（现 keeper）'] not in ms: ms.append(r['match_work（现 keeper）'])
    L.append(wb(cur,'*现挂 '))
    for m in ms: L.append(wb(m,'+匹配 '))
    others=bytitle.get(norm(b.get('title') or ''),set())
    for r in rs: others=others|bytitle.get(norm(re.sub(r'[一二三四五六七八九十百]+卷.*','',r['lib_title'])),set())
    others=others-{cur}-set(ms)
    for k in sorted(others)[:8]: L.append(wb(k,'  同题 '))
    if len(others)>8: L.append(f'  （另 {len(others)-8} 个同题）')
    out.append(('\n'.join(L),rs))
size=-(-len(out)//N); os.makedirs(P+'/nb',exist_ok=True)
for n in range(N):
    open(f'{P}/nb/n{n}.txt','w').write('\n\n'.join(t for t,_ in out[n*size:(n+1)*size])+'\n')
json.dump([rs for _,rs in out],open(P+'/npm_rows.json','w'),ensure_ascii=False)
print('批',N,'每批',size)
