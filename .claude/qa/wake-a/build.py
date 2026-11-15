#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-a：和刻本日本馆藏专项 shard0。用法：build.py [--apply]。补挂 PATCH、新建 NEW。"""
import json, os, re, sys, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); import mintid
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'
NDLU = 'https://ndlsearch.ndl.go.jp/books/'
NDL, KYU, MYG, ISH = '國立國會圖書館', '九州大學附屬圖書館', '宮城縣圖書館', '石川縣立圖書館'
# (book_id, [(機構, 索書號|None, 記錄id, 備註)], 依據)
PATCH = [
 ('988g8t6io5', [(NDL, 'W488-N49', 'R100000002-I031181012', '10冊，木活字版；學訓堂，嘉永5（1852）跋')], '題名、責任者（喜多村直寬）、學訓堂、嘉永五年（1852）一致'),
 ('988fz12txe', [(NDL, '詩文-2225；YD-古-5081～5082', 'R100000002-I023758031', '8冊；奧付「旭松舘藏板」，天保10（1839）')], '題名、責任者（谷斗南）、旭松館、天保十年（1839）一致'),
 ('988g0kn2mj', [(NDL, 'W731-14', 'R100000002-I000007555663', '5册；醫官千賀芳久活字印，寛政10（1798）')], '題名、寬政十年（1798）、活字本一致；千賀芳久即精思堂主人，書肆名異寫'),
 ('988g3op9mz', [(NDL, '121-28', 'R100000002-I000007613449', '5册（合2册）；延享3刊，高野山北室院藏版')], '題名、延享三年（1746）、高野山北室院藏版一致'),
 ('988g4s162z', [(NDL, '848-170', 'R100000002-I000007620131', '2册；須原屋茂兵衞・須原屋平助刊，明和7（1770）'),
                 (KYU, None, 'R100000092-I2324_418561', '須原屋茂兵衛，明和7年；另有須原屋平助本 I2324_419722'),
                 (ISH, None, 'R100000133-IorgnB111617437', '須原屋平助，1770（明和7）')], '題名、明和七年（1770）、江戶須原屋刊一致'),
 ('988g74mhaa', [(NDL, 'W996-N2055', 'R100000002-I032836430', '15册；官板，出雲寺萬次郎，文化2-3（1805-1806）；題簽「唐律疏議」，序題「唐律疏義」')], '題名（義／議異寫）、文化二年（1805）、昌平黌官版（出雲寺發售）一致'),
 ('99513cchdt', [(NDL, '240-16', 'R100000002-I000007510329', '20册；熊本藩時習館據足利學校藏宋刊本影鈔刊，弘化4（1847）')], '題名、弘化四年（1847）、熊本藩時習館影刻足利學校藏宋本一致'),
 ('988g2qd5vm', [(NDL, '240-16', 'R100000002-I000007510329', '20册；熊本藩時習館據足利學校藏宋刊本影鈔刊，弘化4（1847）')], '題名、弘化四年（1847）、熊本藩時習館影刻宋單疏本一致（與 99513cchdt 為同一刊本的不同總目著錄）'),
 ('988g36li4g', [(KYU, None, 'R100000092-I2324_1517613', '狩谷氏求古樓，文政9年；館內注記27/8/043')], '題名、文政九年（1826）、狩谷氏求古樓一致'),
 ('994ynwc740', [(KYU, None, 'R100000092-I2324_1517613', '狩谷氏求古樓，文政9年；館內注記27/8/043')], '題名、文政九年（1826）、狩谷氏求古樓一致（與 988g36li4g 為同一刊本的不同總目著錄）'),
 ('988fz8kiyr', [(MYG, None, 'R000000054-I040_53909', '3卷；淺田氏勿誤藥室，1852；飯川氏藏書印記')], '題名、淺田氏勿誤藥室、嘉永五年（1852）一致'),
 ('993hdnbpc1', [(KYU, None, 'R100000092-I2324_419266', '勝村治右衛門，寛延2年；另有前川六左衛門本 I2324_419678、勝村治右衛門等本 I2324_430777；表紙「明倫堂叢書」')], '題名、寛延二年（1749）、京都書肆刊一致'),
 ('988fz70c92', [(KYU, None, 'R100000092-I2324_419731', '植村藤三郎，元文元年；黃之寀校本 I2324_428044 同刊'),
                 (ISH, None, 'R100000133-IorgnB001503354', '植村藤右衛門，1736（元文1）')], '題名、元文元年（1736）、京都植村氏翻刊黃之寀本一致'),
 ('993ejygiki', [(KYU, None, 'R100000092-I2324_7167633', '前川六左衛門等，延享3年；與《春秋姓名弁異》合記，井上蘭台跋')], '題名、延享三年（1746）、江戶前川六左衛門（崇文堂）一致'),
 ('995137z5s0', [(NDL, '117-10', 'R100000002-I000007509078', '10册（合5册）；上村次郎右衞門刊，寛文5（1665）')], '題名、寛文五年（1665）上村次郎右衛門印本一致'),
 ('99ifez2z9g', [(NDL, 'WA7-76；YD1-80', 'R100000002-I000007680634', '15册；那波道圓校刊，元和4（1618）；貴重書')], '題名、那波道圓、元和四年（1618）一致'),
]
D = lambda **k: k
NEW = [
 D(work='d59f2pw12xhc', title='論語徵集覽', edition='日本寶曆十年江戶前川六左衞門等刊本', et='刻本', era='日本', reign='寶曆', year=1760, meas=[(20, '卷'), (1, '附錄')],
   prov=[(NDL, '136-138', 'R100000002-I000007328024', '20冊（合8冊）；前川六左衛門[ほか]，宝暦10（1760）'), (KYU, None, 'R100000092-I2324_430224', '（江戸）前川六左衛門、ほか2肆，宝暦10年')],
   basis='NDL與九大兩館獨立著錄：寶曆十年（1760）江戶前川六左衛門等刊', rel='本庫另有文化九年（1812）崇文堂校刊本 988g41t8g0（崇文堂為前川六左衛門堂號，疑為同版後印，未硬並）。', desc='松平賴寬輯《論語徵集覽》二十卷附錄一卷，寶曆十年江戶書肆前川六左衛門等刊。'),
 D(work='d59f2q3fnlkx', title='新撰字鏡', edition='日本享和三年大阪葛城長兵衞等刊本', et='刻本', era='日本', reign='享和', year=1803, meas=[(2, '冊')],
   prov=[(NDL, '813.2-Sy968s-k', 'R100000002-I000003284169', '2冊；葛城長兵衛[ほか]，享和3（1803）'), (KYU, None, 'R100000092-I2324_419383', '葛城長兵衛，1803')],
   basis='NDL與九大兩館獨立著錄：享和三年（1803）葛城長兵衛等刊', rel='嘉永四年（1851）河內屋德兵衛本（NDL R100000002-I031828795）疑為此版後印，未另立。本庫另有安政二年傳錄天治本鈔本 988g27y5ty、明治初影寫本 988g928efc，均為鈔本。', desc='釋昌住《新撰字鏡》，享和三年葛城長兵衛等據天治本刊行的刻本。'),
 D(work='d59f2nlcqwaq', title='金鏡內臺方議', edition='日本文政四年敬業樂群樓藏板', et='刻本', era='日本', reign='文政', year=1821, meas=[(12, '卷')],
   prov=[(KYU, None, 'R100000092-I2324_4492040', '敬業楽群樓蔵板，文政4年；巻之1-2「敬業楽群樓蔵板」；另有巻之3-6 I2324_4492339、巻之7-12 I2324_4491953')],
   basis='九大著錄：文政四年（1821）敬業樂群樓藏板，卷首署「敬業樂群樓藏板」', rel='本庫另有文政六年衛生彙編本 988g71i3v0（叢書本，非同版）。', desc='許宏《金鏡內臺方議》十二卷，日本文政四年敬業樂群樓藏板。'),
 D(work='d59fyu8mrf28', title='日本國見在書目錄', edition='日本天保六年鈔本', et='抄本', era='日本', reign='天保', year=1835, meas=[(1, '冊')],
   prov=[(NDL, '025.22-N685-H', 'R100000002-I000003283504', '1冊；天保6（1835）寫；書題簽「現在書目録」')],
   basis='NDL著錄：天保六年（1835）寫本', rel='底本與庫中影刻舊抄卷子本 994d86widc 的關係未核。', desc='藤原佐世《日本國見在書目錄》，天保六年（1835）日本鈔本。'),
 D(work='d59f28mutk3l', title='御註孝經', edition='日本文化五年京都堺屋伊兵衞刊本', et='刻本', era='日本', reign='文化', year=1808, meas=[],
   prov=[(KYU, None, 'R100000092-I2324_1517603', '（京都）堺屋伊兵衛信成，文化5年；責任者著錄菅原朝臣為徳；館內注記27/8/033')],
   basis='九大著錄：文化五年（1808）京都堺屋伊兵衞信成刊', rel='與文政九年求古樓覆宋本（988g36li4g）、寛政十二年刻本（994ynvehhc／d）均非同版。', desc='唐玄宗《御註孝經》，文化五年京都堺屋伊兵衞信成刊，菅原為徳訓點。'),
]
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def leaf(i): return 'Book/%s/%s/%s' % (i[-3], i[-2], i[-1])
def bump(r):
    a = r.split('.'); a[2] = str(int(a[2]) + 1); return '.'.join(a)
nid = mintid.mint('Book', 'wake-a', len(NEW)) if APPLY else ['dryb%06d' % i for i in range(len(NEW))]
if APPLY:
    dirs = sorted({leaf(b) for b, _, _ in PATCH} | {leaf(i) for i in nid})
    subprocess.check_call(['git', 'sparse-checkout', 'add'] + dirs, cwd=BI)
ledger = []; files = {}
for bid, adds, why in PATCH:
    fs = glob.glob(os.path.join(BI, leaf(bid), bid + '-*.json'))
    if len(fs) != 1:
        print('找不到', bid, fs); continue
    d = json.load(open(fs[0], encoding='utf-8'))
    have = {(p.get('institution'), p.get('source')) for p in d.get('provenance', [])}
    srcs = []
    for inst, call, rid, note in adds:
        p = {'institution': inst}
        if call: p['call_number'] = call
        p['notes'] = note; p['source'] = 'NDL Search ' + NDLU + rid
        d.setdefault('provenance', []).append(p); srcs.append(NDLU + rid)
        ledger.append((bid, d['title'], '補掛', inst, NDLU + rid))
        sid = 'ndl-' + rid
        d.setdefault('sources', []).append({'id': sid, 'name': 'NDL Search', 'type': 'url', 'details': NDLU + rid})
    line = '日本館藏補掛（wake-a，2026-11-15）：據NDL Search核對 %s。%s' % ('；'.join(srcs), why)
    d['ai_note'] = (d['ai_note'] + '\n' if d.get('ai_note') else '') + line
    d['revision'] = bump(d.get('revision', '1.0.0')); d['revised_at'] = TODAY
    files[os.path.relpath(fs[0], BI)] = d
for it, bid in zip(NEW, nid):
    dating = {'era': it['era'], 'reign': it['reign'], 'year': it['year'], 'certainty': 'attested', 'source': 'catalog', 'basis': it['basis']}
    d = {'schema_version': 1, 'id': bid, 'type': 'book', 'title': it['title'], 'work_id': it['work'], 'edition': it['edition'], 'edition_type': it['et'], 'dating': dating}
    if it['meas']: d['measures'] = [{'number': n, 'unit': u} for n, u in it['meas']]
    d['provenance'] = [dict([('institution', i)] + ([('call_number', c)] if c else []) + [('notes', n), ('source', 'NDL Search ' + NDLU + r)]) for i, c, r, n in it['prov']]
    d['description'] = {'text': it['desc'], 'sources': ['NDL Search ' + NDLU + r for _, _, r, _ in it['prov']]}
    d['sources'] = [{'id': 'ndl-' + r, 'name': 'NDL Search', 'type': 'url', 'details': NDLU + r} for _, _, r, _ in it['prov']]
    d['ai_note'] = '和刻本日本館藏專項（wake-a，2026-11-15）：據NDL Search記錄新建，刊年／書肆／冊數錄自該記錄，未核原書。' + it['rel']
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', it['edition'])[:24]
    files['%s/%s-%s%s.json' % (leaf(bid), bid, it['title'], safe)] = d
    for i, c, r, n in it['prov']: ledger.append((bid, it['title'], '新建', i, NDLU + r))
print('改動', len(files), '補掛', len(PATCH), '新建', len(NEW))
if not APPLY: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
open(os.path.join(HERE, 'applied_paths.txt'), 'w').write('\n'.join(files) + '\n')
with open(os.path.join(HERE, 'ledger.tsv'), 'w', encoding='utf-8') as f:
    f.write('Book id\t題名\t判定\t日本館藏\t依據URL\n')
    for r in ledger: f.write('\t'.join(r) + '\n')
print('已寫')
