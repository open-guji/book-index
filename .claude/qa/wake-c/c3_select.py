# -*- coding: utf-8 -*-
"""wake-c 第三輪：從 c3_det.json 篩出強證候選並按版本聚簇，輸出 c3_groups.json 與統計。"""
import json, re, sys, collections
sys.path.insert(0, '.')
from c3_map import classify, norm, allowed
det = json.load(open('c3_det.json')); cand = json.load(open('c3_cand.json')); known = json.load(open('c3_known.json'))
REIGN_OK = re.compile(r'^(?P<r>[^\d\[\]\(\)\s・]{2,4}?)(?P<n>\d{1,2}|元)(?:\.\d{1,2})?\s*[\[\(](?P<y>\d{4})[\]\)](?:\s*\[?刊\]?)?$')
def lst(x): return x if isinstance(x, list) else ([] if x is None else [x])
INST = {'大学': '大學', '図書館': '圖書館', '附属': '附屬', '総合': '總合', '経済': '經濟', '医学': '醫學', '国立': '國立', '国会': '國會', '学': '學', '国': '國', '館': '館', '研究所': '研究所', '蔵': '藏', '芸': '藝', '図': '圖', '総': '總', '属': '屬', '経': '經', '済': '濟', '医': '醫', '会': '會', '体': '體', '覚': '覺', '広': '廣', '関': '關', '歴': '歷', '宮内庁': '宮內廳', '内': '內', '庁': '廳', '書陵部': '書陵部', '県': '縣', '立': '立', '横': '橫', '島': '島', '戸': '戶', '仏': '佛', '両': '兩', '徳': '德', '栄': '榮', '来': '來', '斎': '齋', '桜': '櫻', '数': '數', '実': '實', '応': '應', '浜': '濱', '発': '發', '児': '兒', '験': '驗', '検': '檢', '沢': '澤', '渓': '溪', '竜': '龍', '蔵': '藏', '帝': '帝', '経': '經', '参': '參', '剤': '劑', '臓': '臟', '礼': '禮', '歯': '齒', '図': '圖', '双': '雙', '弁': '辨', '黒': '黑', '塩': '鹽', '亜': '亞', '芸': '藝', '聴': '聽', '釈': '釋', '摂': '攝', '気': '氣', '労': '勞', '営': '營', '号': '號', '価': '價'}
def trad(s):
    for k in sorted(INST, key=len, reverse=True): s = s.replace(k, INST[k])
    return re.sub(r'\s+', '', s.replace('　', ''))
rows = []; skip = collections.Counter(); skipped = []
for n, d in det.items():
    if not d: skip['無詳情'] += 1; continue
    i = cand[n]; w = classify(d['title'][0] if isinstance(d['title'], list) else d['title'], d['cr'] or '', d.get('alt'))
    if not w: skip['無Work對應'] += 1; continue
    if not allowed(d['title'], w[1]): skip['題名非本Work本體(衍生/異書)'] += 1; skipped.append((n, d['title'], '衍生'+w[1])); continue
    pd = [p for p in lst(d['pd']) if p]; pubs = [p for p in lst(d['pub']) if p]
    notes = lst(d['note'])
    why = None
    if len(pd) != 1: why = '多出版項/刊年'
    else:
        m = REIGN_OK.match(pd[0].strip())
        if not m: why = '刊年為目錄推定或不含年號(%s)' % pd[0]
    if not why and (not pubs or any(re.search(r'[\[\]不明]', p) for p in pubs)): why = '出版者推定/不明'
    if not why and any(re.search(r'出版事項[はを].*(による|参照|より)|出版事項は|刊記なし|刊年.*推定|推定', x) for x in notes): why = '出版事項借自他書/推定'
    if not why and any(re.search(r'写本|寫本|鈔本|手写|稿本|影印|複製|復刻|復製|活字版（?昭和', x) for x in notes + [d['title'] if isinstance(d['title'], str) else ' '.join(map(str, d['title']))]): why = '寫/影/複製'
    if not why and not d['own']: why = '無所藏館'
    if why: skip[why.split('(')[0]] += 1; skipped.append((n, d['title'], why)); continue
    m = REIGN_OK.match(pd[0].strip()); y = int(m.group('y'))
    if not (1500 <= y <= 1867): skip['非1868前'] += 1; continue
    rows.append(dict(ncid=n, work=w[0], wname=w[1], title=d['title'][0] if isinstance(d['title'], list) else d['title'], cr=d['cr'], pubs=pubs, reign=m.group('r'), rn=m.group('n'), y=y, ext=d['ext'], notes=notes, own=[trad(o) for o in d['own']], size=d.get('size'), alt=d.get('alt')))
print(len(rows), 'rows;', dict(skip))
json.dump(rows, open('c3_rows.json', 'w'), ensure_ascii=False, indent=0)
json.dump(skipped, open('c3_skipped.json', 'w'), ensure_ascii=False, indent=0)
