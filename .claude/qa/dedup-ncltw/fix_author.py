#!/usr/bin/env python3
"""b-01 善后：T09《後漢書》keeper 撰人「華嶤」系「華嶠」之讹（本条隋志、旧唐志原文均作華嶠），改挂華嶠 entity。"""
import glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
FIX = {'d59f27xspq82': ('華嶤', '華嶠', 'hixhd2h9biw1')}
for wid, (old, new, eid) in FIX.items():
    p = glob.glob(os.path.join(ROOT, 'Work', wid[-3], wid[-2], wid[-1], wid + '-*.json'))[0]
    w = json.load(open(p, encoding='utf-8'))
    for a in w['authors']:
        if a['name'] == old:
            a['name'], a['entity_id'] = new, eid
    note = f'【台湾国图线索去重】撰人「{old}」系「{new}」之讹（本条隋志、旧唐志原文作{new}），改挂 {eid}。'
    if note not in (w.get('ai_note') or ''):
        w['ai_note'] = ((w.get('ai_note') or '') + '  ' + note).strip()
    json.dump(w, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(p, 'a', encoding='utf-8').write('\n')
    print('改', wid)
