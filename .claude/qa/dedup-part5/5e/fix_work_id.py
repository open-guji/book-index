#!/usr/bin/env python3
"""去重方案部分 5e 补（2026-10-25）：全库扫描 live Book 的 work_id，
仍写草稿 Work ID（正式库无此文件）且 promotions 有 type=work 晉升記錄的，换成 production_id；
无晉升記錄的，查草稿库（--draft，默认 ../book-index-draft）该草稿 Work 的 merged_into，
若直接指向正式库活 Work 也改指它。目标须是正式库现存、非墓碑的 Work。题名不全等的列入清單備查（實測只差異體字）。
只改 Book；原值写 work_id-原值.json，清单写 work_id-清單.tsv。用法：fix_work_id.py [--draft DIR] [--apply]"""
import json, sys, os, glob, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = '2026-10-25'
def save(f, j): open(f, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
def bump(j):
    a, b, c = [int(x) for x in j.get('revision', '1.0.0').split('.')]
    j['revision'] = f'{a}.{b}.{c+1}'; j['revised_at'] = TODAY
def norm(s): return re.sub(r'^\[.*?\]|[\s（）()]', '', s or '')
pm = {}
for f in glob.glob(f'{ROOT}/promotions/*.json'):
    for k, v in json.load(open(f, encoding='utf-8'))['promotions'].items():
        if v.get('type') == 'work': pm[k] = v['production_id']
DRAFT = sys.argv[sys.argv.index('--draft') + 1] if '--draft' in sys.argv else os.path.join(ROOT, '../book-index-draft')
def draft_merged_into(i):
    fs = glob.glob(f'{DRAFT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')
    return json.load(open(fs[0], encoding='utf-8')).get('merged_into') if fs else None
works = {os.path.basename(f).split('-')[0]: f for f in glob.glob(f'{ROOT}/Work/*/*/*/*.json')}
print(f'載入 promotions(work) {len(pm)}、正式 Work {len(works)}', file=sys.stderr)
assert pm and works
orig, out, rows, miss, n = {}, [], [], [], 0
for f in glob.glob(f'{ROOT}/Book/*/*/*/*.json'):
    n += 1
    j = json.load(open(f, encoding='utf-8'))
    w = j.get('work_id')
    if j.get('merged_into') or not w or w in works: continue
    t, how = pm.get(w), 'promotions'
    if not t:
        t, how = draft_merged_into(w), '草稿墓碑merged_into'
        if t not in works: miss.append((j['id'], j.get('title', ''), w)); continue
    wj = json.load(open(works[t], encoding='utf-8'))
    assert not wj.get('merged_into'), (j['id'], w, t)
    rows.append((j['id'], j.get('title', ''), w, t, wj.get('title', ''), '同' if norm(wj.get('title')) == norm(j.get('title')) else '異', how))
    orig[j['id']] = {'work_id': w}
    j['work_id'] = t; bump(j); out.append((f, j))
print(f'載入 Book {n}，需改 {len(out)}，草稿 ID 無晉升記錄 {len(miss)}（不改，列清單）', file=sys.stderr)
assert n > 0
if '--apply' in sys.argv:
    for f, j in out: save(f, j)
    json.dump(orig, open(os.path.join(HERE, 'work_id-原值.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'work_id-清單.tsv'), 'w', encoding='utf-8') as fo:
        fo.write('book_id\tbook_title\t草稿work_id\t正式work_id\twork_title\t題名\t依據\n')
        for r in sorted(rows): fo.write('\t'.join(r) + '\n')
    if miss:
      if miss:
        with open(os.path.join(HERE, 'work_id-未晉升.tsv'), 'w', encoding='utf-8') as fo:
            fo.write('book_id\tbook_title\t草稿work_id\n')
            for r in sorted(miss): fo.write('\t'.join(r) + '\n')
print(('改 ' if '--apply' in sys.argv else '乾跑 ') + f'{len(out)} 個 Book')
