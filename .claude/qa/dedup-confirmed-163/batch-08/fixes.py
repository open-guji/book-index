#!/usr/bin/env python3
"""第 8 批挂错修复（176 组判定理由栏所列）。原值写 fixes-原值.json。用法：fixes.py [--apply]"""
import json, sys, os, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
HERE = os.path.dirname(os.path.abspath(__file__)); TODAY = '2026-10-25'
def p(i): return glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
W, orig = {}, {}
def get(i):
    if i not in W:
        j = json.load(open(p(i), encoding='utf-8')); assert not j.get('merged_into'), i
        W[i] = j; orig[i] = json.loads(json.dumps(j))
    return W[i]
def note(j, s): j['ai_note'] = ((j.get('ai_note') or '').rstrip() + '\n\n' + s).lstrip()
def move(src, dst, pred, case, why):
    a, b = get(src), get(dst)
    hit = [e for e in a['indexed_by'] if pred(e)]; assert len(hit) == 1, (src, len(hit))
    e = hit[0]; a['indexed_by'].remove(e)
    same = [x for x in b['indexed_by'] if x.get('source') == e.get('source') and x.get('summary') == e.get('summary')]
    if not same: b['indexed_by'].append(e)
    note(a, f'{TODAY} A11 去重 {case}：移出《{e.get("source")}》一條至 {dst}（{why}）。')
    note(b, f'{TODAY} A11 去重 {case}：自 {src} 移入《{e.get("source")}》一條（{why}）。' if not same else f'{TODAY} A11 去重 {case}：{src} 誤掛之《{e.get("source")}》條與本條既有者全同，已自彼處撤去。')
# 史部 H-A002：四庫總目龍虎山志（明張國祥續修，兩淮馬裕家藏本）屬續修本
move('d59f2gp07pj6', 'd59f2ghntpfm', lambda e: e.get('source') == '欽定四庫全書總目', 'H-A002', '四庫所錄為明張國祥續修本，屬續修龍虎山志')
# 集部 COL-R020：大隱居士詩集（鄧深）誤掛李正民《大隱集》提要
move('d59f2hr2uqrk', 'd59f2hu9eu4h', lambda e: e.get('source') == '欽定四庫全書總目' and '李正民' in (e.get('author_info') or ''), 'COL-R020', '提要是李正民《大隱集》的，非鄧深《大隱居士詩集》')
# 經部 JC-1900-H005：經義考卷198 十卷條（汸自序）屬元趙汸
move('d59f2mr6s6bl', 'd59f2j58ml8i', lambda e: e.get('source') == '經義考' and '汸自序' in (e.get('summary') or ''), 'JC-1900-H005', '經義考十卷、汸自序，是元趙汸《春秋左氏傳補注》')
# 經部 JC-OPEN：王肅易傳條混入「曹瞞傳，吳人作」
move('d59f27srzbpe', 'd59f27sczxms', lambda e: e.get('source') == '三國藝文志' and '曹瞞傳' in (e.get('summary') or ''), 'JC-OPEN-d59f27srzbpe', '三國藝文志此條是曹瞞傳')
# 子部 MR-H2000-004：京大富士川藏曲直瀨道三寫本錯掛
j = get('d59f2gljz9c1')
j['resources'] = [r for r in j['resources'] if r.get('group') != 'kokusho-100314944']
j.get('resource_groups', {}).pop('kokusho-100314944', None)
if not j.get('resource_groups'): j.pop('resource_groups', None)
note(j, f'{TODAY} A11 去重 MR-H2000-004：撤去錯掛之國書資源 kokusho-100314944（京大富士川藏，曲直瀨道三著寫本，非本書）。')
# 子部 MR-2022-004：不空羂索神變真言經譯者只留菩提流志
j = get('d59fxwc307b5')
keep = [a for a in j['authors'] if a['name'] == '釋菩提流志']; assert len(keep) == 1
j['authors'] = keep
note(j, f'{TODAY} A11 去重 MR-2022-004：authors 原混入釋地婆訶羅、釋菩提留支、釋菩提流支（總目版本層他經譯者串入），本經三十卷唐釋菩提流志譯，撤去三人（原值存台賬）；可疑版本交 Book 層（去重方案部分 5）核。')
# 集部 COL-H001：忠愍集 keeper 撰人李若水應繫宋人 hixi8u5ywvgi，非唐人 hixhd2h9bmi9
j = get('d59f2huigpvm')
for a in j['authors']:
    if a['name'] == '李若水' and a.get('entity_id') != 'hixi8u5ywvgi':
        assert a.get('entity_id') in (None, 'hixhd2h9bmi9'), a
        a['entity_id'] = 'hixi8u5ywvgi'
        a['name_basis'] = f'{TODAY} A11 去重 COL-H001：宋李若水（忠愍），entity 取宋人 hixi8u5ywvgi；並入條原繫唐人 hixhd2h9bmi9 為錯掛。'
if '--apply' in sys.argv:
    for i, j in W.items():
        a, b, c = [int(x) for x in j.get('revision', '1.0.0').split('.')]
        import subprocess
        rel = os.path.relpath(p(i), ROOT)
        if not subprocess.run(['git', '-C', ROOT, 'diff', '--quiet', 'origin/main', '--', rel]).returncode:
            j['revision'] = f'{a}.{b+1}.0'; j['revised_at'] = TODAY
        open(p(i), 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
    json.dump(orig, open(os.path.join(HERE, 'fixes-原值.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(('改' if '--apply' in sys.argv else '乾跑'), sorted(W))
