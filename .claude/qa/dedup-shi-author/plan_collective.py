#!/usr/bin/env python3
"""史部串 I 档：作者位名字＝已建官署/机构 Entity（collective）主名，按作者位朝代挑对应条。
输入 nohit.json（baseline 中无人物命中的史部首位作者位），输出 attach-collective.json。
唯一 live 候选直接挂；多候选（六部等 concept＋各朝 concrete）取 dynasty 与作者位朝代相同的 concrete；其余不挂。"""
import json, os, sys, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
o = json.load(open(sys.argv[1], encoding='utf-8'))   # colmatch.json: [name, path, dyn, title, [[eid, level, dyn_list]]]
out = []; skip = collections.Counter()
for nm, rel, wd, title, cands in o:
    pick = None
    if len(cands) == 1: pick = cands[0][0]
    else:
        m = [c for c in cands if c[1] == 'concrete' and isinstance(c[2], list) and wd and wd in [x.replace('趙宋', '宋') for x in c[2]] + c[2]]
        if len(m) == 1: pick = m[0][0]
    if not pick: skip[(nm, wd)] += 1; continue
    out.append({'path': rel, 'slot': 0, 'name': json.load(open(os.path.join(ROOT, rel), encoding='utf-8'))['authors'][0]['name'], 'entity_id': pick, 'title': title})
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('可挂', len(out), '不挂', dict(skip))
