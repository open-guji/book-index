#!/usr/bin/env python3
"""split_fz.py 之後：新建 Work 的 related_works 按 check_v2 V07 移到 id 較小一側（新 id 皆較大），附註改從對方角度寫。用法：split_post.py [--apply]"""
import glob, json, sys
TODAY = '2026-10-26'
NOTE = {('d59g2k8yudq8', 'd59f2n7golxc'): '同治魏式曾增修、郭鑑襄增纂本（據本條乾隆原修舊版增刻）',
        ('d59g2k8yudq9', 'd59fyoao7nr5'): '所據之萬曆任弘烈修、段廷選纂六卷本',
        ('d59g2k8yudq9', 'd59f2njx8qgz'): '同題異修：萬曆任弘烈修、段廷選纂六卷本',
        ('d59g2k8yudqa', 'd59fyp0ieuip'): '所據之康熙四年劉沛先修、王吉臣纂原修本',
        ('d59g2k8yudqb', 'd59f2n023y0w'): '所據之雍正呂耀曾、王河修三十三卷本'}
def p(i): return glob.glob(f'Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
for (new, old), note in NOTE.items():
    n = json.load(open(p(new), encoding='utf-8')); o = json.load(open(p(old), encoding='utf-8'))
    n['related_works'] = [r for r in n.get('related_works') or [] if r['id'] != old]
    if not n['related_works']: n.pop('related_works')
    if not any(r['id'] == new for r in o.get('related_works') or []):
        o.setdefault('related_works', []).append({'id': new, 'relation': 'related', 'note': note})
        a, b, _ = (o.get('revision') or '1.0.0').split('.'); o['revision'] = '%s.%d.0' % (a, int(b) + 1) if o.get('revised_at') != TODAY else o['revision']; o['revised_at'] = TODAY
    print(old, '+', new)
    if '--apply' in sys.argv:
        for i, d in ((new, n), (old, o)):
            open(p(i), 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
