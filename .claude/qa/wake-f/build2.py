#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和刻本專項第二輪·車道 wake-f（shard5）：新建 Work 下庫內缺的日本版本。用法：python3 build2.py [--apply]（repo 根目錄）"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa'))
APPLY = '--apply' in sys.argv; TODAY = '2026-11-15'; LANE = 'wake-f'
NDL = lambda r: 'NDL Search https://ndlsearch.ndl.go.jp/books/' + r
CIN = lambda n: 'CiNii Books https://ci.nii.ac.jp/ncid/' + n
def srcent(s):
    name, url = s.split(' ', 1); tail = url.rstrip('/').split('/')[-1]
    return {'id': ('ndl-' if name == 'NDL' else 'cinii-') + tail.lower(), 'name': {'NDL': 'NDL Search 書目', 'CiNii': 'CiNii Books 書目'}[name], 'type': 'url', 'details': url}
def P(inst, call, src, note=None):
    d = {'institution': inst}
    if call: d['call_number'] = call
    if note: d['notes'] = note
    d['source'] = src; return d
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
GJ = '魁本大字諸儒箋解古文眞寶後集'; GJW = 'd59fsvg015a9'
# (title, work, edition, year, reign, juan, basis, provs, sources, memo)
NEW = [
 ('詩人玉屑', 'd59f2hr0o2yq', '日本正德二年（1712）川勝五郎右衞門・瀨尾源兵衞刊本（玄惠批點，據朝鮮正統四年跋刻本重刻後印）', 1712, '正德', 21,
  '正德二年（1712）川勝五郎右衞門・瀨尾源兵衞藏版（刊記「正德二年辛卯首夏」），魏慶之編、玄惠批點，21卷，四周雙邊無界11行21字',
  [P('東北大學附屬圖書館', None, CIN('BC10858817'), '本館；10冊')], [CIN('BC10858817'), NDL('R100000136-I1970867909849537167')],
  '庫內同 Work 另有寬永十六年（1639）田原仁左衞門刊本（99jtrvtqtg），為不同版本。'),
 ('易經蒙引', 'd59f2nkkcb2b', '日本承應元年（1652）堤六左衞門刊本（重刻，宋喜公重訂）', 1652, '承應', 24,
  '承應元年（1652）堤六左衞門開板（卷末「承應元壬辰仲冬」），蔡清撰，24卷24冊，有林希元「重刻易經蒙引叙」',
  [P('名古屋大學文學部圖書室', 'A||II', CIN('BA84432602'), '24冊')], [CIN('BA84432602'), NDL('R100000136-I1971430859831158542'), NDL('R100000092-I2324_418856')],
  '庫內另有 995084axa8 寛文九年野田莊右衞門刊本，為不同版本。'),
 (GJ, GJW, '日本延寶三年（1675）吉田四郎右衞門刊本', 1675, '延寶', 2, '延寶三年（1675）吉田四郎右衞門刊，黃堅編，後集2卷',
  [P('東京國立博物館', '067-6', CIN('BB10842004'))], [CIN('BB10842004'), NDL('R100000136-I1970023484966611492')],
  '大阪大學附屬圖書館另藏吉田四郎右衞門刊「寳曆頃」印本（NCID BB18715587），是否為此版後印未能確認，未併入。'),
 (GJ, GJW, '日本延寶七年（1679）京都弘章堂刊本', 1679, '延寶', None, '延寶七年（1679）京都弘章堂刊（NDL 著錄出版年 1679）',
  [P('靜岡縣立中央圖書館', 'K234/1/', NDL('R100000001-I22111005010030996'), '貴重書庫')], [NDL('R100000001-I22111005010030996')], ''),
 (GJ, GJW, '日本元祿十五年（1702）江戶翠簾屋亦右衞門刊本', 1702, '元祿', None, '元祿十五年（1702）江戶翠簾屋亦右衞門刊（NDL 著錄出版年 1702）',
  [P('靜岡縣立中央圖書館', 'K145/17/', NDL('R100000001-I22111005010031595'), '貴重書庫')], [NDL('R100000001-I22111005010031595')], ''),
 (GJ, GJW, '日本享保十二年（1727）浪華書林刊本', 1727, '享保', 2, '享保十二年（1727）浪華書林刊，後集2卷',
  [P('明治大學圖書館', '092.1||51||H', CIN('BA83842380'), '本館')], [CIN('BA83842380'), NDL('R100000136-I1970304959857875218')], ''),
 ('救急選方', 'd59f2qa4bkld', '日本文化七年（1810）江戶飯島金助等刊本（多紀元簡著）', 1810, '文化', 2,
  '文化七年（1810）江戶飯島金助等刊（早稻田大學本著錄書肆「萬笈堂」、文化七年跋），多紀元簡著，2卷1冊',
  [P('國立國會圖書館', '特1-2941', NDL('R100000002-I000007282474'), '白井文庫；印記「芝山藏書」')], [NDL('R100000002-I000007282474'), NDL('R000000050-I000029765')],
  '庫內 988g2n8sg5 為享和元年（1801）聿修堂刊本，與此文化七年刊本年份不同，另立；早大本書肆著錄「萬笈堂」，與 NDL「飯島金助」是否同一書肆未核，故不掛早大館藏。'),
]
def main():
    import mintid
    ids = mintid.mint('Book', LANE, len(NEW)) if APPLY else ['dry%07d' % i for i in range(len(NEW))]
    files = []; log = []
    for (title, wid, ed, year, reign, juan, basis, provs, srcs, memo), bid in zip(NEW, ids):
        d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': '刻本',
             'dating': {'era': '日本', 'reign': reign, 'year': year, 'certainty': 'attested', 'source': 'catalog', 'basis': 'NDL Search／CiNii Books 書目著錄刊年：' + basis.split('，')[0]}}
        if juan: d['measures'] = [{'number': juan, 'unit': '卷'}]
        d['provenance'] = provs
        d['description'] = {'text': '《%s》，%s。日本和刻本（和刻本專項第二輪補建）。' % (title, basis), 'sources': srcs}
        d['sources'] = [srcent(s) for s in dict.fromkeys(srcs)]
        d['ai_note'] = '和刻本日本館藏專項第二輪（車道 wake-f，%s）：據 NDL Search／CiNii Books 書目頁（含所藏館記錄）新建；刊年、刊者、卷數錄自該書目頁，未核原書。%s' % (TODAY, memo)
        d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
        safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
        path = os.path.join('Book', bid[-3], bid[-2], bid[-1], '%s-%s%s.json' % (bid, title, safe))
        files.append(path)
        log.append(('新建', bid, title + '｜' + ed, ' / '.join(p['institution'] for p in provs), ' '.join(srcs)))
        if APPLY:
            os.makedirs(os.path.dirname(os.path.join(ROOT, path)), exist_ok=True)
            open(os.path.join(ROOT, path), 'w', encoding='utf-8').write(jd(d))
    if APPLY:
        with open(os.path.join(HERE, 'ledger2.tsv'), 'w', encoding='utf-8') as fh:
            for r in log: fh.write('\t'.join(r) + '\n')
        open(os.path.join(HERE, 'changed_files2.txt'), 'w').write('\n'.join(files) + '\n')
    print(len(NEW), '新建'); [print(r[:4]) for r in log]
main()
