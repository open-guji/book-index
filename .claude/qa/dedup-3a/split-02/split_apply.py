#!/usr/bin/env python3
"""去重方案部分3a：拆 5b-研 發現的「不同譯本／不同書掛同一 Work」7 處（2026-10-26）。方案見 plan-yi.json。
新 Work id 由 mintid.py（車道 dedup3a）預先鑄好寫死。用法：split_apply.py [--apply]"""
import glob, json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[4]
TODAY = '2026-10-26'
APPLY = '--apply' in sys.argv
QX, SZ, WX, AF, QY = 'd59g2foxbpj4', 'd59g2foxbpj5', 'd59g2foxbpj6', 'd59g2foxbpj7', 'd59g2foxbpj8'
cache, created = {}, {}
TAG = '%s 去重方案部分3a 拆混記錄（5b-研 轉來）' % TODAY


def path(i, fam):
    p = glob.glob(str(ROOT / fam / i[-3] / i[-2] / i[-1] / (i + '-*.json')))
    assert len(p) == 1, (i, p)
    return p[0]


def rec(i, fam='Work'):
    if i not in cache:
        cache[i] = [path(i, fam), json.load(open(path(i, fam), encoding='utf-8'))]
    return cache[i][1]


def bump(d):
    a, b, c = (d.get('revision') or '1.0.0').split('.')
    d['revision'] = '%s.%d.0' % (a, int(b) + 1)
    d['revised_at'] = TODAY


def note(d, s):
    d['ai_note'] = ((d['ai_note'] + '\n\n') if d.get('ai_note') else '') + '%s：%s' % (TAG, s)


def move_books(bids, frm, to, why):
    for bid in bids:
        b = rec(bid, 'Book')
        assert b['work_id'] == frm, (bid, b['work_id'], frm)
        b['work_id'] = to
        note(b, '%s；work_id 由 %s 改指 %s。' % (why, frm, to)); bump(b)


def new_work(i, title, authors, dyn, period, juan, minfo, desc, cls, why, ib=None, extra=None):
    d = {'schema_version': 1, 'id': i, 'type': 'work', 'title': title, 'authors': authors,
         'dynasty': dyn, 'dynasty_basis': 'author_propagation', 'period': period,
         'period_basis': '據 authors[0].dynasty「%s」' % dyn}
    if juan:
        d['juan_count'] = {'number': juan}; d['measures'] = [{'number': juan, 'unit': '卷'}]
    d['measure_info'] = minfo
    d['description'] = {'text': desc, 'sources': sorted({e['source'] for e in ib}) if ib else ['中國古籍總目']}
    if ib:
        d['indexed_by'] = ib
    d.update(extra or {})
    d['ai_note'] = '%s新建：%s' % (TAG, why)
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    created[i] = (d, cls)


def fmt_members(c):
    rows = ',\n    '.join(json.dumps(m, ensure_ascii=False) for m in c['members'])
    return '{\n  "node": %s,\n  "members": [\n    %s\n  ]\n}\n' % (json.dumps(c['node'], ensure_ascii=False), rows)


ZHENDI = {'name': '釋真諦', 'role': '譯', 'dynasty': '陳', 'entity_id': 'hixi5eks7m6p'}

# ── 大乘起信論：真諦一卷譯本與實叉難陀二卷本分立；蕭士瑋解本歸《起信論解》 ──
A = 'd59fyh384um8'
QXB = ['99400fzv9d', '99400fomps', '99400h8tfl', '99400fzv9c', '99400gmccg', '99400fompt', '99400gxkw0', '99400hk1z5']
new_work(QX, '大乘起信論', [dict(ZHENDI), {'name': '馬鳴', 'role': '撰', 'dynasty': '天竺', 'entity_id': 'hixhd2h9bokr'}],
         '陳', 'nanbeichao', 1, '一卷',
         '馬鳴菩薩造，陳真諦譯《大乘起信論》一卷（大正藏 T1666），與唐實叉難陀二卷本為同本異譯。', 'zm0525',
         '自 %s 拆出真諦一卷譯本 8 個 Book（總目各本皆作「大乘起信論一卷｜…陳釋真諦譯」；普寧、磧砂、東禪、萬曆諸藏兩譯各有記錄）。' % A)
move_books(QXB, A, QX, '真諦一卷譯本，與實叉難陀二卷本為同本異譯')
move_books(['99400f25mp'], A, 'd59f2ngp4gsh', '總目作「梁釋真諦譯;明蕭士瑋解」崇禎十年刻，為蕭士瑋《起信論解》')
d = rec(A)
note(d, '真諦一卷譯本 8 個 Book 移至新建 %s；蕭士瑋解本 99400f25mp 移至 d59f2ngp4gsh《起信論解》。indexed_by 的總目聚合 summary 混有真諦本版本，保留原文；國圖資源 nlc-ZHCH0464（金藏）譯本不明，不動。' % QX)
bump(d)

# ── 攝大乘論釋：世親釋玄奘本留；真諦十五卷本、無性釋各立；笈多本歸《攝大乘論釋論》 ──
S = 'd59fyew93f29'
new_work(SZ, '攝大乘論釋', [dict(ZHENDI), {'name': '世親', 'role': '釋', 'dynasty': '天竺', 'note': '總目或作天親'}],
         '陳', 'nanbeichao', 15, '十五卷',
         '世親（天親）菩薩釋無著《攝大乘論》，陳真諦譯，十五卷（大正藏 T1595），與隋笈多譯十卷本（《攝大乘論釋論》）、唐玄奘譯十卷本為同本異譯。', 'zm0525',
         '自 %s 拆出真諦譯十五卷本 4 個 Book（總目皆作「攝大乘論釋十五卷｜天親菩薩釋;陳釋真諦譯」）。' % S)
move_books(['993xth9o8x', '993xtg0q2o', '993xthkwsg', '993xthkwsh'], S, SZ, '真諦譯十五卷本，譯者、卷數皆異於玄奘十卷本')
new_work(WX, '攝大乘論釋', [{'name': '釋玄奘', 'role': '譯', 'dynasty': '唐', 'entity_id': 'hixhd2h9bntz'}, {'name': '無性', 'role': '釋', 'dynasty': '天竺', 'note': '總目作「外國無性菩薩造」'}],
         '唐', 'sui-tang', 10, '十卷',
         '無性菩薩釋無著《攝大乘論》，唐玄奘譯，十卷（大正藏 T1598），與同名之世親釋（玄奘譯）為兩部不同的書。', 'zm0525',
         '自 %s 拆出無性釋 5 個 Book（造釋者無性，非世親；普寧、東禪、磧砂諸藏兩釋各有記錄）。' % S)
move_books(['993xtgyfpc', '993xtgyfpd', '993xtfphj5', '993xtgn75t', '993xtfphj4'], S, WX, '無性釋，與世親釋為兩部不同論釋')
move_books(['993xtg0q2p'], S, 'd59fyew8s6io', '普寧藏此條總目記錄笈多、玄奘兩譯合錄，笈多本居首，歸 d59fyew8s6io《攝大乘論釋論》（世親造、隋笈多譯）')
d = rec(S)
note(d, '真諦十五卷本 4 個 Book 移至新建 %s，無性釋 5 個 Book 移至新建 %s，普寧藏笈多玄奘合錄本 993xtg0q2p 移至 d59fyew8s6io。Book 993xtgn75s 曾於 2026-10-19 Book 層查重並入笈多本與無性本記錄（merged_from 11so52epypekj、11so52epypeki），應另於 Book 層拆回，本次未動。' % (SZ, WX))
bump(d)

# ── 菩薩修行四法經：普寧、永樂北藏兩本歸 d59fy8mow001 ──
F = 'd59fy74cz08x'
move_books(['99585cpibk', '99585ce9s0'], F, 'd59fy8mow001', '地婆訶羅譯《菩薩修行四法經》，與《大乘四法經》為大正藏分收之兩經')
d = rec(F)
note(d, '題《菩薩修行四法經》之普寧、永樂北藏兩 Book 移至 d59fy8mow001；本條專指地婆訶羅譯《大乘四法經》（T772）。')
bump(d)

# ── 大般涅槃經：南本歸 d59f7z49cf7s；三國藝文志安法賢二卷本另立 ──
N = 'd59f27x5axhf'
move_books(['99585315hc', '99585315hd', '995852pwxs', '9957g269s0', '9957g2hibk', '995853ce0w'], N, 'd59f7z49cf7s', '三十六卷，慧嚴等再治之南本')
d = rec(N)
e = d['indexed_by'].pop(0)
assert e['source'] == '三國藝文志' and '安法賢' in e['summary']
new_work(AF, '大般涅槃經', [{'name': '安法賢', 'role': '譯', 'dynasty': '三國魏'}],
         '三國魏', 'three-kingdoms', 2, '二卷',
         '魏沙門安法賢譯《大般涅槃經》二卷，《開元錄》謂「略大本前數品」，見竺道祖《魏錄》，已佚；與北涼曇無讖四十卷本非一書。', 'zm0321',
         '自 %s 移出《三國藝文志》魏代譯經「大般涅槃經二卷」一條（按語引《開元錄》屬沙門安法賢；曇無讖北涼人，時代、卷數皆不合）。' % N,
         ib=[e], extra={'loss_status': 'lost', 'loss_status_basis': '《三國藝文志》按語引《開元錄》：右二部五卷，其本並闕'})
d['description'] = {'text': '曇無讖（北涼）譯。四十卷（北本）。見著錄於《國史經籍志》及《中國古籍總目》。',
                    'sources': sorted({x['source'] for x in d['indexed_by']})}
note(d, '慧嚴等再治南本三十六卷 6 個 Book 移至 d59f7z49cf7s；《三國藝文志》安法賢譯二卷一條移出，新建 %s。description 原「別作二卷」「列於集部·佛道·魏」「佚文見引於《法苑珠林》」皆由該條帶入，改寫。' % AF)
bump(d)

# ── 佛說須賴經：支施崘譯本歸 d59f2q3jpp1c；白延譯本 sources 去串入之源記錄 ──
X = 'd59fybkjl3i8'
move_books(['993uhs2l8g', '993uhrrcox', '993uhrrcow'], X, 'd59f2q3jpp1c', '總目作「佛說須賴經一卷｜晉支施崘譯」，與白延譯本為同本異譯')
for bid, drop in (('993uhr4vls', 'eycldrjc34syi3bk'), ('993uhqtn28', '5kh35mqmggdi6tbr'), ('993uhqieip', 'y4gxehzpyqgv6dim')):
    b = rec(bid, 'Book')
    n0 = len(b['sources']); b['sources'] = [s for s in b['sources'] if s.get('id') != drop]; assert len(b['sources']) == n0 - 1
    note(b, 'sources 刪去串入之源記錄 %s（屬支施崘譯本，已隨該本改掛 d59f2q3jpp1c）。' % drop); bump(b)
d = rec(X)
note(d, '支施崘譯本 3 個 Book（993uhs2l8g、993uhrrcox、993uhrrcow）移至 d59f2q3jpp1c；本條專指白延譯本。')
bump(d)

# ── 大乘百福莊嚴相經：6 個 Book 歸 d59fy741qgox ──
H = 'd59fy741f85c'
move_books(['9957g6jlds', '9957g762gw', '9957g762gx', '9957g68cu9', '9957g6utxc', '9957g7hb0g'], H, 'd59fy741qgox', '題《大乘百福莊嚴相經》，與《大乘百福相經》為地婆訶羅所譯兩經（大正藏分收）')
d = rec(H)
note(d, '題《大乘百福莊嚴相經》之 6 個 Book 移至 d59fy741qgox；本條專指《大乘百福相經》。')
bump(d)

# ── 黔陽縣志：康熙本另立 ──
Q = 'd59f2n2bw4cg'
d = rec(Q)
e = d['indexed_by'].pop(0)
assert e['title_info'].startswith('[康熙]黔陽縣志')
new_work(QY, '[康熙]黔陽縣志', [{'name': '張扶翼', 'role': '纂修', 'dynasty': '清', 'entity_id': 'hixhd2h9bqea'}],
         '清', 'qing', 10, '十卷',
         '清張扶翼纂修，康熙五年（1666）刻，十卷；二十六年有于棟如增刻本。雍正十一年王光電據此增輯為[雍正]黔陽縣志。', 'zm0285',
         '自 %s 拆出 [康熙] 本（總目分立兩條著錄，與乾隆、同治志分立同例）。' % Q, ib=[e], extra={'additional_titles': ['黔陽縣志']})
move_books(['9951d6bl6p', '9951d6mtq8', '9951d6mtq9'], Q, QY, '[康熙]黔陽縣志（張扶翼纂修，康熙五年刻）')
note(d, '[康熙]本著錄與 3 個 Book 移至新建 %s；本條今指王光電據張扶翼原本增輯之 [雍正] 本（題名暫未改，待定）。' % QY)
bump(d)

if not APPLY:
    print('dry run:', len(cache), 'records', sorted(created)); sys.exit()
for i, (p, d) in cache.items():
    open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
for i, (d, cls) in created.items():
    p = ROOT / 'Work' / i[-3] / i[-2] / i[-1] / ('%s-%s.json' % (i, d['title']))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    cp = ROOT / 'classification/zongmu/members' / (cls + '.json')
    c = json.loads(cp.read_text(encoding='utf-8'))
    c['members'].append([i, '中國古籍總目']); c['members'].sort()
    cp.write_text(fmt_members(c), encoding='utf-8')
print('written', len(cache), 'records,', len(created), 'new works')
