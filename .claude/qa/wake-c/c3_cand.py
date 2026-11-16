# -*- coding: utf-8 -*-
"""wake-c 第三輪：從 c3_harvest.json 篩候選（1912前、日本刊本、未入庫），取 NCID 詳情。"""
import json, re, sys
from ndl import get
H = json.load(open('c3_harvest.json')); known = json.load(open('c3_known.json'))
NORM = str.maketrans('経伝学説証図礼誌覚訳辞処点様楽斎歳'.replace('歳',''), '經傳學說證圖禮誌覺譯辭處點樣樂齋')
KEY = re.compile(r'^[\s\[\(（【]*(?:新刻|新刊|新鐫|新鎸|校正|校訂|校刻|改正|標註|標注|首書|古本|古文|御注|訂正|増補|增補|新撰|新板|頭書|鼇頭|欄外|精校|精選|再刻|再刊|音訓|訓點|補注|縮臨|足利|正平|明應|天保|嘉永|官版|官刻|和刻|影宋|覆宋)*(?:四書|論語|論语|孟子|大學|中庸|孝經|孝経|爾雅|尒雅)(?!.*(?:大學衍義|大學豫備|大學令|女大學|大學院|大學校|大學規則|大學一覽|大學年報|大學講義錄|大學區))')
def yr(d):
    d = d if isinstance(d, str) else (d[0] if d else '')
    m = re.search(r'\d{4}', d or ''); return int(m.group()) if m else None, ('[' in (d or '')) 
cand = {}
for q, items in H.items():
    for i in items:
        t = (i['t'] or '').translate(NORM)
        if not KEY.search(t) and not re.search(r'(古本論語|論語集解|論語集註|論語徵|論語義疏|孟子集註|孟子趙註|古文孝經|孝經孔傳|孝經鄭註|爾雅)',t): continue
        if re.search(r'(女大學|女四書|大學衍義|大學豫備|大學令|大學院|大學校|大學規則|大學一覽|大學年報|大學講義錄)',t): continue
        y, br = yr(i['date'])
        if y is None or y > 1911 or y < 1500: continue
        cand[i['ncid']] = dict(i, y=y, br=br)
print(len(cand), 'candidates;', sum(1 for n in cand if n in known), 'already in repo')
json.dump(cand, open('c3_cand.json', 'w'), ensure_ascii=False)
