#!/usr/bin/env python3
"""people.relations[] 跨记录检查（2026-11-01，A12）。
用法：python3 .claude/qa/check_relations.py [仓根]
查：type 在枚举内；entity_id 存在、是 people、未被并/退役、不是自己；同一 (entity_id,type) 不重复；
对称（甲有 {type:T, 乙} 则乙有 {type:逆称(T), 甲}）；sources 项是对象。
印出「扫 N 檔、含 relations M 檔、关系项 K」，防扫 0 文件假绿。有错退出码 1。"""
import json, os, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
INV = {'父': '子', '子': '父', '祖': '孫', '孫': '祖', '曾祖': '曾孫', '曾孫': '曾祖', '兄': '弟', '弟': '兄', '叔伯': '姪', '姪': '叔伯', '師': '弟子', '弟子': '師'}
recs = {}
scanned = 0
for r, _, fs in os.walk(os.path.join(ROOT, 'Entity')):
    for f in fs:
        if not f.endswith('.json'): continue
        scanned += 1
        try: d = json.load(open(os.path.join(r, f), encoding='utf-8'))
        except Exception: continue
        recs[d.get('id')] = d
errs = []; nfile = 0; nitem = 0
for i, d in recs.items():
    rl = d.get('relations')
    if rl is None: continue
    nfile += 1
    if d.get('subtype') != 'people': errs.append((i, '非 people 不得有 relations')); continue
    seen = set()
    for x in rl:
        nitem += 1
        t, e = x.get('type'), x.get('entity_id')
        if t not in INV: errs.append((i, 'type 不在枚举：%r' % t)); continue
        if e == i: errs.append((i, '指向自己')); continue
        o = recs.get(e)
        if o is None: errs.append((i, '目标不存在 %s' % e)); continue
        if o.get('subtype') != 'people': errs.append((i, '目标不是 people %s' % e)); continue
        if o.get('merged_into') or o.get('retired'): errs.append((i, '目标是墓碑／退役 %s' % e)); continue
        if (e, t) in seen: errs.append((i, '重复项 %s %s' % (t, e))); continue
        seen.add((e, t))
        if not any(y.get('entity_id') == i and y.get('type') == INV[t] for y in (o.get('relations') or [])):
            errs.append((i, '缺对称项：%s 应有 {%s, %s}' % (e, INV[t], i)))
        for s in x.get('sources', []):
            if not isinstance(s, dict): errs.append((i, 'sources 项须为对象'))
print('扫 %d 檔、含 relations %d 檔、关系项 %d；错误 %d' % (scanned, nfile, nitem, len(errs)))
for e in errs[:30]: print(' ', e)
sys.exit(1 if errs else 0)
