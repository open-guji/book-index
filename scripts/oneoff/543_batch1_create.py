"""overview#543 建档批 1：四庫總目 册002／003（易類）。默认干跑，--apply 才写。

清单：overview `项目进展/古籍文本/专名匹配/建档清单-批1.md`（Tamsin，32 条＝16 人＋16 书）。
1. 查重（Eric，2026-10-11）：book-index、book-index-draft 的 Entity／Work 按 primary_name／title／alt_names 逐条查，
   32 条均无同名（「時用書」d59f2pvlsbgi 是鄭揚庭之作，与鄭夬《時用書》不是一书，另建）。
2. CBDB（API，按名查）：劉敏士 1213、王莘叟 38165、蘇師旦 3768、韓侂胄 3326、鄭芝龍 59197、吳全節 33224 收；
   郭文卿（CBDB 336098 是隆慶二年進士，非元人）、張嗣古（CBDB 47275 宜春人，index year 1160，距嘉定癸酉 1213 补刻
   过远，不确定）不收；其余 CBDB 无此名。
3. 新建 Entity 16、Work 16；id 由 mintid 鑄，机器段 2011（专给本批，已固定于下）；既有 Work 补别名 4 处。
读写走 build/v2common.py（保格式）。新记录 revision 1.0.0，review unreviewed。
"""
import os, sys, copy, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'build'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import v2common as v
import mintid

APPLY = '--apply' in sys.argv
TODAY = '2026-10-11'
SRC = '欽定四庫全書總目'
SRC_BID = 'd59dh3vo9af4'
D = '2026-10-11 #543 建档批 1：'

E_IDS = ['hixi48p2fke8', 'hixi48p2fke9', 'hixi48p2fkea', 'hixi48p2fkeb', 'hixi48p2fkec', 'hixi48p2fked', 'hixi48p2fkee',
         'hixi48p2fkef', 'hixi48p2fkeg', 'hixi48p2fkeh', 'hixi48p2fkei', 'hixi48p2fkej', 'hixi48p2fkek', 'hixi48p2fkel',
         'hixi48p2fkem', 'hixi48p2fken']
W_IDS = ['d59fu304ueww', 'd59fu304uewx', 'd59fu304uewy', 'd59fu304uewz', 'd59fu304uex0', 'd59fu304uex1', 'd59fu304uex2',
         'd59fu304uex3', 'd59fu304uex4', 'd59fu304uex5', 'd59fu304uex6', 'd59fu304uex7', 'd59fu304uex8', 'd59fu304uex9',
         'd59fu304uexa', 'd59fu304uexb']
for _i in E_IDS:
    assert mintid.idtype(_i) == 'Entity' and mintid.parse(_i)['machine'] == 2011, _i
for _i in W_IDS:
    assert mintid.idtype(_i) == 'Work' and mintid.parse(_i)['machine'] == 2011, _i

PERIOD = {'東漢': 'qin-han', '晉': 'jin', '宋': 'song', '南宋': 'song', '三國魏': 'three-kingdoms', '春秋': 'pre-qin',
          '明': 'ming', '元': 'liao-jin-yuan'}

# 清单序号 → (规范名, 朝代, 证据, 卷/锚点, 置信, 备注, CBDB 号, CBDB 说明, alt_names, dates, 籍贯)
P = [
    ('第五元先', '東漢', '考元初從第五元先受京氏易，又從馬融受費氏易', '册002 14:3:19，卷001', '高', '鄭玄之师（《後漢書·鄭玄傳》：始事京兆第五元先）。我方 span 作「第五元」少一字，待修', None, None, [], None, None),
    ('閔康之', '晉', '顧悅之…難王弼易義四十餘條，京口閔康之又申王難顧', '册002 24:6:3，卷001', '中', '朝代由顧悅之（晉）推断，原文未写', None, None, [], None, None),
    ('王天悅', '宋', '邵子易受之李之才…陳摶…惟大名王天悅、滎陽張子望嘗從學', '册002 57:7:7，卷002', '中', '陳摶弟子辈，宋初', None, None, [], None, None),
    ('張子望', '宋', '同上', '册002 57:7:12，卷002', '中', '滎陽人', None, None, [], None, None),
    ('劉敏士', '南宋', '南宋時劉敏士嘗刻於浙右漕司', '册002 41:4:11，卷002', '中', '刻书者', 1213, 'CBDB 1213 劉敏士（宋，晉江人）；Hartwell 活動表 1167 年任兩浙運判，與「浙右漕司」相合', [], None, '晉江'),
    ('聞人茂德', '宋', '迥…受經於嘉興聞人茂德、嚴陵喻樗', '册002 96:1:8，卷003', '高', '程迥之师', None, None, [], None, None),
    ('王莘叟', '宋', '乃祖謙門人王莘叟所筆受', '册002 127:7:12，卷003', '高', '呂祖謙門人', 38165, 'CBDB 38165 王莘叟（宋，金華人；呂祖謙亦金華人）', [], None, '金華'),
    ('蘇師旦', '南宋', '慶元六年…周密齊東野語則載其諂事蘇師旦，由司業躐擢左司諫，師旦敗後貶死', '册002 139:1:3，卷003', '高', '韓侂冑党', 3768, 'CBDB 3768 蘇師旦（宋，長洲人，卒 1207，韓侂冑党誅時貶死）', [], {'death': 1207, 'basis': 'CBDB 3768 YearDeath 1207'}, '長洲'),
    ('韓侂胄', '南宋', '楊萬里…致仕，韓侂胄召之不起，開禧間聞北伐啓釁，憂憤不食而卒', '册002 120:9:10，卷003', '高', '规范名用通行字「韓侂胄」；总目原字形作「韓𠈁冑」，记为异体别名', 3326, 'CBDB 3326 韓侂胄（宋，1152–1207，字節夫）',
     [{'name': '節夫', 'type': '字'}, {'name': '韓𠈁冑', 'type': '異體'}], {'birth': 1152, 'death': 1207, 'basis': 'CBDB 3326 YearBirth 1152、YearDeath 1207'}, None),
    ('張嗣古', '南宋', '張嗣古、陳造先後修之…嗣古嘉定癸酉所補刻', '册002 123:6:20，卷003', '高', '嘉定癸酉＝1213。CBDB 有張嗣古（47275，宜春人，index year 1160），與嘉定癸酉补刻相距 53 年，不能定为同一人，**不收**', None, None, [], None, None),
    ('淳于俊', '三國魏', '復引魏淳于俊對高貴鄉公語', '册003 107:4:14，卷005', '高', '', None, None, [], None, None),
    ('鄭公子曼滿', '春秋', '王子伯廖論鄭公子曼滿，稱其在周易豐之離', '册002 84:3:21，卷003', '高', '《左傳》人物，鄭国', None, None, [], None, None),
    ('王子伯廖', '春秋', '同上', '册002 84:3:16，卷003', '高', '《左傳》人物，周', None, None, [], None, None),
    ('鄭芝龍', '明', '旋為鄭芝龍所軋，憤恚而卒', '册003 107:1:5，卷005', '高', '明末。CBDB 把朝代记为清（降清），本库按总目语境记「明」', 59197, 'CBDB 59197 鄭芝龍（1604–1661，南安人；CBDB 朝代作清，生活于明末）',
     [{'name': '飛皇', 'type': '字'}, {'name': '飛虹', 'type': '字'}, {'name': '一官', 'type': '別名'}], {'birth': 1604, 'death': 1661, 'basis': 'CBDB 59197 YearBirth 1604、YearDeath 1661'}, '南安'),
    ('郭文卿', '元', '胡炳文…與吳澄書曰…郭文卿守浮梁時為刋其半', '册003 29:7:21，卷004', '中', '朝代由胡炳文（元）推断。CBDB 的郭文卿（336098）是隆慶二年進士（明），不是此人，**不收**', None, None, [], None, None),
    ('吳全節', '元', '吳全節《序》又稱其有《文集》二十卷（《易圖通變》提要：雷思齊，宋亡後棄儒為道士）', '册002 187:4:17，卷003', '中', '元道士，為雷思齊文集作序，與 CBDB 33224 吳全節（1269–1346，饒州安仁人，道士）相合', 33224, 'CBDB 33224 吳全節（元，1269–1346，饒州安仁人）；《易圖通變》提要稱吳全節為雷思齊作序，雷思齊宋亡後為道士，時代相合',
     [{'name': '成季', 'type': '字'}, {'name': '看雲道人', 'type': '號'}, {'name': '閒閒', 'type': '號'}], {'birth': 1269, 'death': 1346, 'basis': 'CBDB 33224 YearBirth 1269、YearDeath 1346'}, '饒州安仁'),
]

# 作者 entity_id（库里已有，二十八批查得）
AU = {'程迥': 'hixhd2h9bdr4', '鄭鍔': 'hixhd2h9btvr', '吳沆': 'hixhd2h9bdr0', '鄭夬': 'hixhd2h9bttp', '葉盛': 'hixhd2h9bebm',
      '楊時喬': 'hixhd2h9bdu6', '張獻翼': 'hixhd2h9bdsn', '梁寅': 'hixhd2h9bgd6'}

# 书：(标题, 作者, 作者朝代, 存佚, 存佚依据, 别名, 证据, 锚点, 置信, 备注)
W = [
    ('古周易章句外編', '程迥', '宋', 'extant', '总目提要：与《周易古占法》同装一编，传写者误合', ['周易章句外編'], '周易古占法一卷、古周易章句外編一卷…宋程迥撰', '册002 95:8:8，卷003（96:9:13 另称「周易章句外編」）', '高',
     '库内《周易古占法》d59f2hteicch 的 additional_works 已记此书；本条单立 Work'),
    ('周禮全解', '鄭鍔', '宋', None, None, [], '王應麟稱…有三山鄭鍔字剛中，淳熙中進周禮全解', '册002 78:2:4，卷003', '中', '总目说此鄭鍔≠鄭剛中；仅见于引文，依据弱'),
    ('三墳訓義', '吳沆', '宋', 'lost', '总目：「三墳訓義為太學博士王之望所駁，亦不傳」', [], '沆所獻曰易璇璣、曰三墳訓義…三墳訓義為太學博士王之望所駁，亦不傳', '册002 81:9:21，卷003', '高', ''),
    ('易禮圖說', '吳沆', '宋', 'undetermined', '总目：「胡一桂稱沆尚有易禮圖說…今未見其書」', [], '胡一桂稱沆尚有易禮圖說…今未見其書', '册002 83:2:16，卷003', '中', ''),
    ('鄭夬易傳', '鄭夬', '宋', 'lost', '总目：「…今並佚」', [], '書錄解題有鄭夬易傳十三卷，宋史藝文志有鄭夬時用書二十卷、明用書九卷…今並佚', '册002 58:3:4，卷002', '高', '同条五书（#21–25）'),
    ('鄭夬時用書', '鄭夬', '宋', 'lost', '总目：「…今並佚」', [], '同上', '册002 58:3:17，卷002', '高', '二十卷；与库中鄭揚庭《時用書》d59f2pvlsbgi 不是一书'),
    ('明用書', '鄭夬', '宋', 'lost', '总目：「…今並佚」', [], '同上', '册002 58:4:6，卷002', '高', '九卷'),
    ('易傳詞', '鄭夬', '宋', 'lost', '总目：「…今並佚」', [], '同上', '册002 58:4:11，卷002', '高', '三卷'),
    ('易傳詞後語', '鄭夬', '宋', 'lost', '总目：「…今並佚」', [], '同上', '册002 58:4:16，卷002', '高', '一卷'),
    ('綠竹堂書目', '葉盛', '明', None, None, [], '文淵閣書目、葉盛綠竹堂書目尚著於錄', '册002 79:2:11，总目文本', '高', '私家书目'),
    ('傳易考', '楊時喬', '明', None, None, [], '明楊時喬作傳易考，竟斥為異端', '册002 112:7:8，总目文本', '中', '与库内《周易古今文全書》同作者，另一书'),
    ('讀易韻考註', '張獻翼', '明', 'extant', '总目：「朱彝尊經義考載獻翼易注凡五種，惟讀易韻考註存」', [], '朱彝尊經義考載獻翼易注凡五種，惟讀易韻考註存', '册003 82:4:3，总目文本', '高', '总目「别存目」，存'),
    ('讀易約說', '張獻翼', '明', 'undetermined', '总目：「均註曰未見」', [], '同上', '册003 82:4:10，总目文本', '高', '三卷'),
    ('易雜說', '張獻翼', '明', 'undetermined', '总目：「均註曰未見」', [], '同上', '册003 82:4:16，总目文本', '高', '二卷'),
    ('詩書演義', '梁寅', '元末明初', None, None, [], '學者稱曰梁五經，有詩書演義、周禮考註、春秋考義諸書', '册003 54:4:8，总目文本', '中', '《春秋考義》库里已有；《周禮考註》库里的是吳澂的，不是梁寅的，**不并**'),
    ('讀易臆說', '張獻翼', '明', 'undetermined', '总目：「均註曰未見」', [], '同上', '册003 82:4:21，总目文本', '高', '二卷'),
]

# 既有 Work 补别名（title → 加入的 additional_titles），id 在运行时按文件名核对
ALIAS_WORK = {'d59f2htm01du': ('直齋書錄解題', ['書錄解題']), 'd59f2hqd9a81': ('東坡易傳', ['毘陵易傳']),
              'd59f2hute0w0': ('兼山易解', ['兼山易說'])}


def resolve_same(rows, idx):
    """证据栏写「同上」的，换成上一条非「同上」的原文（每条记录自带原文，不写指代词）。"""
    out, last = [], None
    for r in rows:
        r = list(r)
        if r[idx] == '同上':
            r[idx] = last
        else:
            last = r[idx]
        out.append(tuple(r))
    return out


P = resolve_same(P, 2)
W = resolve_same(W, 6)


def entity(eid, p):
    name, dyn, ev, anchor, conf, note, cbdb, cbdb_note, alt, dates, place = p
    d = {'schema_version': 1, 'id': eid, 'type': 'entity', 'subtype': 'people', 'primary_name': name}
    if alt:
        d['alt_names'] = alt
    d['dynasty'] = dyn
    d['dynasty_basis'] = '《欽定四庫全書總目》提要上下文：%s' % ev if conf != '高' else '《欽定四庫全書總目》提要：%s' % ev
    if dates:
        d['dates'] = dates
    if cbdb:
        d['external_ids'] = {'cbdb_id': cbdb, 'cbdb_match': 'manual', 'cbdb_source': '#543 批 1，CBDB API 按名查并核对'}
    d['updated_at'] = TODAY + 'T00:00:00+00:00'
    d['period'] = PERIOD[dyn]
    d['period_basis'] = '據 dynasty「%s」自動歸併' % dyn
    if place:
        d['native_place'] = place
        d['native_place_basis'] = cbdb_note
    d['review'] = {'status': 'unreviewed'}
    d['revision'] = '1.0.0'
    d['revised_at'] = TODAY
    d['ai_note'] = (D + '据 Tamsin 建档清单批 1（四庫總目 册002／003 专名匹配）新建，置信：%s。证据：「%s」（%s）。' % (conf, ev, anchor)
                    + ('备注：%s。' % note if note else '')
                    + ('CBDB：%s。' % cbdb_note if cbdb else '未补 CBDB 号（查无或不能确认同一人）。'))
    return d


def work(wid, w, eents):
    title, au, adyn, loss, lossb, alias, ev, anchor, conf, note = w
    eid = AU[au]
    ed = eents[eid]
    d = {'schema_version': 1, 'id': wid, 'type': 'work', 'title': title}
    if alias:
        d['additional_titles'] = alias
    d['authors'] = [{'name': au, 'role': '撰', 'entity_id': eid, 'dynasty': ed.get('dynasty') or adyn}]
    if loss:
        d['loss_status'] = loss
        d['loss_status_basis'] = lossb
    if ed.get('period'):
        d['period'] = ed['period']
        d['period_basis'] = '据撰人 %s（%s）' % (au, ed.get('dynasty') or adyn)
    d['description'] = {'text': '《%s》，%s%s撰。见《欽定四庫全書總目》提要所引：「%s」。' % (title, ed.get('dynasty') or adyn, au, ev),
                        'sources': [SRC]}
    d['updated_at'] = TODAY + 'T00:00:00+00:00'
    d['review'] = {'status': 'unreviewed'}
    d['revision'] = '1.0.0'
    d['revised_at'] = TODAY
    d['ai_note'] = (D + '据 Tamsin 建档清单批 1 新建；锚点：%s；置信：%s。' % (anchor, conf) + ('备注：%s。' % note if note else '')
                    + '本条只据《總目》提要的提及建档，未覆核原书与他志。')
    return d


recs, _, _ = v.load_repo(ROOT, keep_raw=True)
sample_fmt = next(iter(recs['Entity'].values())).fmt
wsample_fmt = next(iter(recs['Work'].values())).fmt

# 校验：作者 entity 存在
eents = {}
for au, eid in AU.items():
    assert eid in recs['Entity'], (au, eid)
    assert recs['Entity'][eid].data['primary_name'] == au, (au, recs['Entity'][eid].data['primary_name'])
    eents[eid] = recs['Entity'][eid].data
# 查重复核：32 个新名在库里仍无同名（防本脚本在别的提交之后跑）
existing = {}
for fam in ('Entity', 'Work'):
    for r in recs[fam].values():
        d = r.data
        for k in ('primary_name', 'title'):
            if isinstance(d.get(k), str):
                existing.setdefault((fam, d[k]), []).append(d['id'])
        for a in d.get('alt_names') or []:
            if isinstance(a, dict) and a.get('name'):
                existing.setdefault((fam, a['name']), []).append(d['id'])
        for t in d.get('additional_titles') or []:
            if isinstance(t, str):
                existing.setdefault((fam, t), []).append(d['id'])
for p in P:
    assert ('Entity', p[0]) not in existing, ('已有', p[0], existing[('Entity', p[0])])
for w in W:
    assert ('Work', w[0]) not in existing, ('已有', w[0], existing[('Work', w[0])])

created, changed = [], []
for eid, p in zip(E_IDS, P):
    rec = entity(eid, p)
    rel = mintid.path_for(eid, rec['primary_name'])
    created.append(rel)
    if APPLY:
        os.makedirs(os.path.dirname(os.path.join(ROOT, rel)), exist_ok=True)
        open(os.path.join(ROOT, rel), 'w', encoding='utf-8').write(v.dump(rec, sample_fmt))
for wid, w in zip(W_IDS, W):
    rec = work(wid, w, eents)
    rel = mintid.path_for(wid, rec['title'])
    created.append(rel)
    if APPLY:
        os.makedirs(os.path.dirname(os.path.join(ROOT, rel)), exist_ok=True)
        open(os.path.join(ROOT, rel), 'w', encoding='utf-8').write(v.dump(rec, wsample_fmt))

for wid, (title, add) in ALIAS_WORK.items():
    r = recs['Work'][wid]
    d = r.data
    assert d['title'] == title, (wid, d['title'])
    old = list(d.get('additional_titles') or [])
    new = old + [a for a in add if a not in old]
    if new != old:
        d['additional_titles'] = new
        changed.append(r.path)
        if APPLY:
            open(os.path.join(ROOT, r.path), 'w', encoding='utf-8').write(v.dump(d, r.fmt))

print(('APPLY' if APPLY else 'DRY-RUN'), '新建 %d 个，改既有 %d 个' % (len(created), len(changed)))
for p in created:
    print('  新建', p)
for p in changed:
    print('  改', p)
print(json.dumps({'entity': dict(zip([p[0] for p in P], E_IDS)), 'work': dict(zip([w[0] for w in W], W_IDS))}, ensure_ascii=False))
