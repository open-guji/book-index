#!/usr/bin/env python3
"""Work：loss_status_basis／loss_status_note 并成证据对象 loss_status_evidence {basis?, note?}。

默认只报告；--apply 写入（保持原缩进）；--rollback FILE 把旧值记成 tsv（id、basis、note 的 JSON）。
对象落在原 loss_status_basis 的键位置（没有则 loss_status_note 的位置）。幂等。
"""
import glob, json, sys

APPLY = '--apply' in sys.argv
RB = sys.argv[sys.argv.index('--rollback') + 1] if '--rollback' in sys.argv else None
rows = []; n = skip = 0
for p in sorted(glob.glob('Work/*/*/*/*.json')):
    s = open(p, encoding='utf-8').read()
    if 'loss_status_basis' not in s and 'loss_status_note' not in s:
        continue
    d = json.loads(s)
    if 'loss_status_basis' not in d and 'loss_status_note' not in d:
        continue
    nl = '\n' if s.endswith('\n') else ''
    ind = None
    for k in (None, 1, 2, 3, 4, '\t'):
        if json.dumps(d, ensure_ascii=False, indent=k) + nl == s:
            ind = k; break
    if ind is None and json.dumps(d, ensure_ascii=False, indent=None) + nl != s:
        skip += 1; print('skip format', p); continue
    b, t = d.get('loss_status_basis'), d.get('loss_status_note')
    ev = {}
    if isinstance(b, str) and b.strip(): ev['basis'] = b
    if isinstance(t, str) and t.strip(): ev['note'] = t
    new = {}
    placed = False
    for k, v in d.items():
        if k in ('loss_status_basis', 'loss_status_note'):
            if not placed and ev:
                new['loss_status_evidence'] = ev; placed = True
            continue
        new[k] = v
    rows.append((d['id'], json.dumps({'loss_status_basis': b, 'loss_status_note': t}, ensure_ascii=False)))
    n += 1
    if APPLY:
        open(p, 'w', encoding='utf-8').write(json.dumps(new, ensure_ascii=False, indent=ind) + nl)
print({'changed': n, 'skip_format': skip})
if RB:
    with open(RB, 'w', encoding='utf-8') as f:
        for i, j in rows: f.write(f'{i}\t{j}\n')
