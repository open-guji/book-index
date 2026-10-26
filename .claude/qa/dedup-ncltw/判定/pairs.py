import csv,glob,json,os,itertools,collections
BI='/home/user/book-index'
D='/home/user/book-index-manager/docs/馆藏资源挂接/报告/C3续-臺灣國圖存疑與越南漢喃挂接-20261026/'
def wp(i):
    g=glob.glob(f'{BI}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); return g[0] if g else None
cache={}
def W(i):
    if i not in cache:
        p=wp(i); cache[i]=json.load(open(p,encoding='utf-8')) if p else None
    return cache[i]
def res(i):
    seen=set()
    while True:
        w=W(i)
        if not w or not w.get('merged_into') or i in seen: return i
        seen.add(i); i=w['merged_into'] if isinstance(w['merged_into'],str) else w['merged_into'].get('id')
judged=set()
for f in glob.glob(f'{BI}/.claude/qa/dedup-judged/*.tsv'):
    for l in open(f,encoding='utf-8'):
        if l.startswith('#'): continue
        p=l.rstrip('\n').split('\t')
        if len(p)>=2: judged.add(frozenset(p[:2]))
pairs=collections.defaultdict(list)
for fn in ['交去重_疑重复Work.tsv','交去重_同著者多Work.tsv']:
    for r in csv.DictReader(open(D+fn,encoding='utf-8'),delimiter='\t'):
        ids=[res(x) for x in r['候选Work'].split(',')]
        for a,b in itertools.combinations(sorted(set(ids)),2):
            pairs[frozenset((a,b))].append((r['record_id'],r['题名'],r['责任者'],r['原因码']))
st=collections.Counter(); out=[]
for k,recs in pairs.items():
    a,b=sorted(k)
    if k in judged: st['已判']+=1; continue
    wa,wb=W(a),W(b)
    if not wa or not wb: st['缺']+=1; continue
    rel=set(x if isinstance(x,str) else x.get('id') for x in (wa.get('related_works') or [])+(wb.get('related_works') or []))
    if a in rel or b in rel: st['已互链']+=1; continue
    if '叢書子目' in (wa.get('ai_note') or '')+(wb.get('ai_note') or ''): st['子目']+=1; continue
    out.append((a,b,recs)); st['余']+=1
print(len(pairs),st)
json.dump([[a,b,r] for a,b,r in out],open('pairs.json','w'),ensure_ascii=False)
