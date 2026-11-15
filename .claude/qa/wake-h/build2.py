#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和刻本日本館藏專項·第二輪（車道 wake-h，shard7）：新建庫內該 Work 下缺失的日本版本。
用法：build2.py [--apply]。台賬 ledger2.tsv 由本腳本同時寫出。"""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa'))
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); A = ap.parse_args()
TODAY = '2026-11-15'
N = 'https://ndlsearch.ndl.go.jp/books/'; CI = 'https://ci.nii.ac.jp/ncid/'
NDL = '國立國會圖書館'
def nd(x): return 'NDL Search ' + N + x
def ci(x): return 'CiNii Books ' + CI + x

# 每條：work, title, edition, etype, reign, year, certainty, dbasis, publisher, measures, hold[(機構, 索書號|None, source)], src[(id,name,url)], desc, note
ITEMS = [
 dict(work='d59f28k9hlok', title='續高僧傳', edition='日本慶安四年西村又左衞門刊本', etype='刻本', reign='慶安', year=1651,
  cert='attested', dbasis='NDL Search 著錄出版年「慶安4」，出版者西村又左衞門；CiNii Books 多館著錄同為「慶安4［1651］」', pub='西村又左衞門',
  meas=[(40, '卷'), (16, '冊')],
  hold=[(NDL, None, nd('R100000002-I000007614479')), ('東京大學東洋文化研究所', '子;釋家:史傳:6.30', ci('BB22606508')),
        ('東京大學總合圖書館', 'C40:469', ci('BB1619924X')), ('岡山大學附屬圖書館', '4門/181', ci('BB14081169')),
        ('東京大學文學部', '漢籍C:13（存29卷）', ci('BB17043767')), ('佛教大學附屬圖書館', 'G佛書||528（存38卷）', ci('BA85923122'))],
  src=[('ndl-R100000002-I000007614479', 'NDL Search', N + 'R100000002-I000007614479'), ('cinii-BB1619924X', 'CiNii Books', CI + 'BB1619924X')],
  desc='《續高僧傳》四十卷（附音釋），唐釋道宣撰，日本慶安四年（1651）西村又左衞門刊，十六冊（合八冊）。',
  note='與庫內「日本正保四年刊本」(988g6lw8p0) 刊年不同，另立；NDL 著錄「慶安4」、CiNii 另有「慶安辛卯」著錄，皆指同一刊年。'),
 dict(work='d59f2gofm1oi', title='瑞竹堂經驗方', edition='日本寬政七年繕生藥室活字本', etype='活字本', reign='寬政', year=1795,
  cert='attested', dbasis='CiNii Books 著錄出版者繕生藥室、寛政7［1795］，注記「見返しに『寛政乙卯仲秋』『繕生藥室活字刷印』とあり」', pub='繕生藥室',
  meas=[(15, '卷')],
  hold=[('東京大學總合圖書館', 'V11:537', ci('BB18596568')), ('大阪府立中之島圖書館', ':692:94:#', ci('BB20418631'))],
  src=[('cinii-BB18596568', 'CiNii Books', CI + 'BB18596568'), ('cinii-BB20418631', 'CiNii Books', CI + 'BB20418631')],
  desc='《瑞竹堂經驗方》十五卷，元薩謙齋（沙圖穆蘇）編，明高濂校刻本之日本重印；日本桂川國瑞讐勘，寬政七年（1795）繕生藥室活字刷印。',
  note='NDL 另藏「瑞竹堂經驗方15卷 寛政8木活字印 3册」(R100000002-I000007555661)，疑與本版同屬繕生藥室活字本，因年份（寛政8／寛政7）與出版者（無）著錄不一，未併入、未掛 NDL 館藏。'),
 dict(work='d59gdtwu05qe', title='論語語由', edition='日本文化三年晚翠樓刊本', etype='刻本', reign='文化', year=1806,
  cert='attested', dbasis='NDL Search／CiNii Books 著錄出版者晚翠樓，文化3［1806］序跋（跋署文化三年十一月）', pub='晚翠樓',
  meas=[(20, '卷')],
  hold=[('東京大學總合圖書館', 'B60:2222', ci('BB15516788')), ('大阪大學附屬圖書館', '（存12卷）', ci('BB12700510')),
        ('關西大學圖書館', 'L23**100*296', ci('BA83477864')), ('關西大學圖書館', 'L24||||1-1017', ci('BA81930137')),
        ('九州大學中央圖書館', '123/ロ-1/1-1/20', ci('BA80783059')), ('筑波大學附屬圖書館', 'ロ860-75', ci('BA45772509'))],
  src=[('ndl-R100000136-I1970023484883403054', 'NDL Search', N + 'R100000136-I1970023484883403054'), ('cinii-BB15516788', 'CiNii Books', CI + 'BB15516788')],
  desc='《論語語由》二十卷，龜井魯（南冥）撰，其子龜井昱（昭陽）校，日本文化三年（1806）晚翠樓刊。',
  note='庫內此 Work 原僅有「日本東洋圖書刊行會排印本」；NDL 另有 1879 年中野啓藏、1880 年華井聚文堂等明治刊本，屬後出重刊，本輪未建。'),
 dict(work='d59gdtwu05qp', title='論語古義', edition='日本奎文館文會堂刊本（正德二年序）', etype='刻本', reign='正德', year=1712,
  cert='inferred', dbasis='NDL Search／CiNii Books 著錄出版者奎文館、文會堂，出版年「正徳2［1712］序」（以序年繫年）', pub='奎文館、文會堂',
  meas=[(10, '卷'), (4, '冊')],
  hold=[('早稻田大學圖書館', None, nd('R000000050-I000030898')), ('東京大學總合圖書館', 'B60:3826', ci('BB14584159')),
        ('筑波大學附屬圖書館', 'ロ860-51', ci('BA44563886')), ('一橋大學附屬圖書館', 'Umetani/B:253', ci('BD02786194'))],
  src=[('ndl-R000000050-I000030898', 'NDL Search', N + 'R000000050-I000030898'), ('ndl-R100000136-I1970023484963770887', 'NDL Search', N + 'R100000136-I1970023484963770887')],
  desc='《論語古義》十卷，日本伊藤維楨（仁齋）述，奎文館、文會堂刊，伊藤長胤序署正德二年（1712）；NDL 著錄為刊本十卷四冊。',
  note='庫內此 Work 原僅有「日本東洋圖書刊行會排印本」。NDL 另有享保九年（1724）奎文館、文會堂著錄（R100000136-I1971149384783558808），疑為同版後印，本輪未另立。與文政十二年文泉堂再刻本另立互鏈。'),
 dict(work='d59gdtwu05qp', title='論語古義', edition='日本文政十二年文泉堂再刻本', etype='刻本', reign='文政', year=1829,
  cert='attested', dbasis='NDL Search／CiNii Books 著錄出版者文泉堂，文政12［1829］；Waseda 著錄注記「跋題：再刻論語古義」「正德2年序の再刻」', pub='文泉堂',
  meas=[(10, '卷')],
  hold=[('早稻田大學圖書館', None, nd('R000000050-I000072581')), ('京都大學經濟學部圖書室', '漢籍||17||5-1||Ron 132855', ci('BB16820092')),
        ('國立民族學博物館', '牧野漢/123.83/イトウ', ci('BB16029090'))],
  src=[('ndl-R000000050-I000072581', 'NDL Search', N + 'R000000050-I000072581'), ('cinii-BB16820092', 'CiNii Books', CI + 'BB16820092')],
  desc='《論語古義》十卷（附總論一卷），日本伊藤維楨述，文政十二年（1829）文泉堂再刻（正德二年序本之再刻）。',
  note='與正德二年序奎文館、文會堂刊本另立互鏈；古義堂、文泉堂合刻《大學定本・中庸發揮・論語古義・孟子古義》叢刻著錄（CiNii BB21623250）未併入。'),
 dict(work='d59f2gooz5z5', title='飲膳正要', edition='日本天明二年跋寫本', etype='抄本', reign='天明', year=1782,
  cert='inferred', dbasis='NDL Search／CiNii Books 著錄「天明2［1782］跋」，資料形態為書寫資料，書寫者不明', pub=None,
  meas=[(3, '卷')],
  hold=[('東京國立博物館', '052-3-7', ci('BB08329860'))],
  src=[('ndl-R100000136-I1970023484941923894', 'NDL Search', N + 'R100000136-I1970023484941923894'), ('cinii-BB08329860', 'CiNii Books', CI + 'BB08329860')],
  desc='《飲膳正要》三卷，元忽思慧撰，日本天明二年（1782）跋寫本；NDL 注記載原刊記有「成化乙未鼎新刊行」，知所據為明成化刊本。書寫者不明。',
  note='庫內已有「日本傳鈔明成化間刊本」(988g8yssg5，故宮藏，未載年份)，二者可能同屬日本傳鈔明成化本一系，但年份與藏處不能對定，另立互鏈，不合併。'),
 dict(work='d59f2gooz5z5', title='飲膳正要', edition='日本天保十四年寫本', etype='抄本', reign='天保', year=1843,
  cert='inferred', dbasis='NDL Search／CiNii Books 著錄出版年「天保14［1843］」，資料形態為書寫資料，書寫者不明', pub=None,
  meas=[(3, '卷')],
  hold=[('東京國立博物館', '帝漢(旧)-36', ci('BB12111622'))],
  src=[('ndl-R100000136-I1971993809820416144', 'NDL Search', N + 'R100000136-I1971993809820416144'), ('cinii-BB12111622', 'CiNii Books', CI + 'BB12111622')],
  desc='《飲膳正要》三卷，元忽思慧撰，日本天保十四年（1843）寫本，書寫者不明。',
  note='與天明二年跋寫本、故宮藏「日本傳鈔明成化間刊本」(988g8yssg5) 另立互鏈，不合併。'),
 dict(work='d59f2hm0k5j6', title='中庸或問', edition='日本寬政七年菱屋孫兵衞刊倭板四書本', etype='刻本', reign='寬政', year=1795,
  cert='attested', dbasis='NDL Search／CiNii Books 著錄出版者菱屋孫兵衞，寛政7［1795］，注記「刊本」「版心に倭板四書 中庸或問 山崎嘉點」', pub='菱屋孫兵衞',
  meas=[],
  hold=[('九州大學中央圖書館', '碩水文庫/ヤ/4', ci('BA80025083'))],
  src=[('ndl-R100000136-I1971149384777265932', 'NDL Search', N + 'R100000136-I1971149384777265932'), ('cinii-BA80025083', 'CiNii Books', CI + 'BA80025083')],
  desc='《中庸或問》，宋朱熹撰，日本山崎嘉點（闇齋）點，寬政七年（1795）菱屋孫兵衞刊，為《倭板四書》之一種（版心題「倭板四書 中庸或問」）。',
  note='屬《倭板四書》叢刻之一；同一刊本的《四書章句集注》總條見 991mmu8uff（日本寬政七年京菱屋孫兵衛刊本）。庫內另有「倭板四書本」(994ykgq801，北京大學圖書館藏，未載刊年)，是否同版未能核定，另立互鏈。NDL 另有「石田治兵衞、石田忠兵衞發兌」寛政7再校著錄，疑為同版異肆印本，未另立。'),
 dict(work='d59f2nj2c934', title='醫學源流', edition='日本慶長十六年梅壽刊本', etype=None, reign='慶長', year=1611,
  cert='attested', dbasis='NDL Search／CiNii Books 著錄出版者梅壽、出版年「慶長16［1611］」', pub='梅壽',
  meas=[],
  hold=[('東京大學總合圖書館', 'A00:6461', ci('BC03412385'))],
  src=[('ndl-R100000136-I1970023484918660759', 'NDL Search', N + 'R100000136-I1970023484918660759'), ('cinii-BC03412385', 'CiNii Books', CI + 'BC03412385')],
  desc='《醫學源流》，明熊宗立撰，日本慶長十六年（1611）梅壽刊；序首書名「新刋名方類證醫書大全」，題簽書名「毉學源流」。',
  note='庫內已有「日本傳鈔明刊本」(988g4wehos，故宮藏)，與本版是否同源未核；NDL 另有 Waseda 藏「寛永9［1632］」著錄（R000000050-I000016678，未載出版者），因無出版者，未另立。edition_type 因 NDL/CiNii 未明言活字或整版，不填。'),
 dict(work='d59f2py1t81u', title='職官志', edition='日本文化十三年跋和泉屋庄次郎刊本', etype='刻本', reign='文化', year=1816,
  cert='inferred', dbasis='NDL Search／CiNii Books 著錄出版者和泉屋庄次郎，出版年「文化13［1816］跋」（以跋年繫年），注記「刊本」', pub='和泉屋庄次郎',
  meas=[(7, '卷')],
  hold=[('島根大學附屬圖書館', 'NDC:322.134/G18', ci('BB11507617'))],
  src=[('ndl-R100000136-I1970304959923076128', 'NDL Search', N + 'R100000136-I1970304959923076128'), ('cinii-BB11507617', 'CiNii Books', CI + 'BB11507617')],
  desc='《職官志》七卷，蒲生秀實（君平）稿，會澤安跋署文化十三年（1816），和泉屋庄次郎刊。',
  note='庫內已有「日本天保六年浪華書林刊本」(988g5h05jf)，為 1835 年加賀屋善藏等重刊，本版為其前之初刊。'),
 dict(work='d59f2pzf4pvk', title='煎茶小述', edition='日本天保六年小林新兵衞等刊本', etype='刻本', reign='天保', year=1835,
  cert='attested', dbasis='NDL Search 著錄出版者小林新兵衞［ほか4名］、出版年「天保6［1835］」，解題載「天保6年正月刊行」', pub='小林新兵衞（嵩山房）等',
  meas=[(1, '冊')],
  hold=[(NDL, None, nd('R100000002-I000007300251')), ('九州大學中央圖書館', '雅俗文庫/64技芸b/セン', ci('BB22295339')), ('筑波大學附屬圖書館', 'ス420-15', ci('BA73221070'))],
  src=[('ndl-R100000002-I000007300251', 'NDL Search', N + 'R100000002-I000007300251'), ('cinii-BB22295339', 'CiNii Books', CI + 'BB22295339')],
  desc='《煎茶小述》一冊，山本徳潤撰，江戶書肆嵩山房小林新兵衞等於天保六年（1835）正月刊行，藏版者都龍軒；為煎茶道指南書。',
  note='庫內已有「日本嘉永二年1849年刊本」(988g4d1s0c)，為河內屋喜兵衞等後印；本版為其前之初印。'),
 dict(work='d59fxw2fw9og', title='齊家寶要', edition='日本寶永七年林正五郎井上忠兵衞刊本（題「重定齊家寶要」）', etype='刻本', reign='寶永', year=1710,
  cert='attested', dbasis='NDL Search／CiNii Books 著錄出版者林正五郎、井上忠兵衞，出版年「寶永7」', pub='林正五郎、井上忠兵衞',
  meas=[(2, '卷'), (4, '冊')],
  hold=[(NDL, None, nd('R100000002-I000007512101')), ('東京大學東洋文化研究所', '仁井田:子:N3020', ci('BB26812942')),
        ('大阪大學附屬圖書館', None, ci('BB16815784')), ('國立民族學博物館', '牧野漢/124.1/チヨウ', ci('BB16090003'))],
  src=[('ndl-R100000002-I000007512101', 'NDL Search', N + 'R100000002-I000007512101'), ('cinii-BB26812942', 'CiNii Books', CI + 'BB26812942')],
  desc='《重定齊家寶要》二卷，清張文嘉編輯、張廷瑞較閱，日本寶永七年（1710）林正五郎、井上忠兵衞刊，四冊（合二冊）。',
  note='庫內已有「日本享保二十年西村源六等刻本」(993f42ybcx)，NDL 著錄其刊者為西村市郎右衞門，刊年1735，與本版寶永七年版不同。庫內另有 Work「重定齊家寶要」(d59f2malyfpd) 與本 Work 疑為重複立 Work，未動。'),
 dict(work='d59fxw2fw9og', title='齊家寶要', edition='日本元祿十五年吉村吉左衞門刊本（題「重定齊家寶要」）', etype='刻本', reign='元祿', year=1702,
  cert='attested', dbasis='NDL Search 著錄出版者吉村吉左衞門，出版年「元祿15［1702］」', pub='吉村吉左衞門',
  meas=[(2, '卷')],
  hold=[],
  src=[('ndl-R100000136-I1971149384770220834', 'NDL Search', N + 'R100000136-I1971149384770220834')],
  desc='《重定齊家寶要》二卷，清張文嘉編、張廷瑞校，日本元祿十五年（1702）吉村吉左衞門刊。',
  note='本條僅 NDL 一條著錄（印記：樂山堂），館藏機構未能自 NDL/CiNii 頁面確認，故暫不掛日本館藏。'),
 dict(work='d59f28noh3pc', title='尚書注疏', edition='日本安永六年風月莊左衞門等刻本（芥元澄句讀）', etype='刻本', reign='安永', year=1777,
  cert='attested', dbasis='NDL Search 著錄出版年「安永6［1777］」，出版者風月莊左衞門、田中市兵衞、吉田四郎右衞門、今村八兵衞，注記「刻本」', pub='風月莊左衞門、田中市兵衞、吉田四郎右衞門、今村八兵衞',
  meas=[(20, '卷')],
  hold=[('國立國語研究所', 'W481/Ko74', ci('BD10841877')), ('九州大學中央圖書館', '123.2/Ko 11/1', ci('BB15663942')),
        ('東京大學總合圖書館', 'B60:2053', ci('BB15450464'))],
  src=[('ndl-R100000136-I1970304959816525615', 'NDL Search', N + 'R100000136-I1970304959816525615'), ('cinii-BB15663942', 'CiNii Books', CI + 'BB15663942')],
  desc='《尚書註疏》二十卷，漢孔安國傳、唐孔穎達疏，題明李長春等奉敕重校刊（即明萬曆北監本系統）；日本芥元澄句讀，安永六年（1777）風月莊左衞門等刊。',
  note='題名「尚書註疏」；與庫內「日本享保十六年刊寬政三年修補本七經孟子考文補遺之一」(988g3mtudv) 不同版。'),
 dict(work='d59fxvjjq60w', title='周易程朱傳義', edition='日本寬文四年野田庄右衞門刊本（松永寸雲校）', etype='刻本', reign='寬文', year=1664,
  cert='attested', dbasis='NDL Search／CiNii Books 著錄出版者野田庄右衞門，出版年「寛文4年（1664年）」，責任者松永寸雲［校］', pub='野田庄右衞門',
  meas=[(24, '卷')],
  hold=[('尾道市立大學附屬圖書館', '123//6', ci('BN02664200')), ('北海道大學附屬圖書館', 'DC19:181.11/mat', ci('BN02664200'))],
  src=[('ndl-R100000136-I1971712334698495778', 'NDL Search', N + 'R100000136-I1971712334698495778'), ('cinii-BN02664200', 'CiNii Books', CI + 'BN02664200')],
  desc='《周易程朱傳義》二十四卷序目一卷，宋程頤傳、朱熹本義，日本松永寸雲校，寬文四年（1664）野田庄右衞門刊；別名《首書易經集註》。',
  note='庫內已有「日本寶永六年出雲寺和泉刻本」(993ejkq2o2)，為不同版本。'),
]
SHORT = {'d59f28k9hlok': '續高僧傳'}
sys.path.insert(0, os.path.join(BI, '.claude/qa'))
import mintid
ids = mintid.mint('Book', 'wake-h', len(ITEMS)) if A.apply else ['dry%07d' % i for i in range(len(ITEMS))]
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
files = {}; rows = []
for it, bid in zip(ITEMS, ids):
    d = {'schema_version': 1, 'type': 'book', 'title': it['title'], 'work_id': it['work'], 'edition': it['edition']}
    if it['etype']: d['edition_type'] = it['etype']
    d['dating'] = {'era': '日本', 'reign': it['reign'], 'year': it['year'], 'certainty': it['cert'], 'source': 'catalog', 'basis': it['dbasis']}
    if it['pub']: d['publication_info'] = {'publisher': it['pub'], 'place': '日本', 'details': '據 NDL Search／CiNii Books 著錄'} if False else {'publisher': it['pub']}
    if it['meas']: d['measures'] = [{'number': n, 'unit': u} for n, u in it['meas']]
    prov = []
    for inst, call, src in it['hold']:
        e = {'institution': inst}
        if call: e['call_number'] = call
        e['source'] = src; prov.append(e)
    if prov: d['provenance'] = prov
    d['description'] = {'text': it['desc'], 'sources': [s[1] + ' ' + s[2] for s in it['src']]}
    d['sources'] = [{'id': i, 'name': n, 'type': 'url', 'details': u} for i, n, u in it['src']]
    d['ai_note'] = '2026-11-15 和刻本日本館藏專項第二輪（車道 wake-h）：據 NDL Search／CiNii Books 書目頁新建（庫內該 Work 原無此版）；版本名、刊年、出版者、館藏與索書號均錄自上列頁面，未核原書。' + it['note']
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', it['edition'])[:24]
    files['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, it['title'], safe)] = d
    rows.append((bid, it['title'], '新建', '、'.join(sorted({h[0] for h in it['hold']})), ' '.join(s[2] for s in it['src']), it['edition']))
print('Book', len(ITEMS))
for p in files: print(p)
if not A.apply: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
with open(os.path.join(HERE, 'ledger2.tsv'), 'w', encoding='utf-8') as f:
    f.write('Book id\t題名\t判定\t日本館藏\t依據URL\t版本\n')
    for r in rows: f.write('\t'.join(r) + '\n')
json.dump(list(files), open(os.path.join(HERE, 'files2.json'), 'w'), ensure_ascii=False)
print('已寫')
