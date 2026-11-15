#!/usr/bin/env python3
"""build_members.py 之後跑：把本輪結果寫回 members-todo.tsv（加兩列：本輪處理、Work／Book id），並出統計。"""
import csv, json, os, collections, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'result.json'), encoding='utf-8'))
log = json.load(open(os.path.join(HERE, 'rowlog.json'), encoding='utf-8'))
p = os.path.join(HERE, '../sjj-collections/members-todo.tsv')
rows = list(csv.reader(open(p, encoding='utf-8'), delimiter='\t'))
head, body = rows[0][:10], rows[1:]
out = [head + ['本輪處理（2026-11-15 a11-sjj-members）', '新建／挂接 id']]
cnt = collections.Counter()
for i, r in enumerate(body, 2):
    r = r[:10] + [''] * (10 - len(r[:10]))
    l = log.get(str(i), {})
    out.append(r + [l.get('act', ''), l.get('ids', '')])
    cnt[l.get('act', '').split('：')[0]] += 1
with open(p, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n'); w.writerows(out)
for k, v in cnt.most_common(): print(v, k)
