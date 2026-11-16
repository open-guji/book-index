#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NDL Search OpenSearch 查詢（帶緩存、限速）。用法：ndl.py <題名> [責任者] [cnt]"""
import sys, os, json, time, hashlib, urllib.parse, urllib.request, re
import xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); CD = os.path.join('/tmp', 'wb_cache'); os.makedirs(CD, exist_ok=True)
M = {}
for a, b in zip('經傳學國啓讀圖藥醫禮說寶錄號鑑點與義舊體關歷齋釋證華輯處對無總廣覺氣觀繼讓歸書師發蒙濟聖勝畫禪鐵夢對藝稱灣條邊辨應當辭產靈聯興會劍黃樂經錢兒帖鈔寫', '経伝学国啓読図薬医礼説宝録号鑑点与義旧体関歴斎釈証華輯処対无総広覚気観継譲帰書師発蒙済聖勝画禅鉄夢対芸称湾条辺弁応当辞産霊連興会剣黄楽経銭児帖鈔写'):
    M[ord(a)] = b
def jp(s): return s.translate(M)
def fetch(params):
    url = 'https://ndlsearch.ndl.go.jp/api/opensearch?' + urllib.parse.urlencode(params)
    f = os.path.join(CD, hashlib.md5(url.encode()).hexdigest() + '.xml')
    if os.path.exists(f): return open(f, 'rb').read()
    for t in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; research-bot)'})
            data = urllib.request.urlopen(req, timeout=60).read(); break
        except Exception as e:
            data = None; time.sleep(3)
    if data is None: return b''
    open(f, 'wb').write(data); time.sleep(1.1); return data
NS = {'dc': 'http://purl.org/dc/elements/1.1/', 'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'dcterms': 'http://purl.org/dc/terms/'}
def search(title, creator=None, cnt=50):
    p = {'title': jp(title), 'cnt': cnt}
    if creator: p['creator'] = creator
    data = fetch(p)
    try: root = ET.fromstring(data)
    except Exception: return []
    out = []
    for it in root.iter('item'):
        g = lambda t: (it.findtext(t, namespaces=NS) or '').strip()
        out.append({'title': g('dc:title'), 'link': it.findtext('link') or '', 'creator': g('dc:creator'), 'pub': g('dc:publisher'),
                    'date': g('dc:date'), 'issued': g('dcterms:issued'), 'vol': g('dcndl:volume'), 'ext': g('dc:extent'),
                    'cat': '/'.join(c.text for c in it.findall('category')), 'desc': re.sub(r'<[^>]+>', ' ', it.findtext('description') or '')[:200]})
    return out
if __name__ == '__main__':
    t = sys.argv[1]; c = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
    for r in search(t, c, int(sys.argv[3]) if len(sys.argv) > 3 else 50):
        print(r['link'].split('/')[-1], '|', r['title'], '|', r['creator'], '|', r['pub'], '|', r['date'], r['issued'], '|', r['vol'], r['ext'], '|', r['cat'])
