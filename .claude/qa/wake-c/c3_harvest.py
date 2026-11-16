# -*- coding: utf-8 -*-
"""wake-c 第三輪：CiNii OpenSearch(JSON) 逐頁收割。用法：c3_harvest.py"""
import json, urllib.parse, sys, os
from ndl import get
Q = '''論語 論語集解 論語集註 論語義疏 論語徵 論語古義 論語古訓 論語注疏 論語筆解 論語語由 論語集說 論語大全 論語講義 論語鄭註 古本論語 論語訓點 論語首書 標註論語 論語白文 論語考 論語新疏 論語or 論語解 論語知言 論語證解 論語集覽 論語徵集覽 論語徵廣義 論語大疏 論語原義 論語聞書 論語抄 論語諺解 論語示蒙句解
孟子 孟子集註 孟子趙註 孟子古義 孟子定本 孟子訓點 孟子首書 標註孟子 孟子考文 七經孟子考文補遺 孟子注疏 孟子正義 孟子白文 孟子講義 孟子解 孟子抄 孟子諺解 孟子師說 孟子養氣章
大學 中庸 大學章句 中庸章句 大學或問 中庸或問 大學古本 大學啓蒙 大學諺解 大學定本 大學解 中庸解 中庸發揮 中庸錯簡說 大學中庸 大學中庸章句 大學白文
四書 四書集註 四書章句集註 四書集注 四書或問 四書大全 四書語類 四書白文 四書輯釋 四書纂疏 四書示蒙句解 四書訓點 四書集註抄 四書蒙引 四書存疑 四書標註 四書集編 四書講義 四書解
孝經 古文孝經 孝經孔傳 孝經鄭註 孝經注疏 孝經大義 孝經刊誤 孝經直解 孝經啓蒙 孝經外傳 孝經諺解 孝經集覽 孝經新解 孝經國字解 古文孝經孔氏傳 孝經鄭氏解 孝經句解 孝經標註
爾雅 爾雅注 爾雅註疏 爾雅疏 爾雅翼 爾雅音圖 爾雅正義 爾雅郭璞 爾雅釋義 爾雅箋註 爾雅音義 爾雅註 爾雅義疏 爾雅古義 爾雅便覽'''.split()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c3_harvest.json')
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
def fetch(q, y0, y1, items):
    base = {'q': q, 'count': 100, 'format': 'json', 'year_from': y0, 'year_to': y1}
    u = 'https://ci.nii.ac.jp/books/opensearch/search?' + urllib.parse.urlencode(dict(base, p=1))
    t = get(u)
    if not t: return
    try: tot = int(json.loads(t)['@graph'][0].get('opensearch:totalResults', 0))
    except Exception: return
    if tot > 500 and y1 > y0:
        m = (y0 + y1) // 2
        fetch(q, y0, m, items); fetch(q, m + 1, y1, items); return
    for p in range(1, min(5, (tot + 99) // 100) + 1):
        t = get('https://ci.nii.ac.jp/books/opensearch/search?' + urllib.parse.urlencode(dict(base, p=p)))
        if not t: break
        try: its = json.loads(t)['@graph'][0].get('items', [])
        except Exception: break
        for it in its:
            items.append({'ncid': it['@id'].split('/')[-1], 't': it.get('title'), 'cr': it.get('dc:creator'), 'pub': it.get('dc:publisher'), 'date': it.get('dc:date') or it.get('prism:publicationDate'), 'own': it.get('cinii:ownerCount')})
for q in Q:
    if q in res: continue
    items = []
    fetch(q, 1450, 1911, items)
    seen = {}
    for i in items: seen[i['ncid']] = i
    res[q] = list(seen.values())
    print(q, len(res[q]), flush=True)
    json.dump(res, open(OUT, 'w'), ensure_ascii=False)
