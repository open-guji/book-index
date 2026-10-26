"""新-异人登记-史：逐组材料。用法：python3 dossier.py 单元组.tsv 输出.jsonl
单元组.tsv 为 assign_units_20261026.py 输出里本单元的行（第 7 列 ids）。"""
import sys, os, json, csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, ROOT + '/.claude/qa')
import backrefs
rows = list(csv.reader(open(sys.argv[1], encoding='utf-8'), delimiter='\t'))
need = {i for r in rows for i in r[6].split(',')}
W, E = {}, {}
for t, p, d in backrefs.iter_records(ROOT):
    if d.get('merged_into'):
        continue
    if t == 'Work' and d['id'] in need:
        W[d['id']] = d
    elif t == 'Entity':
        E[d['id']] = d
print('载入 Work %d／需 %d，Entity %d' % (len(W), len(need), len(E)), file=sys.stderr)
if not W:
    sys.exit('载入 0')
def ent(eid):
    e = E.get(eid) or {}
    return {k: e.get(k) for k in ('primary_name', 'dynasty', 'birth', 'death', 'person_uri', 'cbdb_id') if e.get(k)} | (
        {'alt': [x if isinstance(x, str) else x.get('name') for x in (e.get('alt_names') or [])][:6]} if e.get('alt_names') else {})
out = open(sys.argv[2], 'w', encoding='utf-8')
for n, r in enumerate(rows, 1):
    mem = []
    for i in r[6].split(','):
        d = W.get(i)
        if not d:
            continue
        au = [a for a in d.get('authors') or [] if isinstance(a, dict)]
        ti = d.get('title_info')
        mem.append({
            'id': i, 'title': d.get('title'), 'dynasty': d.get('dynasty'), 'juan': d.get('juan_count'),
            'authors': [{k: a.get(k) for k in ('name', 'role', 'dynasty', 'entity_id') if a.get(k)} for a in au[:3]],
            'e0': ent(au[0]['entity_id']) if au and au[0].get('entity_id') else None,
            'ti': (ti if isinstance(ti, str) else json.dumps(ti, ensure_ascii=False))[:200] if ti else None,
            'ai': (d.get('author_info') if isinstance(d.get('author_info'), str) else json.dumps(d.get('author_info'), ensure_ascii=False))[:300] if d.get('author_info') else None,
            'idx': [x.get('source') or x.get('id') if isinstance(x, dict) else x for x in (d.get('indexed_by') or [])][:5],
            'rel': [(x.get('id'), x.get('note')) for x in d.get('related_works') or [] if isinstance(x, dict)][:5],
            'note': (d.get('ai_note') or '')[:150] or None,
        })
    out.write(json.dumps({'n': n, 'title': r[5], 'kind': r[4], 'members': mem}, ensure_ascii=False) + '\n')
