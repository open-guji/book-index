# -*- coding: utf-8 -*-
"""wake-d 第三輪輔助：CiNii 書誌頁解析與繁體轉換（build3_wake_d.py 用）。"""
import re, html, os, time, hashlib, urllib.request, urllib.parse
CD = os.environ.get('WK3_CACHE', '/tmp/wk_d4/cache'); os.makedirs(CD, exist_ok=True)
def get(url):
    f = os.path.join(CD, hashlib.md5(url.encode()).hexdigest())
    if os.path.exists(f): return open(f, encoding='utf-8').read()
    d = None
    for t in range(5):
        try:
            d = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (research; wake-d4)'}), timeout=60).read().decode('utf-8', 'replace'); break
        except Exception as e:
            d = None; time.sleep(4 * (t + 1) ** 2 if '429' in str(e) else 3 * (t + 1))
    if d is None: return ''
    open(f, 'w', encoding='utf-8').write(d); time.sleep(2.2); return d
M = dict(zip('寛衛蔵経伝点国学辺沢広弁竜図斎帯当児歴万来続訳変余両与条属証献号参抜摂拠尽礼灯仏区処数断旧暦鉄随発営薬医画関浜栄総会験黒実対縁聴戯覚醸奨献繊剣県効黙読鉄壱弐拝覧舎歳塩嶋',
            '寬衞藏經傳點國學邊澤廣辨龍圖齋帶當兒歷萬來續譯變餘兩與條屬證獻號參拔攝據盡禮燈佛區處數斷舊曆鐵隨發營藥醫畫關濱榮總會驗黑實對緣聽戲覺釀獎獻纖劍縣效默讀鐵壹貳拜覽舍歲鹽嶋'))
def trad(s): return ''.join(M.get(c, c) for c in s)
KN = '〇一二三四五六七八九'
def kanji_year(n):
    n = int(n)
    if n == 1: return '元'
    s = ''
    if n >= 100: s += KN[n // 100] + '百'; n %= 100
    if n >= 10: s += ('' if n // 10 == 1 else KN[n // 10]) + '十'; n %= 10
    if n: s += KN[n]
    return s
def ncid(n):
    d = get('https://ci.nii.ac.jp/ncid/' + n)
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', d, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', '\n', t)); L = [x.strip() for x in t.split('\n') if x.strip()]
    r = dict(ncid=n, title='', au='', publine='', place='', vols='', notes=[], holders=[], aliases=[])
    if '書誌事項' not in L: return r
    i = L.index('書誌事項'); r['title'] = L[i + 1]; r['au'] = L[i + 2] if i + 2 < len(L) else ''; r['publine'] = L[i + 3] if i + 3 < len(L) else ''
    if '大学図書館所蔵' in L:
        j = L.index('大学図書館所蔵'); k = L.index('OPAC') if 'OPAC' in L[j:] else len(L)
        seg = L[j:k]
        LIB = re.compile(r'(大学|大學|図書館|図書室|文庫|研究所|研究室|博物館|センター|学園|機構|資料館|美術館|会館|書館|学校|院|寺|宮)[^\d]{0,12}$')
        cur = None; cn = ''
        for a in range(len(seg)):
            x = seg[a]
            if a > 0 and seg[a - 1] in ('全', '件', '件\xa0/', '図', '電') and False: pass
            if cur is None or True:
                if LIB.search(x) and not re.search(r'[巻卷冊]', x) and not re.match(r'^\d', x) and x not in (',',) and len(x) <= 40 and (a + 1 < len(seg)) and not any(h[0] == x for h in r['holders']):
                    # 館名行：其後（跳過「図」）出現條碼前的行
                    m = a + 1
                    if seg[m] in ('図', '電', '雑'): m += 1
                    between = []
                    while m < len(seg) and not re.match(r'^\d{8,12}$', seg[m]) and len(between) < 4: between.append(seg[m]); m += 1
                    c = ''
                    if between and re.search(r'[0-9A-Za-z/]', between[-1]) and not re.search(r'[巻卷冊・]', between[-1]) and not LIB.search(between[-1]): c = between[-1]
                    if m < len(seg) and re.match(r'^\d{8,12}$', seg[m]):
                        r['holders'].append((x, c))
    if '注記' in L[i:]:
        j = L.index('注記', i); k = L.index('Tweet', j) if 'Tweet' in L[j:] else len(L)
        r['notes'] = L[j + 1:k]
    if 'タイトル別名' in L[i:]:
        j = L.index('タイトル別名', i); r['aliases'] = [L[j + 1]]
    for lab, key in (('出版地', 'place'), ('ページ数/冊数', 'vols')):
        if lab in L[i:]: r[key] = L[L.index(lab, i) + 1]
    return r
