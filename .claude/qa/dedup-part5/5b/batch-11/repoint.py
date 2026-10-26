#!/usr/bin/env python3
"""5b-乙 第 11 批：文淵閣／摛藻堂余组里挂错 Work 的 Book 改挂正确 Work（只改 work_id）。用法：repoint.py [--apply]"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../..'))
MOVES = [  # (Book, 原 Work, 新 Work, 依据)
    ('988g262qks', 'd59f2065yfpc', 'd59f6ssrrv7n', 'R001 起廢疾（鄭玄）是單獨一書，原挂「發墨守・鍼膏肓・起廢疾」合題 Work，同冊另有發墨守'),
    ('988g270g75', 'd59f2065yfpc', 'd59fxwyqn8xs', 'R001 發墨守（鄭玄）單獨一書'),
    ('988g70vmro', 'd59f28kehedd', 'd59f2hdnndvn', 'R017 亢倉子注（何粲注）是注本，四庫另立一條；原誤挂亢倉子 Work'),
    ('988faimy9s', 'd59f2hs6t4aq', 'd59fy9x9fk02', 'R070 摛藻堂第35冊春秋集解是呂本中三十卷，原誤挂蘇轍春秋集解 Work'),
    ('988g5hbe32', 'd59f2nl6tdz4', 'd59f6ejkp43r', 'R153 老子翼（焦竑，第1055冊）單獨一書，原挂「老子翼、莊子翼」合題 Work'),
]
apply = '--apply' in sys.argv
W = {f.split('-')[0] for d, _, fs in os.walk(os.path.join(ROOT, 'Work')) for f in fs if f.endswith('.json')}
for b, old, new, why in MOVES:
    p = glob.glob(os.path.join(ROOT, 'Book', b[-3], b[-2], b[-1], b + '-*.json')); assert len(p) == 1
    j = json.load(open(p[0], encoding='utf-8'))
    assert j['work_id'] == old and new in W and not j.get('merged_into'), (b, j['work_id'])
    j['work_id'] = new
    j['ai_note'] = ((j.get('ai_note') or '') + f'\n2026-10-26 5b-乙：work_id {old}→{new}（{why}）').strip()
    rev = '%d.0.0' % (int((j.get('revision') or '1.0.0').split('.')[0]) + 1)
    j.pop('revision', None); j.pop('revised_at', None); j['revision'] = rev; j['revised_at'] = '2026-10-26'
    print(b, old, '->', new)
    if apply: open(p[0], 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
