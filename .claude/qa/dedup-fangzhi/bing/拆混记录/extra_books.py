#!/usr/bin/env python3
"""方志-并 收尾：盛京通志三條 Book 掛錯修次（子 agent 核資源時順帶核出），併前改掛。用法：extra_books.py [--apply]"""
import glob, json, sys
TODAY = '2026-10-26'
MOVES = [('997989rwc4', 'd59f2ntt35s1', 'd59f2my8vchs', '國圖題「[康熙]盛京通志」，屬伊把漢等康熙二十三年修本'),
         ('9979895f5w', 'd59f2ntt35s1', 'd59f2my8vchs', '國圖題「[康熙]盛京通志」，屬伊把漢等康熙二十三年修本'),
         ('988g6umvwv', 'd59f2my8vchs', 'd59fynrtlqte', '故宮著錄清乾隆十二年武英殿刊本，屬乾隆汪由敦等三十二卷本'),
         ('988g4s1635', 'd59f2my8vchs', 'd59fynrtlqte', '故宮著錄清乾隆十二年武英殿刊本，屬乾隆汪由敦等三十二卷本')]
for b, frm, to, why in MOVES:
    p = glob.glob(f'Book/{b[-3]}/{b[-2]}/{b[-1]}/{b}-*.json')[0]; d = json.load(open(p, encoding='utf-8'))
    assert d['work_id'] == frm, (b, d['work_id'])
    d['work_id'] = to
    a, m, _ = (d.get('revision') or '1.0.0').split('.'); d['revision'] = '%s.%d.0' % (a, int(m) + 1); d['revised_at'] = TODAY
    d['ai_note'] = ((d['ai_note'] + '\n\n') if d.get('ai_note') else '') + '%s 去重方案方志-并：%s；work_id 由 %s 改指 %s。' % (TODAY, why, frm, to)
    print(b, frm, '->', to)
    if '--apply' in sys.argv:
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
