#!/usr/bin/env python3
"""apply_batch 善后：被并者在基线上原有的 merged_in（早先并入它的条目）补进 keeper 的 merged_in，
否则 check-duplicate-audit 报「Later-merged keeper missing from final keeper history」。用法：fix_merged_in.py <批次目录> [基线 rev，默认 origin/main]"""
import glob, json, os, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
B = sys.argv[1]; BASE = sys.argv[2] if len(sys.argv) > 2 else 'origin/main'
def path(i): return glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
n = 0
for g in json.load(open(os.path.join(B, 'merges.json')))['merges']:
    kp = path(g['keeper']); raw = open(kp, encoding='utf-8').read(); kd = json.loads(raw)
    have = {x.get('id') if isinstance(x, dict) else x for x in kd.get('merged_in', [])}
    add = []
    for l in g['losers']:
        rel = os.path.relpath(path(l), ROOT)
        base = json.loads(subprocess.check_output(['git', '-c', 'core.quotePath=false', 'show', f'{BASE}:{rel}'], cwd=ROOT))
        for e in base.get('merged_in') or []:
            i = e.get('id') if isinstance(e, dict) else e
            if i not in have: add.append(e); have.add(i)
    if add:
        kd['merged_in'] = kd.get('merged_in', []) + add; n += len(add)
        open(kp, 'w', encoding='utf-8').write(json.dumps(kd, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
print('补 merged_in', n, '项')
