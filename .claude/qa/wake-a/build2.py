#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-a 第二輪：新建日本版本 Book（來源 CiNii Books）。用法：build2.py [--apply]"""
import json, os, re, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import mintid, spec2, fetch3, fetch4
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'
S = fetch3.S
works = json.load(open(S + '/a_works.json'))
SHIN = str.maketrans({'学':'學','図':'圖','総':'總','属':'屬','医':'醫','経':'經','国':'國','県':'縣','関':'關','歯':'齒','薬':'藥','広':'廣','児':'兒','辺':'邊','区':'區','浜':'濱','沢':'澤','済':'濟','営':'營','験':'驗','検':'檢','渋':'澁','斎':'齋','竜':'龍','会':'會','蔵':'藏','芸':'藝','栄':'榮','応':'應','体':'體','実':'實','気':'氣','号':'號','処':'處','当':'當','満':'滿','条':'條','与':'與','豊':'豐','戸':'戶','台':'臺','画':'畫','労':'勞','歴':'歷','暦':'曆','続':'續','緑':'綠','数':'數','観':'觀','働':'働','・':'·','経':'經','文':'文','禅':'禪','仏':'佛','覚':'覺','縁':'緣','寿':'壽','両':'兩','教':'教'})
def inst(name):
    n = name.replace('大学共同利用機関法人 人間文化研究機構 ', '').replace('大学共同利用機関法人 ', '')
    return re.sub(r'\s+', '', n).translate(SHIN)
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def leaf(i): return 'Book/%s/%s/%s' % (i[-3], i[-2], i[-1])
CI = 'https://ci.nii.ac.jp/ncid/'
wk = {w['i']: w for w in works}
nid = mintid.mint('Book', 'wake-a', len(spec2.SPEC)) if APPLY else ['dryb%06d' % i for i in range(len(spec2.SPEC))]
if APPLY:
    subprocess.check_call(['git', 'sparse-checkout', 'add'] + sorted({leaf(i) for i in nid}), cwd=BI)
files = {}; ledger = []
for sp, bid in zip(spec2.SPEC, nid):
    w = wk[sp['key'][0]]
    prov = []; srcs = []; seen = set()
    for nc in sp['ncids']:
        d = fetch4.detail(nc)
        assert d and d['date'] == str(sp['year']), (nc, d and d['date'])
        pub = ' : '.join(p for p in d['pub'])
        for o in d['owners']:
            p = {'institution': inst(o[0]), 'notes': 'CiNii Books所藏館「%s」；%s；%s' % (o[0], d['title'], pub + ('；' + d['ext'] if d['ext'] else '')), 'source': 'CiNii Books ' + CI + nc}
            prov.append(p); ledger.append((bid, sp['title'], '新建', inst(o[0]), CI + nc))
        srcs.append({'id': 'cinii-' + nc, 'name': 'CiNii Books', 'type': 'url', 'details': CI + nc})
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': sp['title'], 'work_id': w['wid'], 'edition': sp['edition'], 'edition_type': sp.get('et', '刻本'),
         'dating': {'era': '日本', 'reign': sp['reign'], 'year': sp['year'], 'certainty': 'attested', 'source': 'catalog', 'basis': sp['basis']}}
    if sp.get('alt'): d['additional_titles'] = sp['alt']
    if sp['meas']: d['measures'] = [{'number': n, 'unit': u} for n, u in sp['meas']]
    d['provenance'] = prov
    d['description'] = {'text': sp['desc'], 'sources': ['CiNii Books ' + CI + nc for nc in sp['ncids'][:3]]}
    d['sources'] = srcs
    d['ai_note'] = '和刻本日本館藏專項第二輪（wake-a，2026-11-15）：據CiNii Books書目新建（NCID %s）；刊年／書肆／冊數錄自該書目與所附註記，未核原書。%s' % ('、'.join(sp['ncids']), sp['rel'])
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', sp['edition'])[:24]
    files['%s/%s-%s%s.json' % (leaf(bid), bid, sp['title'], safe)] = d
print('新建', len(files), '館藏條', len(ledger))
if not APPLY: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
open(os.path.join(HERE, 'applied_paths2.txt'), 'w').write('\n'.join(files) + '\n')
with open(os.path.join(HERE, 'ledger2.tsv'), 'w', encoding='utf-8') as f:
    f.write('Book id\t題名\t判定\t日本館藏\t依據URL\n')
    for r in ledger: f.write('\t'.join(r) + '\n')
print('已寫')
