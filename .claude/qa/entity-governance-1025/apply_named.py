#!/usr/bin/env python3
"""执行 pr2/batch.py：预修（解繫／撤错误字段）→ 并条 → 台账。
    python3 apply_named.py pr2/batch.py [--apply]   # 不加 --apply 只印计划（逐步骤、受影响 Work 数）"""
import argparse, copy, glob, hashlib, importlib.util, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'dedup-confirmed-163'))
import egov, jio, entity_merge, apply_batch  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('batch'); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
spec = importlib.util.spec_from_file_location('b', a.batch); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
apply_batch.BY = 'A11-去重第2部分'
ROOT = egov.ROOT

def rel_of(kind, i):
    d = {'work': 'Work', 'ent': 'Entity'}[kind]
    h = glob.glob(os.path.join(ROOT, d, *i[-3:], i + '-*.json')); assert len(h) == 1, (i, h)
    return os.path.relpath(h[0], ROOT)

def sha(rel):
    return hashlib.sha256(subprocess.check_output(['git', '-c', 'core.quotePath=false', 'show', 'origin/main:' + rel], cwd=ROOT)).hexdigest()

egov.patch_entity_merge(egov.build_ref_map(egov.scan_authored()))
prefix_log, ledger = [], []

def do_pre(op, g):
    kind = op[0]
    if kind in ('unlink', 'relink'):
        wid, frm = op[1], op[2]; rel = rel_of('work', wid); d, fmt = jio.load(rel); hit = 0
        for au in d.get('authors') or []:
            if au.get('entity_id') == frm:
                hit += 1
                if kind == 'unlink': au.pop('entity_id')
                else: au['entity_id'] = op[3]
        assert hit, ('Work 上没有指向', wid, frm)
        rec = {'case': g['cid'], 'op': kind, 'work': wid, 'path': rel, 'from': frm, 'to': op[3] if kind == 'relink' else None, 'why': op[-1], 'sha256_before': sha(rel)}
        if a.apply: jio.save(rel, d, fmt)
        prefix_log.append(rec); print('  ', kind, wid, frm, '->', rec['to'], '|', op[-1])
    elif kind == 'strip':
        eid, fields = op[1], op[2]; rel = rel_of('ent', eid); d, fmt = jio.load(rel); orig = {}
        for f in fields:
            if f.startswith('alt_names:'):
                names = set(f.split(':', 1)[1].split(','))
                orig['alt_names'] = [x for x in d.get('alt_names', []) if x.get('name') in names]
                d['alt_names'] = [x for x in d.get('alt_names', []) if x.get('name') not in names]
                if not d['alt_names']: d.pop('alt_names')
            elif f.endswith('*'):
                for k in [k for k in d if k.startswith(f[:-1])]: orig[k] = d.pop(k)
            elif f in d: orig[f] = d.pop(f)
        rec = {'case': g['cid'], 'op': 'strip', 'entity': eid, 'path': rel, 'removed': orig, 'why': op[-1], 'sha256_before': sha(rel)}
        if a.apply: jio.save(rel, d, fmt)
        prefix_log.append(rec); print('   strip', eid, list(orig), '|', op[-1])

def carry_sources(keeper, losers):
    krel = rel_of('ent', keeper); k, fmt = jio.load(krel); have = {s.get('details') for s in (k.get('description') or {}).get('sources', [])}; add = []
    for l in losers:
        d, _ = jio.load(rel_of('ent', l))
        for s in (d.get('description') or {}).get('sources', []) or []:
            if s.get('details') not in have: add.append(s); have.add(s.get('details'))
    if add and a.apply:
        k.setdefault('description', {}).setdefault('sources', []).extend(add); jio.save(krel, k, fmt)
    return add

for g in B.G:
    print('=====', g['cid'], g['keeper'], '<-', g['losers'])
    pre_ids = [i for i in [g['keeper']] + g['losers']]
    pre = [{'id': i, 'path': rel_of('ent', i), 'sha256': sha(rel_of('ent', i))} for i in pre_ids]
    for op in g.get('pre', []): do_pre(op, g)
    add = carry_sources(g['keeper'], g['losers'])
    if add: print('   带入上图人物 URI 来源', [s.get('details') for s in add])
    gg = dict(keeper=g['keeper'], losers=g['losers'], why=g['ev'], rule='去重第2部分 2.1：' + g['cid'], cluster_id=g['cid'])
    if a.apply:
        apply_batch.merge_people(gg, True)
    else:
        for l in g['losers']:
            s = entity_merge.merge(l, g['keeper'], reason=g['ev'], rule=gg['rule'], dry=True)
            print('   dry', l, '改繫 Work', len(s['redirected_works']), '新增别名', s['added_alt_names'], '补外部号', s['filled_external_ids'])
    ledger.append({'cluster_id': g['cid'], 'type': 'people', 'keeper': g['keeper'], 'losers': g['losers'], 'evidence': g['ev'], 'rule': gg['rule'],
                   'preconditions': pre, 'retained_alternatives': [], 'classification_decisions': [], 'dropped_author_entities': [], 'loser_original_notes': {}})
for f in getattr(B, 'FIX_ONLY', []):
    print('=====', f['cid'], '(不并，改挂)')
    for op in f['pre']: do_pre(op, f)
if a.apply:
    base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
    out = os.path.join(os.path.dirname(os.path.abspath(a.batch)), 'merges.json')
    json.dump({'base': base, 'merges': ledger, 'prefixes': prefix_log}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('merges.json', len(ledger), '组', len(prefix_log), '预修')
