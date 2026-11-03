#!/usr/bin/env python3
"""步3 独立审计：工作区 vs HEAD。每条旧版本关系信息必须能在新写法里找到（或在 ai_note 里），其余字段不变。"""
import json, subprocess, sys, collections

files = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'diff', '--name-only', 'HEAD', '--', 'Book'], text=True).split('\n')
files = [f for f in files if f]
p = subprocess.Popen(['git', 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
def old(path):
    p.stdin.write(f'HEAD:{path}\n'.encode()); p.stdin.flush()
    h = p.stdout.readline().split()
    n = int(h[2]); data = p.stdout.read(n); p.stdout.read(1)
    return json.loads(data)
bad = collections.Counter(); ex = []
def fail(k, f, m=''):
    bad[k] += 1
    if len(ex) < 15: ex.append((k, f[-40:], m))
for f in files:
    o = old(f); n = json.load(open(f, encoding='utf-8'))
    note = n.get('ai_note') or ''
    be = n.get('base_edition') or []
    rb = n.get('related_books') or []
    ol, nl = o.get('lineage') or {}, n.get('lineage') or {}
    # 1 derived_from
    for x in ol.get('derived_from') or []:
        key = 'hypothetical_id' if x['ref_type'] == 'hypothetical' else 'book_id'
        its = [i for i in be if i.get(key) == x['ref']]
        if len(its) != 1: fail('df_missing', f, x['ref']); continue
        i = its[0]
        for k in ('relation', 'confidence', 'evidence'):
            if x.get(k) and i.get(k) != x[k] and x[k] not in note: fail('df_field_' + k, f, str(x[k]))
    # 2 based_on
    bo = (o.get('dating') or {}).get('based_on')
    if bo:
        raw = json.dumps(bo, ensure_ascii=False)
        ok = raw in note or any(i.get('relation') == bo['relation'] for i in be)
        if not ok: fail('bo_lost', f, raw)
        if bo['relation'] and raw not in note and not any(i.get('relation') == bo['relation'] for i in be): fail('bo_rel', f)
    # 3 related_to / related_books
    for x in ol.get('related_to') or []:
        if 'ref' in x:
            if not any(i.get('book_id') == x['ref'] and i.get('relation') == x['relation'] for i in be): fail('rt_ref_lost', f)
        else:
            m = [r for r in rb if r.get('book_id') == x['book_id']]
            if len(m) != 1: fail('rt_lost', f); continue
            for k in ('relation', 'confidence', 'evidence'):
                if x.get(k) and m[0].get(k) != x[k] and x[k] not in note: fail('rt_field_' + k, f)
    for s in o.get('related_books') or []:
        if not any(r.get('book_id') == s for r in rb): fail('rb_lost', f, s)
    if any(not isinstance(r, dict) for r in rb): fail('rb_shape', f)
    # 4 category
    if 'category' in ol:
        c = ol['category']
        if not (n.get('edition_type') == c or f'原 lineage.category：{c}' in note): fail('cat_lost', f, c)
    # 5 old base_edition items preserved (name/book_id/role/source/note)
    for i, oi in enumerate(o.get('base_edition') or []):
        ni = be[i] if i < len(be) else {}
        for k, v in oi.items():
            if ni.get(k) != v: fail('be_changed_' + k, f)
    # 6 other keys unchanged
    skip = {'lineage', 'dating', 'base_edition', 'related_books', 'ai_note', 'edition_type'}
    for k in set(o) | set(n):
        if k not in skip and o.get(k) != n.get(k): fail('other_changed_' + k, f)
    od, nd = dict(o.get('dating') or {}), dict(n.get('dating') or {})
    od.pop('based_on', None)
    if od != nd: fail('dating_other', f)
    ol2 = {k: v for k, v in ol.items() if k not in ('derived_from', 'related_to', 'category')}
    if ol2 != nl: fail('lineage_other', f)
    if not str(n.get('ai_note') or '').startswith(str(o.get('ai_note') or '')): fail('ai_note_prefix', f)
    if o.get('edition_type') and o.get('edition_type') != n.get('edition_type'): fail('et_overwritten', f)
    for k in ('derived_from', 'related_to', 'category'):
        if k in nl: fail('old_left_' + k, f)
    if 'based_on' in nd: fail('old_left_bo', f)
print('files', len(files), 'anomalies', dict(bad))
for e in ex: print(e)
sys.exit(1 if bad else 0)
