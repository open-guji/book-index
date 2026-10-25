#!/usr/bin/env python3
"""split_apply.py 之後的補正：check_v2 V07 要求 related 存在 id 較小一側，把 d59g24d8rsw3→d59fyt0b2f40 的互鏈改存 d59fyt0b2f40。"""
import glob, json
W4, X = 'd59g24d8rsw3', 'd59fyt0b2f40'
p4 = glob.glob('Work/s/w/3/%s-*.json' % W4)[0]; d4 = json.load(open(p4))
rel = d4.pop('related_works'); assert rel[0]['id'] == X
open(p4, 'w').write(json.dumps(d4, ensure_ascii=False, indent=2) + '\n')
px = glob.glob('Work/%s/%s/%s/%s-*.json' % (X[-3], X[-2], X[-1], X))[0]; dx = json.load(open(px))
dx.setdefault('related_works', []).append({'id': W4, 'relation': 'related', 'note': '黃錫齡注黃宗羲《今水經》之《今水經注要覽》三卷；本條一卷疑為其節本，未證同，不併'})
a, b, c = dx['revision'].split('.'); dx['revision'] = '%s.%d.0' % (a, int(b) + 1); dx['revised_at'] = '2026-10-25'
dx['ai_note'] = (dx.get('ai_note') or '') + '\n\n2026-10-25 去重方案部分3a 拆混記錄：與新建 %s《今水經注要覽》互鏈 related（疑本條為其節本，未證同）。' % W4
open(px, 'w').write(json.dumps(dx, ensure_ascii=False, indent=2) + '\n')
