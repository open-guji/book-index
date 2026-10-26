#!/usr/bin/env python3
"""草稿库补丁：fix_draft.py 不改键名为 id 的值，related_works[].id 指向被并者时漏改；此处按行替换补上。
用法：fix_draft_related.py <merges.json> <草稿库根>"""
import json, subprocess, sys, pathlib, re
mp = {l: m['keeper'] for m in json.load(open(sys.argv[1]))['merges'] for l in m['losers']}
root = pathlib.Path(sys.argv[2])
files = subprocess.run(['rg', '-l', '-F', '-f', '/dev/stdin', '--glob', 'Work/**/*.json', '.'], input='\n'.join(mp) + '\n',
                       cwd=root, text=True, capture_output=True).stdout.split()
n = 0
for f in files:
    p = root / f; s = p.read_text(encoding='utf-8'); d = json.loads(s)
    rel = d.get('related_works') or []
    hit = [r['id'] for r in rel if isinstance(r, dict) and r.get('id') in mp]
    for i in hit:
        s = s.replace(f'"id": "{i}"', f'"id": "{mp[i]}"'); n += 1
    if hit: p.write_text(s, encoding='utf-8')
print('related_works 改指', n)
