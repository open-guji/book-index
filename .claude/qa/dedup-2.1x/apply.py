#!/usr/bin/env python3
"""2.1续 人物同名组并条：按 plan.py 产出的 batch.json 并人物 Entity，被并条写墓碑、作者位改指 keeper，写 merges.json。
    python3 apply.py <batch.json> [--apply] [--only N] [--skip N]
在 entity_merge.py（alt_names、external_ids 补缺、merged_in、墓碑）之外补两件事：
  1. keeper 缺的朝代／period／生卒／籍贯（连同各自 basis）从被并条补上，description.sources 取并集（总目 person_uri 不丢）；
     被并条的 cbdb_id 与 keeper 不同时写进 merged_in.why（CBDB 一人两号，留给 2.4）。
  2. 判定表证据栏要求「先拆」的组：混挂的他人作品先摘掉 entity_id（作者名保留、记 ai_note），再并（见 SPECIAL）。"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(QA, 'entity-governance-1025'), os.path.join(QA, 'dedup-confirmed-163'), QA]
import egov, entity_merge, apply_batch, jio  # noqa: E402

# 组 → 特别处理。keeper：改定 keeper；dynasty：并后 keeper 朝代改为此值（判定证据明说原朝代误）；
# unlink：[(work_id, 原 entity_id, 理由)]，并前把该 Work 作者位上这个 entity_id 摘掉。
SPECIAL = {
    '2.1续-沈璟-A': {'unlink': [('d59fsgg0f3t0', 'hixi23ur76rn', '《雲巢詩鈔》為清代同名沈璟（CBDB 79545，卒 1816）之作，非明吳江沈璟')]},
    '2.1续-顧乃德-A': {'keeper': 'hixi5n900q52',
                     'unlink': [('d59fsevbwsuc', 'hixi8u61q0h3', '《未央硯室詩卷》總目題名行作清人，非明代通書編者顧乃德')]},
    '2.1续-甘霖-A': {'keeper': 'hixi5icd9geo',
                   'unlink': [('d59fsg1w8rgg', 'hixi8u655maa', '《吟秀書屋詩》總目作清甘霖（道光《章門萍約詩選》本），非明代術數家甘霖')]},
    '2.1续-俞泰-A': {'unlink': [('d59fsce1eyv5', 'hixi8u5rf6j4', '《滌煙樓集》總目作清俞泰撰、康熙刻本，疑清代同名者，非明無錫俞泰（字國昌）')]},
    '2.1续-劉孝孫-A': {'unlink': [('d59f28l19q10', 'hixhd2h9bhc4', '隋開皇曆為隋曆家劉孝孫（廣平人）所造，非唐初荊州文士劉孝孫（cbdb 92625）'),
                                 ('d59f28j6gxse', 'hixhd2h9bhc4', '隋開皇曆為隋曆家劉孝孫（廣平人）所造，非唐初荊州文士劉孝孫（cbdb 92625）'),
                                 ('d59f9c1evojr', 'hixhd2h9bhc4', '劉孝孫曆法屬隋曆家劉孝孫，非唐初荊州文士劉孝孫（cbdb 92625）')]},
    '2.1续-江朝宗-A': {'dynasty': '中華民國'},
    '2.1续-武陵逸史-A': {'dynasty': '明'},
    '2.1续-陳乃乾-A': {'dynasty': '中華民國'},
    # 线索组（2.2续-丙、3c 等交来，名不同或研究判存疑而本串复核可并）
    '线索-李寶洤': {'alt_type': '訛名'},
    '线索-吳修祜': {'alt_type': '訛名'},
    '线索-俞樾': {'alt_type': '訛名'},
    '线索-宋子安': {'alt_type': '訛名'},
    '线索-傅恆': {'alt_type': '異寫'},
    '线索-吳曾祺': {'noalt': True, 'slotfix': {'name': '吳曾祺', 'dynasty': '清'}},
    '线索-郭璞': {'noalt': True, 'slotfix': {'name': '郭璞', 'role': '注'}},
}
FILL = [('dynasty', ('dynasty_basis',)), ('period', ('period_basis',)), ('dates', ()),
        ('native_place', ('native_place_entity_id', 'native_place_basis'))]
NOTE_TAG = '2026-10-26 去重 2.1续'

ap = argparse.ArgumentParser(); ap.add_argument('batch'); ap.add_argument('--apply', action='store_true')
ap.add_argument('--only', type=int); ap.add_argument('--skip', type=int, default=0)
a = ap.parse_args()
apply_batch.BY = 'A11-去重2.1续'
spec = json.load(open(a.batch, encoding='utf-8'))
groups = spec['groups'][a.skip:]
groups = groups[:a.only] if a.only else groups
print('本次 %d 组' % len(groups))
assert groups
refmap = egov.build_ref_map(egov.scan_authored())
egov.patch_entity_merge(refmap)


def find_work(wid):
    return apply_batch.path_of('work', wid)


ledger, report = [], []
for g in groups:
    sp = SPECIAL.get(g['cluster_id'], {})
    members = [g['keeper']] + g['losers']
    if sp.get('keeper'):
        assert sp['keeper'] in members
        g['keeper'] = sp['keeper']; g['losers'] = [m for m in members if m != sp['keeper']]
    pre = []
    for i in [g['keeper']] + g['losers']:
        rel = apply_batch.path_of('people', i); sha, _ = apply_batch.base_sha(rel)
        pre.append({'id': i, 'path': rel, 'sha256': sha})
    krel = apply_batch.path_of('people', g['keeper'])
    keeper, kfmt = jio.load(krel)
    kcb = (keeper.get('external_ids') or {}).get('cbdb_id')
    filled, notes, unlinked = [], [], []
    for wid, eid, why in sp.get('unlink', []):
        rel = find_work(wid); d, fmt = jio.load(rel)
        hit = [x for x in d.get('authors') or [] if isinstance(x, dict) and x.get('entity_id') == eid]
        assert len(hit) == 1, (wid, eid, hit)
        unlinked.append({'work': wid, 'entity_id': eid, 'name': hit[0].get('name'), 'why': why})
        if a.apply:
            del hit[0]['entity_id']
            jio.addnote(d, '%s：作者位「%s」原繫 %s，摘去 entity_id——%s（人物同名組判定，見 .claude/qa/dedup-2.1x/）。' % (NOTE_TAG, hit[0].get('name'), eid, why))
            jio.save(rel, d, fmt)
            refmap[eid].discard(rel)
    for l in g['losers']:
        ld, _ = jio.load(apply_batch.path_of('people', l))
        for f, extra in FILL:
            if not keeper.get(f) and ld.get(f):
                keeper[f] = ld[f]
                for x in extra:
                    if ld.get(x): keeper[x] = ld[x]
                filled.append('%s←%s' % (f, l))
        ks = keeper.setdefault('description', {}).setdefault('sources', []) if (ld.get('description') or {}).get('sources') else None
        if ks is not None:
            have = {json.dumps(s, sort_keys=True, ensure_ascii=False) for s in ks}
            for s in ld['description']['sources']:
                if json.dumps(s, sort_keys=True, ensure_ascii=False) not in have:
                    ks.append(s); filled.append('description.sources←%s' % l)
        lcb = (ld.get('external_ids') or {}).get('cbdb_id')
        if lcb and kcb and lcb != kcb:
            notes.append('被并条 %s 另有 cbdb_id %s（keeper 為 %s；CBDB 一人兩號或誤配，待 2.4 覆核）' % (l, lcb, kcb))
    for l in g['losers']:
        ld, _ = jio.load(apply_batch.path_of('people', l))
        ln = ld.get('primary_name')
        names = {keeper.get('primary_name')} | {x.get('name') for x in keeper.get('alt_names') or [] if isinstance(x, dict)}
        if sp.get('alt_type') and ln not in names:
            keeper.setdefault('alt_names', []).append({'name': ln, 'type': sp['alt_type'], 'note': '并入重出人物条（%s）；见 %s' % (l, g['cluster_id'])})
            filled.append('alt_names %s(%s)' % (ln, sp['alt_type']))
        if sp.get('slotfix'):
            for rel in sorted(refmap.get(l, ())):
                d, fmt = jio.load(rel)
                for x in d.get('authors') or []:
                    if isinstance(x, dict) and x.get('entity_id') == l:
                        unlinked.append({'work': d['id'], 'entity_id': l, 'name': x.get('name'), 'slotfix': sp['slotfix']})
                        if a.apply:
                            old = {k: x.get(k) for k in sp['slotfix']}
                            x.update(sp['slotfix'])
                            jio.addnote(d, '%s：作者位 %s 係切分之誤，改為 %s（人物同名組判定，見 .claude/qa/dedup-2.1x/）。' % (NOTE_TAG, json.dumps(old, ensure_ascii=False), json.dumps(sp['slotfix'], ensure_ascii=False)))
                if a.apply:
                    jio.save(rel, d, fmt)
    if sp.get('dynasty'):
        if keeper.get('dynasty') != sp['dynasty']:
            filled.append('dynasty %s→%s' % (keeper.get('dynasty'), sp['dynasty']))
            keeper['dynasty'] = sp['dynasty']
            keeper['dynasty_basis'] = '%s：同名組判定（%s）' % (NOTE_TAG, g['evidence'][:80])
    if filled:
        jio.addnote(keeper, '%s：並入同人重出條 %s，補入／訂正：%s。' % (NOTE_TAG, '、'.join(g['losers']), '；'.join(filled)))
    why = g['why'] + ('；' + '；'.join(notes) if notes else '')
    if a.apply:
        jio.save(krel, keeper, kfmt)
        g2 = dict(g, why=why)
        if sp.get('noalt'):
            for l in g['losers']:
                entity_merge.merge(l, g['keeper'], reason=why, rule=g['rule'], date=apply_batch.TODAY, by=apply_batch.BY)
        else:
            apply_batch.merge_people(g2, True)
    report.append({'cluster_id': g['cluster_id'], 'keeper': g['keeper'], 'losers': g['losers'], 'filled': filled,
                   'unlinked': unlinked, 'cbdb_notes': notes,
                   'redirect': {l: sorted(refmap.get(l, ())) for l in g['losers']}})
    ledger.append({'cluster_id': g['cluster_id'], 'type': 'people', 'keeper': g['keeper'], 'losers': g['losers'],
                   'evidence': g['evidence'], 'rule': g['rule'], 'preconditions': pre, 'retained_alternatives': [],
                   'classification_decisions': [], 'dropped_author_entities': unlinked, 'loser_original_notes': {}})

out = os.path.dirname(os.path.abspath(a.batch))
tag = '' if not (a.only or a.skip) else '-%d-%d' % (a.skip, a.skip + len(groups))
json.dump(report, open(os.path.join(out, 'report%s%s.json' % ('' if a.apply else '-dry', tag)), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if a.apply:
    base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=egov.ROOT, text=True).strip()
    json.dump({'base': base, 'merges': ledger}, open(os.path.join(out, 'merges%s.json' % tag), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('%s %d 组，被并 %d 条，补字段 %d 组，摘作者位 %d，cbdb 两号 %d 组' % (
    '已并' if a.apply else '乾跑', len(report), sum(len(r['losers']) for r in report), sum(1 for r in report if r['filled']),
    sum(len(r['unlinked']) for r in report), sum(1 for r in report if r['cbdb_notes'])))
