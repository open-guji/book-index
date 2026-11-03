#!/usr/bin/env python3
"""S1 阶段 3：Work／Collection 一遍清洗（schema 审查 2026-11-02）。默认只报告，--apply 写入。
Work：删顶层空容器（''、[]、{}）；删 updated_at。review 不动（用户 11-02 定）。
Collection：同上；publisher／publish_year 并入 publication_info.publisher／.year（无则补，冲突则保留 publication_info 并报告）；
total_works／total_volumes 删（仅当与 count.zhong／count.ce 相等或 count 对应项为 null/缺且不丢信息时迁入 count，否则报告不动）；
editors 并入 authors 末尾（去重）；sections 删；holder 不动。"""
import json, glob, sys, collections as C
R = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '.'
APPLY = '--apply' in sys.argv
cnt = C.Counter(); notes = []
def dump(d, nl): return json.dumps(d, ensure_ascii=False, indent=2) + nl
def clean(d, typ):
    ch = []
    for k in [k for k, v in d.items() if v in ('', [], {}) and not isinstance(v, (int, float, bool))]:
        if k in ('review',): continue
        del d[k]; ch.append('empty:' + k)
    if '--updated-at' in sys.argv and 'updated_at' in d: del d['updated_at']; ch.append('updated_at')
    if typ == 'Collection':
        pi = d.get('publication_info')
        for top, sub in (('publisher', 'publisher'), ('publish_year', 'year')):
            if top in d:
                if pi is None: pi = d['publication_info'] = {}
                if sub not in pi: pi[sub] = d.pop(top); ch.append('pub:' + top)
                elif pi[sub] == d[top]: del d[top]; ch.append('pub_dup:' + top)
                else: notes.append((d['id'], top, d[top], pi[sub]))
        c = d.get('count')
        for top, sub in (('total_works', 'zhong'), ('total_volumes', 'ce')):
            if top in d:
                if c is None: notes.append((d['id'], top, 'no count')); continue
                if c.get(sub) is None: c[sub] = d.pop(top); ch.append('mv:' + top)
                elif c[sub] == d[top]: del d[top]; ch.append('del:' + top)
                else: notes.append((d['id'], top, d[top], c[sub]))
        if 'editors' in d:
            au = d.setdefault('authors', [])
            have = {(a['name'], a['role']) for a in au}
            for e in d['editors']:
                if (e['name'], e['role']) not in have: au.append(e)
            del d['editors']; ch.append('editors')
        if 'sections' in d: del d['sections']; ch.append('sections')
    return ch
for typ in ('Work', 'Collection'):
    for p in glob.iglob(f'{R}/{typ}/*/*/*/*.json'):
        t = open(p, encoding='utf-8').read(); d = json.loads(t)
        nl = '\n' if t.endswith('\n') else ''
        if json.dumps(d, ensure_ascii=False, indent=2) + nl != t: cnt['fmt_skip'] += 1; continue
        ch = clean(d, typ)
        if not ch: continue
        cnt[typ] += 1
        for c in ch: cnt[typ + ':' + c] += 1
        if APPLY: open(p, 'w', encoding='utf-8').write(dump(d, nl))
for k, v in sorted(cnt.items()): print(k, v)
for n in notes: print('NOTE', n)
