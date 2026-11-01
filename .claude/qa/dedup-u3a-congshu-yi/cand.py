#!/usr/bin/env python3
"""U3-a 子部：首位责任者无 entity_id 的叢書部（乙份） Work → 候选人物（只读）。
    python3 cand.py <输出目录>   → slots.jsonl（每个 Work 一行，带候选）、summary.txt
范围：Work 未并、authors[0] 无 entity_id、非佚名/失譯类，且任一 indexed_by.section 以「叢書部」开头；名字 md5(norm)%2==1 为乙份。"""
import hashlib, collections, json, os, re, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(QA, 'entity-governance-1025'), os.path.join(QA, '..', '..', 'scripts')]
import egov, dyn  # noqa: E402
spec = importlib.util.spec_from_file_location('census', os.path.join(egov.ROOT, 'scripts', 'dedup-census.py'))
C = importlib.util.module_from_spec(spec); _a = sys.argv; sys.argv = sys.argv[:1]; spec.loader.exec_module(C); sys.argv = _a
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
URI = re.compile(r'person/(\w+)')

people = egov.load_people()
live = {k: v[1] for k, v in people.items() if not v[1].get('merged_into')}
idx = collections.defaultdict(list)
for k, d in live.items():
    idx[C.norm_name(d['primary_name'])].append((k, '主名'))
    for a in d.get('alt_names') or []:
        if isinstance(a, dict) and a.get('name'): idx[C.norm_name(a['name'])].append((k, '别名:' + str(a.get('type'))))
for n in idx:
    seen, keep = set(), []
    for e, h in idx[n]:
        if e not in seen: seen.add(e); keep.append((e, h))
    idx[n] = keep
recs = egov.scan_authored(('Work',))
works_of = collections.defaultdict(list)
for t, rel, d in recs:
    for a in d.get('authors') or []:
        if isinstance(a, dict) and a.get('entity_id') in live:
            sec = ((d.get('indexed_by') or [{}])[0].get('section') or '')[:8]
            works_of[a['entity_id']].append((d.get('title'), sec, a.get('dynasty') or d.get('dynasty')))
rows = []; stat = collections.Counter()
for t, rel, d in recs:
    aus = d.get('authors') or []
    if not aus or not isinstance(aus[0], dict) or aus[0].get('entity_id'): continue
    if not any((ib.get('section') or '').startswith('叢書部') for ib in d.get('indexed_by') or []): continue
    au = aus[0]; nm = C.norm_name(au.get('name'))
    if not nm or nm in C.ANONYMOUS or nm == '失譯': stat['佚名失譯'] += 1; continue
    if int(hashlib.md5(nm.encode('utf-8')).hexdigest(), 16) % 2 != 1: stat['甲份'] += 1; continue
    stat['作品'] += 1
    cands = list(idx.get(nm, [])); how = 'direct'
    if not cands and nm.startswith('釋') and len(nm) > 2:
        cands = [(e, h + '(去釋)') for e, h in idx.get(nm[1:], [])]; how = 'shi'
    sd = au.get('dynasty') or d.get('dynasty')
    m = URI.search(json.dumps(au.get('source') or {}))
    cl = []
    for e, h in cands:
        ed = live[e]
        cl.append({'eid': e, 'how': h, 'pname': ed['primary_name'], 'dyn': ed.get('dynasty'), 'rel': dyn.rel(sd, ed.get('dynasty')),
                   'dates': ed.get('dates'), 'np': ed.get('native_place'), 'uris': sorted(egov.uris_of(ed)), 'nworks': len(works_of[e]), 'works': works_of[e][:8]})
    ib = (d.get('indexed_by') or [{}])[0]
    rows.append({'path': rel, 'id': d['id'], 'name': au.get('name'), 'norm': nm, 'role': au.get('role'), 'dyn': sd, 'uri': m.group(1) if m else None,
                 'title': d.get('title'), 'section': (ib.get('section') or ''), 'author_info': ib.get('author_info'), 'sum': (ib.get('summary') or '')[:90],
                 'how': how, 'cands': cl})
    stat['有候选' if cl else '无候选'] += 1
with open(os.path.join(out, 'slots.jsonl'), 'w', encoding='utf-8') as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
names = collections.Counter(r['norm'] for r in rows)
hit = {r['norm'] for r in rows if r['cands']}
s = ['基线 main %s' % os.popen('git -C %s rev-parse --short HEAD' % egov.ROOT).read().strip()] + ['%s\t%d' % kv for kv in stat.items()]
s += ['名字数\t%d\t有候选名字\t%d' % (len(names), len(hit))]
open(os.path.join(out, 'summary.txt'), 'w', encoding='utf-8').write('\n'.join(s) + '\n'); print('\n'.join(s))
