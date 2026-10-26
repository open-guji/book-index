#!/usr/bin/env python3
"""方志续修／增修本互链（用户 2026-10-26 定：E 类分立并互链）。

    python3 link_e.py <E-核对.tsv> [--apply]

只取结论为「互链」的对，按 check_v2 V07 只在 ID 较小的一侧加 related_works {id, relation: related, note: 续修：<关系说明>}，已有指向对方的链接则跳过。"""
import glob, json, sys
TODAY = '2026-10-26'
def path(i): return glob.glob(f'Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def bump(rev):
    a, b, c = (rev or '1.0.0').split('.'); return '%s.%s.%d' % (a, b, int(c) + 1)
rows = [l.rstrip('\n').split('\t') for l in open(sys.argv[1], encoding='utf-8')][1:]
rows = [r for r in rows if len(r) > 3 and r[2] == '互链']
print('载入互链对 %d' % len(rows))
if not rows: sys.exit('载入为 0，停')
apply = '--apply' in sys.argv; n = 0
for a, b, _, rel, *_ in rows:
    for x, y in ((min(a, b), max(a, b)),):
        p = path(x); d = json.load(open(p, encoding='utf-8'))
        if d.get('merged_into'): print('墓碑跳过', x); continue
        if any(r.get('id') == y for r in d.get('related_works') or []): continue
        d.setdefault('related_works', []).append({'id': y, 'relation': 'related', 'note': '續修／增修：' + rel})
        d['revision'] = bump(d.get('revision')); d['revised_at'] = TODAY; n += 1
        if apply: open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('新增链接 %d' % n)
