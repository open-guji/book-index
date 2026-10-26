#!/usr/bin/env python3
"""去重方案部分3a：拆 3a 并条时发现的混记录（2026-10-25）。逐处方案见同目录 README.md 与 plan-*.json。
只改本处列出的记录；新 Work 的 id 由 mintid.py（车道 dedup3a）预先铸好写死。用法：split_apply.py [--apply]"""
import copy, glob, json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[4]
TODAY = '2026-10-25'
APPLY = '--apply' in sys.argv
W1, W2, W3, W4 = 'd59g24d8rsw0', 'd59g24d8rsw1', 'd59g24d8rsw2', 'd59g24d8rsw3'
cache, created = {}, {}


def path(i, fam):
    p = glob.glob(str(ROOT / fam / i[-3] / i[-2] / i[-1] / (i + '-*.json')))
    assert len(p) == 1, (i, p)
    return p[0]


def rec(i, fam='Work'):
    if i not in cache:
        cache[i] = [path(i, fam), json.load(open(path(i, fam), encoding='utf-8')), False]
    return cache[i][1]


def touch(i):
    cache[i][2] = True


def bump(d):
    a, b, c = (d.get('revision') or '1.0.0').split('.')
    d['revision'] = '%s.%d.0' % (a, int(b) + 1)
    d['revised_at'] = TODAY


def note(d, s):
    d['ai_note'] = ((d.get('ai_note') or '') + '\n\n' if d.get('ai_note') else '') + '%s 去重方案部分3a 拆混記錄：%s' % (TODAY, s)


def pop_ib(wid, k, expect):
    d = rec(wid); e = d['indexed_by'][k]
    assert expect in e['title_info'] + e.get('author_info', '') + e.get('summary', ''), (wid, k, e['title_info'])
    del d['indexed_by'][k]; touch(wid)
    return e


def move_book(bid, frm, to, why):
    b = rec(bid, 'Book')
    assert b['work_id'] == frm, (bid, b['work_id'], frm)
    b['work_id'] = to
    note(b, '%s；work_id 由 %s 改指 %s。' % (why, frm, to)); bump(b); touch(bid)


def fmt_members(c):
    """classification/zongmu/members/*.json 的原排版：每個成員一行。"""
    rows = ',\n    '.join(json.dumps(m, ensure_ascii=False) for m in c['members'])
    return '{\n  "node": %s,\n  "members": [\n    %s\n  ]\n}\n' % (json.dumps(c['node'], ensure_ascii=False), rows)


def new_work(i, title, authors, juan, minfo, ib, desc, cls, extra=None):
    a0 = authors[0]
    from_dyn = {'明': 'ming', '清': 'qing', '宋': 'song', '北宋': 'song'}[a0['dynasty']]
    d = {'schema_version': 1, 'id': i, 'type': 'work', 'title': title, 'authors': authors,
         'dynasty': a0['dynasty'], 'dynasty_basis': 'author_propagation', 'period': from_dyn,
         'period_basis': '據 authors[0].dynasty「%s」' % a0['dynasty']}
    if juan:
        d['juan_count'] = {'number': juan}; d['measures'] = [{'number': juan, 'unit': '卷'}]
    d['measure_info'] = minfo
    d['description'] = {'text': desc, 'sources': ['中國古籍總目']}
    d['indexed_by'] = ib
    d.update(extra or {})
    d['ai_note'] = '%s 去重方案部分3a 拆混記錄新建：%s' % (TODAY, extra.pop('_why') if extra and '_why' in extra else '')
    d.pop('_why', None)
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    created[i] = (d, cls)


# ── G0806 唐荆川先生文集：石韞玉選一卷本（明八家文選子目）拆出 ──
A = 'd59fyuadth4w'
e = pop_ib(A, 1, '石韞玉')
d = rec(A); d['authors'][0]['dynasty'] = '明'
note(d, 'indexed_by「唐荆川先生文集一卷 明唐順之撰;清石韞玉選（明八大家文選本）」與 Book 994y4r47wg 是石韞玉《明八家文選》所收一卷選本，移出至新建 Work %s；authors[0].dynasty 補「明」。' % W1)
bump(d)
new_work(W1, '唐荆川先生文集',
         [{'name': '唐順之', 'role': '撰', 'dynasty': '明', 'entity_id': 'hixhd2h9beaa'},
          {'name': '石韞玉', 'role': '選', 'dynasty': '清', 'entity_id': 'hixhd2f8wakk'}],
         1, '一卷', [e],
         '明唐順之撰、清石韞玉選，一卷，收入石韞玉所編《明八家文選》（總目作「明八大家文選本」），國家圖書館藏。',
         'zm0671', {'_why': '自 %s 拆出（石韞玉選一卷本，與唐氏文集十二／十七／十八卷全本非一書；同叢子目如王守溪文集 d59fsek9x88z 皆單立）。' % A})
move_book('994y4r47wg', A, W1, '石韞玉選一卷本，隨著錄移至新建 Work')

# ── G0313 東坡詩選：d59fxwsx6ww0 混入譚選十二卷本、陳訏選一卷本、沈德潛選二卷本與鄭德徵輯本著錄 ──
D1, D2, T = 'd59fxwsx6ww0', 'd59fyicx5c01', 'd59f2nj97h1c'
pop_ib(D1, 1, '鄭德徵')       # 同源記錄已在 d59fyicx5c01，刪去不移
d = rec(D1)
d['indexed_by'][0]['summary'] = '共 2 個版本：清抄本（北京大學圖書館）；明刻本（浙江圖書館）'
note(d, '本條原彙 7 條源記錄，混入他人選本：譚元春選十二卷附年譜本（Book 993fq3szcw、993fq447wg、993fq4fgg0）改掛 %s；陳訏選宋十五家詩選本一卷（993fq447wh）移至新建 %s；沈德潛選亦園刻本二卷（993fq3hqtd）移至新建 %s；鄭德徵輯本之版本待定著錄刪去（%s 已收同批源記錄）。今專指清孟濤輯二卷本；明刻本（993fq3szcy，選者未著，明刻不得為清人孟濤輯）與國圖無版本一部（993fq4fgg1）暫留待查。indexed_by[0].summary 隨之刪去移出之版本。' % (T, W2, W3, D2))
bump(d)
for b in ('993fq3szcw', '993fq447wg', '993fq4fgg0'):
    move_book(b, D1, T, '譚元春選、袁宏道評《東坡詩選》十二卷附年譜本，與孟濤輯二卷本非一書；%s 即同一文盛堂刻本' % T)
d = rec(T)
d['indexed_by'] = d.get('indexed_by', []) + [{
    'source': '中國古籍總目', 'source_bid': 'd59frnrt4lxc', 'title_info': '東坡詩選十二卷附東坡先生年譜一卷',
    'author_info': '宋蘇軾撰;明譚元春選;明袁宏道評;（東坡先生年譜）宋王宗稷編', 'section': '集部/別集類/宋代之屬',
    'summary': '共 3 個版本：明天啓間文盛堂刻本（南京圖書館、國家圖書館、天津圖書館、北京大學圖書館、上海圖書館、湖北省圖書館、山東省圖書館）；清刻本（天津圖書館）；清抄本（國家圖書館）',
    'note': '%s 自 %s 移來（總目源記錄 mfc4ql2x1zuthvg1 等）。' % (TODAY, D1)}]
note(d, '自 %s 移入譚元春選十二卷附年譜本之總目著錄與 Book 993fq3szcw、993fq447wg、993fq4fgg0（明天啓間文盛堂刻本即本條故宮所藏天啟元年譚氏文盛堂刊本）。authors 仍以袁宏道居首未動（總目作宋蘇軾撰、明譚元春選、明袁宏道評），待作者治理串定。' % D1)
bump(d); touch(T)
SONG_SU = {'name': '蘇軾', 'role': '撰', 'dynasty': '宋', 'entity_id': 'hixhd2h9bdqq'}
new_work(W2, '東坡詩選', [dict(SONG_SU), {'name': '陳訏', 'role': '選', 'dynasty': '清', 'entity_id': 'hixhd2h9bd4k'}],
         1, '一卷',
         [{'source': '中國古籍總目', 'source_bid': 'd59frnrt4lxc', 'title_info': '東坡詩選一卷', 'author_info': '宋蘇軾撰;清陳訏選',
           'section': '集部/別集類/宋代之屬', 'summary': '共 2 個版本：宋十五家詩選本（馆藏未载）；（國家圖書館、湖北省圖書館、上海圖書館）'}],
         '宋蘇軾撰、清陳訏選，一卷，為陳訏《宋十五家詩選》子目之一，有清康熙三十二年刻宋十五家詩選本（國家圖書館、湖北省圖書館、上海圖書館藏）。',
         'zm0669', {'_why': '自 %s 拆出 Book 993fq447wh（宋十五家詩選本），並自 %s 移入 Book 994188c54x（一卷，館藏國圖、湖北、上海與宋十五家詩選康熙刻本全同；同叢子目劍南詩選 d59fxu76kc8w 等同此）。' % (D1, D2)})
move_book('993fq447wh', D1, W2, '陳訏選宋十五家詩選本一卷')
move_book('994188c54x', D2, W2, '一卷無選者，館藏與陳訏宋十五家詩選康熙刻本全同，判為該本')
d = rec(D2)
d['indexed_by'][0]['summary'] = '共 2 個版本：（山東大學圖書館）；（國家圖書館、湖北省圖書館）'
note(d, 'Book 994188c54x（一卷，源記錄 m6k78lr2uimp8wqo）為陳訏宋十五家詩選本，移至新建 %s；indexed_by[0].summary 隨之刪去該本。' % W2)
bump(d); touch(D2)
new_work(W3, '東坡詩選', [dict(SONG_SU), {'name': '沈德潛', 'role': '選', 'dynasty': '清', 'entity_id': 'hixhd2h9bcu8'}],
         2, '二卷',
         [{'source': '中國古籍總目', 'source_bid': 'd59frnrt4lxc', 'title_info': '東坡詩選二卷', 'author_info': '宋蘇軾撰;清沈德潛選',
           'section': '集部/別集類/宋代之屬', 'summary': '共 1 個版本：清乾隆三十四年亦園刻本（復旦大學圖書館）'}],
         '宋蘇軾撰、清沈德潛選，二卷，有清乾隆三十四年亦園刻本（復旦大學圖書館藏）。',
         'zm0669', {'_why': '自 %s 拆出 Book 993fq3hqtd（總目該本責任者明記清沈德潛選，與孟濤輯本選者不同）。' % D1})
move_book('993fq3hqtd', D1, W3, '沈德潛選二卷本')

# ── G0940 劍南詩鈔：宋詩鈔初集本一卷歸 d59fyid32ubk ──
J1, J2 = 'd59fxywkoge8', 'd59fyid32ubk'
pop_ib(J1, 1, '劍南詩鈔一卷')
d = rec(J1)
s = d['indexed_by'][0]['summary']
assert s.startswith('共 13 個版本') and s.endswith('；宋詩鈔初集本（馆藏未载）')
d['indexed_by'][0]['summary'] = '共 12 個版本' + s[len('共 13 個版本'):-len('；宋詩鈔初集本（馆藏未载）')]
note(d, '宋詩鈔初集本一卷（Book 993htraiv4、源記錄 umowvsi7tvukvb5w、67tuhkqjhp0twwnm）是吳之振等《宋詩鈔》所收，移入 %s；本條專指清楊大鶴選六卷本。' % J2)
bump(d)
move_book('993htraiv4', J1, J2, '宋詩鈔初集本一卷')
d = rec(J2)
d['indexed_by'][0]['author_info'] = '宋陸游撰;清呂留良、清吳之振、清吳爾堯輯'
d['indexed_by'][0]['summary'] = '共 2 個版本：宋詩鈔初集本（馆藏未载）；（上海圖書館、遼寧省圖書館、國家圖書館、北京大學圖書館）'
note(d, '自 %s 移入 Book 993htraiv4（宋詩鈔初集本）；館藏與宋詩鈔初集康熙十年刻本 d59fxvbhqlmp 全同，本條即吳之振等《宋詩鈔》所收劍南詩鈔一卷。' % J1)
bump(d); touch(J2)

# ── G0534 今水經：黃錫齡注本拆出 ──
K = 'd59fxu434pvk'
e = pop_ib(K, 1, '黃錫齡')
d = rec(K)
note(d, '「今水經注要覽三卷 清黃宗羲撰;清黃錫齡注」（indexed_by、Book 9955zzq801）是後人注本，移出至新建 %s。薛鳳昌編宣統二年時中書局鉛印本即梨洲遺著彙刊本，留下。' % W4)
bump(d)
new_work(W4, '今水經注要覽',
         [{'name': '黃宗羲', 'role': '撰', 'dynasty': '清', 'entity_id': 'hixhd2f8wait'},
          {'name': '黃錫齡', 'role': '注', 'dynasty': '清', 'source': {'name': '中國古籍總目', 'type': 'url', 'details': 'http://data.library.sh.cn/entity/person/cms1kwr14f21b4ig'}}],
         3, '三卷', [e],
         '清黃錫齡就黃宗羲《今水經》加注之本，三卷，有清嘉慶二年刻本（國家圖書館藏）。',
         'zm0278', {'_why': '自 %s 拆出（注本，題名、卷數、責任方式皆異）。' % K,
                    'related_works': [{'id': 'd59fyt0b2f40', 'relation': 'related', 'note': '黃錫齡《水經要覽》一卷（小方壺齋輿地叢鈔本），疑為本書節本，未證同，不併'}]})
move_book('9955zzq801', K, W4, '黃錫齡注本《今水經注要覽》三卷')
b = rec('9956ar3q4g', 'Book')
for a in b.get('authors', []):
    if a.get('name') == '黃宗義':
        a['name'] = '黃宗羲'
note(b, '撰者「黃宗義」為總目形近誤字，改「黃宗羲」。')
bump(b); touch('9956ar3q4g')

# ── G0610 雲南通志：刪明修本著錄、康熙志 Book 改掛 ──
Y = 'd59f2mdca6tc'
pop_ib(Y, 1, '十七卷')
d = rec(Y)
d['description'] = {'text': '清鄂爾泰、尹繼善修，靖道謨纂。三十卷，首一卷。雍正七年奉詔纂輯，乾隆元年書成。見著錄於《欽定四庫全書總目》《中國古籍總目》。',
                    'sources': ['欽定四庫全書總目', '中國古籍總目']}
note(d, '刪去《國史經籍志》「《雲南通志》十七卷」一條：焦竑書成於明萬曆，所著必為明修本（隆慶志，鄒應龍修、李元陽纂），2026-08-26 雙向鏈回補誤繫於此；其正主 d59f2ncxc8hs 已有同一條著錄。description 原「佚文見引於《通志》」為套板誤生，改寫。康熙志 Book 9979895f9f 改掛 d59f2n7qzfup。')
bump(d)
move_book('9979895f9f', Y, 'd59f2n7qzfup', '題「[康熙]雲南通志」，國圖版本項清康熙，屬范承勳等修康熙志')

# ── G0005 晉畧：重複著錄去一 ──
G = 'd59fyro6c35s'
d = rec(G)
assert d['indexed_by'][0]['title_info'] == d['indexed_by'][3]['title_info'] == '晉畧二卷' and d['indexed_by'][0]['summary'] == d['indexed_by'][3]['summary']
pop_ib(G, 0, '晉畧二卷')
note(d, '刪去重複著錄「晉畧二卷」（史評類議論之屬；與叢編之屬一條同出源記錄 g1a0p40y10781k8e 等三條，文字全同）。該二卷為《史論彙函甲編》摘論節本，依庫內史論彙函子目掛原書之例不另立。')
bump(d)

# ── G0518 易章句：宋志程迥之節改繫 d59f2hjwe8zn ──
E, C = 'd59f2hgz79xd', 'd59f2hjwe8zn'
e = pop_ib(E, 1, '十卷')
e['note'] = '宋志頂真格，前節「《周易玩辭》十六卷程迥」之尾名屬本節，撰人程迥；章句十卷又外編、占法與直齋所著同。%s 自 %s 改繫（原繫磁鐵條 1ev85diqsbqww）。' % (TODAY, E)
d = rec(E)
d['authors'][0]['dynasty'] = '北宋'
d['description'] = {'text': '《易章句》一卷，北宋呂大臨撰。見《宋史·藝文志》。', 'sources': ['宋史藝文志']}
note(d, '宋志「《易章句》十卷又《外編》一卷《占法》」一節屬程迥（頂真格前節尾名），改繫 %s《沙隨易章句》；description 原誤作龔原並混入十卷之說，改寫；authors[0].dynasty 補「北宋」。' % C)
bump(d)
d = rec(C)
d['indexed_by'].append(e)
note(d, '自 %s 移入宋志「《易章句》十卷又《外編》一卷《占法》」一節（撰人程迥）。卷數欄仍作一卷未改，直齋與宋志皆作十卷，待核。' % E)
bump(d); touch(C)

if not APPLY:
    print('dry run:', sorted(k for k, v in cache.items() if v[2]), sorted(created)); sys.exit()
for i, (p, d, ch) in cache.items():
    if ch or i in (A, D1, J1, K, Y, G, E):
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
