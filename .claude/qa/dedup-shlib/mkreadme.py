#!/usr/bin/env python3
"""生成批次 README 的组表。用法：mkreadme.py <批目录> → 打印 markdown 表"""
import json, sys, subprocess
d = sys.argv[1]
m = json.load(open(d + '/merges.json', encoding='utf-8'))['merges']
def t(i):
    p = [x for x in subprocess.check_output(['git', '-c', 'core.quotePath=false', 'ls-tree', '-r', '--name-only', 'origin/main', f'Work/{i[-3]}/{i[-2]}/{i[-1]}/'], text=True).split()
         if x.split('/')[-1].startswith(i + '-')][0]
    return json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + p]))
au = lambda x: '、'.join(a.get('name', '') for a in x.get('authors') or [])
print('| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |\n|---|---|---|---:|---:|')
for g in m:
    k = t(g['keeper']); ls = [t(l) for l in g['losers']]
    print(f"| {g['cluster_id']} | {k['title']}（{au(k)}） | {'；'.join(x['title'] + '（' + au(x) + '）' for x in ls)} | "
          f"{sum(len(r['fields']) for r in g.get('retained_alternatives', []))} | {len(g.get('classification_decisions', []))} |")
