#!/usr/bin/env python3
"""2.2a 按总目 person_uri 补挂 entity_id：作者位无 entity_id，其 source 里的 person_uri 恰对应唯一 live 人物 Entity，
且名字（主名／别名）一致、朝代同或相邻或缺。输出补挂清单与不挂登记。
    python3 plan_attach_uri.py <输出目录> [--types Work,Book,Collection]"""
import collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import egov, dyn  # noqa: E402

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
types = tuple((sys.argv[sys.argv.index('--types') + 1] if '--types' in sys.argv else 'Work').split(','))
people = egov.load_people()
live = {k: v[1] for k, v in people.items() if not v[1].get('merged_into')}
eu = collections.defaultdict(set)
for k, d in live.items():
    for m in egov.uris_of(d): eu[m].add(k)
names = collections.defaultdict(set)
for k, d in live.items():
    names[k].add(d['primary_name'])
    for a in d.get('alt_names') or []:
        if isinstance(a, dict) and a.get('name'): names[k].add(a['name'])
recs = egov.scan_authored(types)
attach, skip = [], collections.Counter(); skipped_rows = []
for t, rel, d in recs:
    for i, au in enumerate(d.get('authors') or []):
        if not isinstance(au, dict) or au.get('entity_id'): continue
        m = re.search(r'person/(\w+)', json.dumps(au.get('source'), ensure_ascii=False))
        if not m or m.group(1) not in eu: continue
        cand = eu[m.group(1)]
        if len(cand) != 1:
            skip['uri对应多个Entity'] += 1; skipped_rows.append((rel, i, au.get('name'), 'uri对应多个Entity', ','.join(sorted(cand)))); continue
        e = next(iter(cand))
        if au.get('name') not in names[e]:
            skip['名字不在主名/别名'] += 1; skipped_rows.append((rel, i, au.get('name'), '名字不在主名/别名', e + ':' + live[e]['primary_name'])); continue
        r = dyn.rel(au.get('dynasty') or d.get('dynasty'), live[e].get('dynasty'))
        if r == 'incompat':
            skip['朝代不兼容'] += 1; skipped_rows.append((rel, i, au.get('name'), '朝代不兼容', e + ':' + str(live[e].get('dynasty')) + '/' + str(au.get('dynasty') or d.get('dynasty')))); continue
        attach.append({'path': rel, 'type': t, 'id': d['id'], 'slot': i, 'name': au.get('name'), 'entity_id': e, 'entity_name': live[e]['primary_name'],
                       'dyn_rel': r, 'dynasty_slot': au.get('dynasty') or d.get('dynasty'), 'dynasty_entity': live[e].get('dynasty')})
json.dump(attach, open(os.path.join(out, 'attach.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(out, 'skipped.tsv'), 'w', encoding='utf-8').write('path\tslot\tname\treason\tdetail\n' + '\n'.join('\t'.join(map(str, r)) for r in skipped_rows) + '\n')
print('可补挂', len(attach), '其中朝代 相邻', sum(a['dyn_rel'] == 'adj' for a in attach), '缺', sum(a['dyn_rel'] == 'unk' for a in attach), '不挂', dict(skip))
