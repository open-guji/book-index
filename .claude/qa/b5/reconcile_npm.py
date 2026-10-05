"""B5：故宮善本匹配表加「本仓既有 Book 反查」列：馆藏号（故善…）已挂在哪个 Book、该 Book 的 work_id 与本表是否一致。
独立于题名匹配，是本仓自己的人工／既有著录，可当第二证据。用法：python3 reconcile_npm.py 匹配表.json 输出.json
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import *
rows = json.load(open(sys.argv[1]))
d = load_lib('臺灣故宮博物院善本古籍'); hmap = {r['url']: r['holding_id'] for r in d}
item2work = collections.defaultdict(set)
for b in iter_books():
    md = b.get('metadata') or {}
    ids = {md['npm_item_id']} if md.get('npm_item_id') else set()
    for x in b.get('resources', []):
        if 'npm' in (x.get('id') or ''):
            i = (x.get('metadata') or {}).get('item_id')
            if i: ids.add(i)
    for i in ids: item2work[i].add(b.get('work_id'))
for r in rows:
    h = hmap.get(r['url']); ws = item2work.get(h)
    r['holding_id'] = h
    r['book_work_ids'] = ','.join(sorted(ws)) if ws else ''
    r['book_agree'] = '无Book' if not ws else ('无候选' if not r['work_id'] else ('同' if r['work_id'] in ws else '异'))
json.dump(rows, open(sys.argv[2], 'w'), ensure_ascii=False)
print(collections.Counter((r['tier'], r['book_agree']) for r in rows))
