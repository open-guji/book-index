#!/usr/bin/env python3
"""读 stdin 的冲突路径，列出其中属本批（batch.json）各组的 Work id（Book 取其 work_id）。用法：conflict_ids.py <批次目录> <merge-base>"""
import sys, json, subprocess
B, MB = sys.argv[1], sys.argv[2]
batch = json.load(open(B + '/batch.json'))
mine = {i for g in batch['groups'] for i in [g['keeper'], *g['losers']]}
out = set()
for p in sys.stdin.read().split('\n'):
    p = p.strip()
    if p.startswith('Work/'):
        i = p.split('/')[-1][:12]
        if i in mine: out.add(i)
    elif p.startswith('Book/'):
        for rev in (MB, 'origin/main', 'HEAD'):
            try:
                w = json.loads(subprocess.check_output(['git', 'show', f'{rev}:{p}'], stderr=subprocess.DEVNULL)).get('work_id')
                if w in mine: out.add(w)
            except Exception: pass
print(' '.join(sorted(out)))
