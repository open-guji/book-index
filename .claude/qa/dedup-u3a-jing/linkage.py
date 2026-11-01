#!/usr/bin/env python3
"""同书互证（机械 A 档）：作者位与其 Work／Book 兄弟记录中「同名且已挂 entity_id」的作者位指向同一人。
  Book 作者位：所属 Work 的同名作者位已挂 X → 挂 X；
  Work 作者位：其下 Book 的同名作者位已挂 X（且只有一个 X）→ 挂 X；
  Collection 作者位：其成员 Work 的同名作者位全挂同一 X → 挂 X（成员两部以上）。
X 须在本作者位的名字候选里（主名／别名命中），且朝代不冲突（incompat 送复核）。
    python3 linkage.py <baseline 输出目录>   → linkage.json（A 档挂接）、rest.jsonl（余下送复核）"""
import collections, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(os.path.dirname(HERE), 'entity-governance-1025')]
import egov  # noqa: E402
import importlib.util
spec = importlib.util.spec_from_file_location('census', os.path.join(egov.ROOT, 'scripts', 'dedup-census.py'))
C = importlib.util.module_from_spec(spec); _a = sys.argv; sys.argv = _a[:1]; spec.loader.exec_module(C); sys.argv = _a
d0 = sys.argv[1]
rows = [json.loads(l) for l in open(os.path.join(d0, 'slots.jsonl'), encoding='utf-8')]
print('载入作者位', len(rows)); assert rows


def named_eids(d):
    m = collections.defaultdict(set)
    for a in d.get('authors') or []:
        if isinstance(a, dict) and a.get('entity_id'):
            m[C.norm_name(a.get('name'))].add(a['entity_id'])
    return m


work_named = {}       # work id -> {norm: {eid}}
book_named = collections.defaultdict(lambda: collections.defaultdict(set))   # work id -> {norm: {eid}}
coll_members = {}
for t, rel, d in egov.scan_authored(('Work', 'Book', 'Collection')):
    if t == 'Work': work_named[d['id']] = named_eids(d)
    elif t == 'Book' and d.get('work_id'):
        for k, v in named_eids(d).items(): book_named[d['work_id']][k] |= v
    elif t == 'Collection':
        coll_members[d['id']] = [x.get('work_id') or x.get('id') for x in (d.get('works') or d.get('members') or []) if isinstance(x, dict)]
print('Work', len(work_named), 'Collection', len(coll_members))
attach, rest, why = [], [], collections.Counter()
book_work = {}
for r in rows:
    if r['type'] == 'Book':
        b = json.load(open(os.path.join(egov.ROOT, r['path']), encoding='utf-8')); book_work[r['id']] = b.get('work_id')
for r in rows:
    cand = {c['eid']: c for c in r['cands']}
    if r['type'] == 'Book':
        hit = work_named.get(book_work.get(r['id']), {}).get(r['norm'], set()); src = '所属Work同名作者已挂'
    elif r['type'] == 'Work':
        hit = book_named.get(r['id'], {}).get(r['norm'], set()); src = '下属Book同名作者已挂'
    else:
        ms = [work_named.get(w, {}).get(r['norm'], set()) for w in coll_members.get(r['id'], [])]
        ms = [m for m in ms if m]
        hit = set.union(*ms) if len(ms) >= 2 else set(); src = '成员Work同名作者已挂'
    if len(hit) == 1:
        x = next(iter(hit))
        if x in cand and cand[x]['rel'] != 'incompat':
            attach.append({'path': r['path'], 'slot': r['slot'], 'name': r['name'], 'entity_id': x, 'tier': 'A-同书互证', 'why': src}); why[src] += 1; continue
        why['互证所指不在候选或朝代冲突'] += 1
    elif len(hit) > 1: why['互证多个'] += 1
    rest.append(r)
json.dump(attach, open(os.path.join(d0, 'linkage.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
with open(os.path.join(d0, 'rest.jsonl'), 'w', encoding='utf-8') as f:
    for r in rest: f.write(json.dumps(r, ensure_ascii=False) + '\n')
print('A 档同书互证', len(attach), dict(why), '余', len(rest))
