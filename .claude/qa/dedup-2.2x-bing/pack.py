#!/usr/bin/env python3
"""把 rest.jsonl 按名字聚成复核包（每名一条：候选 Entity 摘要＋本名各作者位所在书目摘要），分档切片。
    python3 pack.py <baseline 输出目录>   → pack/<档>-NN.jsonl 与 tiers.tsv"""
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(os.path.dirname(HERE), 'entity-governance-1025')]
import egov  # noqa: E402
d0 = sys.argv[1]; PER = int(os.environ.get('PER', '60'))
rows = [json.loads(l) for l in open(os.path.join(d0, 'rest.jsonl'), encoding='utf-8')]
print('载入', len(rows)); assert rows
people = egov.load_people()
by = collections.defaultdict(list)
for r in rows: by[r['norm']].append(r)


def tier(rs):
    c = rs[0]['cands']
    if len(c) > 1: return 'R3多候选'
    rel = c[0]['rel']
    if rel == 'incompat': return 'R4朝代冲突'
    if rs[0]['how'] == 'shi': return 'R2去釋'
    if not c[0]['how'].startswith('主名'): return 'R2别名'
    if rel != 'same': return 'R2朝代' + rel
    return 'R1唯一同朝'


def ent(eid, c):
    d = people[eid][1]
    return {'eid': eid, 'name': d['primary_name'], 'how': c['how'], 'dyn': d.get('dynasty'), 'dates': {k: v for k, v in (d.get('dates') or {}).items() if k in ('birth', 'death')},
            'np': d.get('native_place'), 'alt': [a.get('name') + '(' + str(a.get('type')) + ')' for a in d.get('alt_names') or [] if isinstance(a, dict)][:8],
            'note': (d.get('ai_note') or '')[:240], 'uris': c['uris'][:4], 'nworks': c['nworks'], 'works': ['%s｜%s｜%s' % tuple(w) for w in c['works']]}


def slot(r):
    d = json.load(open(os.path.join(egov.ROOT, r['path']), encoding='utf-8'))
    s = {'k': '%s:%s#%d' % (r['type'][0], r['id'], r['slot']), 'title': d.get('title'), 'role': r['role'], 'dyn': r['dyn'], 'sec': r['section'][:16], 'uri': r.get('uri')}
    if r['type'] == 'Book': s['ed'] = d.get('edition'); s['co'] = [a.get('name') + a.get('role', '') for a in d.get('authors') or []][:4]
    else:
        s['ai'] = r.get('author_info')
        s['sum'] = ((d.get('indexed_by') or [{}])[0].get('summary') or '')[:90]
    return s


tiers = collections.defaultdict(list)
for n, rs in by.items():
    t = tier(rs)
    rs.sort(key=lambda r: (r['type'] != 'Work', r['path']))
    tiers[t].append({'name': n, 'nslots': len(rs), 'cands': [ent(c['eid'], c) for c in rs[0]['cands']], 'slots': [slot(r) for r in rs[:14]],
                     'more': max(0, len(rs) - 14), 'tier': t})
os.makedirs(os.path.join(d0, 'pack'), exist_ok=True)
with open(os.path.join(d0, 'tiers.tsv'), 'w', encoding='utf-8') as f:
    for t, L in sorted(tiers.items()):
        L.sort(key=lambda x: x['name'])
        f.write('%s\t名%d\t位%d\n' % (t, len(L), sum(x['nslots'] for x in L)))
        print(t, '名', len(L), '位', sum(x['nslots'] for x in L))
        for i in range(0, len(L), PER):
            with open(os.path.join(d0, 'pack', '%s-%02d.jsonl' % (t, i // PER)), 'w', encoding='utf-8') as g:
                for x in L[i:i + PER]: g.write(json.dumps(x, ensure_ascii=False) + '\n')
