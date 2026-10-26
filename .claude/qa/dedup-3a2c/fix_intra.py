#!/usr/bin/env python3
"""同批多组并条时，apply_batch 的反查缓存取自批前，后一组被并者若被前一组 keeper（或其并入内容）引用会漏改。
本脚本把本批改动过的 Work 文件里、值恰等于本批被并 id 的 related_works[].id 改指其 keeper。用法：fix_intra.py <批次目录>"""
import json, subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'build'))
import v2common as V  # noqa: E402
L = json.load(open(pathlib.Path(sys.argv[1]) / 'merges.json'))['merges']
mp = {l: m['keeper'] for m in L for l in m['losers']}
names = subprocess.check_output(['git', '-c', 'core.quotePath=false', 'diff', '--name-only', 'origin/main'], cwd=ROOT, text=True).split('\n')
n = 0
for rel in names:
    if not rel.startswith('Work/') or not rel.endswith('.json'): continue
    p = ROOT / rel; d = json.loads(p.read_text(encoding='utf-8'))
    if d.get('merged_into'): continue
    ch = False
    for r in d.get('related_works') or []:
        if isinstance(r, dict) and r.get('id') in mp and mp[r['id']] != d['id']:
            r['id'] = mp[r['id']]; ch = True; n += 1
    if ch:
        txt = p.read_text(encoding='utf-8')
        p.write_text(V.dump(d, V.detect_format(txt, d)), encoding='utf-8')
print('批内引用改指', n)
