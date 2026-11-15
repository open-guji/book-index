#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-g（和刻本日本馆藏专项 shard6）：补挂日本馆藏 + 新建日本刻本 Book。用法：build.py [--apply]"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); import mintid
APPLY = '--apply' in sys.argv
S = '/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g/'
PATHS = json.load(open(S + 'bookpaths.json'))
TODAY = '2026-11-15'
NDLU = 'https://ndlsearch.ndl.go.jp/books/'; CNU = 'https://ci.nii.ac.jp/ncid/'
NDL = '國立國會圖書館'
def ndl(rid, cn=None): return {'institution': NDL, **({'call_number': cn} if cn else {}), 'source': 'NDL Search ' + NDLU + rid}
def cin(inst, rid, ncid, cn=None, note=None):
    d = {'institution': inst}
    if cn: d['call_number'] = cn
    if note: d['notes'] = note
    d['source'] = 'CiNii Books %s%s（NDL Search %s%s）' % (CNU, ncid, NDLU, rid); return d
def kyu(rid): return {'institution': '九州大學附屬圖書館', 'source': 'NDL Search %s%s（九大コレクション）' % (NDLU, rid)}
# (book id, [provenance], 依据说明)
ATT = [
 ('988fzvo361', [cin('九州大學醫學圖書館', 'R100000136-I1971430859862105498', 'BA59298767', '和漢古醫書/シ-51')], '傷寒論註來蘇集（柯琴）文政4[1821]刊，年份一致'),
 ('99511ucfeo', [ndl('R100000002-I000007509306')], '京 林甚右衞門刊 正保4，《國立國會圖書館漢籍目録》4頁左'),
 ('99511tpybk', [ndl('R100000002-I000007509411')], '京 上村次郎右衞門刊 寛文5（1665），與「正保四年刻寛文五年印」相合'),
 ('988g8dvw25', [ndl('R100000002-I000000487155')], '東京 印文學會本部 明治36-38，與「明治三十六年至三十八年刊本」相合'),
 ('988fzcmm17', [cin('關西大學圖書館', 'R100000136-I1970304959941864722', 'BA76359857', 'L23||||C||2438')], '和泉屋金右衛門 嘉永4.11[1851]，年份一致（獺祭居為藏版）'),
 ('993fnqa29t', [{'institution': '京都府立京都學・歷彩館', 'source': 'NDL Search ' + NDLU + 'R100000001-I2612119019148（前川六左衞門等刊，寶曆10[1760]）'}], '論語徵集覽 前川六左衞門等刊 寶曆10=1760，與「寶曆十年刻本」相合'),
 ('988g2mb2tr', [cin('京都大學附屬圖書館', 'R100000136-I1970586434794228665', 'BB19228275', '7-02||ナ||4')], '刊記「慶安五歳孟夏日/武村市兵衞刊行」，與「慶安五年武村市兵衛刊本」相合'),
 ('995115zx1d', [cin('大阪府立中之島圖書館', 'R100000136-I1971430859724745617', 'BB20298904', ':282:3:#')], '精溪文房（昌谷碩）和泉屋半兵衞·須原屋茂兵衞 弘化4[1847]；總目作弘化三年，差一年（序年／刊年之別），刊者一致'),
 ('988fzt66tf', [cin('東京大學總合圖書館', 'R100000136-I1971149384870001154', 'BC0956814X', 'W20:212')], '昌平坂學問所官版 文久3[1863]刊，年份一致'),
 ('993bq23mrm', [cin('九州大學中央圖書館', 'R100000136-I1970586434865313173', 'BA68083284', '碩水文庫/シ/101')], '野田庄右衞門刊 寛文9[1669]，年份一致'),
 ('9950a8s2dd', [cin('島根大學附屬圖書館', 'R100000136-I1970586434936783417', 'BB1121098X', 'NDC:123.1/Sh99')], '晦庵先生朱文公易説23卷 寛政11[1799]刊；本 Book edition「寛正十一年」疑為「寛政十一年」之誤，年份相合（未改 edition，待人工）'),
 ('993e47wsn4', [ndl('R100000002-I000007537716')], '東都 西村源六等刊 延享4，《國立國會圖書館漢籍目録》57頁左'),
 ('988g7dd4hw', [ndl('R100000002-I000007278499'), kyu('R100000092-I2324_4738387')], '延曆交替式（岸本由豆流=朝田由豆流校本）須原屋伊八等刊 天保9[1838]，九大本刊記「天保九年戊戌夏六月刻成」'),
 ('988g2zf1mp', [cin('神戶大學附屬圖書館社會科學系', 'R100000136-I1970586434794925952', 'BB21488836', '10-3-69')], '河内屋茂兵衞·河内屋新次郎·河内屋藤兵衞刊，萬延2[1861]'),
 ('988g5ji1vv', [cin('一橋大學附屬圖書館', 'R100000136-I1970023484952614662', 'BC11264363', 'Umetani/G:51'), kyu('R100000092-I2324_431383')], '珍錢奇品圖録 文化14[1817]序刊，年份一致'),
 ('988g4io1s3', [cin('東京大學駒場圖書館', 'R100000136-I1971430859869066662', 'BB19602178')], '晏子春秋音義 大關惟孝（琢堂）天保4[1833]序刊'),
 ('988g7ajzm4', [ndl('R100000002-I000007300453')], '叢桂偶記 水戸 須原屋安治郎ほか刊 嘉永7[1854]，與「嘉永甲寅(七年)叢桂亭重刊本」相合'),
 ('99524lyg3l', [kyu('R100000092-I2324_419255')], '詩經說約 芳野屋權兵衞 寛文9[1669]，年份一致（日本版僅此一版）'),
 ('9950i05gjl', [cin('佛教大學附屬圖書館', 'R100000136-I1970867909875637509', 'BA85363323')], '左傳杜解補正 文泉堂·風月堂·林權兵衞刊 明和4[1767]，年份一致'),
 ('988g87ydqk', [cin('福井大學附屬圖書館', 'R100000136-I1971149384779096979', 'BB10737757', '183.08||HUI||27')], '一切經音義100卷續10卷 前田嘉右衞門 元文3[1738]-延享3[1746]刊，元文三年一致'),
 ('988g7dzll9', [ndl('R100000002-I000001032693')], '韓子解詁21卷 大阪 河内屋喜兵衞等 1849（嘉永2）印；題簽「校正韓非子解詁全書」，與「文化十四年半千塾刊嘉永二年印本」的嘉永二年印相合；初刻文化14年'),
 ('988g1fjket', [cin('京都大學人文科學研究所', 'R100000136-I1970023484879995707', 'BB10193692', '128.6||O-262')], '増讀韓非子 河内屋吉兵衞·柏原屋與左衞門等 嘉永元[1848]，享和2年脩文齋刊之補刻'),
 ('988g7fjsaq', [cin('關西大學圖書館', 'R100000136-I1970304959884738951', 'BA68478442', 'L23||||700||602')], '歷朝名公款譜 青藜閣（翠雲山房）文化5[1808]刊'),
 ('988g52c00a', [cin('大阪府立中之島圖書館', 'R100000136-I1970586434842771901', 'BB20335330', ':691:45:#')], '黃帝八十一難經疏證 聿修堂 文政2[1819]'),
 ('99521h9s00', [cin('東京大學總合圖書館', 'R100000136-I1970586434840929347', 'BB14094036', 'B60:1725')], '呂氏家塾讀詩記32卷 山形屋善兵衞（森本直助等）寳永元[1704]；NDL 另有同年漢籍目録著錄 R100000002-I000007512357'),
 ('988g8ivoqz', [cin('名古屋大學文學部', 'R100000136-I1971149384744250923', 'BA85548588', 'A||IX||5')], '周禮12卷 松崎明復（慊堂）縮刻唐石經 天保15[1844]跋'),
 ('99je93h7w0', [cin('京都大學人文科學研究所', 'R100000136-I1970023484841055260', 'BB19797179', '126.2||H-33')], '林羅山 老子鬳齋口義發題3卷 崑山舘道可處士刊 承應元[1652]；題名與本 Book「老子經抄」不同，刊年刊者作者一致（同書異題簽，另有田原仁左衞門1669刊《老子經鈔》未建）'),
 ('99je93h7wf', [cin('大阪府立中之島圖書館', 'R100000136-I1970586434907239951', 'BA67916442', ':188.6:70:#'), kyu('R100000092-I2324_419316')], '老子道德經補註（林氏口義，吉田利行）林磊落堂（林斧介）明治17[1884]'),
 ('99je93h7wc', [cin('京都產業大學圖書館', 'R100000136-I1971993809690902659', 'BA67862671', 'C XIV||WAN')], '王註老子標釋 青木嵩山堂 1908（明治41）'),
 ('99je93h7wd', [cin('金澤大學附屬圖書館', 'R100000136-I1971712334825024306', 'BN09590893', '124.22:N724')], '老子講義 西村豐 二書房 1893（明治26）'),
 ('99jihj15hh', [kyu('R100000092-I2324_418549')], '沖虛至德眞經（張湛）山本平左衞門 延享4[1747]；本 Book 括注「1744」與延享四年(1747)不符，未改'),
 ('988g1dcwlq', [ndl('R100000002-I000007681812')], '新樂府1卷 片山舍正刊 慶安3[1650]，《國立國會圖書館漢籍目録》540頁左'),
 ('988g92uvin', [cin('お茶の水女子大學附屬圖書館', 'R100000136-I1970304959962519707', 'BB20559010', 'C30/562')], '文選錦字録21卷 官版（昌平坂學問所）文政元[1818]'),
]
# 新建：(題, work, edition, edition_type, reign, year, publisher/details, measures, provenance, 依据, desc)
NEW = [
 ('毛詩蒙引', 'd59fxs6eegap', '日本寬文十二年京都村上平樂寺刊本', '刻本', '寬文', 1672, '村上平樂寺', [{'number': 20, 'unit': '卷'}, {'number': 1, 'unit': '卷首'}],
  [cin('九州大學中央圖書館', 'R100000136-I1970304959816525342', 'BB15751405', '123.3/Sh 34/6'), {'institution': NDL, 'source': 'NDL Search ' + NDLU + 'R100000002-I000007508280（《國立國會圖書館漢籍目録》6頁左）'}],
  '卷末「寛文12年仲春吉辰 村上平樂寺」', '陳子龍訂、唐士稚撰，二十卷首一卷。'),
 ('毉斷', 'd59f2q7zj6yq', '日本寶曆九年浪華加賀屋善藏刊本', '刻本', '寶曆', 1759, '加賀屋善藏（浪華書林吉田松根堂）', None,
  [kyu('R100000092-I2324_4491931')], '延享丁卯(1747)自序，寶曆己卯(1759)中西惟忠跋，卷末附「浪華書林吉田松根堂藏書目錄」', '鶴田元逸（鶴沖元逸）撰，吉益為則後序。'),
 ('出證配劑', 'd59f2q4no2kg', '日本寬永十年杉田勘兵衞刊本（與醫學天正記合刊）', '刻本', '寬永', 1633, '杉田勘兵衞', [{'number': 2, 'unit': '卷'}],
  [cin('東京大學總合圖書館', 'R100000136-I1970304959817375549', 'BB18689170', 'V11:778')], 'NDL/CiNii 書誌：出證配劑2卷·醫學天正記2卷，杉田勘兵衞，寬永10[1633]', '曲直瀨道三撰；與曲直瀨玄朔《醫學天正記》合刊。'),
 ('察證辨治啟迪集', 'd59f2puy29s1', '日本慶安二年上村次郎右衞門刊本', '刻本', '慶安', 1649, '上村次郎右衞門', None,
  [kyu('R100000092-I2324_4491917')], 'NDL Search 九大コレクション著錄：上村次郎右衞門，慶安2年', '曲直瀨道三撰。'),
 ('增讀韓非子', 'd59f2pzcbkzk', '日本享和二年脩文齋刊本', '刻本', '享和', 1802, '脩文齋', [{'number': 20, 'unit': '卷'}, {'number': 1, 'unit': '附錄'}],
  [cin('天理大學附屬天理圖書館', 'R100000136-I1970023484917603654', 'BB2717318X', '128.8||17')], '封面及版心下部「脩文齋」，享和2[1802]；本庫另有嘉永元年重刊本', '物茂卿（荻生徂徠）讀，蒲坂青莊增；二十卷附錄一卷。'),
 ('沖虛至德真經', 'd59fy18krocg', '日本寬政三年京都鳳城書舖小川多右衞門刊本', '刻本', '寬政', 1791, '鳳城書舖（小川多右衞門）', [{'number': 8, 'unit': '卷'}],
  [kyu('R100000092-I2324_423094'), {'institution': '早稻田大學圖書館', 'source': 'NDL Search ' + NDLU + 'R000000050-I000017948（古典籍總合データベース）'}], '鳳城（京都）小川夛右ヱ門，寬政3[1791]；題簽書名「張注列子」', '晉張湛注；題簽作「張注列子」。'),
]
LEDGER = []
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def blob(p): return subprocess.run(['git', '-C', BI, 'show', 'HEAD:' + p], capture_output=True, check=True).stdout.decode()
changed = []
for bid, provs, why in ATT:
    p = PATHS[bid]; d = json.loads(blob(p))
    have = {(x.get('institution'), x.get('source')) for x in d.get('provenance', [])}
    assert d['id'] == bid
    d.setdefault('provenance', [])
    for pv in provs:
        if (pv['institution'], pv['source']) not in have: d['provenance'].append(pv)
    a, b, c = d.get('revision', '1.0.0').split('.'); d['revision'] = '%s.%s.%d' % (a, b, int(c) + 1); d['revised_at'] = TODAY
    note = '和刻本日本馆藏专项（2026-11-15，車道 wake-g）：補挂日本館藏——' + why + '。據 NDL Search／CiNii Books 書誌頁，未核原書；原有館藏保留。'
    d['ai_note'] = (d['ai_note'] + '\n' if d.get('ai_note') else '') + note
    changed.append((p, d))
    LEDGER.append((bid, d['title'], '補挂', '、'.join(x['institution'] for x in provs), ' '.join(re.findall(r'https?://[^\s）]+', ' '.join(x['source'] for x in provs)))))
n = len(NEW)
ids = mintid.mint('Book', 'wake-g', n) if APPLY else ['dry%07d' % i for i in range(n)]
for (t, w, ed, et, reign, yr, pub, meas, provs, basis, desc), bid in zip(NEW, ids):
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': t, 'work_id': w, 'edition': ed, 'edition_type': et,
         'dating': {'era': '日本', 'reign': reign, 'year': yr, 'certainty': 'attested', 'source': 'catalog', 'basis': basis},
         'publication_info': {'publisher': pub, 'place': '日本'}}
    if meas: d['measures'] = meas
    d['provenance'] = provs
    d['description'] = {'text': desc, 'sources': sorted({re.search(r'https?://[^\s）]+', p['source']).group(0) for p in provs})}
    urls = sorted({u for p in provs for u in re.findall(r'https?://[^\s）]+', p['source'])})
    d['sources'] = [{'id': 'wakeg-%d' % i, 'name': 'NDL Search／CiNii Books', 'type': 'url', 'details': u} for i, u in enumerate(urls)]
    d['ai_note'] = '和刻本日本馆藏专项（2026-11-15，車道 wake-g）：據 NDL Search／CiNii Books 書誌頁新建（刊年、刊者、館藏據該頁；未核原書）。本庫該 Work 原無此日本刊本；與庫內其他版本不硬並。'
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
    changed.append(('Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, t, safe), d))
    LEDGER.append((bid, t, '新建', '、'.join(x['institution'] for x in provs), ' '.join(urls)))
print(len(ATT), '補挂', len(NEW), '新建')
if APPLY:
    for p, d in changed:
        fp = os.path.join(BI, p); os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, 'w', encoding='utf-8').write(jd(d))
    open(os.path.join(HERE, 'ledger_changed.tsv'), 'w', encoding='utf-8').write('\n'.join('\t'.join(r) for r in LEDGER) + '\n')
    open(os.path.join(HERE, 'changed_paths.txt'), 'w').write('\n'.join(p for p, _ in changed) + '\n')
