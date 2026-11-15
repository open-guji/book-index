#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析緩存的 NDL 結果，產出每個 Work 的日本版本候選（按 年+書肆 分組），並與庫內 Book 對照。"""
import json, os, re, sys, html, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch2
S = fetch2.S
FOLD = str.maketrans({'註':'注','説':'說','経':'經','伝':'傳','関':'關','医':'醫','学':'學','国':'國','礼':'禮','義':'義','与':'與','弁':'辨','辯':'辨','対':'對','証':'證','斎':'齋','斉':'齊','訳':'譯','数':'數','広':'廣','応':'應','万':'萬','両':'兩','処':'處','図':'圖','気':'氣','体':'體','台':'臺','当':'當','会':'會','覚':'覺','観':'觀','読':'讀','続':'續','続':'續','経':'經','銭':'錢','巻':'卷','槀':'稿','藁':'稿','縁':'緣','総':'總','聴':'聽','陽':'陽','寿':'壽','剤':'劑','髄':'髓','拠':'據','点':'點','実':'實','称':'稱','頼':'賴','団':'團','乱':'亂','将':'將','刪':'刪','参':'參','恒':'恆','盖':'蓋','蔵':'藏','隠':'隱','遅':'遲','暦':'曆','歴':'歷','暦':'曆','徳':'德','兪':'俞','効':'效','楽':'樂','薬':'藥','覧':'覽','撰':'撰','號':'號','号':'號','譲':'讓','訂':'訂','説':'說','擬':'擬','録':'錄','鈔':'抄','鈔':'抄','写':'寫','辺':'邊','虫':'蟲','獣':'獸','猟':'獵','塩':'鹽','党':'黨','択':'擇','択':'擇','従':'從','舎':'舍','予':'預','余':'餘','両':'兩','経':'經','属':'屬','駅':'驛','歳':'歲','済':'濟','済':'濟','乗':'乘','済':'濟','営':'營','亀':'龜','焼':'燒','騒':'騷','猶':'猶','圓':'圓','円':'圓','聖':'聖','遊':'遊','変':'變','択':'擇','論':'論','抜':'拔','荘':'莊','圧':'壓','衛':'衛','衞':'衛','佛':'佛','仏':'佛','并':'並','併':'並','沢':'澤','釈':'釋','駁':'駁','駮':'駁','呉':'吳','競':'兢','栢':'柏','頴':'穎','槀':'稿','徳':'德','兢':'兢','帰':'歸','尭':'堯','寀':'案','鼒':'鼎','惺':'惺','観':'觀','號':'號','聞':'聞','宝':'寶','蘆':'蘆','箚':'札','説':'說','荘':'莊','経':'經','體':'體','邨':'村','隆':'隆','倶':'俱','劉':'劉','帷':'惟'})
def nz(s): return re.sub(r'[\s　　・·,，.。()（）\[\]［］〔〕「」『』《》\-—∥]', '', s or '').translate(FOLD)
ERAS = '慶長|元和|寛永|寬永|正保|慶安|承応|承應|明暦|明曆|万治|萬治|寛文|寬文|延宝|延寶|天和|貞享|元禄|元祿|宝永|寶永|正徳|享保|元文|寛保|寬保|延享|寛延|寬延|宝暦|寶曆|寶暦|明和|安永|天明|寛政|寬政|享和|文化|文政|天保|弘化|嘉永|安政|万延|萬延|文久|元治|慶応|慶應|明治|天正|文禄|文祿|永禄|永祿|元亀|應仁|応仁|明応|延徳|文明|長享|寛正|應永|応永'
ERA_RE = re.compile('(' + ERAS + r')(元|\d+)')
ERA_START = {'慶長':1596,'元和':1615,'寛永':1624,'寬永':1624,'正保':1644,'慶安':1648,'承応':1652,'承應':1652,'明暦':1655,'明曆':1655,'万治':1658,'萬治':1658,'寛文':1661,'寬文':1661,'延宝':1673,'延寶':1673,'天和':1681,'貞享':1684,'元禄':1688,'元祿':1688,'宝永':1704,'寶永':1704,'正徳':1711,'享保':1716,'元文':1736,'寛保':1741,'寬保':1741,'延享':1744,'寛延':1748,'寬延':1748,'宝暦':1751,'寶曆':1751,'寶暦':1751,'明和':1764,'安永':1772,'天明':1781,'寛政':1789,'寬政':1789,'享和':1801,'文化':1804,'文政':1818,'天保':1830,'弘化':1844,'嘉永':1848,'安政':1854,'万延':1860,'萬延':1860,'文久':1861,'元治':1864,'慶応':1865,'慶應':1865,'明治':1868,'天正':1573,'文禄':1592,'文祿':1592,'永禄':1558,'元亀':1570}
def era_year(s):
    m = ERA_RE.search(s or '')
    if not m: return None
    n = 1 if m.group(2) == '元' else int(m.group(2))
    return ERA_START[m.group(1)] + n - 1
def parse(xml):
    out = []
    for it in re.findall(r'<item>(.*?)</item>', xml, re.S):
        g = lambda t: [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<%s(?:\s[^>]*)?>(.*?)</%s>' % (t, t), it, re.S)]
        link = (g('link') or [''])[0]
        out.append(dict(title=(g('dc:title') or g('title') or [''])[0], vol=(g('dcndl:volume') or [''])[0], cre=g('dc:creator'), pub=(g('dc:publisher') or [''])[0],
                        date=(g('dc:date') or [''])[0], issued=(g('dcterms:issued') or [''])[0], ext=(g('dc:extent') or [''])[0], desc=[d for d in g('dc:description') if d], link=link, cat=g('category')))
    return out
def load_work_items(title, extra=''):
    import hashlib
    f = os.path.join(fetch2.CACHE, hashlib.md5(fetch2.q(title, extra).encode()).hexdigest() + '.xml')
    return parse(open(f, encoding='utf8').read()) if os.path.exists(f) else None
def lib(link):
    m = re.search(r'/(R\d{9})-', link)
    return {'R100000002':'國立國會圖書館','R100000039':'國立國會圖書館','R000000050':'早稻田大學圖書館','R100000092':'九州大學附屬圖書館','R100000102':'東京大學','R100000105':'京都大學','R000000054':'宮城縣圖書館','R100000133':'石川縣立圖書館','R100000138':'名古屋市鶴舞中央圖書館','R100000094':'西尾市岩瀨文庫','R100000136':'CiNii聚合','R100000001':'?','R100000103':'?'}.get(m.group(1) if m else '', m.group(1) if m else '')
if __name__ == '__main__':
    db = json.load(open(S + '/a_db.json')); works = json.load(open(S + '/a_works.json'))
    bw = collections.defaultdict(list)
    for b in db['books']: bw[b['work_id']].append(b)
    res = []
    for w in works:
        items = load_work_items(w['title'])
        W = db['works'][w['wid']]
        tset = {nz(w['title'])} | {nz(t) for t in W.get('additional_titles', [])}
        cands = collections.defaultdict(list)
        if items is None: res.append(dict(w=w, status='NOFETCH')); continue
        for x in items:
            if nz(re.sub(r'\d+巻.*$', '', x['title'])) not in tset and nz(x['title']) not in tset: continue
            yr = era_year(x['issued'])
            if yr is None: continue
            key = (yr, nz(x['pub']))
            cands[key].append(x)
        res.append(dict(w=w, n=len(items), cands={'%d|%s' % k: v for k, v in cands.items()}))
    json.dump(res, open(S + '/a_cands.json', 'w'), ensure_ascii=False)
    tot = 0
    for r in res:
        if r.get('status'): print(r['w']['i'], r['w']['title'], r['status']); continue
        print(r['w']['i'], r['w']['title'], r['w']['au'], 'NDL', r['n'], '候選組', len(r['cands']))
        for k, v in r['cands'].items(): print('   ', k, [lib(x['link']) for x in v][:5], v[0]['issued'], v[0]['pub'], v[0]['cre'][:2])
        tot += len(r['cands'])
    print('total groups', tot)
