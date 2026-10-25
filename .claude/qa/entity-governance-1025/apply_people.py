#!/usr/bin/env python3
"""按 batch.json 并人物 Entity（复用 dedup-confirmed-163/apply_batch.py 与 entity_merge.py，反查改用预建索引）。
    python3 apply_people.py <batch.json> [--apply] [--only N]   # 乾跑只印每组摘要；--only 取前 N 组做样本"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'dedup-confirmed-163'))
import egov, entity_merge, apply_batch  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('batch'); ap.add_argument('--apply', action='store_true'); ap.add_argument('--only', type=int)
a = ap.parse_args()
apply_batch.BY = 'A11-去重第2部分'
spec = json.load(open(a.batch, encoding='utf-8'))
groups = spec['groups'][:a.only] if a.only else spec['groups']
egov.patch_entity_merge(egov.build_ref_map(egov.scan_authored()))
ledger = []
for g in groups:
    pre = []
    for i in [g['keeper']] + g['losers']:
        rel = apply_batch.path_of('people', i); sha, _ = apply_batch.base_sha(rel)
        pre.append({'id': i, 'path': rel, 'sha256': sha})
    if a.apply:
        out = apply_batch.merge_people(g, True)
    else:
        out = '\n'.join(json.dumps(entity_merge.merge(l, g['keeper'], reason=g['why'], rule=g['rule'], dry=True), ensure_ascii=False)[:400] for l in g['losers'])
    print('=====', g['cluster_id'], g['keeper'], '<-', g['losers']); print(out)
    ledger.append({'cluster_id': g['cluster_id'], 'type': 'people', 'keeper': g['keeper'], 'losers': g['losers'], 'evidence': g['evidence'],
                   'rule': g['rule'], 'preconditions': pre, 'retained_alternatives': [], 'classification_decisions': [],
                   'dropped_author_entities': [], 'loser_original_notes': {}})
if a.apply:
    base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=egov.ROOT, text=True).strip()
    json.dump({'base': base, 'merges': ledger}, open(os.path.join(os.path.dirname(os.path.abspath(a.batch)), 'merges.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('merges.json 已写', len(ledger), '组')
