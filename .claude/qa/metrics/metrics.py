#!/usr/bin/env python3
"""三轴指标快照（G2）。只读。

  python3 -I .claude/qa/metrics/metrics.py [--root ROOT] [--append .claude/qa/metrics/history.tsv] [--sources sources.tsv]

输出一行：日期 提交 在世Work 在世Book 有period 有description 无作者 首位无entity(含佚名) 无indexed_by
Work自身有资源 Work或其Book有资源 Book有资源。--sources 另写每个 indexed_by.source 的 Work 数（目录书覆盖看板 C0 的底表）。
覆盖率以「分子/分母」两个数一起记（分母会随新建 Work 变大）。
"""
import argparse, collections, datetime, glob, json, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument('--root', default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
ap.add_argument('--append')
ap.add_argument('--sources')
a = ap.parse_args()
ANON = {'', '佚名', '闕名', '缺名', '無名氏', '不著撰人', '不著撰者', '不題撰人', '不詳', '撰者不詳'}
W = collections.Counter()
src = collections.Counter()
work_has_res, book_work_res, nbook = set(), set(), 0
for p in glob.glob(os.path.join(a.root, 'Work/*/*/*/*.json')):
    d = json.load(open(p, encoding='utf-8'))
    if d.get('merged_into'):
        continue
    W['work'] += 1
    W['period'] += bool(d.get('period'))
    W['desc'] += bool(d.get('description'))
    au = [x for x in d.get('authors') or [] if isinstance(x, dict)]
    W['noauthor'] += not au
    if au and not au[0].get('entity_id') and (au[0].get('name') or '') not in ANON:
        W['first_noentity_real'] += 1
    ib = d.get('indexed_by') or []
    W['noib'] += not ib
    for s in {x.get('source') for x in ib if isinstance(x, dict)}:
        src[s] += 1
    if d.get('resources'):
        work_has_res.add(d['id'])
for p in glob.glob(os.path.join(a.root, 'Book/*/*/*/*.json')):
    d = json.load(open(p, encoding='utf-8'))
    if d.get('merged_into'):
        continue
    nbook += 1
    if d.get('resources'):
        W['book_res'] += 1
        book_work_res.add(d.get('work_id'))
any_res = work_has_res | (book_work_res - {None})
try:
    head = subprocess.check_output(['git', '-C', a.root, 'rev-parse', '--short', 'HEAD'], text=True).strip()
except Exception:
    head = '?'
row = [datetime.date.today().isoformat(), head, W['work'], nbook, W['period'], W['desc'], W['noauthor'],
       W['first_noentity_real'], W['noib'], len(work_has_res), len(any_res), W['book_res']]
hdr = ['date', 'commit', 'work', 'book', 'period', 'desc', 'noauthor', 'first_noentity_real', 'no_indexed_by',
       'work_res', 'work_or_book_res', 'book_res']
print('\t'.join(hdr)); print('\t'.join(map(str, row)))
if a.append:
    new = not os.path.exists(a.append)
    with open(a.append, 'a', encoding='utf-8') as f:
        if new:
            f.write('\t'.join(hdr) + '\n')
        f.write('\t'.join(map(str, row)) + '\n')
if a.sources:
    with open(a.sources, 'w', encoding='utf-8') as f:
        for s, c in src.most_common():
            f.write('%s\t%d\n' % (s, c))
