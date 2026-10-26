#!/usr/bin/env python3
"""獨撰子目补撰人：执行。
    python3 .claude/qa/dedup-duzhuan/apply.py PLAN.json BATCH_DIR [--ids FILE] [--skip-ids FILE] [--start S --count N] [--apply]
逐条重验：Work 存在、非墓碑、authors 仍空、entity 仍是活人物。只写 authors（一条）、revision 升 minor、revised_at、ai_note 加一行。
台账 BATCH_DIR/applied.json（含前置 sha256，回滚＝authors 置空、revision 退回、删去 ai_note 该行）。"""
import argparse, glob, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import jio  # noqa: E402
TODAY = '2026-10-26'
ap = argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('batch')
ap.add_argument('--ids'); ap.add_argument('--skip-ids'); ap.add_argument('--start', type=int, default=0); ap.add_argument('--count', type=int)
ap.add_argument('--apply', action='store_true')
a = ap.parse_args()
plan = json.load(open(a.plan))
if a.ids:
    want = {l.split()[0] for l in open(a.ids) if l.strip()}; plan = [x for x in plan if x['id'] in want]
if a.skip_ids:
    sk = {l.split()[0] for l in open(a.skip_ids) if l.strip()}; plan = [x for x in plan if x['id'] not in sk]
plan = plan[a.start:a.start + a.count if a.count else None]
live = set()
for f in glob.glob(os.path.join(jio.ROOT, 'Entity', '*', '*', '*', '*.json')):
    d = json.load(open(f))
    if d.get('subtype') == 'people' and not d.get('merged_into'): live.add(d['id'])
print('载入人物 Entity', len(live), '计划条目', len(plan), file=sys.stderr)
assert live and plan
def bump(v):
    try: x, y, _ = (int(t) for t in (v or '1.0.0').split('.')); return '%d.%d.0' % (x, y + 1)
    except Exception: return '1.1.0'
done = []; skip = 0
for it in plan:
    p = os.path.join(jio.ROOT, it['path'])
    if not os.path.exists(p): skip += 1; print('跳过（不存在）', it['path']); continue
    raw = open(p, 'rb').read(); d, fmt = jio.load(it['path'])
    if d.get('merged_into') or any((x.get('name') or '').strip() for x in d.get('authors') or []):
        skip += 1; print('跳过（已并或已有撰人）', it['path']); continue
    au = dict(it['author'])
    if not au.get('dynasty'): au.pop('dynasty', None)
    eid = it.get('entity_id') if it.get('entity_id') in live else None
    if eid: au['entity_id'] = eid
    au['role_basis'] = '總目叢書部獨撰類子目不另題撰人，據所屬叢書《%s》（%s）撰者著錄' % (it['col_title'], it['col_id']) + ('；責任方式據題名括注' if au['role'] != '撰' else '')
    if it.get('reviewed'):
        cn = [x.get('name') for x in json.load(open(os.path.join(jio.ROOT, it['col_path']))).get('authors') or [] if x.get('name')]
        if au['name'] not in cn and len(cn) == 1:
            au['original_name'] = cn[0]; au['name_basis'] = '叢書著錄作「%s」，逐條覆核改正' % cn[0]
        au['role_basis'] = '總目叢書部獨撰類子目不另題撰人；據所屬叢書《%s》（%s）責任者著錄並逐條覆核：%s' % (it['col_title'], it['col_id'], it['reviewed'])
    d['authors'] = [au]
    old = d.get('revision')
    d['revision'] = bump(old); d['revised_at'] = TODAY
    jio.addnote(d, '【獨撰子目补撰人】據所屬叢書《%s》（%s）撰者%s%s補 authors%s（%s）' % (
        it['col_title'], it['col_id'], au['name'], '（%s）' % au['dynasty'] if au.get('dynasty') else '',
        ('；entity_id 依據：' + it['entity_basis'] if eid else '') + ('；逐條覆核' if it.get('reviewed') else ''), TODAY))
    if a.apply: jio.save(it['path'], d, fmt)
    done.append(dict(id=it['id'], path=it['path'], sha256_before=hashlib.sha256(raw).hexdigest(), revision_before=old,
                     author=au, col_id=it['col_id'], col_title=it['col_title'], entity_basis=it.get('entity_basis') if eid else None))
os.makedirs(a.batch, exist_ok=True)
if a.apply: json.dump(done, open(os.path.join(a.batch, 'applied.json'), 'w'), ensure_ascii=False, indent=1)
print('补撰人', len(done), '挂 entity', sum(1 for x in done if x['author'].get('entity_id')), '跳过', skip, '' if a.apply else '（乾跑）')
