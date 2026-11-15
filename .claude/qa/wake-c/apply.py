#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""車道 wake-c：和刻本日本馆藏专项（shard2）。用法：apply.py [--apply]"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa')); import mintid
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'; TAG = '和刻本日本馆藏专项（車道 wake-c，2026-11-15）'
NDL = 'https://ndlsearch.ndl.go.jp/books/'; CINII = 'https://ci.nii.ac.jp/ncid/'
# 補挂：book id -> (依據說明, [(機構, 索書號|None, source)], 判定備註)
def ndl(i): return 'NDL Search ' + NDL + i
def cinii(n, i): return 'CiNii Books %s%s（NDL Search %s%s）' % (CINII, n, NDL, i)
NDLINST = '國立國會圖書館'
SUP = {
 '988g678364': ('NDL 古典籍 WA6-23：新刊勿聽子俗解八十一難經 卷1-3圖要1卷，越前一乘谷朝倉孝景刊，天文5年（1536）', [(NDLINST, 'WA6-23', ndl('R100000002-I000007552503'))]),
 '988g5i93ph': ('CiNii BB2023499X：趙註孫子 5卷，窪田清音訂刻，文久3年（1863）', [('大阪府立中之島圖書館', '587:9', cinii('BB2023499X', 'R100000136-I1970023484915530891'))]),
 '995234w3r4': ('國書データベース/NDL Search 著錄：毛詩名物圖說，堀野屋儀助，文化5年（1808）', [('九州大學附屬圖書館', None, ndl('R100000092-I2324_419017'))]),
 '9950hexbls': ('CiNii BB14025441：春秋左氏傳補注 10巻，昌平坂學問所（官版），享和元年（1801）刊', [('東京大學總合圖書館', 'B60:1645', cinii('BB14025441', 'R100000136-I1971993809724437453'))]),
 '988g36wqo2': ('CiNii BB1811825X：校正註方眞本易簡方論（王碩撰，望月正的校），戶倉屋喜兵衞，寬延元年（1748）', [('京都大學附屬圖書館', '図 7-02||エ||7', cinii('BB1811825X', 'R100000136-I1970023484840489644'))]),
 '988g87n56s': ('NDL 210.04-To339k：好古日錄，京兆鷦鷯惣四郎〔ほか〕，寛政9年（1797）', [(NDLINST, '210.04-To339k', ndl('R100000002-I000003283507'))]),
 '988g43zw9a': ('CiNii BN13480061：世說新語補 20巻，林九兵衞，元祿7年（1694）', [('神戶松蔭大學', '924 H057015', cinii('BN13480061', 'R100000136-I1970586434889200274'))]),
 '988g1m3jt1': ('CiNii BA3496533X：縮臨古本論語集解 10巻，津藩有造館，天保8年（1837）跋', [('廣島大學中央圖書館', '123.83:Ka-11', cinii('BA3496533X', 'R100000136-I1970304959827436221'))]),
 '988g7f8jri': ('CiNii BB19132824：少小嬰孺方 不分卷，偸閑書屋，文政13年（1830）', [('京都大學附屬圖書館', '図 7-02||シ||126', cinii('BB19132824', 'R100000136-I1970304959817459075'))]),
 '988g3bwjde': ('CiNii BB25741601：縮刻唐開成石經，松崎慊堂（松崎明復），天保15年（1844）跋', [('東京大學東洋文化研究所', None, cinii('BB25741601', 'R100000136-I1970023484842685338'))]),
 '988g0pbmrv': ('NDL 65-211：深志茗讌圖錄，東京須原鐵二，明治13年（1880）', [(NDLINST, '65-211', ndl('R100000002-I000000487036'))]),
 '988g6tp6a2': ('NDL 118-144：宋大家曾文定公文抄 10卷，慶應元年（1865）官版（昌平坂學問所）', [(NDLINST, '118-144', ndl('R100000002-I000007682274'))]),
 '993e330phe': ('CiNii BA85441551：論語 10卷（論語集解標記），千鍾堂・大野木市兵衞，須原屋茂兵衞發賣，天明3年（1783）', [('佛教大學附屬圖書館', None, cinii('BA85441551', 'R100000136-I1971993809684215963'))]),
 '993foionpc': ('CiNii BC07267663：四書味根錄 37巻，樂善堂，明治16年（1883）', [('東京大學總合圖書館', 'SB:28', cinii('BC07267663', 'R100000136-I1970304959939622211'))]),
 '9956aghngg': ('CiNii BB19769763：裨農最要 3卷附1卷，永義和，光緒23年（1897）', [('京都大學附屬圖書館', '図 9-28||ヒ||4', cinii('BB19769763', 'R100000136-I1970023484985605381'))]),
 '993dldxcsg': ('CiNii BA83863198：韻府古篆彙選 5巻，柳枝軒，元祿10年（1697）序', [('關西大學圖書館', None, cinii('BA83863198', 'R100000136-I1970304959844656017'))]),
 '993dldm48x': ('NDL W581-N1：韻府古篆彙選 5卷，京都柳枝軒書林多左衞門，正德3年（1713）', [(NDLINST, 'W581-N1', ndl('R100000002-I000011139800'))]),
 '99516prsow': ('CiNii BA80112508：禮記陳氏集說補正 38巻，尚友堂（昌平坂學問所系），享和2年（1802）', [('九州大學中央圖書館', '碩水文庫/ラ/7', cinii('BA80112508', 'R100000136-I1971149384884858124'))]),
 '988g4xc7bi': ('NDL 128-108：醫餘 3巻，江戶山城屋佐兵衞（玉山堂）〔ほか〕；國文研著錄文久3年（1863）', [(NDLINST, '128-108', ndl('R100000002-I000007276710'))]),
 '99je93h7x9': ('NDL 139-272：夢中老子 4巻，須原屋平左衞門，延享4年（1747）', [(NDLINST, '139-272', ndl('R100000002-I000007324978'))]),
 '993b88y70g': ('NDL 特56-221：孝經纂註，大阪此村欽英堂，明治16年（1883）', [(NDLINST, '特56-221', ndl('R100000002-I000000418899'))]),
 '988g1uu70r': ('NDL W812-N5：唐李長吉歌詩 4卷外卷1卷，文政元年（1818）官版（昌平坂學問所）', [(NDLINST, 'W812-N5', ndl('R100000002-I000007681962'))]),
 '996jc9z0cw': ('NDL 特40-468：七曲吟社閨媛絶句，東京太田金右衞門〔ほか〕，明治10年（1877）', [(NDLINST, '特40-468', ndl('R100000002-I000000516270'))]),
 '988g5kfrij': ('CiNii BC18517966：東萊呂氏周易音訓 2巻，精溪文房，弘化4年（1847）', [('滋賀大學附屬圖書館教育學部分館', '経||5', cinii('BC18517966', 'R100000136-I1971149384870916610'))]),
 '996jc9nrvd': ('NDL 821.1-M756s：三音正譌 2巻，浪華柏原屋清右衞門，天明8年（1788）', [(NDLINST, '821.1-M756s', ndl('R100000002-I000003283967'))]),
 '988g8y6bd1': ('NDL W488-73：祕傳證治類方 12巻（祕傳證治要訣合刻），京都武村新兵衞，據萬曆33年王肯堂重校本重刊', [(NDLINST, 'W488-73', ndl('R100000002-I000011054327'))]),
 '993f20nu2q': ('NDL 123.65-R73t-K2：評註東萊博議 6巻，東京坂上半七・吉川半七（泛愛堂），明治12年（1879）', [(NDLINST, '123.65-R73t-K2', ndl('R100000002-I000001032690'))]),
 '993e4zowzl': ('CiNii BB17621295：頭字韻 5卷，封面「天保壬辰晩春新鎸」「稽古精舍版」', [('京都大學附屬圖書館', '4-06||ト||1', cinii('BB17621295', 'R100000136-I1970586434841982493'))]),
 '993g6sdo8x': ('CiNii BB14155866／BA70762642：論語 10巻附札記1巻（正平本論語集解），青歸書屋，文化13年（1816）序', [('東京大學總合圖書館', 'B60:1808', cinii('BB14155866', 'R100000136-I1971149384890863655')), ('關西大學圖書館', None, cinii('BA70762642', 'R100000136-I1970867909803980293'))]),
 '988fzvo35s': ('CiNii BB14155866：論語 10巻附札記1巻（市野迷庵覆刻正平本），青歸書屋，文化13年（1816）序', [('東京大學總合圖書館', 'B60:1808', cinii('BB14155866', 'R100000136-I1971149384890863655'))]),
}
# 新建：(work_id, title, edition, edition_type, dating, prov[(inst,call,source)], sources[(id,name,url)], 說明)
NEW = [
 ('d59f27xfwzya', '論語集解', '日本寬政三年（1791）吉田篁墩箕林山房聚珍版活字本', '活字本',
  {'era': '日本', 'reign': '寬政', 'year': 1791, 'text': '寬政三年（1791）跋；寬政二年（1790）已有刷印本', 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books BB13466124（寛政3 [1791] 跋）、BB14156621（寛政2 [1790]）'},
  [('東京大學總合圖書館', 'B60:909', cinii('BB13466124', 'R100000136-I1970586434831632277')), ('東京大學總合圖書館', 'B60:1809', cinii('BB14156621', 'R100000136-I1971430859867597441'))],
  [('ncid-BB13466124', 'CiNii Books BB13466124', CINII + 'BB13466124'), ('ncid-BB14156621', 'CiNii Books BB14156621', CINII + 'BB14156621'), ('ncid-BA75331262', 'CiNii Books BA75331262（論語集解攷異）', CINII + 'BA75331262')],
  '何晏集解，吉田篁墩（吉田漢宦）校，寬政間箕林山房據乾隆聚珍版式用木活字排印（刊記「聚珍版藏在于箕林山房」「增田利房刷印」），另有《論語集解攷異》十卷附刊（九州大學中央圖書館碩水文庫藏攷異）。'),
 ('d59f2hrpn2f4', '易簡方', '日本文化十四年（1817）鉛屋安兵衞觀宜堂刻淺井惟亨校訂本', '刻本',
  {'era': '日本', 'reign': '文化', 'year': 1817, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books BA5875639X（文化14 [1817]，見返し「觀宜堂藏版」）'},
  [('九州大學醫學圖書館', '医分 和漢古醫書/エ-3', cinii('BA5875639X', 'R100000136-I1971993809797692331'))],
  [('ncid-BA5875639X', 'CiNii Books BA5875639X', CINII + 'BA5875639X')],
  '宋王碩撰，淺井南皋（惟亨）校訂，鉛屋安兵衞刊，見返し「觀宜堂藏版」。與庫內「寬延戊辰（1748）戶倉屋喜兵衞生白堂刊本」（988g36wqo2）刊者年代不同，另立。'),
 ('d59f2hrpn2f4', '易簡方', '日本安永七年（1778）大阪澁川清右衞門刊本', '刻本',
  {'era': '日本', 'reign': '安永', 'year': 1778, 'certainty': 'attested', 'source': 'catalog', 'basis': 'NDL 漢籍目錄著錄「安永7」；國書データベース校正註方眞本易簡方論（1778）'},
  [(NDLINST, 'W731-18', ndl('R100000002-I000007555659'))],
  [('ndl-R100000002-I000007555659', 'NDL Search', NDL + 'R100000002-I000007555659'), ('ndl-R100000094-I201103', 'NDL Search（校正註方真本易簡方論）', NDL + 'R100000094-I201103')],
  '大阪澁川清右衞門刊，安永七年。內容為《校正註方真本易簡方論》（醫簡方）系統，與寬延元年戶倉屋本（988g36wqo2）是否同版式未核，故另立；二者宜互參。'),
 ('d59f2mcbrf9d', '明朝紀事本末', '日本弘化三年（1846）江戶須原屋茂兵衞等刊二本松藩敬學館藏版', '刻本',
  {'era': '日本', 'reign': '弘化', 'year': 1846, 'certainty': 'attested', 'source': 'catalog', 'basis': 'NDL 漢籍目錄著錄「弘化3」，二本松藩敬學館藏版'},
  [(NDLINST, '157-30', ndl('R100000002-I000007520008'))],
  [('ndl-R100000002-I000007520008', 'NDL Search', NDL + 'R100000002-I000007520008')],
  '谷應泰撰，安積艮齋訓點，江戶須原屋茂兵衞等發兌，二本松藩敬學館藏版，80卷。庫內另有「天保癸卯（十四年）東京書肆玉岩書堂刊本」（988g3h7klr，故宮藏），年代與刊者不同，是否同一版本待核，現另立；二者宜互參。'),
]
def git(*a): return subprocess.run(['git', '-c', 'core.quotepath=off', '-C', ROOT] + list(a), capture_output=True, text=True).stdout
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def find_path(bid):
    pre = 'Book/%s/%s/%s/' % (bid[-3], bid[-2], bid[-1])
    for l in git('ls-tree', '--name-only', 'origin/main', pre).splitlines():
        if os.path.basename(l).startswith(bid + '-'): return l
    return None
def bump(v):
    p = (v or '1.0.0').split('.'); p[-1] = str(int(p[-1]) + 1); return '.'.join(p)
changed = {}; rows = []
for bid, (ev, provs) in SUP.items():
    path = find_path(bid)
    if not path: print('MISSING', bid); continue
    d = json.loads(git('show', 'origin/main:' + path))
    have = {p.get('institution') for p in d.get('provenance', [])}
    add = []
    for inst, call, src in provs:
        e = {'institution': inst}
        if call: e['call_number'] = call
        e['source'] = src
        if any(p.get('institution') == inst and p.get('call_number') == call for p in d.get('provenance', [])): continue
        add.append(e)
    if not add: print('SKIP-have', bid); continue
    d.setdefault('provenance', []).extend(add)
    note = '%s：補挂日本館藏（%s）。同版依據：題名、責任者、刊年／刊者與本條著錄一致；%s。' % (TAG, '、'.join(a['institution'] for a in add), ev)
    d['ai_note'] = (d['ai_note'] + '\n' + note) if d.get('ai_note') else note
    d['revision'] = bump(d.get('revision')); d['revised_at'] = TODAY
    changed[path] = d
    for a in add: rows.append((bid, d['title'], '補挂', a['institution'] + (' ' + a.get('call_number', '')), a['source']))
ids = mintid.mint('Book', 'wake-c', len(NEW)) if APPLY else ['dryb%06d' % i for i in range(len(NEW))]
for (wid, title, ed, et, dt, provs, srcs, desc), bid in zip(NEW, ids):
    d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': et, 'dating': dt}
    d['provenance'] = [dict([('institution', i)] + ([('call_number', c)] if c else []) + [('source', s)]) for i, c, s in provs]
    d['description'] = {'text': desc, 'sources': ['%s %s' % (n, u) for _, n, u in srcs]}
    d['sources'] = [{'id': i, 'name': n, 'type': 'url', 'details': u} for i, n, u in srcs]
    d['ai_note'] = '%s：新建。據 NDL Search／CiNii Books 著錄的日本刊本，庫內該 Work 下無對應版本；題名、刊者、年代均錄自目錄頁，未核原書。' % TAG
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
    changed['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, title, safe)] = d
    rows.append((bid, title, '新建', '; '.join(p[0] for p in provs), provs[0][2]))
print('changed files:', len(changed), ' 補挂:', len(SUP), ' 新建:', len(NEW))
if not APPLY: sys.exit(0)
for p, d in changed.items():
    os.makedirs(os.path.join(ROOT, os.path.dirname(p)), exist_ok=True)
    open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(jd(d))
json.dump(list(changed), open(os.path.join(HERE, 'changed.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(rows, open(os.path.join(HERE, 'rows.json'), 'w'), ensure_ascii=False, indent=1)
print('已寫')
