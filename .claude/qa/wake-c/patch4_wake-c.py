# -*- coding: utf-8 -*-
"""複抽意見修訂（PR #2879）：直接改已生成 Book，不重鑄號。"""
import json, glob, os, copy
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))
def P(i): return glob.glob(os.path.join(ROOT, 'Book/*/*/*/%s-*.json' % i))[0]
def L(i): return json.load(open(P(i), encoding='utf-8'))
def S(d, path=None):
    open(path or P(d['id']), 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
def bump(d):
    a, b, c = d['revision'].split('.'); d['revision'] = '%s.%s.%d' % (a, b, int(c) + 1); d['revised_at'] = '2026-11-16'
def add_note(d, t):
    d['ai_note'] = ((d.get('ai_note') or '') + ' ' + t).strip()
TAG = '和刻本專項第四輪（wake-c，2026-11-16）：'
NEW = '99jwdzvksg'
# ① me / md / mf
me = L('99jw91n2me')
me['description']['text'] += '書肆著錄：CiNii出版者欄共五名（須原屋源助・須原屋伊八・須原屋茂兵衞・秋田屋太右衞門・須原屋平左衞門）；島根大學BB12627024裏表紙見返所載為「須原屋源助ら4書林」，與五名數不一致，此處取出版者欄。'
add_note(me, '複抽修訂：阪大BB12831905無見返／刊記著錄、僅叢書題「四書集註」，依據較弱，僅憑出版項併入，不作定版證據。疑與庫內991k9ne9e8（孟子集注，大坂秋田屋太右衞門文政八年，國書著錄存4冊）及整套四書章句集注991mmu8ufb同版（秋田屋太右衞門在本條書肆內），國書著錄不足以判定，故另立互注、不並；同套另有論語集註99jw91n2md、中庸章句99jw91n2mf、庫內大學章句99judsxpmr。')
S(me)
for i, t in (('99jw91n2md', '孟子集註99jw91n2me、中庸章句99jw91n2mf'), ('99jw91n2mf', '論語集註99jw91n2md、孟子集註99jw91n2me')):
    d = L(i); add_note(d, '複抽修訂：與%s、庫內大學章句99judsxpmr同套（林家正本四書集註）；疑與庫內四書章句集注991mmu8ufb（大坂秋田屋太右衞門文政八年）為同一套，國書著錄不足，另立互注、未並。' % t); S(d)
for i, t in (('991k9ne9e8', '孟子集註99jw91n2me（CiNii五NCID，須原屋源助等五書肆）'), ('991mmu8ufb', '論語集註99jw91n2md、孟子集註99jw91n2me、中庸章句99jw91n2mf（CiNii，須原屋源助等五書肆）')):
    d = L(i); bump(d); add_note(d, TAG + '疑與新建%s同版（同年、書肆含秋田屋太右衞門），國書著錄缺見返／行款，未能確認，兩條互注、不並。' % t); S(d)
# ② mj
mj = L('99jw91n2mj')
add_note(mj, '複抽修訂：與庫內991k9ne9ec（孟子集注，平安北村四郎兵衞安政五年，國書著錄存4冊）疑為同版，國書SPA無法取行款，另立互注、不並；與99ifez2z9e（整套四書集註六版本，書陵部）互注。')
S(mj)
for i, t in (('991k9ne9ec', '孟子集註99jw91n2mj'), ('99ifez2z9e', '孟子集註99jw91n2mj（新刻改正後藤點，CiNii四NCID，題簽「再刻後藤點」六刻）')):
    d = L(i); bump(d); add_note(d, TAG + '疑與新建%s為同版或所屬整套，著錄不足以確認，兩條互注、不並。' % t); S(d)
# ③ mh 拆分
mh = L('99jw91n2mh'); nh = copy.deepcopy(mh); nh['id'] = NEW
for d, nc, other, extra in ((mh, 'BB16949077', NEW, '本條依BB16949077：七冊（兩卷一冊），內匡郭19.7×14.4cm，無訓點；刊記「延享四年丁卯五月／東都書肆／竹川藤兵衞／坪内茂左衞門／橋本勝吉／前川六左衞門」。'),
                            (nh, 'BB23048255', '99jw91n2mh', '本條依BB23048255：四冊（卷1-3／4-6／7-10／11-14），內匡廓19.7×13.7cm；刊記中「前川六左衞門」鈐朱印「直安之印」；出版項書肆同上四名。')):
    d['provenance'] = [p for p in d['provenance'] if nc in p['source']]
    d['description']['sources'] = ['CiNii Books https://ci.nii.ac.jp/ncid/%s' % nc]
    d['sources'] = [s for s in d['sources'] if nc in s['id']]
    d['description']['text'] = '趙岐註、金蟠訂：《趙註孟子》，日本延享四年（1747）東都竹川藤兵衞・坪內茂左衞門・橋本勝吉・前川六左衞門刊本。題辭書名「趙氏孟子」，題簽「趙註孟子」，四周雙邊有界九行二十字注文雙行，單魚尾；京都大學附屬圖書館藏。' + extra
    d['ai_note'] = TAG + '據CiNii Books新建（NCID %s）；複抽指出原併條兩NCID冊數／匡郭／訓點不同（4冊13.7cm vs 7冊14.4cm無訓點），現拆為兩條，互注（%s）；是否同版／同一書版之別印未核。庫內993gjlqf40（孟子趙岐注十四卷，日本延亨四年刻本，中國總目著錄，掛通用孟子Work d59fxxkb9on6）與本條疑為同版或其一，無書肆著錄，未補挂，雙向互注。同年另有前川六左衞門・須原茂兵衞組（99jw91n2mi）。' % (nc, other)
    if nc == 'BB23048255': d['dating']['basis'] = 'CiNii Books（BB23048255）出版項「延享4 [1747]」，書肆與BB16949077刊記所載東都四書林一致；刊記全文未見著錄'
    else: d['dating']['basis'] = 'CiNii Books（BB16949077）刊記「延享四年丁卯五月／東都書肆／竹川藤兵衞／坪内茂左衞門／橋本勝吉／前川六左衞門」'
S(mh)
nh_path = os.path.join(os.path.dirname(P('99jw91n2mh')).replace('/2/m/h', ''), '')
dirp = os.path.join(ROOT, 'Book/%s/%s/%s' % (NEW[-3], NEW[-2], NEW[-1])); os.makedirs(dirp, exist_ok=True)
S(nh, os.path.join(dirp, '%s-趙註孟子日本延享四年1747東都竹川藤兵衞四書林刊本四冊.json' % NEW))
g = L('993gjlqf40'); bump(g)
add_note(g, TAG + '疑與新建趙註孟子99jw91n2mh（BB16949077，七冊）、%s（BB23048255，四冊）（延享四年東都竹川藤兵衞等四書林刊本）或99jw91n2mi（前川六左衞門・須原茂兵衞組）之一同版；本條無書肆著錄，不能確認，未補挂，互注。' % NEW)
S(g)
# ④ mi
mi = L('99jw91n2mi')
mi['edition'] = '日本延享四年（1747）原刊前川六左衞門・須原茂兵衞印本'
mi['dating'].update({'certainty': 'inferred', 'basis': '延享四年為原刊記年（CiNii出版項「延享4 [1747]」）；本組書肆含須原茂兵衞，原刊記四書林（竹川藤兵衞等）中無此人，疑為後印，實際印行年待核'})
bb = 'BB13446896'
mi['provenance'].append({'institution': '東京大學總合圖書館', 'notes': 'CiNii Books所藏館「東京大學總合圖書館」；孟子 14巻；4冊；巻末附「崇文堂藏版書目」（前川六左衞門）', 'source': 'CiNii Books https://ci.nii.ac.jp/ncid/' + bb})
mi['sources'].append({'id': 'cinii-' + bb, 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + bb})
mi['description']['sources'].append('CiNii Books https://ci.nii.ac.jp/ncid/' + bb)
mi['description']['text'] = '趙岐註、金蟠訂：《趙註孟子》，日本延享四年（1747）原刊，前川六左衞門・須原茂兵衞印本（原刊年；印行年待核）。題辭書名「趙氏孟子」，題簽及版心「趙註孟子」；京都大學藏本四周雙邊有界九行二十字注文雙行，內匡郭19.7×13.7cm，單魚尾；句點付。東京大學BB13446896卷末附「崇文堂藏版書目」。'
mi['ai_note'] = TAG + '據CiNii Books新建（NCID BB15726204、BB19943055、BB13446896）；三者書肆（前川六左衞門・須原茂兵衞，崇文堂前川六左衞門）一致，統一並為一條（含東大附崇文堂藏版書目之BB13446896）；島根大學BB10129682（行款著錄八行）未並，見TODO4。無刊記著錄，且書肆含須原茂兵衞而原刊記四書林不含，判為原刊年後印，dating標inferred。與東都四書林刊記本99jw91n2mh、%s互注；庫內993gjlqf40未能確認同版，互注。' % NEW
old = P('99jw91n2mi'); os.rename(old, os.path.join(os.path.dirname(old), '99jw91n2mi-趙註孟子日本延享四年1747原刊前川六左衞門須原茂兵衞印本.json')); S(mi, os.path.join(os.path.dirname(old), '99jw91n2mi-趙註孟子日本延享四年1747原刊前川六左衞門須原茂兵衞印本.json'))
# ⑤ mk
mk = L('99jw91n2mk')
mk['dating'].update({'certainty': 'inferred', 'basis': 'CiNii Books出版項「寛永18.8[1641]」「寛永18 [1641]」（非括號推定），但兩NCID均無刊記著錄，作inferred'})
S(mk)
