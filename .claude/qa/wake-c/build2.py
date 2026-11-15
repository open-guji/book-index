#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""車道 wake-c 第二輪：和刻本專項新建線。用法：build2.py [--apply]
數據在 items2.py（NEW 列表）。每條：(work_id, title, edition, edition_type, dating, prov, sources, desc)
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa')); sys.path.insert(0, HERE)
import mintid
from items2 import NEW
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'; TAG = '和刻本日本馆藏专项第二輪（車道 wake-c，2026-11-15）'
ids = mintid.mint('Book', 'wake-c', len(NEW)) if APPLY else ['dryb%06d' % i for i in range(len(NEW))]
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
changed = {}; rows = []
for (wid, title, ed, et, dt, provs, srcs, desc), bid in zip(NEW, ids):
    d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': et, 'dating': dt}
    d['provenance'] = [dict([('institution', i)] + ([('call_number', c)] if c else []) + [('source', s)]) for i, c, s in provs]
    d['description'] = {'text': desc, 'sources': ['%s %s' % (n, u) for _, n, u in srcs]}
    d['sources'] = [{'id': i, 'name': n, 'type': 'url', 'details': u} for i, n, u in srcs]
    d['ai_note'] = '%s：新建。據 NDL Search／CiNii Books 著錄的日本刊本，庫內該 Work 下無對應版本（已按 Work 下全部 Book 之版本／刊年／刊者查重）；題名、刊者、年代、館藏均錄自目錄頁，未核原書。' % TAG
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
    changed['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, title, safe)] = d
    rows.append((bid, title, '新建', '; '.join(p[0] for p in provs), srcs[0][2], wid))
print('changed files:', len(changed), ' 新建:', len(NEW))
if not APPLY: sys.exit(0)
for p, d in changed.items():
    os.makedirs(os.path.join(ROOT, os.path.dirname(p)), exist_ok=True)
    open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(jd(d))
json.dump(list(changed), open(os.path.join(HERE, 'changed2.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(rows, open(os.path.join(HERE, 'rows2.json'), 'w'), ensure_ascii=False, indent=1)
print('已寫')
