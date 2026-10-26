#!/usr/bin/env python3
"""方志-并 收尾：d59f2nfx13pc（明孔天胤汾州府志八卷）混入書目答問「汾州府志⟨戴震⟩」，移到乾隆戴震纂本 d59fyo9ebrwg。用法：split_fenzhou.py [--apply]"""
import glob, json, sys
TODAY = '2026-10-26'
def p(i): return glob.glob(f'Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def bump(d):
    a, b, _ = (d.get('revision') or '1.0.0').split('.'); d['revision'] = '%s.%d.0' % (a, int(b) + 1); d['revised_at'] = TODAY
def note(d, s): d['ai_note'] = ((d['ai_note'] + '\n\n') if d.get('ai_note') else '') + '%s 去重方案方志-并 拆混記錄：%s' % (TODAY, s)
W, T = 'd59f2nfx13pc', 'd59fyo9ebrwg'
w, t = json.load(open(p(W), encoding='utf-8')), json.load(open(p(T), encoding='utf-8'))
hits = [k for k, e in enumerate(w['indexed_by']) if e.get('source') == '書目答問']
assert len(hits) == 1, hits
e = w['indexed_by'].pop(hits[0]); e['note'] = ((e['note'] + '；') if e.get('note') else '') + '%s 自 %s 移來：書目答問注戴震，庫中戴震纂汾州府志唯乾隆本' % (TODAY, W)
t.setdefault('indexed_by', []).append(e)
w['description'] = {'text': '孔天胤（明）撰。八卷。見著錄於《明史藝文志》。本書惟《明史藝文志》一志著錄，別無他證。《明史藝文志》清張廷玉等修——本書之目賴之以存。', 'sources': ['明史藝文志']}
note(w, '書目答問「汾州府志（戴震）」為乾隆戴震纂本，移至 %s；description 改寫。' % T); bump(w)
note(t, '自 %s 移入書目答問「汾州府志（戴震）」一條。' % W); bump(t)
if '--apply' in sys.argv:
    for i, d in ((W, w), (T, t)):
        open(p(i), 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('ok')
