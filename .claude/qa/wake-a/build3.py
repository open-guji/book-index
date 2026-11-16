#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-a 第三輪：通名大 Work（周易／尚書／詩經）日本印本窮盡。用法：build3.py [--apply]"""
import json, os, re, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
BI = os.environ.get('BI_ROOT') or os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import mintid
from spec3_src import SPEC, EXTRA
APPLY = '--apply' in sys.argv
TODAY = '2026-11-16'
DET = json.load(open(os.path.join(HERE, 'details3.json'), encoding='utf8'))
SEL = json.load(open(os.path.join(HERE, 'groups_sel2.json'), encoding='utf8'))
SHIN = str.maketrans({'学':'學','図':'圖','総':'總','属':'屬','医':'醫','経':'經','国':'國','県':'縣','関':'關','歯':'齒','薬':'藥','広':'廣','児':'兒','辺':'邊','区':'區','浜':'濱','沢':'澤','済':'濟','営':'營','験':'驗','検':'檢','渋':'澁','斎':'齋','竜':'龍','会':'會','蔵':'藏','芸':'藝','栄':'榮','応':'應','体':'體','実':'實','気':'氣','号':'號','処':'處','当':'當','満':'滿','条':'條','与':'與','豊':'豐','戸':'戶','台':'臺','画':'畫','労':'勞','歴':'歷','暦':'曆','続':'續','緑':'綠','数':'數','観':'觀','・':'·','禅':'禪','仏':'佛','覚':'覺','縁':'緣','寿':'壽','両':'兩'})
def inst(name):
    n = name.replace('大学共同利用機関法人 人間文化研究機構 ', '').replace('大学共同利用機関法人 ', '')
    return re.sub(r'\s+', '', n).translate(SHIN)
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def leaf(i): return 'Book/%s/%s/%s' % (i[-3], i[-2], i[-1])
CI = 'https://ci.nii.ac.jp/ncid/'
def cleancre(c): return re.sub(r'\s+', '', re.sub(r'[\[\]]', '', c or ''))
def norm(s): return re.sub(r'[\s\[\]]', '', s or '')
RELS = {
 ('周易程朱傳義',1724): '同版原板之後印／再刻另立：文政六年河內屋茂兵衞求版本、文政十三年河內屋喜兵衞等本、明治九年汲書房本；庫內另有寬文四年野田庄右衞門刊本（99ju9rh0r2）、寶永六年出雲寺和泉刻本（993ejkq2o2），年份刊者不同。',
 ('周易程朱傳義',1823): '據享保九年今村八兵衞板（本輪另立）求版後印，刊記「文政六年癸未正月求版」，按有獨立刊記另立並互見。',
 ('周易程朱傳義',1830): '昌易首書本系統之後印本，與享保九年今村八兵衞本（本輪新建）、文政六年河內屋茂兵衞求版本互見。',
 ('周易程朱傳義',1876): '汲書房版權免許本，書肆多家署名；同期汲書房本另有書經集傳、詩經各一條。',
 ('周易程朱傳義',1649): '24卷8冊，題「周易傳義」，與慶安元年八尾助左衞門重刊文之點本（本輪新建）為不同版。',
 ('周易經傳',1648): '寬永四年如竹跋文之點本之慶安元年重刊；各館著錄冊數（4／6／8冊）為裝訂差異。庫內另有寬文四年野田庄右衞門刊本（99ju9rh0r2）。',
 ('易經集註',1651): '20卷10冊；與寬文三年野田庄右衞門刊易經集註（本輪新建）為不同版。',
 ('易經集註',1663): '20卷，與寬文四年野田庄右衞門刊昌易首書本（99ju9rh0r2，24卷）為不同版。',
 ('周易本義附錄纂註',1814): '昌平坂學問所官版，岡村庄助、出雲寺萬次郎發行之著錄並入。',
 ('周易禪解',1711): '庫內另有享保十三年京都梅村三郎兵衛刻本（99505zts74），年份刊者不同。',
 ('尚書',1856): '奧付「安政三丙辰年改正」；CiNii BA86631122 著錄刊年誤作1774，已按奧付改正；殘本BB15237048同刊者。',
 ('尚書',1788): '清家正本；CiNii BA85119708 著錄1787，餘作1788，奧付「天明八年戊申十二月」，按1788。庫內另有寛延四年丸屋市兵衛等刻本（993gjusav5）、享和二年同書肆刊本（本輪另立）。',
 ('尚書',1802): '清家正本之享和二年再刊，與天明八年本（本輪新建）互見。',
 ('書經集傳',1724): '昌易首書本；庫內另有享和元年今村八兵衛刻本（995123eb5s）、寬文四年刻本（9951217ncx），年份不同。',
 ('書經集傳',1830): '昌易首書本系統之後印本。',
 ('書經集傳',1876): '汲書房版權免許本。',
 ('書經集傳',1663): '10卷10冊，無首書；庫內另有寬文四年刻本（9951217ncx）不同卷數。',
 ('書集傳纂疏',1811): '後見返「學問所御蔵板」，和泉屋庄二郎等發行。',
 ('毛詩',1749): '各館另有書肆署名略異之著錄（風月莊左衞門等），按同刊年同書肆組合歸並。庫內另有天明八年刻本（993e2fao74）。',
 ('毛詩補義',1746): '岡白駒補義，刊記「延享三年丙寅之春發行 京師書坊 風月堂莊左衞門登梓」。',
 ('詩經',1664): '庫內另有寛永五年容膝亭刻本（993gk45f5u）；寬政三年今村八兵衛再刻本（本輪新建）為其再刻。',
 ('詩經',1724): '與寬文四年野田庄右衞門本（本輪新建）、寬政三年今村八兵衛再刻本互見。',
 ('詩經',1791): '刊記「寛文四甲辰歳九月吉辰 寛政三辛亥歳五月再刻 今村八兵衛藏板」。',
 ('詩經',1876): '汲書房版權免許本。',
 ('詩經繹解',1812): '皆川愿自著，文化九年刊，葛西市郎兵衞蔵版印。',
 ('詩集傳名物鈔',1813): '文化十年昌平坂學問所官版；岡村庄助、山城屋佐兵衞、岡田屋嘉七（文政六年印）等發行之著錄並入。',
 ('詩集傳通釋',1816): '昌平坂學問所刊。',
 ('周易本義',1675): '奧付「延寶三年乙卯春三月壽文堂刋行」；寬政元年再刻本（988g47qqrs）原刊記「延寳三年乙卯春三月壽文堂旧板燒亡」。',
}
specs = []
for s in SPEC:
    s = dict(s)
    if s.get('work') is None: s['work'] = SEL[s['gids'][0]]['work']
    nc = s.get('ncids')
    if not nc:
        nc = []
        for g in s['gids']: nc += SEL[g]['ncids']
        out = []
        for n in nc:
            d = DET.get(n)
            if not d or d['date'] != str(s['year']): continue
            if s.get('pubre') and not re.search(s['pubre'], ' '.join(d['pub'])): continue
            out.append(n)
        nc = out
    nc = [x for x in nc if x not in s.get('exclude', [])] + [x for x in s.get('add', []) if x not in nc]
    s['ncids'] = nc; s['rel'] = RELS.get((s['title'], s['year']), ''); specs.append(s)
for e in EXTRA:
    e = dict(e); e['rel'] = RELS.get((e['title'], e['year']), ''); specs.append(e)
nid = mintid.mint('Book', 'wake-a', len(specs)) if APPLY else ['dryb%06d' % i for i in range(len(specs))]
if APPLY: subprocess.check_call(['git', 'sparse-checkout', 'add'] + sorted({'/' + leaf(i) + '/' for i in nid}), cwd=BI)
files = {}; ledger = []
for sp, bid in zip(specs, nid):
    reps = [DET[n] for n in sp['ncids']]
    rep = max(reps, key=lambda d: int(d['own'] or 0))
    prov = []; srcs = []
    for n in sp['ncids']:
        d = DET[n]; pub = ' : '.join(d['pub'])
        for o in d['owners']:
            prov.append({'institution': inst(o[0]), 'notes': 'CiNii Books所藏館「%s」；%s；%s' % (o[0], d['title'], pub + ('；' + d['ext'] if d['ext'] else '')), 'source': 'CiNii Books ' + CI + n})
            ledger.append((bid, sp['title'], '新建', inst(o[0]), CI + n))
        srcs.append({'id': 'cinii-' + n, 'name': 'CiNii Books', 'type': 'url', 'details': CI + n})
    kj = []
    for n in sp['ncids']:
        for t in DET[n]['note'] or []:
            if re.search(r'刊記|奥付|奧付|見返', t) and t not in kj: kj.append(t)
    pubs = []; seenp = set()
    for n in sp['ncids']:
        for p in DET[n]['pub']:
            for t in re.split(r'[:/;,；、]|\[ほか\]|ほか', p):
                t = re.sub(r'[\[\]\s()（）]', '', t)
                k = t.translate(str.maketrans('衞荘庄莊', '衛莊莊莊'))
                if t and k not in seenp: seenp.add(k); pubs.append(t)
    pubs = pubs[:6]
    basis = 'CiNii Books%s著錄：刊年%d（%s）；出版者%s' % ('多館獨立' if len(sp['ncids']) > 1 else '', sp['year'], '／'.join(x for x in (rep['pd'] or []) if x)[:40] or str(sp['year']), '・'.join(pubs)[:80])
    if kj: basis += '；註記：' + kj[0][:110]
    cre = cleancre(rep['cre'])
    meas = sp['meas']
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': sp['title'], 'work_id': sp['work'], 'edition': sp['edition'], 'edition_type': '刻本',
         'dating': {'era': '日本', 'reign': sp['reign'], 'year': sp['year'], 'certainty': 'attested', 'source': 'catalog', 'basis': basis}}
    if sp['alt']: d['additional_titles'] = sp['alt']
    if meas: d['measures'] = [{'number': n, 'unit': u} for n, u in meas]
    d['provenance'] = prov
    d['description'] = {'text': '%s《%s》，%s。' % (cre, sp['title'], sp['edition'][2:] if sp['edition'].startswith('日本') else sp['edition']), 'sources': ['CiNii Books ' + CI + n for n in sp['ncids'][:3]]}
    d['sources'] = srcs
    d['ai_note'] = '和刻本日本館藏專項第三輪（wake-a，2026-11-16）：據CiNii Books書目新建（NCID %s）；刊年／書肆／冊數錄自該書目與所附註記，未核原書。%s' % ('、'.join(sp['ncids']), sp.get('rel', ''))
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', sp['edition'])[:24]
    files['%s/%s-%s%s.json' % (leaf(bid), bid, sp['title'], safe)] = d
print('新建', len(files), '館藏條', len(ledger))
for sp, bid in zip(specs, nid): print(bid, sp['title'], sp['year'], len(sp['ncids']), sp['ncids'][:3])
if not APPLY: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
open(os.path.join(HERE, 'applied_paths3.txt'), 'w').write('\n'.join(files) + '\n')
with open(os.path.join(HERE, 'ledger3.tsv'), 'w', encoding='utf-8') as f:
    f.write('Book id\t題名\t判定\t日本館藏\t依據URL\n')
    for r in ledger: f.write('\t'.join(r) + '\n')
print('已寫')
