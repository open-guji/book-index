#!/usr/bin/env python3
"""2.1续 第二批：按 ops.tsv 拆混并人物条（改挂／摘作者位、改 Entity 朝代、挪别名）。
    python3 split.py ops.tsv [--apply]
move／unlink 作用于该 Work 本身及 work_id 指它的 Book 上、entity_id＝from 的作者位；每个改动记录写 ai_note。
输出 split-report.json（逐处原值），供回滚。"""
import argparse, collections, csv, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [QA, os.path.join(QA, 'entity-governance-1025')]
import jio, egov  # noqa: E402

TAG = '2026-10-26 去重 2.1续 拆混并'
ap = argparse.ArgumentParser(); ap.add_argument('ops'); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
ops = [r for r in csv.reader(open(a.ops, encoding='utf-8'), delimiter='\t') if r and not r[0].startswith('#')]
print('ops %d' % len(ops))
people = egov.load_people()
recs = egov.scan_authored()
byeid = collections.defaultdict(list)
for t, rel, d in recs:
    for x in d.get('authors') or []:
        if isinstance(x, dict) and x.get('entity_id'):
            byeid[x['entity_id']].append((rel, d))
report, problems = [], []
for op, key, frm, to, why in ops:
    if op in ('move', 'unlink'):
        assert frm in people and not people[frm][1].get('merged_into'), frm
        if op == 'move':
            assert to in people and not people[to][1].get('merged_into'), to
        hits = []
        seen = set()
        for rel, d in byeid.get(frm, []):
            if rel in seen: continue
            if d['id'] == key or d.get('work_id') == key:
                seen.add(rel); hits.append(rel)
        if not any(os.path.basename(r).startswith(key) for r in hits):
            problems.append((op, key, frm, 'Work 本身未见作者位指 from')); continue
        for rel in hits:
            d, fmt = jio.load(rel)
            n = 0
            for x in d.get('authors') or []:
                if isinstance(x, dict) and x.get('entity_id') == frm:
                    report.append({'op': op, 'record': d['id'], 'path': rel, 'name': x.get('name'), 'from': frm, 'to': to or None, 'why': why})
                    if op == 'move': x['entity_id'] = to
                    else: del x['entity_id']
                    n += 1
            if n and a.apply:
                if op == 'move':
                    note = '%s：作者位「%s」由 %s（%s）改繫 %s（%s）——%s' % (TAG, report[-1]['name'], frm, people[frm][1].get('dynasty') or '', to, people[to][1].get('dynasty') or '', why)
                else:
                    note = '%s：作者位「%s」原繫 %s，摘去 entity_id——%s' % (TAG, report[-1]['name'], frm, why)
                jio.addnote(d, note); jio.save(rel, d, fmt)
    elif op == 'set':
        rel, _ = people[frm]; d, fmt = jio.load(rel)
        report.append({'op': op, 'record': frm, 'path': rel, 'field': key, 'old': d.get(key), 'new': to, 'why': why})
        if a.apply:
            d[key] = to
            if key == 'dynasty':
                d['dynasty_basis'] = '%s：%s' % (TAG, why)
            jio.addnote(d, '%s：%s 改為「%s」（原「%s」）——%s' % (TAG, key, to, report[-1]['old'], why)); jio.save(rel, d, fmt)
    elif op == 'alt':
        names = key.split(',')
        rf, _ = people[frm]; rt, _ = people[to]
        df, ff = jio.load(rf); dt, ft = jio.load(rt)
        moved = [x for x in df.get('alt_names') or [] if isinstance(x, dict) and x.get('name') in names]
        report.append({'op': op, 'record': frm, 'to': to, 'moved': moved, 'why': why})
        if a.apply:
            df['alt_names'] = [x for x in df.get('alt_names') or [] if x not in moved]
            if not df['alt_names']: del df['alt_names']
            have = {x.get('name') for x in dt.get('alt_names') or []}
            dt.setdefault('alt_names', []).extend(x for x in moved if x.get('name') not in have)
            jio.addnote(df, '%s：別名 %s 挪歸 %s——%s' % (TAG, '、'.join(names), to, why))
            jio.addnote(dt, '%s：自 %s 挪入別名 %s——%s' % (TAG, frm, '、'.join(names), why))
            jio.save(rf, df, ff); jio.save(rt, dt, ft)
json.dump({'report': report, 'problems': problems}, open(os.path.join(HERE, 'split-report%s.json' % ('' if a.apply else '-dry')), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('%s：作者位改动 %d 处（move %d、unlink %d），Entity 字段 %d，别名挪 %d；问题 %d' % ('已写' if a.apply else '乾跑',
      sum(1 for r in report if r['op'] in ('move', 'unlink')), sum(1 for r in report if r['op'] == 'move'), sum(1 for r in report if r['op'] == 'unlink'),
      sum(1 for r in report if r['op'] == 'set'), sum(1 for r in report if r['op'] == 'alt'), len(problems)))
for p in problems: print('  ', p)
