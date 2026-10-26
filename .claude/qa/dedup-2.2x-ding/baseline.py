#!/usr/bin/env python3
"""2.2续-丁（撞名补挂，md5(norm_name)%4==3；脚本沿用乙份）基线与候选特征表（只读）。
    python3 baseline.py <输出目录> [--shard 1]
对本份每个「无 entity_id、非佚名」的作者位（Work／Book／Collection），找名字命中的 live 人物 Entity：
  主名命中（norm_name 相同）；别名命中（alt_names，另记别名类型）；去「釋」前缀命中（单列，僧俗不得混）。
输出 slots.jsonl（每作者位一行，带候选及其特征）与 summary.txt。"""
import collections, hashlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(QA, 'entity-governance-1025'), os.path.join(QA, '..', '..', 'scripts')]
import egov, dyn  # noqa: E402
import importlib.util
spec = importlib.util.spec_from_file_location('census', os.path.join(egov.ROOT, 'scripts', 'dedup-census.py'))
C = importlib.util.module_from_spec(spec); sys.argv, _argv = sys.argv[:1], sys.argv; spec.loader.exec_module(C); sys.argv = _argv

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
SHARD = int(sys.argv[sys.argv.index('--shard') + 1]) if '--shard' in sys.argv else 1


def shard_of(n):
    return int(hashlib.md5(n.encode('utf-8')).hexdigest(), 16) % 4


def uri(x):
    m = re.search(r'person/(\w+)', json.dumps(x, ensure_ascii=False)) if x else None
    return m.group(1) if m else None


def bulei(d):
    for ib in d.get('indexed_by') or []:
        s = ib.get('section') or ''
        if s: return s
    return ''


people = egov.load_people()
live = {k: v[1] for k, v in people.items() if not v[1].get('merged_into')}
idx = collections.defaultdict(list)   # norm -> [(eid, how)]
for k, d in live.items():
    idx[C.norm_name(d['primary_name'])].append((k, '主名'))
    for a in d.get('alt_names') or []:
        if isinstance(a, dict) and a.get('name'):
            idx[C.norm_name(a['name'])].append((k, '别名:' + str(a.get('type'))))
for n in idx:   # 同一 Entity 主名、别名都命中时只留一条（主名优先）
    seen, keep = set(), []
    for e, h in idx[n]:
        if e not in seen: seen.add(e); keep.append((e, h))
    idx[n] = keep

recs = egov.scan_authored()
works_of = collections.defaultdict(list)   # eid -> [(title, section, dynasty)]
for t, rel, d in recs:
    for a in d.get('authors') or []:
        if isinstance(a, dict) and a.get('entity_id') in live and t == 'Work':
            works_of[a['entity_id']].append((d.get('title'), bulei(d)[:12], a.get('dynasty') or d.get('dynasty')))

stat = collections.Counter(); names = collections.Counter(); rows = []
for t, rel, d in recs:
    for i, au in enumerate(d.get('authors') or []):
        if not isinstance(au, dict) or au.get('entity_id'): continue
        nm = C.norm_name(au.get('name'))
        if not nm or nm in C.ANONYMOUS: continue
        stat['全库无id非佚名作者位'] += 1
        if shard_of(nm) != SHARD: continue
        stat['本份作者位'] += 1
        cands = list(idx.get(nm, []))
        how = 'direct'
        if not cands and nm.startswith('釋') and len(nm) > 2:
            cands = [(e, h + '(去釋)') for e, h in idx.get(nm[1:], [])]; how = 'shi'
        if not cands: stat['本份无人物命中'] += 1; continue
        sd = au.get('dynasty') or d.get('dynasty')
        su = uri(au.get('source'))
        cl = []
        for e, h in cands:
            ed = live[e]
            cl.append({'eid': e, 'how': h, 'pname': ed['primary_name'], 'dyn': ed.get('dynasty'), 'rel': dyn.rel(sd, ed.get('dynasty')),
                       'dates': ed.get('dates'), 'np': ed.get('native_place'), 'uris': sorted(egov.uris_of(ed)), 'nworks': len(works_of[e]),
                       'works': works_of[e][:8]})
        rows.append({'type': t, 'path': rel, 'id': d['id'], 'slot': i, 'name': au.get('name'), 'norm': nm, 'role': au.get('role'), 'dyn': sd,
                     'uri': su, 'title': d.get('title'), 'section': bulei(d), 'author_info': ((d.get('indexed_by') or [{}])[0].get('author_info')),
                     'how': how, 'cands': cl})
        stat['本份有命中作者位'] += 1; names[nm] += 1
with open(os.path.join(out, 'slots.jsonl'), 'w', encoding='utf-8') as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
# 分档
tier = collections.Counter()
for r in rows:
    c = r['cands']
    if len(c) > 1: k = '多候选'
    elif r['how'] == 'shi': k = '唯一·去釋'
    elif not c[0]['how'].startswith('主名'): k = '唯一·别名'
    else: k = '唯一·主名'
    k += '/朝代' + c[0]['rel'] if len(c) == 1 else ''
    if len(c) == 1 and r['uri'] and c[0]['uris']:
        k += '/URI' + ('同' if r['uri'] in c[0]['uris'] else '异')
    tier[k] += 1
s = ['基线 main %s，shard %d' % (os.popen('git -C %s rev-parse --short HEAD' % egov.ROOT).read().strip(), SHARD)]
s += ['%s\t%d' % kv for kv in stat.items()]
s += ['本份命中名字数\t%d' % len(names)]
s += ['%s\t%d' % kv for kv in sorted(tier.items(), key=lambda x: -x[1])]
open(os.path.join(out, 'summary.txt'), 'w', encoding='utf-8').write('\n'.join(s) + '\n')
print('\n'.join(s))
