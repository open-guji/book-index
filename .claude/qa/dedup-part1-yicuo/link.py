#!/usr/bin/env python3
"""部分1 存疑核定：证据不足、不并的组补齐双向 related_works（另立+互链）。python3 link.py [--apply]"""
import csv, glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio  # noqa: E402
APPLY = '--apply' in sys.argv
SKIP = {'PNA-1900-003', 'PNA-H004', 'PRV-H2000-005', 'PRV-N005', 'JC-OPEN-d59f27srzbpe',
        'MR-037', 'MR-035', 'MR-A003', 'H-C090', 'MR-H003', 'COL-2000-008', 'COL-R016'}
NOTE = '存疑核定（部分1）：同题而证据不足以证同书，不并，另立互链'
def rel(i):
    g = glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json'))
    return os.path.relpath(g[0], ROOT) if len(g) == 1 else None
rows = list(csv.DictReader(open('/mnt/project-files/总目/去重方案/台账/部分1/存疑-176组待核.tsv', encoding='utf-8'), delimiter='\t'))
n = 0
for r in rows:
    if r['case_id'] in SKIP: continue
    ids = r['ids'].split(',')
    P = {i: rel(i) for i in ids}
    if not all(P.values()): print('skip', r['case_id']); continue
    for a in ids:
        d, fmt = jio.load(P[a]); ch = False
        have = {w['id'] for w in d.get('related_works', [])}
        # 对称 related 只存于 id 较小一侧（check_v2 V07）；大侧如有本脚本先前写入的项则撤掉
        rw = d.get('related_works', [])
        keep = [w for w in rw if not (w.get('note') == NOTE and w['id'] < a)]
        if len(keep) != len(rw):
            d['related_works'] = keep; ch = True
        for b in ids:
            if b > a and b not in have:
                d.setdefault('related_works', []).append({'id': b, 'relation': 'related', 'note': NOTE}); ch = True
        if ch:
            n += 1
            if APPLY: jio.save(P[a], d, fmt)
print('改', n, '个文件', '(已写)' if APPLY else '(乾跑)')
