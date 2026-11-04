#!/usr/bin/env python3
"""第 12 组②：office 具体条、官署(collective) 具体条的顶层 parent_id 改名 concept_id（与 place 朝代条同名同义：具体→概念）。
dynasty／publisher 的 parent_id 是真上下级，不动；place 沿革 history[].parent_id 不动。
幂等；默认只数数，--apply 才写。只重写「标准格式」的文件。"""
import glob, json, sys

APPLY = '--apply' in sys.argv
n = {'office': 0, 'collective': 0}
bad = 0
for f in sorted(glob.glob('Entity/*/*/*/*.json')):
    raw = open(f, encoding='utf8').read()
    d = json.loads(raw)
    if d.get('subtype') not in n or 'parent_id' not in d:
        continue
    if 'concept_id' in d:
        print('冲突：已有 concept_id', f); bad += 1; continue
    std = json.dumps(d, ensure_ascii=False, indent=2) + '\n'
    if std != raw:
        print('非标准格式，跳过', f); bad += 1; continue
    out = {}
    for k, v in d.items():           # 保键序：原位改名
        out['concept_id' if k == 'parent_id' else k] = v
    n[d['subtype']] += 1
    if APPLY:
        open(f, 'w', encoding='utf8').write(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(n, 'bad', bad, '(applied)' if APPLY else '(dry-run)')
sys.exit(1 if bad else 0)
