#!/usr/bin/env python3
"""新-子目异名-史：抽每组每条 Work 的特征。
用法（book-index 根目录）：python3 feat.py <units.tsv> <单元代号> <out.json>
units.tsv 为 ai-team 细拆脚本 assign_units_20261026.py 的输出。"""
import csv, glob, json, os, re, sys
ROOT = os.environ.get('BOOK_INDEX', '.')
def wpath(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p); return p[0]
def cpath(i):
    p = glob.glob(f'{ROOT}/Collection/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); return p[0] if len(p) == 1 else None
# Collection：按源記錄 id 与本身 id 两种索引
colsrc, colid = {}, {}
for p in glob.glob(ROOT + '/Collection/*/*/*/*.json'):
    c = json.load(open(p, encoding='utf-8'))
    colid[c['id']] = c
    for s in c.get('sources') or []:
        if isinstance(s, dict) and s.get('id'): colsrc[s['id']] = c
print('载入 Collection', len(colid), file=sys.stderr)
assert colid
P_COLREC = re.compile(r'所屬叢書記錄 ([0-9a-z]{16})（(.*?)）')
rows = [r for r in csv.DictReader(open(sys.argv[1], encoding='utf-8'), delimiter='\t') if r['单元'] == sys.argv[2]]
print('本单元组数', len(rows), file=sys.stderr)
assert rows
def colauth(c):
    return [(a.get('name'), a.get('role'), a.get('dynasty'), a.get('entity_id')) for a in c.get('authors') or [] if isinstance(a, dict)]
out = []
for r in rows:
    g = {'bulei': r['部类'], 'cat': r['类别'], 'sub': r['异作者细分'], 'key': r['题名'], 'works': []}
    for i in r['ids'].split(','):
        w = json.load(open(wpath(i), encoding='utf-8'))
        note = w.get('ai_note') or ''
        cols = []
        for m in P_COLREC.finditer(note):
            c = colsrc.get(m.group(1))
            cols.append({'rec': m.group(1), 'title': m.group(2), 'id': c['id'] if c else None,
                         'ctitle': c.get('title') if c else None, 'auth': colauth(c) if c else []})
        g['works'].append({
            'id': i, 'title': w.get('title'), 'merged': w.get('merged_into'),
            'authors': [(a.get('name'), a.get('role'), a.get('dynasty'), a.get('entity_id')) for a in w.get('authors') or [] if isinstance(a, dict)],
            'butu': '【獨撰子目补撰人】' in note, 'dyn': w.get('dynasty'),
            'juan': (w.get('juan_count') or {}).get('number') if isinstance(w.get('juan_count'), dict) else None,
            'cols': cols, 'congshu': '叢書子目' in note,
            'ib': [(x.get('title_info'), x.get('author_info'), x.get('section'), x.get('summary') or '') for x in w.get('indexed_by') or [] if isinstance(x, dict)],
            'rel': [x.get('id') for x in w.get('related_works') or [] if isinstance(x, dict)],
            'nres': len(w.get('resources') or []),
            'note': note[:600]})
    out.append(g)
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('写出', len(out), '组', sum(len(g['works']) for g in out), '条', file=sys.stderr)
