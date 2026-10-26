#!/usr/bin/env python3
"""3c 補：同一誤字在同題組外的著錄（Work／Book）一併勘正並改掛人物。用法：fix_extra.py [--apply]"""
import glob, json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TODAY = datetime.date.today().isoformat()
B洪 = '3c 誤字勘誤：補晉書藝文志（秦）系著錄誤「僧」為「洪」，同批《寶藏論》《物不遷論》等已據同題著錄勘正為「僧肇」，本條同為僧肇著作（肇論諸篇），一併勘正'
FIX = [  # (目錄, id, 舊名, 新名, 改掛 Entity, 依據)
    ('Work', 'd59f9ux293i8', '洪肇', '僧肇', 'hixhd2h9bixi', B洪),
    ('Work', 'd59f9ux2kc1t', '洪肇', '僧肇', 'hixhd2h9bixi', B洪),
    ('Work', 'd59f9ux2kc1u', '洪肇', '僧肇', 'hixhd2h9bixi', B洪),
    ('Work', 'd59f9nmws83l', '僧洪肇', '僧肇', 'hixhd2h9bixi', B洪.replace('誤「僧」為「洪」', '衍「洪」字')),
    ('Book', '993h2lylmo', '鄭賁', '鄭蕡', 'hixicabcxc1r', '3c 誤字勘誤：所屬 Work d59fxy2w78jl 已據同題著錄勘正為「鄭蕡」'),
    ('Book', '994fz5g3y9', '齊晝', '劉晝', 'hixi8us3ii5t', '3c 誤字勘誤：所屬 Work d59fywzkzs3l 已據同題著錄勘正為「劉晝」'),
    ('Book', '993g6b7mdd', '陳廷堅', '元廷堅', 'hixicabcm3n1', '3c 誤字勘誤：所屬 Work d59fxx74syyq 已據同題著錄勘正為「元廷堅」'),
    ('Work', 'd59f6endf20x', '明初', '佚名', '', '3c 佔位名勘誤：千頃堂書目著錄作「明初明良隆遇録」，「明初」為時代標識，非撰人；撰人不詳，作佚名（明）'),
    ('Work', 'd59f6es2log2', '明初', '佚名', '', '3c 佔位名勘誤：千頃堂書目著錄作「明初郊壇祭享儀注」，「明初」為時代標識，非撰人；撰人不詳，作佚名（明）'),
]
apply = '--apply' in sys.argv
for typ, i, old, new, ent, basis in FIX:
    p = glob.glob(os.path.join(ROOT, typ, i[-3], i[-2], i[-1], i + '-*.json'))[0]
    d = json.load(open(p, encoding='utf-8'))
    for k, a in enumerate(d.get('authors', [])):
        if a.get('name') != old: continue
        print(typ, i, d.get('title'), k, old, '→', new, ent)
        if not apply: continue
        a['name'] = new
        a['original_name'] = old
        a['name_basis'] = basis
        if ent: a['entity_id'] = ent
        else:
            a.pop('entity_id', None); a['dynasty'] = '明'
        r = (d.get('revision') or '1.0.0').split('.'); r[2] = str(int(r[2]) + 1); d['revision'] = '.'.join(r)
        d['revised_at'] = TODAY
        d['ai_note'] = (d.get('ai_note') or '') + '；3c 責任者名勘誤（%s）：authors[%d]「%s」→「%s」' % (TODAY, k, old, new)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')
