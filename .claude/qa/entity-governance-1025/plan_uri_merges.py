#!/usr/bin/env python3
"""2.1 同 person_uri 的 live 人物 Entity → 并条规格（batch.json）与排除清单。
口径（00 文件 Entity 一节）：同总目 person_uri 为独立证据；再要求 朝代同或相邻、无 CBDB 冲突、
生年不冲突、名相同（或异体字）。其余登记待核，不并。
    python3 plan_uri_merges.py <输出目录>"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import egov, dyn  # noqa: E402

VARIANT_OK = {frozenset(['袁繼咸', '袁繼鹹']), frozenset(['吳騫', '吳鶱'])}   # 已人工核：异体字
PREFIX_OK = {'吳蘭修': '吳蘭', '錢文選': '錢文', '李英華': '李英', '嚴澂': '嚴澂華'}  # 省称／署名多一字，逐条由子 agent 核

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
people = egov.load_people()
recs = egov.scan_authored(('Work',))
nw = collections.Counter(a['entity_id'] for t, rel, d in recs for a in d.get('authors') or [] if isinstance(a, dict) and a.get('entity_id'))
live = {k: v[1] for k, v in people.items() if not v[1].get('merged_into')}
uri = collections.defaultdict(set)
for k, d in live.items():
    for m in egov.uris_of(d): uri[m].add(k)

def score(i):
    d = live[i]; e = d.get('external_ids') or {}
    return (bool(e.get('cbdb_id')), bool(d.get('dates')), nw[i], i)

groups, held = [], []
for u, v in sorted(uri.items()):
    if len(v) < 2: continue
    v = sorted(v); L = [live[i] for i in v]
    reasons = []
    if len({d['external_ids'].get('cbdb_id') for d in L if d.get('external_ids', {}).get('cbdb_id')}) > 1: reasons.append('cbdb冲突')
    births = [d['dates']['birth'] for d in L if (d.get('dates') or {}).get('birth')]
    if births and max(births) - min(births) > 40: reasons.append('生年冲突')
    if len(v) > 2: reasons.append('三成员')
    rels = {dyn.rel(L[a].get('dynasty'), L[b].get('dynasty')) for a in range(len(L)) for b in range(a + 1, len(L))}
    if 'incompat' in rels: reasons.append('朝代不兼容')
    names = [d['primary_name'] for d in L]
    tier = 'A'
    if len(set(names)) > 1:
        if frozenset(names) in VARIANT_OK: tier = 'B'
        elif any(PREFIX_OK.get(n) in names for n in names): tier = 'B'
        else: reasons.append('名不同')
    desc = [{'id': i, 'name': live[i]['primary_name'], 'dynasty': live[i].get('dynasty'), 'dates': live[i].get('dates'),
             'cbdb': (live[i].get('external_ids') or {}).get('cbdb_id'), 'works': nw[i]} for i in v]
    if reasons:
        held.append({'uri': u, 'reasons': reasons, 'members': desc}); continue
    keeper = max(v, key=score); losers = [i for i in v if i != keeper]
    ev = '总目 person_uri %s 相同；%s；朝代 %s；无 CBDB／生年冲突' % (u, '、'.join('%s(%s,%d作)' % (live[i]['primary_name'], live[i].get('dynasty') or '无朝代', nw[i]) for i in v), '/'.join(str(live[i].get('dynasty')) for i in v))
    groups.append({'case_id': 'P2-U-%03d' % (len(groups) + 1), 'type': 'people', 'tier': tier, 'keeper': keeper, 'losers': losers,
                   'cluster_id': 'P2-U-%03d' % len(groups).__add__(1) if False else 'P2-U-%03d' % (len(groups) + 1),
                   'evidence': ev, 'rule': '去重第2部分 2.1：同总目 person_uri（%s档）' % tier, 'why': ev, 'members': desc})
json.dump({'groups': groups}, open(os.path.join(out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(held, open(os.path.join(out, 'held.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('可并', len(groups), 'A', sum(g['tier'] == 'A' for g in groups), 'B', sum(g['tier'] == 'B' for g in groups), '待核', len(held))
