#!/usr/bin/env python3
"""把 authors[].entity_id 指向墓碑的作者位改指墓碑的 merged_into（链到 live 为止）。
    python3 repoint_tomb_refs.py <台账输出.json> [--apply]"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import egov, jio  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('ledger'); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
people = egov.load_people()
recs = egov.scan_authored()
rows = []
for t, rel, d in recs:
    for i, au in enumerate(d.get('authors') or []):
        e = au.get('entity_id') if isinstance(au, dict) else None
        if e in people and people[e][1].get('merged_into'):
            to = egov.resolve(people, e)
            assert to in people and not people[to][1].get('merged_into'), (rel, e, to)
            rows.append({'path': rel, 'id': d['id'], 'type': t, 'slot': i, 'name': au.get('name'), 'from': e, 'to': to,
                         'to_name': people[to][1]['primary_name']})
print('待改指作者位', len(rows))
byp = {}
for r in rows: byp.setdefault(r['path'], []).append(r)
if a.apply:
    for rel, rs in byp.items():
        d, fmt = jio.load(rel)
        for r in rs:
            assert d['authors'][r['slot']]['entity_id'] == r['from']
            d['authors'][r['slot']]['entity_id'] = r['to']
        jio.save(rel, d, fmt)
json.dump({'repointed': rows}, open(a.ledger, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已写' if a.apply else '乾跑', len(byp), '个文件')
