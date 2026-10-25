#!/usr/bin/env python3
"""活记录引用墓碑之机械收口（去重方案部分 7b；规则 3：引用全改写）。乾跑默认，--apply 才写。

    python3 .claude/qa/fix_tomb_refs.py [--apply]

改写处：Book／Collection.work_id、*.contained_in、Work.related_works、promotions 的 production_id、
墓碑之 merged_into（二跳链改指链末）。一律顺 merged_into 走到链末活条；链末悬空／成环、或改后自指者跳过并报出。
**不改**：分类成员行（keeper 只挂第一个节点，须按分类互斥登记人工处理）、并条账、indexed_by 之 in_note_of。
原文件若不能按 indent=2 无损往返则跳过并报出（同 fix_draft.py）。
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import backrefs  # noqa: E402

ROOT = backrefs.ROOT
apply = '--apply' in sys.argv
tomb, path, live = {}, {}, set()
for t, p, d in backrefs.iter_records(ROOT):
    path[d['id']] = p
    if d.get('merged_into'):
        tomb[d['id']] = d['merged_into']
    else:
        live.add(d['id'])
print('载入 墓碑 %d 活条 %d' % (len(tomb), len(live)))
if not tomb or not live:
    sys.exit('载入为 0')


def final(i):
    seen = {i}
    while i in tomb:
        i = tomb[i]
        if i in seen:
            return None
        seen.add(i)
    return i if i in live else None


def fix(rid, cur, where):
    end = final(cur)
    if end is None or end == rid:
        print('跳过', where, rid, cur, '->', end or '链末悬空／成环')
        return cur
    print(where, rid, cur, '->', end)
    return end


def save(p, d, raw):
    if apply:
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))


files = 0
moves = []   # (存放側 id, 關係項)
for rid, p in sorted(path.items()):
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    before = json.dumps(d, ensure_ascii=False, sort_keys=True)
    if rid in tomb:
        if tomb[rid] in tomb:
            d['merged_into'] = fix(rid, tomb[rid], 'merged_into')
    else:
        if isinstance(d.get('work_id'), str) and d['work_id'] in tomb:
            d['work_id'] = fix(rid, d['work_id'], '%s.work_id' % d.get('type'))
        ci = d.get('contained_in')
        for c in (ci if isinstance(ci, list) else []):
            if isinstance(c, dict) and c.get('id') in tomb:
                c['id'] = fix(rid, c['id'], 'contained_in')
        keep = []
        for r in d.get('related_works') or []:
            if isinstance(r, dict) and r.get('id') in tomb:
                r['id'] = fix(rid, r['id'], 'related_works')
                if r['id'] in live and r['id'] < rid:   # 對稱關係存小 id 側（V07）：挪到對方檔
                    moves.append((r['id'], dict(r, id=rid)))
                    continue
            keep.append(r)
        if 'related_works' in d and len(keep) != len(d['related_works']):
            if keep:
                d['related_works'] = keep
            else:
                del d['related_works']
    if json.dumps(d, ensure_ascii=False, sort_keys=True) != before:
        if json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else '') != raw:
            print('跳过(格式不可无损往返):', p)
            continue
        files += 1
        save(p, d, raw)

for rid, r in moves:
    p = path[rid]
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    rel = d.setdefault('related_works', [])
    if any(isinstance(x, dict) and x.get('id') == r['id'] for x in rel):
        print('related_works 已有', rid, '->', r['id'])
        if not apply:
            continue
    else:
        print('related_works 挪至小 id 側', rid, '->', r['id'])
        rel.append(r)
    files += 1
    save(p, d, raw)

for p in sorted(glob.glob(os.path.join(ROOT, 'promotions/*.json'))):
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    n = 0
    for k, v in d['promotions'].items():
        if v.get('production_id') in tomb:
            new = fix(k, v['production_id'], 'promotions')
            n += new != v['production_id']
            v['production_id'] = new
    if n:
        if json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else '') != raw:
            print('跳过(格式不可无损往返):', p)
            continue
        files += 1
        save(p, d, raw)
print('%s 文件 %d' % ('已写' if apply else '乾跑', files))
