#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和刻本日本馆藏专项·车道 wake-e（shard4）：補挂 NDL 館藏 + 新建日本刊本。用法 build.py [--apply]"""
import json, os, re, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); import mintid
APPLY = '--apply' in sys.argv; TODAY = '2026-11-15'; LANE = 'wake-e'
NDL = 'https://ndlsearch.ndl.go.jp/books/'
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
# (book id, NDL 記錄號, 依據說明)
ATTACH = [
 ('988g0gw841', 'R100000002-I000011138564', '明和8年（1771）河内屋茂八ほか刊，江田益英校，9册'),
 ('988g1wpmac', 'R100000002-I029961000', '嘉永7年（1854）英大助ほか8名，丹波元堅撰（存誠藥室叢書）'),
 ('988g1m3jsw', 'R100000002-I033855682', '天保10年（1839）英大助ほか，丹波元堅撰，叢書名存誠藥室叢書'),
 ('988g3epo98', 'R100000002-I028016275', '文化6年（1809）萬笈堂英平吉刊，丹波元簡撰；萬笈堂為聿修堂版書肆，年同責任者同'),
 ('988g0a105f', 'R100000002-I000007296694', '安永8年（1779）須原屋伊八（青藜閣）刊，山田正珍撰'),
 ('988g7r3kei', 'R100000002-I000007529954', '明暦2年（1656）上村次郎衞門印，新刻釋名8卷，明畢效欽校'),
 ('993fny2zup', 'R100000002-I000007512386', '嘉永3年（1850）重刊官版，出雲寺萬次郎發兌，詩集傳通釋20卷，8册'),
 ('994xclvvuo', 'R100000002-I000007508889', '享和2年（1802）官版，出雲寺萬次郎發兌，周易本義辯證5卷，3册'),
]
# 新建：(title, work, edition, reign, year, publisher, ndl, extra_note)
NEW = [
 ('韻鏡', 'd59f2og22fi8', '日本貞享四年長尾平兵衞刊本', '貞享', 1687, '長尾平兵衞', 'R100000002-I000007537980', '韻鏡3卷首1卷，宋張麟之撰，1册。庫內該Work下既有寬永十八年田原仁右衛門覆刊本、寬永間活字本、享祿元年釋宗仲本，刊年刊者皆不同，故另立。'),
 ('孝經', 'd59f28nl1hqe', '日本寬政十二年河南儀兵衞堺屋伊兵衞刊本', '寬政', 1800, '河南儀兵衞、堺屋伊兵衞', 'R100000002-I000007514174', '孝經1卷，唐玄宗註，佐野山陰（藤原憲）點，20丁。庫內該Work下既有寬政四年刻本、寬政九年明道館刊本，刊年刊者皆不同，故另立。'),
 ('詩緝', 'd59f2hunrr42', '日本天保十五年姬路藩仁壽館刊本（河內屋喜兵衞執次）', '天保', 1844, '姬路藩仁壽館；河內屋喜兵衞執次', 'R100000002-I000007512377', '詩緝36卷，宋嚴粲撰，18册（合9册）。庫內另有99522lumm9「天保十五年姬路仁壽館覆明味經堂刻弘化二年印本」，同為仁壽館版，但NDL此本著錄為天保十五年刊、未見弘化二年印記，是否同一印次無法確認，故另立並互見。'),
]
def find_book(bid):
    d = 'Book/%s/%s/%s/' % (bid[-3], bid[-2], bid[-1])
    for f in os.listdir(os.path.join(BI, d)):
        if f.startswith(bid + '-'): return d + f
rows = []; changed = []
for bid, ndl, why in ATTACH:
    p = find_book(bid); d = json.load(open(os.path.join(BI, p), encoding='utf-8'))
    url = NDL + ndl
    if any(url in (x.get('source') or '') for x in d.get('provenance', [])): continue
    d.setdefault('provenance', []).append({'institution': '國立國會圖書館', 'source': 'NDL Search ' + url})
    a, b, c = d['revision'].split('.'); d['revision'] = '%s.%s.%d' % (a, b, int(c) + 1); d['revised_at'] = TODAY
    note = '2026-11-15 和刻本日本馆藏专项（wake-e）：補挂國立國會圖書館藏，依據NDL Search %s（%s）；題名、責任者、刊年、書肆與本條版本名一致。' % (url, why)
    d['ai_note'] = (d.get('ai_note', '') + '\n' + note).strip()
    changed.append((p, d)); rows.append((bid, d['title'], '補挂', '國立國會圖書館', url))
newfiles = []
ids = mintid.mint('Book', LANE, len(NEW)) if APPLY else ['dryb%06d' % i for i in range(len(NEW))]
for (title, wk, ed, reign, year, pub, ndl, extra), bid in zip(NEW, ids):
    url = NDL + ndl
    d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wk, 'edition': ed, 'edition_type': '刻本',
         'dating': {'era': '日本', 'reign': reign, 'year': year, 'certainty': 'attested', 'source': 'catalog', 'basis': 'NDL Search 著錄刊年 %d（%s）' % (year, reign)},
         'publication_info': {'publisher': pub, 'place': '日本'},
         'provenance': [{'institution': '國立國會圖書館', 'source': 'NDL Search ' + url}],
         'description': {'text': '《%s》，%s。%s國立國會圖書館藏。' % (title, ed, extra), 'sources': ['NDL Search ' + url]},
         'sources': [{'id': 'ndl-' + ndl, 'name': '國立國會圖書館サーチ', 'type': 'url', 'details': url}],
         'ai_note': '2026-11-15 和刻本日本馆藏专项（wake-e）：據NDL Search和古書・漢籍著錄新建（出版者、刊年錄自該記錄），未核原書。',
         'id': bid, 'revision': '1.0.0', 'revised_at': TODAY}
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
    changed.append(('Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, title, safe), d)); rows.append((bid, title, '新建', '國立國會圖書館', url))
for p, d in changed: print(p)
if APPLY:
    for p, d in changed:
        os.makedirs(os.path.dirname(os.path.join(BI, p)), exist_ok=True)
        open(os.path.join(BI, p), 'w', encoding='utf-8').write(jd(d))
    with open(os.path.join(HERE, 'files.txt'), 'w') as f: f.write('\n'.join(p for p, _ in changed) + '\n')
    json.dump(rows, open(os.path.join(HERE, 'rows.json'), 'w'), ensure_ascii=False)
