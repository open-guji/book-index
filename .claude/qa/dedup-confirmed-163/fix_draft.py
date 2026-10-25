#!/usr/bin/env python3
"""草稿库善后：把草稿库里指向被并者的 _promoted_to／work_id／merged_into／related_works／分类成员等引用改指 keeper
（规则 5，避免「草稿墓碑→正式墓碑→keeper」两跳）。用法：fix_draft.py <merges.json> <草稿库根> [--apply]
只改值恰等于被并 ID 的字符串（键 id 除外）；原文件若不能按 indent=2 无损往返则跳过并报出。"""
import json, subprocess, sys, pathlib
led = json.load(open(sys.argv[1]))['merges']; root = pathlib.Path(sys.argv[2]); apply = '--apply' in sys.argv
mp = {l: m['keeper'] for m in led for l in m['losers']}
files = subprocess.run(['rg', '-l', '-F', '-f', '/dev/stdin', '--glob', '*.json', '--glob', '!index/**', '.'], input='\n'.join(mp) + '\n',
                       cwd=root, text=True, capture_output=True).stdout.split()
def walk(o, key=None):
    n = 0
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if isinstance(v, str) and v in mp and k != 'id':
                o[k] = mp[v]; n += 1
            else:
                n += walk(v, k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, str) and v in mp:
                o[i] = mp[v]; n += 1
            else:
                n += walk(v)
    return n
changed = skipped = refs = 0
for f in files:
    p = root / f; raw = p.read_text(encoding='utf-8'); d = json.loads(raw)
    nl = '\n' if raw.endswith('\n') else ''
    if json.dumps(d, ensure_ascii=False, indent=2) + nl != raw:
        skipped += 1; print('跳过(格式不可无损往返):', f); continue
    k = walk(d)
    if k:
        refs += k; changed += 1
        if apply: p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + nl, encoding='utf-8')
print('文件', changed, '引用', refs, '跳过', skipped)
