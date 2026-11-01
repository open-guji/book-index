#!/usr/bin/env python3
"""轨 B：verdB → plan.json（applyB.py 输入）与 attachB.json（dup_of 异写挂已有人物）。python3 mkplanB.py <scratch> <outdir>"""
import collections, glob, json, os, sys
S, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
VOC = None
V = {}
for f in glob.glob(S + '/verdB/B-*.jsonl'):
    for l in open(f, encoding='utf-8'):
        if l.strip():
            d = json.loads(l); V[(d['name'], d['dyn'])] = d
rows = [json.loads(l) for l in open(S + '/c/slots.jsonl', encoding='utf-8')]
by = collections.defaultdict(list)
for r in rows:
    if not r['cands']: by[(r['norm'], r['dyn'] or '')].append(r)
OKDY = {'日本', '朝鮮', '高麗', '天竺', '新羅'}
FOREIGN = {'英國', '美國', '法國', '德國', '意大利', '俄羅斯', '西班牙', '比利時', '奧地利', '葡萄牙', '瑞典', '荷蘭', '瑞士', '丹麥', '印度'}
MERGE = {('釋曇摩難提', '晉'): ('釋曇摩難提', '前秦'), ('愛同', '唐'): ('釋愛同', '唐')}
groups = collections.OrderedDict(); attach = []
for (n, dy), v in V.items():
    rs = by.get((n, dy)) or []
    if v['verdict'] == 'SKIP':
        e = v.get('dup_of')
        if e and rs and (n in (v.get('reason') or '') or True):
            for r in rs: attach.append({'path': r['path'], 'slot': 0, 'name': r['name'], 'entity_id': e, 'work_id': r['id'], 'title': r['title'], 'reason': v.get('reason')})
        continue
    if v['verdict'] != 'NEW' or not rs: continue
    key = MERGE.get((n, dy), (n, dy))
    dyn = v.get('dynasty') or ''
    g = groups.setdefault(key, {'name': key[0], 'dynasty': None, 'country': None, 'cd': None, 'cbdb': None, 'cbdb_cand': None, 'cbdb_n': 0, 'uris': [], 'namesakes': [], 'slots': []})
    if dyn in FOREIGN: g['country'] = dyn
    elif dyn and not g['dynasty']: g['dynasty'] = dyn
    for r in rs:
        g['slots'].append({'path': r['path'], 'id': r['id'], 'title': r['title'], 'slot': 0, 'name': r['name'], 'dynasty': r['dyn'], 'role': r['role'], 'author_info': r['author_info'], 'summary': r['sum']})
# 同名一组空朝代、一组有朝代：并入有朝代者
plan = list(groups.values())
byn = collections.defaultdict(list)
for g in plan: byn[g['name']].append(g)
final = []
for n, gs in byn.items():
    dated = [g for g in gs if g['dynasty'] or g['country']]; empty = [g for g in gs if not g['dynasty'] and not g['country']]
    if len(dated) == 1 and empty:
        for e in empty: dated[0]['slots'] += e['slots']
        final += dated
    else: final += gs
# 宽归一撞名／撞非人物实体名／被撤回过的名字：不建，进 held
import importlib.util
QA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('plan23', os.path.join(QA, 'dedup-part2-3', 'plan23.py'))
_a = sys.argv; sys.argv = sys.argv[:1]; P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P); sys.argv = _a
import csv
ROOT = os.path.abspath(os.path.join(QA, '..', '..'))
nameidx = collections.defaultdict(set); other = set()
for f in glob.glob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')):
    d = json.load(open(f, encoding='utf-8'))
    if d.get('subtype') == 'people':
        for n in {d.get('primary_name')} | {x.get('name') for x in d.get('alt_names') or [] if isinstance(x, dict)}:
            if n: nameidx[P.loose(n)].add(d['id'])
    elif d.get('subtype') in ('collective', 'publisher', 'office') and d.get('primary_name'): other.add(P.loose(d['primary_name']))
wd = set()
for f in glob.glob(os.path.join(QA, 'dedup-part2-3', '*', '撤出*.tsv')) + glob.glob(os.path.join(QA, 'dedup-part2-3', 'recheck-*withdrawn.tsv')):
    wd |= {r.get('name') for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t') if r.get('name')}
import re
def strip2(x):
    x = P.loose((x or '').replace('囉', '羅').replace('耶捨', '耶舍'))
    return re.sub(r'^(釋|僧|沙門)', '', x)
idx2 = collections.defaultdict(set)
for f in glob.glob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')):
    d = json.load(open(f, encoding='utf-8'))
    if d.get('subtype') == 'people' and not d.get('merged_into'):
        for n in {d.get('primary_name')} | {x.get('name') for x in d.get('alt_names') or [] if isinstance(x, dict)}:
            if n and len(strip2(n)) >= 2: idx2[strip2(n)].add(d['id'])
EXTRA_HOLD = {'彌勒約翰', '何道全'}
keep, held = [], []
for g in final:
    k = P.loose(g['name'])
    why = '撞已有人物' if nameidx.get(k) else ('撞非人物实体名' if k in other else ('撤回过' if g['name'] in wd else None))
    if not why and strip2(g['name']) in idx2 and len(strip2(g['name'])) >= 2: why = '去釋/僧近似撞名'
    if not why and g['name'] in EXTRA_HOLD: why = '抽检判疑同人'
    (held if why else keep).append((g, why))
final = [g for g, _ in keep]
with open(out + '/held.tsv', 'w', encoding='utf-8') as f:
    f.write('name\tdynasty\tn\twhy\tdetail\n')
    for g, w in held: f.write('%s\t%s\t%d\t%s\t%s\n' % (g['name'], g['dynasty'] or g['country'] or '', len(g['slots']), w, ','.join(sorted(nameidx.get(P.loose(g['name']), ()) or idx2.get(strip2(g['name']), ())))))
print('宽归一撞名等不建', len(held))
for g in final:
    g['uris'] = []
json.dump(final, open(out + '/plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump(attach, open(out + '/attachB.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('新建组', len(final), '作者位', sum(len(g['slots']) for g in final), 'dup_of 挂接', len(attach), 'SKIP无dup', sum(1 for v in V.values() if v['verdict'] == 'SKIP' and not v.get('dup_of')))
