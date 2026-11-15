#!/usr/bin/env python3
"""第二批（車道 a11-sjj-book-cn）：古人著作的當代整理／點校／影印本 Book（十三經注疏整理本、十三經清人注疏、老子相關）。
出版信息均據 CiNii Books 母記錄（ci.nii.ac.jp/ncid/<NCID>.json）核定；用法：build1.py [--apply]"""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa'))
import mintid
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); A = ap.parse_args()
TODAY = '2026-11-15'; LANE = 'a11-sjj-book-cn'
PKU = ('北京大學出版社', '北京'); SGJ = ('上海古籍出版社', '上海'); ZH = ('中華書局', '北京'); JS = ('江蘇古籍出版社', '南京'); HD = ('華東師範大學出版社', '上海')
# (ncid, work_id, 書名, 出版者, 年, 冊數或None, edition, 類型, 備註)
PKU_S = '《十三經注疏（整理本）》'
def pku(n, w, t, vol, who, chk, nce):
    return (n, w, t, PKU, 2000, None, '北京大學出版社2000年%s第%s冊，%s整理，%s審定' % (PKU_S, vol, who, chk), '印刷本', 'CiNii 叢書項：十三經注疏 : 整理本 / 十三經注疏整理委員會整理，%s；%s' % (vol, nce))
ITEMS = [
 ('BN10863279', 'd59f2mqyz8qp', '詩經原始', ZH, 1986, 2, '中華書局1986年李先耕點校本', '印刷本', 'CiNii 無叢書項'),
 ('BB23505368', 'd59f2huigpvk', '詩集傳', ZH, 2017, None, '中華書局2017年《中國古典文學基本叢書》本，趙長征點校', '印刷本', 'CiNii 叢書項：中國古典文學基本叢書'),
 ('BB01265817', 'd59fxz40tekg', '周易本義', ZH, 2009, None, '中華書局2009年《易學典籍選刊》本，廖名春點校', '印刷本', 'CiNii 叢書項：易學典籍選刊'),
 ('BN12135250', 'd59f23nsnu9t', '老子指歸', ZH, 1994, None, '中華書局1994年《道教典籍選刊》本，王德有點校', '印刷本', 'CiNii 叢書項：道教典籍選刊'),
 ('BA46608420', 'd59f2n8yzwg2', '毛詩後箋', ('黃山書社', '合肥'), 1999, 2, '黃山書社1999年《安徽古籍叢書》第12輯本，郭全芝校點、賀友齡審訂', '印刷本', 'CiNii 叢書項：安徽古籍叢書，第12輯'),
 ('BA90637235', 'd59f2nacxvcx', '論語後案', ('鳳凰出版社', '南京'), 2008, None, '鳳凰出版社2008年張涅、韓嵐點校本', '印刷本', 'CiNii 無叢書項'),
 ('BN03133298', 'd59f2n9qgs8y', '春秋左傳詁', ZH, 1987, 2, '中華書局1987年《十三經清人注疏》本，李解民點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BA30358470', 'd59f2n9eaj2a', '禮記訓纂', ZH, 1996, 2, '中華書局1996年《十三經清人注疏》本，饒欽農點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN05607644', 'd59f2n8t2e4i', '今文尚書考證', ZH, 1989, None, '中華書局1989年《十三經清人注疏》本，盛冬鈴、陳抗點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BA49771621', 'd59f284rdaf4', '論語集解義疏', ZH, 1985, 4, '中華書局1985年《叢書集成初編》第0481–0484冊本', '印刷本', 'CiNii 叢書項：叢書集成初編，0481-0484'),
 ('BB07546513', 'd59fy1cj3u9s', '周易程氏傳', ZH, 2011, None, '中華書局2011年《易學典籍選刊》本，王孝魚點校', '印刷本', 'CiNii 叢書項：易學典籍選刊；2011 年為該局重印著錄'),
 ('BB11650020', 'd59fxw15p5a8', '春秋公羊經傳通義', PKU, 2012, None, '北京大學出版社2012年《清代經學著作叢刊》本，崔冠華校點', '印刷本', 'CiNii 叢書項：清代經學著作叢刊'),
 ('BB2928734X', 'd59f2hpex6gx', '尚書全解', ('人民出版社', '北京'), 2019, 2, '人民出版社2019年陳良中點校本', '印刷本', 'CiNii 無叢書項'),
]
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
bids = mintid.mint('Book', LANE, len(ITEMS)) if A.apply else ['dryb%06d' % i for i in range(len(ITEMS))]
files = {}
for it, bid in zip(ITEMS, bids):
    n, wid, title, (pub, place), year, ce, ed, etype, note = it
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': etype,
         'dating': {'year': year, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books %s 著錄出版年「%d」' % (n, year)},
         'publication_info': {'publisher': pub, 'place': place}}
    if ce: d['measures'] = [{'number': ce, 'unit': '冊'}]
    d['sources'] = [{'id': n, 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + n}]
    d['ai_note'] = ('2026-11-15 十三經縱向補全·中國傳世版本（用戶口徑：古人著作的近現代排印本、整理本、影印本亦建 Book）：出版者、年份、點校整理者據 CiNii Books %s 母記錄核定；%s。出版地為出版者所在地（常識補，非 CiNii 所載）。未核原書。' % (n, note))
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    fn = '%s-%s%s.json' % (bid, title, re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、–]', '', ed)[:20])
    files['Book/%s/%s/%s/%s' % (bid[-3], bid[-2], bid[-1], fn)] = d
print('Book 新建', len(files))
for p in files: print(p)
if not A.apply: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
json.dump({d['id']: p for p, d in files.items()}, open(os.path.join(HERE, 'result1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已寫')
