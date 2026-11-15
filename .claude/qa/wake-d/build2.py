#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-d 第二輪：新建庫內缺的日本刊本 Book，寫 ledger2.tsv。用法：build2.py [--apply]"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import mintid
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'; LANE = 'wake-d'
CI = 'CiNii Books https://ci.nii.ac.jp/ncid/'
ND = 'NDL Search https://ndlsearch.ndl.go.jp/books/'
WUL = '早稻田大學圖書館'
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
# 每條：key(同組互鏈用), work, title, edition, reign, year, publisher, place, measure, basis, desc, hold[(機構,索書號,來源)], 他本互記[Book id], ncids, ndls, 原 Book 備註
N = []
def add(**k): N.append(k)

add(key='weiwu', work='d59f2ew0o268', title='魏武帝註孫子', edition='日本天保四年昌平坂學問所官板山城屋佐兵衞發行本', reign='天保', year=1833,
    pub='昌平坂學問所、山城屋佐兵衞', meas=(3, '卷'),
    basis='CiNii BB19346464 著錄出版者昌平坂學問所、山城屋佐兵衞（發弘）、天保4 [1833]',
    desc='（魏）曹操註；別題「孫子：官板：平津舘叢書本」。', also=[],
    hold=[('京都大學附屬圖書館', '8-21||ソ||13', CI + 'BB19346464')], ncids=['BB19346464'], ndls=[])
# 蒙求六本
ME = 'd59f2ogat2ps'
add(key='mengqiu', work=ME, title='標題徐狀元補注蒙求', edition='日本天和二年大坂菱屋刊本', reign='天和', year=1682, pub='菱屋', place='大坂', meas=(3, '冊'),
    basis='NDL R000000050-I000005942 著錄出版者菱屋、天和2 [1682]',
    desc='李瀚撰、徐子光補注；卷中卷頭卷末作「新刋徐狀元補注蒙求」，題簽作「校正蒙求」，序為李良（天寶5年）。', also=['988g4jlres（日本江戶初年刊寬永十二年中野市右衛門印本）'],
    hold=[(WUL, '', ND + 'R000000050-I000005942；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/bunko31/bunko31_e1935/')], ncids=[], ndls=['R000000050-I000005942'])
add(key='mengqiu', work=ME, title='標題徐狀元補注蒙求', edition='日本寬保元年東都植村藤三郎刊服部南郭考訂本', reign='寬保', year=1741, pub='植村藤三郎', place='東都（江戶）', meas=(3, '冊'),
    basis='NDL R000000050-I000005980 著錄出版者植村藤三郎、寛保元 [1741]，南郭考訂，共同刊行栂井藤右衛門（皇都）',
    desc='李瀚撰、徐子光補注、服部南郭考訂；序、題簽、版心作「新刻蒙求」，卷末作「蒙求」。', also=['988g4jlres（日本江戶初年刊寬永十二年中野市右衛門印本）'],
    hold=[(WUL, '', ND + 'R000000050-I000005980；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/bunko31/bunko31_e1938/')], ncids=[], ndls=['R000000050-I000005980'])
add(key='mengqiu', work=ME, title='標題徐狀元補注蒙求', edition='日本明和四年京都栂井藤兵衞刊服部南郭考訂本', reign='明和', year=1767, pub='栂井藤兵衞', place='皇都（京都）', meas=(3, '冊'),
    basis='NDL R000000050-I000029386 著錄出版者栂井藤兵衞、明和4 [1767]，注「元文4年序の再板」，共同刊行植村藤三郎（東都）ほか',
    desc='李瀚撰、徐子光補注、服部南郭考訂；序、題簽、版心作「新刻蒙求」，卷末作「蒙求」；元文四年序本的再板。', also=['988g4jlres（日本江戶初年刊寬永十二年中野市右衛門印本）'],
    hold=[(WUL, '', ND + 'R000000050-I000029386；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/i17/i17_02068/')], ncids=[], ndls=['R000000050-I000029386'])
add(key='mengqiu', work=ME, title='標題徐狀元補注蒙求', edition='日本寬政二年東都山崎金兵衞刊服部南郭考訂本', reign='寬政', year=1790, pub='山崎金兵衞', place='東都（江戶）', meas=(3, '冊'),
    basis='NDL R000000050-I000005981 著錄出版者山崎金兵衞、寛政2 [1790]，注「再板」，共同刊行栂井藤右衛門（皇都）ほか',
    desc='李瀚撰、徐子光補注、服部南郭考訂；序、題簽、版心作「新刻蒙求」，卷末作「蒙求」；再板。', also=['988g4jlres（日本江戶初年刊寬永十二年中野市右衛門印本）'],
    hold=[(WUL, '', ND + 'R000000050-I000005981；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/bunko31/bunko31_e1939/')], ncids=[], ndls=['R000000050-I000005981'])
add(key='mengqiu', work=ME, title='標題徐狀元補注蒙求', edition='日本寬政四年京都森嶋吉兵衞刊岡白駒箋註本', reign='寬政', year=1792, pub='森嶋吉兵衞', place='平安（京都）', meas=(3, '冊'),
    basis='NDL R000000050-I000005945 著錄出版者森嶋吉兵衞、寛政4 [1792]，岡白駒箋註，注「明和4年刊の再刻」，共同刊行出雲寺和泉掾（平安）ほか',
    desc='李瀚撰、徐子光補注、岡白駒箋註；目錄、版心作「箋註蒙求」，卷末作「徐狀元補注蒙求」；跋為黑田善（文政13年）。', also=['988g4jlres（日本江戶初年刊寬永十二年中野市右衛門印本）'],
    hold=[(WUL, '', ND + 'R000000050-I000005945；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/bunko31/bunko31_e1940/')], ncids=[], ndls=['R000000050-I000005945'])
add(key='mengqiu', work=ME, title='標題徐狀元補注蒙求', edition='日本天保三年大坂橋本德兵衞刊岡白駒箋註本', reign='天保', year=1832, pub='橋本德兵衞', place='浪華（大坂）', meas=(3, '冊'),
    basis='NDL R000000050-I000005941 著錄出版者橋本德兵衞、天保3 [1832]，岡白駒箋註，注「明和4年初版」，共同刊行出雲寺文治郎（平安）ほか',
    desc='李瀚撰、徐子光補注、岡白駒箋註；跋、題簽作「箋注蒙求」，版心作「箋註蒙求」，卷末作「徐狀元補注蒙求」；跋為黑田善（文政13年）。', also=['988g4jlres（日本江戶初年刊寬永十二年中野市右衛門印本）'],
    hold=[(WUL, '', ND + 'R000000050-I000005941；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/bunko31/bunko31_e1941/')], ncids=[], ndls=['R000000050-I000005941'])
MY = 'd59f2nkdsb9e'
add(key='mingyi', work=MY, title='名醫類案', edition='日本寬永十二年杉田勘兵衞刊本', reign='寬永', year=1635, pub='杉田勘兵衞', meas=(12, '卷'),
    basis='CiNii BA81923368 著錄出版者杉田勘兵衞、寛永12 [1635]',
    desc='（明）江瓘撰，江應元校正，江應宿述補；別題「古今名醫類案」「類按」。', also=[],
    hold=[('九州大學中央圖書館', '490/メ-1', CI + 'BA81923368')], ncids=['BA81923368'], ndls=[])
add(key='mingyi', work=MY, title='名醫類案', edition='日本寬文元年京都野田庄右衞門刊本', reign='寬文', year=1661, pub='野田庄右衞門', place='京都（烏丸通下立賣下町）', meas=(12, '卷'),
    basis='CiNii BB21132827、NDL R000000050-I000007601 著錄出版者野田庄右衞門、寛文元 [1661]',
    desc='（明）江瓘集，江應元校正，江應宿述補；題簽作「古今名醫類案」，跋題「名醫類按」，版心「類按」；序為游震得等。CiNii 神戶大學藏本存十一卷（缺卷一）。', also=[],
    hold=[('神戶大學附屬圖書館醫學分館', 'Sh-268', CI + 'BB21132827'), (WUL, '', ND + 'R000000050-I000007601；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/ya09/ya09_00517/')], ncids=['BB21132827'], ndls=['R000000050-I000007601'])
add(key='wamyo', work='d59f2q6wtrsw', title='和名類聚抄', edition='日本寬文七年大坂澁川清右衞門刊本', reign='寬文', year=1667, pub='澁川清右衞門', place='大阪', meas=(20, '卷'),
    basis='NDL R100000114-I000600024／32／41／59／67 五冊分卷記錄（卷1–4至卷17–20）著錄出版者澁川清右衞門、寛文7 [1667]；卷頭作「倭名類聚鈔」',
    desc='源順撰；卷頭題「倭名類聚鈔」，書中少量書入。', also=[],
    hold=[('關西大學圖書館', '', ND + 'R100000114-I000600024（關西大學東アジアデジタルアーカイブ，卷1–4；卷5–8 R100000114-I000600032，卷9–12 R100000114-I000600041，卷13–16 R100000114-I000600059，卷17–20 R100000114-I000600067）')],
    ncids=[], ndls=['R100000114-I000600024', 'R100000114-I000600032', 'R100000114-I000600041', 'R100000114-I000600059', 'R100000114-I000600067'])
add(key='shanghan', work='d59f2j4v7dvk', title='傷寒明理論', edition='日本享保十三年唐本屋清兵衞等刊伊東定幹句讀本', reign='享保', year=1728, pub='唐本屋清兵衞、唐本屋八郎兵衞、萬屋七郎兵衞、林權兵衞、唐本屋吉左衞門', meas=(4, '卷'),
    basis='CiNii BB22128188、NDL R100000002-I000007553404 著錄出版者唐本屋清兵衞等（國會本著錄「林權兵衞加賀屋卯兵衞刊」）、享保13 [1728]',
    desc='（金）成無己撰，（日本）伊東定幹句讀；別題「傷寒朙理論」「明理論」。', also=['988g1rptl4（日本傳刻宋開禧間張孝忠刊本，總目著錄；是否同版未核，另立）'],
    hold=[('東京大學醫學圖書館', 'V11:s41', CI + 'BB22128188'), ('國立國會圖書館', '169-12', ND + 'R100000002-I000007553404')], ncids=['BB22128188'], ndls=['R100000002-I000007553404'])
add(key='jingxue', work='d59f2q5xv6kg', title='經穴彙解', edition='日本文化四年須原屋平左衞門等刊本', reign='文化', year=1807, pub='須原屋平左衞門、秋田屋太右衞門、須原屋伊八、須原屋安次郎', meas=(8, '卷'),
    basis='CiNii BC03163746、BC02902265、BB0853710X 著錄文化4 [1807] 序，出版者須原屋平左衞門等；NDL 著錄藏版[叢桂亭]',
    desc='原昌克（南陽）編輯。', also=['988g2rxclu（日本嘉永七年叢桂亭重刊本）'],
    hold=[('天理大學附屬天理圖書館', '490//21', CI + 'BC03163746'), ('城西大學水田記念圖書館', '', CI + 'BC02902265'), ('神戶大學附屬圖書館醫學分館', 'Sh-46', CI + 'BB0853710X（存六卷）')],
    ncids=['BC03163746', 'BC02902265', 'BB0853710X'], ndls=[])
add(key='dadai', work='d59f2n9fups1', title='大戴禮記補注', edition='日本文政六年昌平坂學問所官板堀野屋儀助刊本', reign='文政', year=1823, pub='堀野屋儀助、前川六左衞門', place='江戶', meas=(13, '卷'),
    basis='NDL R000000050-I000040167 著錄出版者堀野屋儀助、文政6 [1823]，注「文化3年刋の再刊」「昌平坂學問所藏板」，題簽作「官板大戴禮記補注」',
    desc='（清）孔廣森撰；原校刊孔廣廉（乾隆59年），原序阮元；昌平坂學問所藏板，文化三年刊本的再刊，四冊。', also=['99516wn0n4（日本文化三年刻本，其初刊）', '99516wbs3k（日本文化六年翻刻乾隆甲寅本）'],
    hold=[(WUL, '', ND + 'R000000050-I000040167；古典籍總合データベース http://archive.wul.waseda.ac.jp/kosho/ro12/ro12_02002/')], ncids=[], ndls=['R000000050-I000040167'])
add(key='jinyin', work='d59f2pxhisxs', title='金銀圖錄', edition='日本文政六年河內屋源七郎等刊本', reign='文政', year=1823, pub='河內屋源七郎、須原屋茂兵衞、和泉屋庄次郎、植村藤右衞門', meas=(6, '卷'),
    basis='CiNii BB24316906、BB10822685 著錄出版者河內屋源七郎等、文政6 [1823]，六卷附言一卷',
    desc='近藤守重（重藏）輯；六卷附言一卷。', also=['988g8gdsej（日本文化七年彩色套印本）'],
    hold=[('東京大學總合圖書館', 'N50:246', CI + 'BB24316906'), ('島根大學附屬圖書館', 'NDC:337.21/Ko73', CI + 'BB10822685（存六冊，缺卷一）')],
    ncids=['BB24316906', 'BB10822685'], ndls=[])
add(key='wuxing', work='d59f28knuio3', title='五行大義', edition='日本元祿十二年井上忠兵衞刊本', reign='元祿', year=1699, pub='井上忠兵衞', place='京都', meas=(5, '卷'),
    basis='NDL R100000002-I000007553404 之外：NDL R100000002-I000007567087（國會，京都井上忠兵衞刊、大阪象牙屋治郎兵衞等印）、CiNii BA86749836、BB21311462 著錄井上忠兵衞、元祿12 [1699]',
    desc='（隋）蕭吉撰；五卷五冊。', also=['988g8s8t1j（清嘉慶間阮元進呈日本活字佚存叢書本）', '99819vlwjn、994xxq9zwg（日本刻佚存叢書本）'],
    hold=[('國立國會圖書館', '特2-1453', ND + 'R100000002-I000007567087'), ('名古屋大學文學部圖書室', 'C||VIII||6', CI + 'BA86749836'), ('大阪大學附屬圖書館總合圖書館', '', CI + 'BB21311462')],
    ncids=['BA86749836', 'BB21311462'], ndls=['R100000002-I000007567087'])
add(key='luxin', work='d59f2husrjsy', title='顱顖經', edition='日本寬政十二年稽古齋木活字本', et='活字本', reign='寬政', year=1800, pub='稽古齋', meas=(2, '卷'),
    basis='CiNii BD09056349、NDL R100000136-I1971430859808589591 著錄稽古齋、寛政12 [1800]；見返題「清國乾隆秘府所藏無版書一活字刋行／寛政十二年庚申秋九月 稽古齋」，跋為醫師小川文菴忠實（寛政十二年九月）',
    desc='依聚珍版（四庫全書）本木活字排印；含聚珍版顱顖經序、四庫提要、原序，二卷。', also=['988g5qoidn（日本傳鈔四庫全書本）'],
    hold=[('天理大學附屬天理圖書館', '498//173', CI + 'BD09056349')], ncids=['BD09056349'], ndls=['R100000136-I1971430859808589591'])
add(key='lunyu', work='d59f284r21vn', title='論語集解義疏', edition='日本寬延三年刊根本遜志校正本', reign='寬延', year=1750, pub='藤木久市、奥村喜兵衞、前川六左衞門、伏見屋善六', meas=(10, '卷'),
    basis='CiNii BB15451241、BA83472088、BB10131232 俱著錄（魏）何晏集解、（梁）皇侃義疏、（日本）根本遜志校正，出版者藤木久市等、寛延3 [1750] 刊',
    desc='何晏集解、皇侃義疏，根本遜志（武夷）校正；序題「論語集解」，新刻序題「皇侃論語義疏」，敘及題簽題「論語義疏」；訓點付。為皇侃《論語義疏》自中國佚失後回傳的日本刊本，寛延三年序刊。',
    also=['994yl5p7gg、994yl60g00（日本寛政七年萬蘊堂刻元治元年浪華萬蘊堂補刻本，據寛延三年序刊本增刻後修）', '99jiagxzbt（日本元治元年萬蘊堂刊本）'],
    hold=[('東京大學總合圖書館', 'B60:2054', CI + 'BB15451241'), ('關西大學圖書館', 'L23**A*1099', CI + 'BA83472088'), ('島根大學附屬圖書館', 'NDC:123.83/Ka11', CI + 'BB10131232'),
          ],
    ncids=['BB15451241', 'BA83472088', 'BB10131232'], ndls=[])
add(key='chazhi', work='d59g10f169zt', title='和漢茶誌', edition='日本天保十三年秋田屋太右衞門等刊本', reign='天保', year=1842, pub='秋田屋太右衞門、勝村治右衞門、山城屋佐兵衞、岡田屋嘉七、須原屋伊八、須原屋茂兵衞', meas=(3, '卷'),
    basis='CiNii BB2594496X 著錄出版者秋田屋太右衞門等、天保13 [1842]',
    desc='三谷良朴（宗鎮）著；別題「茶志」「茶誌」「南川氏茶誌」。', also=['996jc9z0cl（日本享保十三年本）'],
    hold=[('東京大學總合圖書館', 'YB20:23', CI + 'BB2594496X')], ncids=['BB2594496X'], ndls=[])

# 修正 wuxing basis 誤植
for n in N:
    if n['key'] == 'wuxing': n['basis'] = 'NDL R100000002-I000007567087（國會，京都井上忠兵衞刊、大阪象牙屋治郎兵衞等印）、CiNii BA86749836、BB21311462 著錄井上忠兵衞、元祿12 [1699]'

LINE = '和刻本日本館藏專項第二輪（車道 wake-d，2026-11-15）：'
ids = mintid.mint('Book', LANE, len(N)) if APPLY else ['dry%07d' % i for i in range(len(N))]
grp = {}
for n, bid in zip(N, ids): n['bid'] = bid; grp.setdefault(n['key'], []).append(bid)
files = {}
for n in N:
    bid = n['bid']
    d = {'schema_version': 1, 'type': 'book', 'title': n['title'], 'work_id': n['work'], 'edition': n['edition'], 'edition_type': n.get('et', '刻本'),
         'dating': {'era': '日本', 'reign': n['reign'], 'year': n['year'], 'certainty': 'attested', 'source': 'catalog', 'basis': n['basis']}}
    pi = {'publisher': n['pub']}
    if n.get('place'): pi['place'] = n['place']
    d['publication_info'] = pi
    d['measures'] = [{'number': n['meas'][0], 'unit': n['meas'][1]}]
    d['provenance'] = [dict(institution=i, **({'call_number': c} if c else {}), source=s) for i, c, s in n['hold']]
    srcs = [{'id': 'cinii-' + x.lower(), 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + x} for x in n['ncids']]
    srcs += [{'id': 'ndl-' + x.lower(), 'name': 'NDL Search', 'type': 'url', 'details': 'https://ndlsearch.ndl.go.jp/books/' + x} for x in n['ndls']]
    d['description'] = {'text': n['desc'], 'sources': ['%s %s' % (s['name'], s['details']) for s in srcs]}
    d['sources'] = srcs
    sib = [x for x in grp[n['key']] if x != bid]
    note = LINE + '新建（庫內該 Work 下無此日本刊本）。據 CiNii Books／NDL Search 書誌與所藏頁核定（刊者、年、卷冊、所藏館及索書號錄自該頁），未核原書。'
    if sib: note += '同 Work 下並列另立的日本刊本（異版，未硬並）：' + '、'.join(sib) + '。'
    if n['also']: note += '庫內相關他本（互記，不硬並）：' + '；'.join(n['also']) + '。'
    d['ai_note'] = note
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', n['edition'])[:24]
    files['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, n['title'], safe)] = d
rows = [('Book id', '題名', '判定', '日本館藏', '依據URL', '說明')]
for n in N:
    rows.append((n['bid'], n['title'], '新建', '；'.join(dict.fromkeys(h[0] for h in n['hold'])), (CI + n['ncids'][0]) if n['ncids'] else ND + n['ndls'][0], n['edition']))
print('新建', len(N))
for p in files: print(p)
if not APPLY: sys.exit(0)
for p, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(p)), exist_ok=True); open(os.path.join(BI, p), 'w', encoding='utf-8').write(jd(d))
open(os.path.join(HERE, 'ledger2.tsv'), 'w', encoding='utf-8').write('\n'.join('\t'.join(r) for r in rows) + '\n')
json.dump(list(files), open(os.path.join(HERE, 'changed2.json'), 'w'), ensure_ascii=False, indent=0)
print('已寫')
