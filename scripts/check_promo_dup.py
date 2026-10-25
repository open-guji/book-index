#!/usr/bin/env python3
"""合并前闸：本分支新增的 promotions 条目，其草稿 id 若已在 origin/main 的 promotions 里映射到别的正式 id，
说明同一草稿被两个批次各晋升了一次（正式库会出现两份同书）。先 git merge origin/main 再跑；有 DUP 就停下，
把本分支里该草稿对应的新 Work/Book 文件从晋升集里剔除（或改用 main 已有的正式 id），不要合。用法：python3 scripts/check_promo_dup.py
"""
import json, glob, subprocess, sys
def main_shards():
    out = {}
    for n in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'origin/main', 'promotions/'], text=True).split():
        out.update(json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + n]))['promotions'])
    return out
base = main_shards(); bad = 0
def merged_into(pid):
    # 并条后：main 里的旧正式 id 在本分支已是墓碑且 merged_into 指向新值，则这条变动是并条改指，不是双晋升
    for t in ('Work', 'Book', 'Collection', 'Entity'):
        for f in glob.glob(f'{t}/{pid[-3]}/{pid[-2]}/{pid[-1]}/{pid}-*.json'):
            return json.load(open(f)).get('merged_into')
for p in glob.glob('promotions/*.json'):
    for k, v in json.load(open(p))['promotions'].items():
        if k in base and base[k]['production_id'] != v['production_id'] and merged_into(base[k]['production_id']) != v['production_id']:
            bad += 1; print('DUP', k, 'main:', base[k]['production_id'], '本分支:', v['production_id'])
print('重复晋升', bad, '处'); sys.exit(1 if bad else 0)
