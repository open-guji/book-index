#!/usr/bin/env python3
"""第 8 批抽检善后：fixes.py 移走 indexed_by 后 description 未跟改的 5 条重写；履齋遺稿吳潛朝代改南宋；
上蔡先生語錄补回被并者的朱熹「輯」。原值写 postfix8-原值.json。用法：postfix8.py [--apply]"""
import json, glob, sys, pathlib
HERE = pathlib.Path(__file__).parent; ROOT = HERE.parents[3]; apply = '--apply' in sys.argv
def path(i): return glob.glob(str(ROOT / f'Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'))[0]
DESC = {
 'd59f2mr6s6bl': ('沈欽韓（清）撰。十二卷。見著錄於《續修四庫全書》《清史稿藝文志》。《續修四庫全書》列於经部 春秋類。經注之屬。本書為《左傳》之注釋，其文附原典以行。《續修四庫全書》一九九五年影印。', ['續修四庫全書', '清史稿藝文志']),
 'd59f2hr2uqrk': ('《大隱居士詩集》，宋鄧深撰。', []),
 'd59f2gp07pj6': ('元明善（元）撰。三卷。見著錄於《補遼金元藝文志》《元史藝文志》《中國古籍總目》。其著錄之文，《補遼金元藝文志》作「元元明善龍虎山志三卷」；《中國古籍總目》作「龍虎山志三卷續編一卷」，續編元周召撰。', ['補遼金元藝文志', '元史藝文志', '中國古籍總目']),
 'd59f2ghntpfm': ('元明善（元）撰，明張國祥續修。三卷。見著錄於《四庫全書存目叢書》《欽定四庫全書總目》。《四庫全書存目叢書》列於史部，作「《續修龍虎山志》三卷」，明張國祥、張顯庸續撰；《欽定四庫全書總目》題《龍虎山志》三卷，兩淮馬裕家藏本，提要云「元元明善撰，明張國祥續修」。', ['四庫全書存目叢書', '欽定四庫全書總目']),
 'd59f27srzbpe': ('王肅撰。見著錄於《宋史藝文志》，作「王肅《傳》十一卷」。撰人王肅之爵里事跡，諸志不載。《宋史藝文志》元脫脫等修。', ['宋史藝文志']),
}
orig, n = {}, 0
def save(i, d, before):
    global n
    orig[i] = before; n += 1
    if apply:
        open(path(i), 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
for i, (t, s) in DESC.items():
    d = json.load(open(path(i), encoding='utf-8')); before = {'description': d.get('description')}
    d['description'] = {'text': t, 'sources': s}
    if i == 'd59f2hr2uqrk':  # 存佚原據誤掛之李正民提要，撤後無據
        before.update(loss_status=d.get('loss_status'), loss_status_basis=d.get('loss_status_basis'))
        d['loss_status'] = None; d['loss_status_basis'] = None
    save(i, d, before)
# 履齋遺稿：吳潛嘉定十年進士第一，南宋人
i = 'd59f2htpfncx'; d = json.load(open(path(i), encoding='utf-8'))
before = {'description': d['description'], 'authors': d['authors']}
d['description'] = dict(d['description'], text=d['description']['text'].replace('北宋吳潛', '宋吳潛'))
d['authors'] = [dict(a, dynasty='南宋', dynasty_basis='四庫提要「嘉定十年進士第一」（2026-10-25 第 8 批抽检改）') if a['name'] == '吳潛' else a for a in d['authors']]
save(i, d, before)
# 上蔡先生語錄：被并者 d59fy1ygub5t 署「宋朱熹輯」
i = 'd59fy3s5cveo'; d = json.load(open(path(i), encoding='utf-8'))
if not any(a.get('entity_id') == 'hixhd2h9bgah' for a in d['authors']):
    before = {'authors': d['authors']}
    d['authors'] = d['authors'] + [{'name': '朱熹', 'role': '輯', 'entity_id': 'hixhd2h9bgah', 'dynasty': '宋'}]
    save(i, d, before)
if apply:
    (HERE / 'postfix8-原值.json').write_text(json.dumps(orig, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('改', n, '条', '' if apply else '（试跑）')
