#!/usr/bin/env python3
"""方志-并：由 fangzhi_judge.py 的 判定-全部对.tsv 出 A／B 并簇与逐簇核对卷宗。

    BOOK_INDEX=. python3 .claude/qa/dedup-fangzhi/bing/clusters.py <fangzhi 输出目录> <卷宗目录>

簇＝同题组内 A、B 边的连通块。簇内任一对另判 C／E（异修次、续修）或 D 的，整簇标「簇内冲突」，
不进并批，交人工（多为无年号的故宫／史志条同时连上两个修次）。
keeper：总目 [年号] 条优先（有 indexed_by 中國古籍總目且题名带 [年号]），再总目条，再 indexed_by 多者。
卷宗：每簇一段，列各条 Work 的关键字段与所挂 Book，供子 agent 逐簇核同修次、同名异地。只读。
"""
import collections, glob, json, os, sys
bi = os.environ.get('BOOK_INDEX', '.')
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
rows = [l.rstrip('\n').split('\t') for l in open(os.path.join(src, '判定-全部对.tsv'), encoding='utf-8')][1:]
print('载入对 %d' % len(rows))
if not rows: sys.exit('载入为 0，停')
par = {}
def f(x):
    par.setdefault(x, x)
    while par[x] != x: x = par[x]
    return x
lab = {}
for g, a, b, l, *_ in rows:
    lab[frozenset((a, b))] = l
    if l[0] in 'AB': par[f(a)] = f(b)
cl = collections.defaultdict(set); grp = {}
for g, a, b, l, *_ in rows:
    if l[0] in 'AB':
        cl[f(a)].update((a, b)); grp[f(a)] = g
def path(i): return glob.glob(os.path.join(bi, f"Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json"))[0]
books = collections.defaultdict(list)
for fn in glob.glob(os.path.join(bi, 'index/books/*.json')):
    for k, v in json.load(open(fn, encoding='utf-8')).items():
        if v.get('work_id'): books[v['work_id']].append(dict(v, id=k))
def kscore(d):
    src = [x.get('source') for x in d.get('indexed_by') or []]
    return ('中國古籍總目' in src and d['title'].startswith('['), '中國古籍總目' in src, len(src), len(books.get(d['id'], [])))
out_cl = []
for r, ms in sorted(cl.items(), key=lambda x: (grp[x[0]], sorted(x[1]))):
    ms = sorted(ms); docs = {i: json.load(open(path(i), encoding='utf-8')) for i in ms}
    labs = {}
    conflict = []
    for i in ms:
        for j in ms:
            if i < j:
                l = lab.get(frozenset((i, j)), '?'); labs[i + '|' + j] = l
                if l[0] not in 'AB': conflict.append((i, j, l))
    keeper = max(ms, key=lambda i: kscore(docs[i]))
    out_cl.append(dict(cid='FZ%04d' % (len(out_cl) + 1), group=grp[r], members=ms, keeper=keeper,
                       losers=[i for i in ms if i != keeper], pairs=labs, conflict=conflict))
json.dump(out_cl, open(os.path.join(out, 'clusters.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def slim(d):
    keep = {k: d.get(k) for k in ('id', 'title', 'dynasty', 'authors', 'juan_count', 'measure_info') if d.get(k)}
    keep['indexed_by'] = [{k: x.get(k) for k in ('source', 'section', 'title_info', 'author_info', 'summary', 'measure_info') if x.get(k)} for x in d.get('indexed_by') or []]
    if d.get('description'): keep['description'] = (d['description'].get('text') or '')[:600]
    if d.get('ai_note'): keep['ai_note'] = str(d['ai_note'])[:300]
    keep['books'] = [{k: b.get(k) for k in ('id', 'edition', 'sort_year', 'holder', 'title') if b.get(k)} for b in books.get(d['id'], [])][:10]
    for a in keep.get('authors') or []: a.pop('entity_id', None)
    return keep
by_n = collections.Counter(len(c['members']) for c in out_cl)
print('簇 %d，涉及 Work %d，簇内冲突 %d；簇大小 %s' % (len(out_cl), sum(len(c['members']) for c in out_cl), sum(1 for c in out_cl if c['conflict']), dict(by_n)))
for c in out_cl:
    c['docs'] = {i: slim(json.load(open(path(i), encoding='utf-8'))) for i in c['members']}
json.dump(out_cl, open(os.path.join(out, 'dossier.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
