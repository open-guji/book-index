#!/usr/bin/env python3
"""2.1续 人物同名组「可并」组 → batch.json（在最新 main 上重算）。
    python3 plan.py <判定表.tsv> <输出目录>
判定表来自 ai-team 去重方案目录 2.1续-人物同名组判定/判定表.tsv（末列「执行建议」）。
只取执行建议以「可并」开头的行；同组同簇字母的成员并成一人。成员已成墓碑的按 merged_into 解析到 live 条。
keeper：有 cbdb_id ＞ 字段多（朝代、生卒、籍贯、别名、wikidata 等）＞ 作者位引用多 ＞ id 字典序小（旧条）。
另写 review.tsv：每组成员的朝代、生卒、籍贯、cbdb、引用书名，以及字段冲突提示，供人工过目。"""
import collections, csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'entity-governance-1025'))
import egov  # noqa: E402

tsv, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
rows = list(csv.DictReader(open(tsv, encoding='utf-8'), delimiter='\t'))
assert rows, '判定表 0 行'
print('判定表 %d 行' % len(rows))
people = egov.load_people()
recs = egov.scan_authored()
refs = collections.defaultdict(list)   # eid -> [(id, title, slot dynasty, role)]
for t, rel, d in recs:
    for a in d.get('authors') or []:
        if isinstance(a, dict) and a.get('entity_id'):
            refs[a['entity_id']].append((d['id'], d.get('title') or d.get('primary_name') or '', a.get('dynasty') or '', a.get('role') or ''))

clusters = collections.OrderedDict()
for r in rows:
    if r['执行建议'].startswith('可并'):
        clusters.setdefault((r['主名'], r['簇']), []).append(r)


def score(eid):
    d = people[eid][1]
    ext = d.get('external_ids') or {}
    nf = sum(1 for k in ('dynasty', 'dates', 'native_place', 'alt_names', 'description') if d.get(k))
    nf += sum(1 for k in ('wikidata_id', 'viaf_id') if ext.get(k))
    return (1 if ext.get('cbdb_id') else 0, nf, len(refs.get(eid, ())), [-ord(c) for c in eid])


groups, review, skipped = [], [], []
for (name, cl), rs in clusters.items():
    orig = [r['entity_id'] for r in rs]
    live = []
    for e in orig:
        if e not in people:
            skipped.append((name, e, '不存在')); continue
        x = egov.resolve(people, e)
        if x not in live:
            live.append(x)
    if len(live) < 2:
        skipped.append((name, ','.join(orig), '已同为 %s' % live)); continue
    live.sort(key=score, reverse=True)
    keeper, losers = live[0], live[1:]
    ev = rs[0]['证据']
    cid = '2.1续-%s-%s' % (name, cl)
    flags = []
    for f in ('dynasty', 'native_place'):
        vals = {people[e][1].get(f) for e in live if people[e][1].get(f)}
        if len(vals) > 1: flags.append('%s不一:%s' % (f, '/'.join(sorted(vals))))
    cb = {(people[e][1].get('external_ids') or {}).get('cbdb_id') for e in live} - {None, ''}
    if len(cb) > 1: flags.append('cbdb不一:%s' % '/'.join(map(str, sorted(cb))))
    for f in ('birth', 'death'):
        vals = {(people[e][1].get('dates') or {}).get(f) for e in live} - {None, ''}
        if len(vals) > 1: flags.append('%s不一:%s' % (f, '/'.join(map(str, sorted(vals, key=str)))))
    groups.append({'cluster_id': cid, 'type': 'people', 'keeper': keeper, 'losers': losers, 'evidence': ev,
                   'rule': '去重方案 2.1续 人物同名组判定（%s／把握%s；%s）' % (rs[0]['组判定'], rs[0]['把握'], rs[0]['执行建议']),
                   'why': ev, 'flags': flags})
    for e in live:
        d = people[e][1]
        review.append([cid, '保留' if e == keeper else '并入', e, d.get('dynasty') or '',
                       json.dumps(d.get('dates') or {}, ensure_ascii=False) if d.get('dates') else '',
                       d.get('native_place') or '', str((d.get('external_ids') or {}).get('cbdb_id') or ''),
                       '；'.join('%s(%s%s)' % (t, dy, ro) for _, t, dy, ro in refs.get(e, ())[:8]),
                       '｜'.join(flags), ev])
json.dump({'groups': groups}, open(os.path.join(outdir, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(os.path.join(outdir, 'review.tsv'), 'w', encoding='utf-8') as f:
    f.write('\t'.join(['组', '动作', 'entity_id', '朝代', '生卒', '籍贯', 'cbdb', '作者位(前8)', '冲突', '证据']) + '\n')
    for r in review: f.write('\t'.join(x.replace('\t', ' ').replace('\n', ' ') for x in r) + '\n')
with open(os.path.join(outdir, 'skipped.tsv'), 'w', encoding='utf-8') as f:
    for s in skipped: f.write('\t'.join(s) + '\n')
print('簇 %d → 待并组 %d（被并 %d 条），跳过 %d；有冲突提示 %d 组' % (
    len(clusters), len(groups), sum(len(g['losers']) for g in groups), len(skipped), sum(1 for g in groups if g['flags'])))
