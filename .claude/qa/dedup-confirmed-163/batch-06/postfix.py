#!/usr/bin/env python3
"""batch-06 并条后的逐条修正（H-H001 污染修复、MR-H2000-005 描述与作者、JC-007 存佚）。
原值写入 postfix-原值.json，供台账与回滚。用法：postfix.py [--apply]"""
import json, sys, os, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
TODAY = '2026-10-25'
def p(t, i): return glob.glob(f'{ROOT}/{t}/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def load(t, i): f = p(t, i); return f, json.load(open(f, encoding='utf-8'))
def save(f, j): open(f, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
orig = {}
def keep(i, k, v): orig.setdefault(i, {})[k] = v
def note(j, s): j['ai_note'] = ((j.get('ai_note') or '').rstrip() + '\n\n' + s).lstrip()
CUT = ('《宋史·藝文志》經部春秋類此段原為連寫，每條作者綴於下一條書名之前；本庫錄作「{rec}」係按行切分之誤，'
       '作者應為{right}。證據：《古今圖書集成·經籍典》卷180引宋志分列「宋庠《國語補音》三卷」「林概《辨國語》三卷」。'
       '引文照錄不改（2026-10-25 A11 去重 H-H001）。')
changes = []
# 1. 國語補音
f, j = load('Work', 'd59f2hswekua')
for e in j['indexed_by']:
    if e.get('source') == '宋史藝文志' and '林概' in (e.get('summary') or ''):
        keep(j['id'], 'indexed_by[宋史藝文志].note', e.get('note'))
        e['note'] = CUT.format(rec='《國語補音》三卷林概', right='宋庠（「林概」屬下條《辨國語》）')
note(j, f'{TODAY} A11 去重 H-H001：宋史藝文志條「林概」為跨條斷行污染，非另一作者，已於該條 note 說明；並入叢書子目重出條 d59fyfefz9c0（總目「宋宋庠補葺」）。')
changes.append((f, j))
# 2. 辨國語
f, j = load('Work', 'd59f2q0i5ds1')
for e in j['indexed_by']:
    if e.get('source') == '宋史藝文志' and '崔表' in (e.get('summary') or ''):
        keep(j['id'], 'indexed_by[宋史藝文志].note', e.get('note'))
        e['note'] = CUT.format(rec='《辨國語》三卷崔表', right='林概（「崔表」屬下條）')
keep(j['id'], 'authors', j.get('authors'))
if not j.get('authors'):
    j['authors'] = [{'name': '林概', 'role': '撰', 'dynasty': '北宋',
                     'note': '據《古今圖書集成·經籍典》卷180引宋志「林概《辨國語》三卷」；《經義考》作林槩，字端甫，福清人，景祐元年試禮部第一。entity 待建（去重方案部分 2）。'}]
note(j, f'{TODAY} A11 去重 H-H001 連帶：宋史藝文志條「崔表」為跨條斷行污染，補撰人林概。')
changes.append((f, j))
# 3. Book 993fzgxdkw
f, j = load('Book', '993fzgxdkw')
note(j, f'{TODAY} A11 去重 H-H001 核查：edition「元至元間杭州路餘杭大普寧寺刻;影印微波榭叢書本」為上圖聯合目錄原串（兩版本項連寫），publication_info 的「影印者：杭州路餘杭大普寧寺」是機械拆分之誤，待版本層（去重方案部分 5）覆核，本次未改。')
changes.append((f, j))
# 4. 三教平心論
f, j = load('Work', 'd59f2ghlbt34')
keep(j['id'], 'description', j.get('description')); keep(j['id'], 'authors', json.loads(json.dumps(j['authors'])))
j['authors'][0]['entity_id'] = 'hixhd2h9bh1y'
j['description'] = {'text': '元劉謐撰，二卷。劉謐號靜齋學士，故《補遼金元藝文志》《元史藝文志》《千頃堂書目》題「劉謐靜齋學士三教平心論」；《國史經籍志》括注「靜同劉字十」為亂序殘文，非撰人名。中國古籍總目著錄存本。',
                    'sources': ['國史經籍志', '補遼金元藝文志', '元史藝文志', '千頃堂書目', '中國古籍總目']}
note(j, f'{TODAY} A11 去重 MR-H2000-005：並入 d59f2gpjvnr5、d59f6ekv7h1c；舊 description 以「靜同劉字十」為撰人且稱惟一志著錄，已改寫，原文存 batch-06 台賬。')
changes.append((f, j))
# 5. 王肅周易注
f, j = load('Work', 'd59f27yxltdu')
keep(j['id'], 'loss_status', j.get('loss_status')); keep(j['id'], 'loss_status_basis', j.get('loss_status_basis'))
j['loss_status'] = 'partially_extant'
j['loss_status_basis'] = '並入之條著錄馬國翰、孫堂、黃奭、張惠言等輯本（玉函山房輯佚書、漢魏二十一家易注、黃氏逸書考等），原書十卷已佚，今存輯本（2026-10-25 A11 去重 JC-007）。'
changes.append((f, j))
if '--apply' in sys.argv:
    for f, j in changes: save(f, j)
    json.dump(orig, open(os.path.join(os.path.dirname(__file__), 'postfix-原值.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for f, _ in changes: print(('改 ' if '--apply' in sys.argv else '乾跑 ') + os.path.relpath(f, ROOT))
