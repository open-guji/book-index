#!/usr/bin/env python3
"""晋升后修 V07（related 存在 id 较大一侧）。用法（在正式库 book-index 仓根，已 checkout 你的晋升分支）：
    python3 fix_v07.py            # 只查本分支相对 origin/main 改动的 Work，打印将挪几条
    python3 fix_v07.py apply      # 落笔：小 id 侧纯追加该条 related，大 id 侧去掉；之后重跑 check_v2 应为 0
原则：正式库只追加（小侧是正式库既有文件时只加一项 related_works，不改旧值）；小侧是墓碑／不存在的记入 stdout 留人看。
"""
import json, glob, os, subprocess, sys, collections
apply = len(sys.argv) > 1 and sys.argv[1] == 'apply'
changed = subprocess.run(['git', '-c', 'core.quotepath=false', 'diff', '--name-only', '-z', 'origin/main...'], capture_output=True, text=True).stdout.split('\0')
changed += subprocess.run(['git', '-c', 'core.quotepath=false', 'ls-files', '-z', '-m', '-o', '--exclude-standard'], capture_output=True, text=True).stdout.split('\0')
changed = sorted({p for p in changed if p.startswith('Work/') and p.endswith('.json') and os.path.exists(p)})
loc = {os.path.basename(p).split('-')[0]: p for p in glob.glob('Work/*/*/*/*.json')}
load = lambda p: json.load(open(p, encoding='utf-8'))
dump = lambda p, d: open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
cache = {}; get = lambda p: cache.setdefault(p, load(p)); stat = collections.Counter()
for p in changed:
    big = get(p); bid = big['id']
    for e in list(big.get('related_works') or []):
        t = e.get('id')
        if e.get('relation') not in ('related', 'related_to') or not t or bid <= t: continue
        sp = loc.get(t)
        if not sp: stat['小侧不存在'] += 1; print('小侧不存在', bid, t); continue
        small = get(sp)
        if small.get('merged_into'): stat['小侧墓碑'] += 1; print('小侧墓碑', bid, t); continue
        sr = small.setdefault('related_works', [])
        if not any(x.get('id') == bid for x in sr): sr.append({**e, 'id': bid}); stat['挪'] += 1
        else: stat['小侧已有'] += 1
        big['related_works'] = [x for x in big['related_works'] if x is not e]
        if not big['related_works']: del big['related_works']
print(dict(stat), len(cache), '档涉及')
if apply:
    for p, d in cache.items(): dump(p, d)
