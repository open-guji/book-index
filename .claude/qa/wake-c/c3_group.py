# -*- coding: utf-8 -*-
"""wake-c 第三輪：校驗年號-西曆一致、聚簇同版多 NCID、與庫內既有日本刊本比對查重。輸出 c3_groups.json。"""
import json, re, sys, collections
sys.path.insert(0, '.')
S = '/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
START = {'慶長': 1596, '元和': 1615, '寬永': 1624, '正保': 1644, '慶安': 1648, '承應': 1652, '明曆': 1655, '萬治': 1658, '寬文': 1661, '延寶': 1673, '天和': 1681, '貞享': 1684, '元祿': 1688, '寶永': 1704, '正德': 1711, '享保': 1716, '元文': 1736, '寬保': 1741, '延享': 1744, '寬延': 1748, '寶曆': 1751, '明和': 1764, '安永': 1772, '天明': 1781, '寬政': 1789, '享和': 1801, '文化': 1804, '文政': 1818, '天保': 1830, '弘化': 1844, '嘉永': 1848, '安政': 1854, '萬延': 1860, '文久': 1861, '元治': 1864, '慶應': 1865}
ALIAS = str.maketrans('宝暦寛禄応歴万徳亨貞眀寳', '寶曆寬祿應曆萬德享貞明寶')
def reign_norm(r):
    r = r.translate(ALIAS).replace('寳', '寶').replace('貞亨', '貞享').replace('延寳', '延寶').replace('寶歴', '寶曆').replace('寶暦', '寶曆')
    r = r.replace('曆', '曆').replace('暦', '曆').replace('歴', '曆').replace('歷', '曆').replace('眀', '明')
    return r
KAN = '〇一二三四五六七八九'
def kn(n):
    n = int(n)
    if n == 1: return '元'
    if n < 10: return KAN[n]
    if n == 10: return '十'
    if n < 20: return '十' + KAN[n - 10]
    return KAN[n // 10] + '十' + (KAN[n % 10] if n % 10 else '')
SN = str.maketrans('衞弥祟栢冨', '衛彌崇柏富')
def shops(pubs):
    out = []
    for p in pubs:
        p = p.translate(SN)
        p = re.sub(r'[\[\]]|ほか|ほか\d+書肆', '', p)
        for s in re.split(r'\s*[;:；：]\s*', p):
            s = s.strip()
            if s and s not in out: out.append(s)
    return out
from c3_map import core_title
def nshop(x):
    x = re.sub(r'^.{1,3}[堂房舘館閣軒樓齋]', '', x) if re.search(r'^.{1,3}[堂房舘館閣軒樓齋].{3,}', x) else x
    return x.replace('屋', '').replace('書肆', '').replace('東都', '').replace('江戶', '').replace('皇都', '').replace('浪華', '')
def anno(cr):
    c = cr or ''
    out = []
    for pat, nm in [(r'道春|信勝|羅山|林點|林訓點|林信', '林羅山'), (r'後藤|芝山|世鈞', '後藤芝山'), (r'東涯|東厓|長胤', '伊藤東涯'), (r'山崎|闇齋|嘉點', '山崎闇齋'), (r'佐藤一齋|一齋', '佐藤一齋'), (r'赤澤', '赤澤太一郎'), (r'根遜志|根本遜志|武內義雄', '根本遜志'), (r'山本惟孝', '山本惟孝'), (r'明倫堂|藤原良國', '加賀明倫堂'), (r'山本龍|山本信有', '山本北山')]:
        if re.search(pat, c): out.append(nm)
    return '+'.join(out)
rows = json.load(open('c3_rows.json')); good = []; bad = []
for r in rows:
    rg = reign_norm(r['reign']); n = 1 if r['rn'] == '元' else int(r['rn'])
    if rg not in START or START[rg] + n - 1 != r['y']: bad.append((r['ncid'], r['reign'], r['rn'], r['y'])); continue
    r['reign'] = rg; r['n'] = n; r['shops'] = shops(r['pubs']); good.append(r)
print(len(good), 'ok', len(bad), 'bad-year', bad[:8])
# 既有庫
ex = {}
for l in open(S + 'c_ed.txt', encoding='utf-8'):
    p = l.split(':', 3); bid = p[1].split('/')[-1].split('-')[0]; fn = p[1].split('/')[-1][:-5]
    e = re.search(r'"edition": "(.*)"', l); ex[bid] = (fn, e.group(1) if e else '')
def exmatch(r):
    hits = []
    ys = [str(r['y']), r['reign'] + kn(r['n']) + '年', r['reign'] + str(r['n']) + '年']
    for bid, (fn, e0) in ex.items():
        e = reign_norm(e0).translate(SN)
        if any(y in e for y in ys):
            hits.append((bid, e0[:50], any(s[:3] in e or s[:2] in e for s in r['shops'] if len(s) >= 2)))
    return hits
mine = json.load(open('c3_mine_full.json'))
groups = collections.OrderedDict()
def normcr(c): return re.sub(r'[\s\[\]\(\)（）]', '', c or '')
for r in good:
    r['shops'] = [re.sub(r'\s+', '', x) for x in r['shops']]
    r['vol'] = (re.search(r'(\d+)[巻卷]', r['title'].split(' ; ')[0]) or [None, ''])[1]
    r['anno'] = anno(r['cr'])
    r['nshops'] = sorted(set(nshop(x) for x in r['shops']))
    key = (r['work'], core_title(r['title']), r['y'], tuple(r['nshops']), r['vol'], r['anno'])
    groups.setdefault(key, []).append(r)
out = []
for k, rs in groups.items():
    r0 = rs[0]; own = []
    for r in rs:
        for o in r['own']:
            if o not in own: own.append(o)
    hits = exmatch(r0)
    out.append(dict(work=r0['work'], wname=r0['wname'], title=r0['title'], y=r0['y'], reign=r0['reign'], n=r0['n'], shops=r0['shops'], cr=r0['cr'], ncids=[r['ncid'] for r in rs], own=own, ext=[r['ext'] for r in rs], notes=[r['notes'] for r in rs], hits=hits, alt=r0['alt'], mine_same=[h[0] for h in hits if h[0] in mine and mine[h[0]].get('work_id') == r0['work']]))
bysig = collections.defaultdict(list)
for k, rs in groups.items(): bysig[(k[0], k[1], k[2])].append(k[3])
for sig in list(bysig): bysig[sig] = list({tuple(x) for x in bysig[sig]})
amb = {sig for sig, v in bysig.items() if len(v) > 1 and any(set(a) & set(b) for i, a in enumerate(v) for b in v[i+1:])}
for o in out: o['amb'] = (o['work'], core_title(o['title']), o['y']) in amb
print(len(out), 'groups;', sum(1 for g in out if any(h[2] for h in g['hits'])), 'with same-year&shop hit;', sum(1 for g in out if g['hits'] and not any(h[2] for h in g['hits'])), 'year-only hit')
json.dump(out, open('c3_groups.json', 'w'), ensure_ascii=False, indent=0)
