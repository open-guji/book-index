#!/usr/bin/env python3
"""2.2 补挂：把已复核判 SAME 的作者位挂上现成人物 Entity（只设 authors[slot].entity_id，别的不动）。
    python3 apply_attach.py <attach-list.json> [--apply]   # 条目 {path,slot,name,entity_id,...}
前提逐条重验：作者位名未变、尚无 entity_id、Entity 存在且非墓碑。--out 写出实际挂上的清单。"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import jio  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('lst'); ap.add_argument('--apply', action='store_true'); ap.add_argument('--out')
a = ap.parse_args()
items = json.load(open(a.lst, encoding='utf-8'))
import glob
live = {}
for f in glob.glob(os.path.join(jio.ROOT, 'Entity', '*', '*', '*', '*.json')):
    d = json.load(open(f, encoding='utf-8'))
    if d.get('subtype') == 'people' and not d.get('merged_into'): live[d['id']] = 1
done = skip = 0; applied = []
for it in items:
    d, fmt = jio.load(it['path'])
    aus = d.get('authors') or []
    if d.get('merged_into') or it['slot'] >= len(aus) or not isinstance(aus[it['slot']], dict):
        skip += 1; print('跳过（记录已并或作者位不存在）', it['path'], it['slot']); continue
    au = aus[it['slot']]
    if au.get('name') != it['name'] or au.get('entity_id') or it['entity_id'] not in live or d.get('merged_into'):
        skip += 1; print('跳过', it['path'], it['slot']); continue
    au['entity_id'] = it['entity_id']
    if a.apply: jio.save(it['path'], d, fmt)
    done += 1; applied.append(it)
if a.out: json.dump(applied, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('挂接', done, '跳过', skip, '（乾跑）' if not a.apply else '')
