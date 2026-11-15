#!/usr/bin/env python3
"""第三批（車道 a11-sjj-book-cn）：阮刻《十三經注疏》（清嘉慶二十年南昌府學重刻儀徵阮氏文選樓藏宋本）庫內缺的尚書／左傳／穀梁三種，補入同版 Collection。用法：build3.py [--apply]"""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa'))
import mintid
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); A = ap.parse_args()
TODAY = '2026-11-15'; LANE = 'a11-sjj-book-cn'; CID = '8rle1yr1kubr'
ITEMS = [('尚書注疏', 'd59f28noh3pc', '二十卷'), ('春秋左傳注疏', 'd59fxwpca0aq', '六十卷'), ('春秋穀梁傳注疏', 'd59f28na46pw', '二十卷')]
SRC = [{'id': 'rujiazg-16076', 'name': '儒家中國網《十三經注疏》版本考', 'type': 'url', 'details': 'https://www.rujiazg.com/article/16076'},
       {'id': 'wikipedia-13jing', 'name': '維基百科·十三經注疏', 'type': 'url', 'details': 'https://zh.wikipedia.org/wiki/十三經注疏'}]
bids = mintid.mint('Book', LANE, len(ITEMS)) if A.apply else ['dryb%06d' % i for i in range(len(ITEMS))]
files = {}
for (t, wid, mi), bid in zip(ITEMS, bids):
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': t, 'work_id': wid,
         'edition': '清嘉慶二十年南昌府學重刻儀徵阮氏文選樓藏宋本（阮元校刻《十三經注疏》本，附校勘記）', 'edition_type': '刻本',
         'dating': {'era': '清', 'reign': '嘉慶', 'year': 1815, 'certainty': 'attested', 'source': 'catalog', 'basis': '同版 Collection（中國古籍總目著錄）版本項「清嘉慶二十年南昌府學重刻」'},
         'measure_info': mi, 'contained_in': [{'id': CID}], 'sources': SRC,
         'ai_note': '2026-11-15 十三經縱向補全·中國傳世版本：阮刻《十三經注疏》十三經俱全（見所附兩種資料），庫內同版 Collection %s 僅挂六種，補入本種。卷數取通行阮刻（尚書注疏二十卷、春秋左傳注疏六十卷、春秋穀梁傳注疏二十卷）；各館藏號未逐館核。' % CID,
         'revision': '1.0.0', 'revised_at': TODAY}
    files['Book/%s/%s/%s/%s-%s清嘉慶二十年南昌府學刻阮刻本.json' % (bid[-3], bid[-2], bid[-1], bid, t)] = d
print('Book 新建', len(files))
if not A.apply: sys.exit(0)
for p, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(p)), exist_ok=True)
    open(os.path.join(BI, p), 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
json.dump({d['id']: p for p, d in files.items()}, open(os.path.join(HERE, 'result3.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
