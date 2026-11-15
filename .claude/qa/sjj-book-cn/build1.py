#!/usr/bin/env python3
"""第一批（車道 a11-sjj-book-cn）：古人著作的當代整理／點校／影印本 Book（十三經注疏整理本、十三經清人注疏、老子相關）。
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
 pku('BA5280090X', 'd59f28kra4n7', '周易正義', '1', '盧光明、李申', '呂紹綱', ''),
 pku('BA52801844', 'd59f28mpiiv9', '尚書正義', '2–3', '廖名春、陳明', '呂紹綱', ''),
 pku('BA52802359', 'd59f28ngzeo1', '毛詩正義', '4–6', '龔抗雲等', '劉家和', ''),
 pku('BA52802891', 'd59f28np3ksk', '周禮注疏', '7–9', '趙伯雄', '王文錦', ''),
 pku('BA52803078', 'd59f28np3ksj', '儀禮注疏', '10–11', '彭林', '王文錦', ''),
 pku('BA5280317X', 'd59f28nhx4ap', '禮記正義', '12–15', '龔抗雲', '王文錦', ''),
 pku('BA52803282', 'd59f28nf3zeq', '春秋左傳正義', '16–19', '浦衛忠等', '楊向奎', ''),
 pku('BA52803577', 'd59f28nosc90', '春秋公羊傳注疏', '20–21', '浦衛忠', '楊向奎', ''),
 pku('BA5280368X', 'd59f28na46pw', '春秋穀梁傳注疏', '22', '夏先培', '楊向奎', ''),
 pku('BA52803748', 'd59f2hqvd1qa', '論語注疏', '23', '朱漢民', '張豈之', ''),
 pku('BA52803839', 'd59f2ht89lhc', '爾雅注疏', '24', '李傳書', '徐朝華', ''),
 pku('BA52803996', 'd59f24mpohs0', '孟子注疏', '25', '廖名春、劉佑平', '錢遜', ''),
 pku('BA5280406X', 'd59f28noh3ph', '孝經注疏', '26', '鄧洪波', '錢遜', ''),
 # 上海古籍出版社《十三經注疏》整理本
 ('BA86584474', 'd59f28mpiiv9', '尚書正義', SGJ, 2007, None, '上海古籍出版社2007年《十三經注疏》整理本，黃懷信整理', '印刷本', 'CiNii 叢書項：十三經注疏'),
 ('BA90074063', 'd59f28np3ksj', '儀禮注疏', SGJ, 2008, 3, '上海古籍出版社2008年《十三經注疏》整理本，王輝整理', '印刷本', 'CiNii 叢書項：十三經注疏'),
 ('BA88285587', 'd59f28nhx4ap', '禮記正義', SGJ, 2008, 3, '上海古籍出版社2008年《十三經注疏》整理本，呂友仁整理', '印刷本', 'CiNii 叢書項：十三經注疏'),
 ('BA90833980', 'd59f28noh3ph', '孝經注疏', SGJ, 2009, None, '上海古籍出版社2009年《十三經注疏》整理本，金良年整理', '印刷本', 'CiNii 叢書項：十三經注疏'),
 ('BB04802774', 'd59f28np3ksk', '周禮注疏', SGJ, 2010, 3, '上海古籍出版社2010年《十三經注疏》整理本，彭林整理', '印刷本', 'CiNii 叢書項：十三經注疏'),
 ('BB04801771', 'd59f2ht89lhc', '爾雅注疏', SGJ, 2010, None, '上海古籍出版社2010年《十三經注疏》整理本，王世偉整理', '印刷本', 'CiNii 叢書項：十三經注疏'),
 ('BB15776676', 'd59f28ngzeo1', '毛詩注疏', SGJ, 2013, 3, '上海古籍出版社2013年《十三經注疏》整理本，朱傑人、李慧玲整理（附陸德明音釋）', '印刷本', 'CiNii 叢書項：十三經注疏'),
 ('BB18899071', 'd59f28nosc90', '春秋公羊傳注疏', SGJ, 2014, 2, '上海古籍出版社2014年《十三經注疏》整理本，刁小龍整理', '印刷本', 'CiNii 叢書項：十三經注疏；同年另有 BB17986567 著錄，同書'),
 # 中華書局《十三經清人注疏》及其他
 ('BN11987630', 'd59f2n88rytc', '周易集解纂疏', ZH, 1994, None, '中華書局1994年《十三經清人注疏》本，潘雨廷點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN05495460', 'd59f2n94m681', '詩三家義集疏', ZH, 1987, 2, '中華書局1987年《十三經清人注疏》本，吳格點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN04565174', 'd59f2n9dctfl', '禮記集解', ZH, 1989, 3, '中華書局1989年《十三經清人注疏》本，沈嘯寰、王星賢點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BA32464253', 'd59fxvjnh0jl', '春秋穀梁經傳補注', ZH, 1996, 3, '中華書局1996年《十三經清人注疏》本，駢宇騫、郝淑慧點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN14691018', 'd59f2ntm7xts', '孟子正義', ZH, 1987, 2, '中華書局1987年《新編諸子集成》本，沈文倬點校', '印刷本', 'CiNii 叢書項：新編諸子集成，第1輯'),
 ('BN0327402X', 'd59f2n97qjnk', '周禮正義', ZH, 1987, 14, '中華書局1987年《十三經清人注疏》本，王文錦、陳玉霞點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN0561375X', 'd59f2nup8lq9', '尚書今古文注疏', ZH, 1986, 2, '中華書局1986年《十三經清人注疏》本，陳抗、盛冬鈴點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN04568037', 'd59f2n91t1c0', '毛詩傳箋通釋', ZH, 1989, 3, '中華書局1989年《十三經清人注疏》本，陳金生點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN05526994', 'd59fyroaperk', '論語正義', ZH, 1990, 2, '中華書局1990年《十三經清人注疏》本，高流水點校', '印刷本', 'CiNii 叢書項：十三經清人注疏'),
 ('BN13064613', 'd59f2n9a8g02', '儀禮正義', JS, 1993, 3, '江蘇古籍出版社1993年段熙仲點校本', '印刷本', 'CiNii 著錄無叢書項'),
 ('BN06141645', 'd59f2hry2h34', '四書章句集注', ZH, 1983, None, '中華書局1983年《新編諸子集成》本', '印刷本', 'CiNii 叢書項：新編諸子集成，第1輯'),
 ('BN06788511', 'd59fxw10e41u', '十三經注疏附校勘記', ZH, 1980, 2, '中華書局1980年影印阮元校刻本', '影印本', 'CiNii 責任者「阮元校刻」；底本即阮刻（清嘉慶二十年南昌府學刻本），未核原書'),
 ('BB0105706X', 'd59fxw10e41u', '十三經注疏（清嘉慶刊本）', ZH, 2009, None, '中華書局2009年影印清嘉慶刊本（阮元校刻）', '影印本', 'CiNii 副題「清嘉慶刊本」、責任者「阮元校刻」'),
 ('BA49830607', 'd59f2nkwtse9', '老子集解附考異', ZH, 1985, None, '中華書局1985年《叢書集成初編》本', '印刷本', 'CiNii 叢書項：叢書集成初編，0540'),
 ('BN08777968', 'd59f2nmkg075', '老子衍', ZH, 1962, None, '中華書局1962年王孝魚點校本（與《莊子通》合冊）', '印刷本', 'CiNii 書名「老子衍 ; 莊子通」；合冊著錄，本條只就《老子衍》立'),
 ('BB04109104', 'd59f2hf5nfuo', '老子道德經古本集註', HD, 2010, None, '華東師範大學出版社2010年《歷代文史要籍注釋選刊》本，黃曙輝點校', '印刷本', 'CiNii 叢書項：歷代文史要籍注釋選刊 老子'),
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
