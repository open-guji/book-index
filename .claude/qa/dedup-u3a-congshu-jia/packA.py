#!/usr/bin/env python3
"""轨 A：有候选的名字 → 复核包（每名一条）。python3 packA.py <cand 输出目录> <包输出目录> [每包名数=40]
朝代冲突(incompat)的名字不进包（不挂）。"""
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); QA = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(QA, 'entity-governance-1025')]
import egov  # noqa: E402
src, out = sys.argv[1], sys.argv[2]; PER = int(sys.argv[3]) if len(sys.argv) > 3 else 40
os.makedirs(out, exist_ok=True)
people = egov.load_people()
rows = [json.loads(l) for l in open(os.path.join(src, 'slots.jsonl'), encoding='utf-8')]
by = collections.defaultdict(list)
for r in rows:
    if r['cands']: by[r['norm']].append(r)
def ent(c):
    d = people[c['eid']][1]
    return {'eid': c['eid'], 'name': d['primary_name'], 'how': c['how'], 'rel': c['rel'], 'dyn': d.get('dynasty'), 'dates': {k: v for k, v in (d.get('dates') or {}).items() if k in ('birth', 'death')},
            'np': d.get('native_place'), 'alt': [a.get('name') + '(' + str(a.get('type')) + ')' for a in d.get('alt_names') or [] if isinstance(a, dict)][:8],
            'note': (d.get('ai_note') or '')[:120], 'uris': c['uris'][:3], 'nworks': c['nworks'], 'works': ['%s｜%s｜%s' % tuple(w) for w in c['works'][:5]]}
items = []; skip = 0
for n, rs in sorted(by.items(), key=lambda x: -len(x[1])):
    c = rs[0]['cands']
    if all(x['rel'] == 'incompat' for x in c): skip += 1; continue
    items.append({'name': rs[0]['name'], 'norm': n, 'cands': [ent(x) for x in c if x['rel'] != 'incompat'], 'more': max(0, len(rs) - 6),
                  'works': [{'k': r['id'], 'title': r['title'], 'role': r['role'], 'dyn': r['dyn'], 'sec': r['section'][:16], 'ai': r['author_info'], 'sum': r['sum'], 'uri': r['uri']} for r in rs[:6]]})
print('名字', len(items), '朝代冲突不进包', skip)
for i in range(0, len(items), PER):
    with open(os.path.join(out, 'A-%02d.jsonl' % (i // PER + 1)), 'w', encoding='utf-8') as f:
        for it in items[i:i + PER]: f.write(json.dumps(it, ensure_ascii=False) + '\n')
