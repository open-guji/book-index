#!/usr/bin/env python3
"""国書等日本馆藏线索：Work 漏著者补著者。
    python3 .claude/qa/dedup-kokusho/add_authors.py PLAN.tsv BATCH_DIR [--skip-ids FILE] [--apply]
PLAN.tsv 七列（无表头）：序号、work_id、补、姓名、朝代、责任方式、依据（Work 自身著录原文）。
逐条重验：跟 merged_into 到活 Work；同名（去空白）已在 authors 里的跳过。只在 authors 末尾追加（原有「佚名」／空名占位一并去掉，记入台账），不挂 entity_id
（留给 2.2续／2.3 从 main 重跑覆盖）；revision 升 minor，ai_note 加一行【馆藏线索补著者】。
台账 BATCH_DIR/applied.json（含前置 sha256；回滚＝删去所补 author、revision 退回、删去该行 ai_note）。"""
import argparse, csv, glob, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import jio  # noqa: E402
TODAY = '2026-10-26'
ap = argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('batch')
ap.add_argument('--skip-ids'); ap.add_argument('--apply', action='store_true')
a = ap.parse_args()
sk = {l.split()[0] for l in open(a.skip_ids) if l.strip()} if a.skip_ids else set()
def rel(i):
    g = glob.glob(os.path.join(jio.ROOT, 'Work', i[-3], i[-2], i[-1], i + '-*.json'))
    return os.path.relpath(g[0], jio.ROOT) if g else None
def bump(v):
    try: x, y, _ = (int(t) for t in (v or '1.0.0').split('.')); return '%d.%d.0' % (x, y + 1)
    except Exception: return '1.1.0'
want = {}
for r in csv.reader(open(a.plan), delimiter='\t'):
    if len(r) >= 7 and r[2] == '补' and r[3].strip():
        want.setdefault(r[1], []).append(dict(name=r[3].strip(), dynasty=r[4].strip(), role=r[5].strip() or '撰', basis=r[6].strip()))
done = []; skip = 0
for wid, adds in want.items():
    w = wid
    for _ in range(6):
        p = rel(w)
        if not p: break
        d, fmt = jio.load(p)
        if d.get('merged_into'): w = d['merged_into']; continue
        break
    if not p or d.get('merged_into') or d.get('deleted') or w in sk:
        skip += 1; print('跳过', wid, w); continue
    raw = open(os.path.join(jio.ROOT, p), 'rb').read()
    have = {(x.get('name') or '').replace(' ', '') for x in d.get('authors') or []}
    new = []
    for ad in adds:
        if ad['name'].replace(' ', '') in have: continue
        au = {'name': ad['name'], 'role': ad['role']}
        if ad['dynasty']: au['dynasty'] = ad['dynasty']
        au['role_basis'] = '據本條著錄補（日本館藏本另題此人，逐條覆核）：' + ad['basis']
        new.append(au); have.add(ad['name'].replace(' ', ''))
    if not new: skip += 1; continue
    old = d.get('revision')
    removed = [x for x in d.get('authors') or [] if (x.get('name') or '').strip() in ('', '佚名')]
    d['authors'] = [x for x in d.get('authors') or [] if x not in removed] + new; d['revision'] = bump(old); d['revised_at'] = TODAY
    jio.addnote(d, '【馆藏线索补著者】日本館藏（國書／內閣／NDL）本另題%s，本條著錄亦載，逐條覆核後補入 authors（%s）' % (
        '、'.join('%s（%s）' % (x['name'], x['role']) for x in new), TODAY))
    if a.apply: jio.save(p, d, fmt)
    done.append(dict(id=w, path=p, sha256_before=hashlib.sha256(raw).hexdigest(), revision_before=old, added=new, removed_placeholder=removed))
os.makedirs(a.batch, exist_ok=True)
if a.apply: json.dump(done, open(os.path.join(a.batch, 'applied.json'), 'w'), ensure_ascii=False, indent=1)
print('补著者 Work', len(done), '人次', sum(len(x['added']) for x in done), '跳过', skip, '' if a.apply else '（乾跑）')
