#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和刻本日本馆藏專項·車道 wake-f（shard5）：補挂日本館藏 + 新建日本刊本 Book。
用法：python3 apply.py [--apply]   （須在 repo 根目錄；無 --apply 為乾跑）
依據（逐條已抓取覆核）：NDL Search 書目頁 https://ndlsearch.ndl.go.jp/books/<R-id>、CiNii Books https://ci.nii.ac.jp/ncid/<NCID>。"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa'))
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'; LANE = 'wake-f'
NDL = lambda r: 'NDL Search https://ndlsearch.ndl.go.jp/books/' + r
CIN = lambda n: 'CiNii Books https://ci.nii.ac.jp/ncid/' + n
def srcent(s):
    name, url = s.split(' ', 1)
    tail = url.rstrip('/').split('/')[-1]
    return {'id': ('ndl-' if name == 'NDL' else 'cinii-') + tail.lower(), 'name': {'NDL': 'NDL Search 書目', 'CiNii': 'CiNii Books 書目'}.get(name, name), 'type': 'url', 'details': url}
def P(inst, call, src, note=None):
    d = {'institution': inst}
    if call: d['call_number'] = call
    if note: d['notes'] = note
    d['source'] = src
    return d
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def find(bid):
    g = glob.glob(os.path.join(ROOT, 'Book', bid[-3], bid[-2], bid[-1], bid + '-*.json'))
    assert len(g) == 1, (bid, g); return g[0]
def bump(rev):
    a, b, c = rev.split('.'); return '%s.%s.%d' % (a, b, int(c) + 1)

TD = '東京大學綜合圖書館'; TM = '東京大學醫學圖書館'; KF = '京都大學附屬圖書館'; WS = '早稻田大學圖書館'; NDLI = '國立國會圖書館'
# ---- 一、補挂：bid -> (依據說明, [provenance...])
HOKAN = {
 '988g4a8n4g': ('享保八年（1723）平野屋佐兵衞等刊、八木梅庵訓點本（見返「平安書林梓行」），NDL／CiNii 各館藏記錄同此版', [
    P(TD, 'V11:1360', NDL('R100000102-I000228639'), '鶚軒文庫'), P(TM, 'V11:s33', CIN('BB2212380X')), P(WS, None, NDL('R000000050-I000016660'))]),
 '9951y11bsw': ('文政二年（1819）官版（昌平坂學問所）；國會藏本，《國立國會圖書館漢籍目録》24頁左著錄', [
    P(NDLI, '307-47', NDL('R100000002-I000007519257'))]),
 '993g7ryq68': ('文化六年（1809）刊，松下葵岡著、重野櫟軒讀，丹霞樓・和泉屋金右衞門等發兌', [
    P(NDLI, None, NDL('R100000002-I034203019')), P('佛教大學附屬圖書館', '247737', CIN('BA86620895')), P('九州大學附屬圖書館', None, NDL('R100000092-I2324_7451447'), '印記「碩水藏書」')]),
 '995084axa8': ('寬文九年（1669）野田庄右衞門刊本；CiNii 另載筑波大藏本', [
    P('筑波大學附屬圖書館', '123.1:Sa-17', CIN('BN1036452X'))]),
 '99505ol8n4': ('弘化三年（1846）須原屋伊八・和泉屋善兵衞等刊、大橋順藏校讀本；CiNii 另載武藏大學藏本', [
    P('武藏大學圖書館', '123.1||15', CIN('BA80057873'))]),
 '988g66wumd': ('寬延三年（1750）藤木久市等刊、根本遜志校正本（東都書肆）', [
    P('關西大學圖書館', 'L23**A*1099', CIN('BA83472088')), P(TD, 'B60:2054', CIN('BB15451241'))]),
 '988g077v9f': ('寬文九年（1669）刊本（NDL 著錄刊者「婦屋仁兵衞」），《國立國會圖書館漢籍目録》446頁右', [
    P(NDLI, None, NDL('R100000002-I000007596798'))]),
 '988g23w2rs': ('慶安二年（1649）中野小左衞門刊本（任廣編、喬應甲重校）；以刊年相合確認，刊者未見於本條著錄', [
    P(NDLI, None, NDL('R100000002-I000007603542')), P(KF, '4-85||シ||10', CIN('BB07617564'))]),
 '988g1ztzpg': ('寬政二年（1790）刊《陸宣公全集》（永樂屋東四郎）；僅以題名與刊年相合確認，刊者未見於本條著錄，姑補一館', [
    P('茨城大學圖書館', None, NDL('R100000143-I1000103351'), '茨城大學デジタルコレクション')]),
 '988g3q9gcv': ('寶永六年（1709）京都刊本（NDL 著錄めとぎ屋宗八）', [
    P('京都大學人文科學研究所', '180.4||409||松本文庫', CIN('BB07269366'))]),
 '988g12qu4m': ('天保七年（1836）昌平坂學問所官板《王荊文公詩》50卷補遺1卷，翻刊清乾隆六年張氏本', [
    P('名古屋大學文學部圖書室', 'D||II||3', CIN('BA89861887')), P(WS, None, NDL('R000000050-I000076484'), '題簽書名：官板王半山詩箋註')]),
 '988g1yl1jo': ('天保七年（1836）昌平黌官板《大唐六典》30卷', [
    P('東京大學東洋文化研究所', '史;職官:官制:3-1', CIN('BD04651753')), P(TD, 'L11:699', CIN('BB28895689'), '存卷11-30')]),
 '99jidudamu': ('天保四年（1833）官版（昌平叢書本）；《國立國會圖書館漢籍目録》500頁右著錄', [
    P(NDLI, None, NDL('R100000002-I000007620513'))]),
 '988g732akk': ('天保八年（1837）英大助（萬笈堂，聿修堂藏版）刊《素問識》8卷', [
    P(NDLI, None, NDL('R100000002-I000003280054')), P('九州大學醫學圖書館', '宮入文庫/Ta 71', CIN('BA59385872'))]),
 '988g2n8sg5': ('享和元年（1801）序聿修堂刊《救急選方》2卷', [
    P(TM, '三宅:299', CIN('BB22457485'))]),
 '988g4uuayt': ('寬政十一年（1799）津輕氏刊、津輕意伯校刊《外科精要》3卷', [
    P(TD, 'V11:1092', CIN('BB18799190'))]),
 '9951xhom4g': ('寬政十一年（1799）刊（寬政庚申〔1800〕印），足利屋勘六等刊、山本信有訓點《經問》9卷', [
    P('筑波大學附屬圖書館', 'ロ869-98', CIN('BA82262363'))]),
 '9951xdxrls': ('文化六年（1809）和泉屋庄次郎（慶元堂）刊《經典釋文》30卷附攷證30卷', [
    P('名古屋大學文學部圖書室', 'A||IX||3', CIN('BA85497818')), P(WS, None, NDL('R000000050-I000072549'))]),
 '993e4zdog2': ('文化十三年（1816）官版《通叶集覽》2卷', [
    P(WS, None, NDL('R000000050-I000028953'), '題簽書名：官板通叶集覽'), P(NDLI, None, NDL('R100000002-I000007539789'))]),
 '993a8mnegx': ('文久元年（1861）海仙庵刊小田海僊《海仙畫譜》', [
    P('佛教大學附屬圖書館', '15074', CIN('BB21003518'))]),
 '9937tjr30i': ('天明九年（1789）須原屋茂兵衞等刊《費氏山水畫式》3卷', [
    P('大阪府立中之島圖書館', ':913:2:#', CIN('BB20340068'))]),
 '99je93h7vs': ('寬延二年（1749）西村源六（文刻堂）等刊、近藤蘆陰《老子本義徵》2卷', [
    P(NDLI, None, NDL('R100000002-I000007327876'))]),
 '988fzkqs5y': ('寬政十一年（1799）濯纓堂刊《是齋百一選方》20卷（NDL 著錄「濯纓堂」）', [
    P(NDLI, None, NDL('R100000002-I000011112131'))]),
 '99jsd2n3t7': ('寬文八年（1668）荒川宗長刊、林羅山訓點《新刊公穀白文》本《公羊傳》12卷', [
    P('神戶大學附屬圖書館', '160-H322-1', CIN('BD12289764'))]),
 '988g820vf4': ('萬治二年（1659）刊《列子鬳齋口義》2卷（NDL／CiNii 著錄大和田九左衞門）', [
    P('天理大學附屬天理圖書館', '126.3||タ1(2)||1', CIN('BB26870257'))]),
 '9952080d8h': ('明和五年（1768）錢屋善兵衞刊《談經》9卷', [
    P('名古屋大學文學部圖書室', 'A||IX||1', CIN('BA85430748'))]),
 '993fp9j2f5': ('文政三年（1820）昌平坂學問所刊《鄭志》3卷附鄭司農集', [
    P('關西大學圖書館', 'L23||||A||1', CIN('BA8142918X'))]),
 '988g1xc3d9': ('享保十六年（1731）刊、寬政三年（1791）須原屋茂兵衞等修補《七經孟子考文補遺》', [
    P(KF, '1-61||シ||2||1', CIN('BB19171917'))]),
 '994yl60g00': ('寬政七年萬蘊堂刻、元治元年（1864）萬蘊堂・須原屋平左衞門補刻（發兌）《論語集解義疏》10卷', [
    P('佛教大學附屬圖書館', '200564758', CIN('BA87123411'))]),
}
# ---- 二、新建：(title, work_id, edition, 刊年, 年號, 卷數, 依據說明, [prov], [sources], 備註)
NEW = [
 ('清俗紀聞', 'd59f2n6dny0w', '日本寬政十一年（1799）翫月堂堀野屋仁兵衞等刊本', 1799, '寬政', 13, '寬政十一年（1799）中川忠英輯、石崎融思繪，翫月堂堀野屋仁兵衞（另有尚古堂岡田屋嘉七・芳雲堂鴈金屋利兵衞同年印本）',
  [P('宮城縣圖書館', None, NDL('R000000054-I040_51128'), '翫月堂堀野屋仁兵衞；印記「伊達伯觀瀾閣圖書印」'), P('宮城縣圖書館', None, NDL('R000000054-I040_55447'), '尚古堂岡田屋嘉七・芳雲堂鴈金屋利兵衞本')],
  [NDL('R000000054-I040_51128'), NDL('R000000054-I040_55447'), NDL('R100000092-I2324_429044')], '庫內原有《清俗紀聞》僅明治間博文館覆刻本（988g1cqfi9），此為其所據寬政十一年原刊。'),
 ('名公妙選陸放翁詩集', 'd59f2hqvzitd', '日本承應二年（1653）田中庄兵衞刊本', 1653, '承應', 18, '承應二年（1653）田中庄兵衞刊，前集10卷（羅椅編）後集8卷（劉辰翁編）',
  [P('京都大學文學研究科圖書館', 'D||IIf||17-4', CIN('BB20108419'))], [CIN('BB20108419'), NDL('R100000136-I1970586434868942374')], ''),
 ('華嚴經旨歸', 'd59fykwcqxhc', '日本明曆二年（1656）永田長左衞門刊本', 1656, '明曆', 1, '明曆二年（1656）刊（卷末刊記「明曆二丙申年仲夏」），永田長左衞門',
  [P('大倉精神文化研究所附屬圖書館', None, NDL('R100000147-I105336'), '題箋書名《華嚴經旨歸》，版心及尾題《華嚴旨歸》')], [NDL('R100000147-I105336'), NDL('R100000136-I1970304959864845202')], ''),
 ('華嚴經旨歸', 'd59fykwcqxhc', '日本文政元年（1818）菱屋孫兵衞刊本', 1818, '文政', 1, '文政元年（1818）菱屋孫兵衞刊',
  [P('身延山大學圖書館', '30035345', CIN('BB03360207'))], [CIN('BB03360207'), NDL('R100000136-I1970304959854294922')], ''),
 ('詩人玉屑', 'd59f2hr0o2yq', '日本寬永十六年（1639）田原仁左衞門刊本（洗心子玄惠批點句讀）', 1639, '寬永', 21, '寬永十六年（1639）田原仁左衞門刊，玄惠批點句讀，21卷（NDL 另載同年角屋清左衞門刊本）',
  [P('佛教大學附屬圖書館', '093.1||2026', CIN('BB06930491'))], [CIN('BB06930491'), NDL('R100000136-I1970867909913198640'), NDL('R100000001-I10111100229687')], ''),
 ('王翰林集註黃帝八十一難經', 'd59f2ndkfsaq', '日本慶安五年（1652）武村市兵衞刊本', 1652, '慶安', 5, '慶安五年（1652）武村市兵衞刊《王翰林集註黃帝八十一難經》5卷（版心書名《難經集註》）',
  [P(KF, '7-02||ナ||4', CIN('BB19228275')), P(WS, None, NDL('R000000050-I000007590'), '序題：集註難經；版心書名：難經集註')], [CIN('BB19228275'), NDL('R000000050-I000007590')], '庫內該 Work 下「影印日本活字本」三條與此本無證據可互證，未合併。'),
 ('外科精要', 'd59f2htrb2m8', '日本承應三年（1654）武村市兵衞刊本（薛己註、陸鶴校）', 1654, '承應', 3, '承應三年（1654）武村市兵衞刊，陳自明編、薛己註、陸鶴校，3卷',
  [P(KF, '7-02||ケ||26', CIN('BB18191453'))], [CIN('BB18191453'), NDL('R100000136-I1971993809677527966'), NDL('R100000133-IorgnB001388073')], ''),
 ('詩經世本古義', 'd59f2njvok5c', '日本寬政十年（1798）會津藩刊本', 1798, '寬政', None, '寬政十年（1798）會津藩刊，何楷撰，28卷首1卷後1卷',
  [P(TD, 'B60:1549', CIN('BB13916242'))], [CIN('BB13916242'), NDL('R100000001-I05111009810574498')],
  '庫內另有 99524ke9ds「日本刻本」（上海圖書館藏，著錄無年份刊者），疑即此本但無證據，按口徑另立 Book、不硬並，請覆核。'),
 ('儀禮經傳通解', 'd59f2htnvgn6', '日本寬文二年（1662）五倫書屋刊本', 1662, '寬文', 37, '寬文二年（1662）五倫書屋刊，37卷（朱熹撰）；庫內 9951cdaiv5 為此板清末上海樂善堂後印，另立',
  [P(TD, 'B60:137', CIN('BC15385042')), P(WS, None, NDL('R000000050-I000022855'), '目錄題：儀禮經傳；版心書名：儀禮經傳通解')], [CIN('BC15385042'), NDL('R000000050-I000022855')], ''),
 ('儀禮經傳通解', 'd59f2htnvgn6', '日本寬文九年（1669）山本平左衞門刊本', 1669, '寬文', None, '寬文九年（1669）山本平左衞門刊（京都），《儀禮經傳通解》23卷《集傳集註》14卷',
  [P('京都大學文學研究科圖書館', 'A||Ve||6-3', CIN('BB16830722')), P(WS, None, NDL('R000000050-I000070572'))], [CIN('BB16830722'), NDL('R000000050-I000070572')], ''),
 ('列子鬳齋口義', 'd59f2hqot2bn', '日本寬永四年（1627）安田安昌刊本', 1627, '寬永', 2, '寬永四年（1627）安田安昌刊，林希逸撰，2卷',
  [P(NDLI, None, NDL('R100000002-I000007621296'), '《國立國會圖書館漢籍目録》502頁右'), P('駒澤大學圖書館', None, NDL('R100000087-I42429'), '駒澤大學電子貴重書庫')], [NDL('R100000002-I000007621296'), NDL('R100000087-I42429')], ''),
 ('列子鬳齋口義', 'd59f2hqot2bn', '日本慶安五年（1652）崑山館道可處士刊本', 1652, '慶安', 2, '慶安五年（1652）崑山館道可處士刊，林希逸撰，2卷',
  [P(TD, 'B60:136', CIN('BB12973353')), P(WS, None, NDL('R000000050-I000036513'), '版心書名：列子')], [CIN('BB12973353'), NDL('R000000050-I000036513')], ''),
 ('日本書紀', 'd59f28lkb75v', '日本寬政五年（1793）小寺清先校正刊本', 1793, '寬政', 30, '寬政五年（1793）序，小寺清先校《校正日本書紀》30卷',
  [P('九州大學中央圖書館', '210.3/To 63', CIN('BC16165857'), '存卷1-2')], [CIN('BC16165857'), NDL('R100000136-I1970586434917193773')], ''),
 ('續日本紀', 'd59f2pymq4u8', '日本明曆三年（1657）立野春節校刊本', 1657, '明曆', 40, '明曆三年（1657）跋，立野春節校《續日本紀》40卷',
  [P(NDLI, None, NDL('R100000002-I000007297572')), P(TD, 'G24:404', CIN('BD00478679')), P('宮城縣圖書館', None, NDL('R000000054-I040_50540'), '印記「伊達伯觀瀾閣圖書印」')], [NDL('R100000002-I000007297572'), CIN('BD00478679'), NDL('R000000054-I040_50540')], '庫內該 Work 原有僅明治間石印本。'),
]
SEQ = [  # 逐條人工確認過、需在被補挂條 ai_note 互鏈的
]
def main():
    log = []
    for bid, (basis, provs) in HOKAN.items():
        f = find(bid); d = json.load(open(f, encoding='utf-8'))
        d.setdefault('provenance', []).extend(provs)
        d['revision'] = bump(d.get('revision', '1.0.0')); d['revised_at'] = TODAY
        srcs = d.setdefault('sources', []); have = {s.get('id') for s in srcs}
        for p in provs:
            for s in [srcent(p['source'])]:
                if s['id'] not in have: srcs.append(s); have.add(s['id'])
        line = '和刻本日本館藏專項（車道 wake-f，%s）：據 NDL Search／CiNii Books 書目頁核對，確認為同一版本（%s），補挂日本館藏 %d 條；原有中國館藏未動。' % (TODAY, basis, len(provs))
        d['ai_note'] = (d['ai_note'] + '\n' + line) if d.get('ai_note') else line
        if bid == '988g1ztzpg': pass
        log.append(('補挂', bid, d['title'], ' / '.join(p['institution'] for p in provs), ' '.join(p['source'].split(' ', 2)[2] for p in provs)))
        if APPLY: open(f, 'w', encoding='utf-8').write(jd(d))
    import mintid
    ids = mintid.mint('Book', LANE, len(NEW)) if APPLY else ['dry%07d' % i for i in range(len(NEW))]
    files = []
    for (title, wid, ed, year, reign, juan, basis, provs, srcs, memo), bid in zip(NEW, ids):
        d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': '刻本',
             'dating': {'era': '日本', 'reign': reign, 'year': year, 'certainty': 'attested', 'source': 'catalog', 'basis': 'NDL Search／CiNii Books 書目著錄刊年：' + basis.split('，')[0]}}
        if juan: d['measures'] = [{'number': juan, 'unit': '卷'}]
        d['provenance'] = provs
        d['description'] = {'text': '《%s》，%s。日本和刻本（和刻本日本館藏專項補建）。' % (title, basis), 'sources': srcs}
        d['sources'] = [srcent(s) for s in dict.fromkeys(srcs)]
        d['ai_note'] = '和刻本日本館藏專項（車道 wake-f，%s）：據 NDL Search／CiNii Books 書目頁（含所藏館記錄）新建；刊年、刊者、卷數錄自該書目頁，未核原書。%s' % (TODAY, memo)
        d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
        safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
        path = os.path.join('Book', bid[-3], bid[-2], bid[-1], '%s-%s%s.json' % (bid, title, safe))
        files.append(path)
        log.append(('新建', bid, title + '｜' + ed, ' / '.join(p['institution'] for p in provs), ' '.join(srcs)))
        if APPLY:
            os.makedirs(os.path.dirname(os.path.join(ROOT, path)), exist_ok=True)
            open(os.path.join(ROOT, path), 'w', encoding='utf-8').write(jd(d))
    # 在疑似同版的舊條 ai_note 互鏈（詩經世本古義）
    f = find('99524ke9ds'); d = json.load(open(f, encoding='utf-8'))
    newid = [l[1] for l in log if l[0] == '新建' and l[2].startswith('詩經世本古義')][0]
    d['revision'] = bump(d['revision']); d['revised_at'] = TODAY
    line = '和刻本日本館藏專項（車道 wake-f，%s）：本條「日本刻本」無刊年刊者；NDL／CiNii 有寬政十年（1798）會津藩刊本，已另立 Book %s，二者是否同版未能確認，未合併，請覆核。' % (TODAY, newid)
    d['ai_note'] = (d['ai_note'] + '\n' + line) if d.get('ai_note') else line
    log.append(('互鏈', '99524ke9ds', d['title'], '', ''))
    if APPLY: open(f, 'w', encoding='utf-8').write(jd(d))
    out = os.path.join(HERE, 'ledger_done.tsv')
    if APPLY:
        with open(out, 'w', encoding='utf-8') as fh:
            for r in log: fh.write('\t'.join(r) + '\n')
        open(os.path.join(HERE, 'changed_files.txt'), 'w').write('\n'.join(files + [os.path.relpath(find(b), ROOT) for b in list(HOKAN) + ['99524ke9ds']]) + '\n')
    print(len(HOKAN), '補挂', len(NEW), '新建')
    for r in log[:3]: print(r)
main()
