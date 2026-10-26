#!/usr/bin/env python3
"""去重方案部分 2.3：为正式库 Work 作者位里「库中没有对应人物 Entity」的人规划新建 Entity（只读，出计划）。

    python3 plan23.py <输出目录> [--cbdb /path/cbdb_20260919.sqlite3]

口径（2026-10-25 重算后修订，见同目录 README.md）：
- 总目 person_uri 在本库实为「一名一号」（67,137 个名字对 67,024 个 uri；李賢唐／明同号），不作同人证据，只记溯源。
- 聚类单位＝（作者位原名，粗朝代）。不兼容朝代各自成人；相邻朝代、无朝代而同名另有定代者、异体同名者不建，登记。
- 名字（宽归一：scan.VARIANTS＋繁简）撞到库中任何人物 Entity（主名／别名，含墓碑）且朝代兼容或缺 → 不建，归 2.2 补挂登记；
  撞到的同名 Entity 朝代全不兼容 → 照建，ai_note 写明对方 id。
- CBDB 只作同名多人风险信号：同名同粗朝代 ≥2 人且本组作者位 ≥2 → 不建登记。不写 cbdb_id（抽检 spot1：同名同代唯一者错配 11/73），留给 2.4 带时地核对再写。
- 组内 ≥2 位：硃卷与他书混组、各书最早年代相距逾 80 年、谱牒异省或刊年相距逾 40 年 → 不建登记。
- 名字撞已有人物的「姓＋字号」也算撞名；名尾粘「藏／並／等」不建。
- 占位名（佚名等）、缺字名（□、&）、机构名不建，登记。
输出：plan.json（每组一项）、held.tsv（不建登记）、stats.json。"""
import argparse, collections, glob, json, os, re, sqlite3, sys
HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(QA, '..', '..'))
sys.path[:0] = [QA]
from scan import VARIANTS  # noqa: E402
import opencc  # noqa: E402
sys.path.insert(0, os.path.join(QA, 'entity-governance-1025'))
import eras  # noqa: E402

T2S = opencc.OpenCC('t2s')
EXTRA = str.maketrans('髙寜啓啟爲衆敎峯煕熈彜彞誌', '高寧启启为众教峰熙熙彝彝志')
URI = re.compile(r'entity/person/(\w+)')
ANON = re.compile(r'^(佚名|闕名|缺名|無名氏?|失名|不著撰人|不著撰者|不題撰人|不詳|撰者不詳|未詳|不詳纂修人|不詳撰人|撰人不詳)$|^□+$')
BROKEN = re.compile(r'[□〓\[\]【】&;；,，、 \ue000-\uf8ff]|\?|？|⿰|⿱|⿲|⿳|⿴|⿵|⿶|⿷|⿸|⿹|⿺|⿻|（|）|\(|\)')
ORG4 = re.compile(r'(局|館|会|會|公司|廳|院|社|處|部|府|衙門|學堂|學校|委員會|書店|書莊|銀號|總號|藥號|藥房|署|司|所|廠|營|堂|書院|政府|議會|大學|中學|小學|女學|省|報|股|室|團|組|監|科|大臣|會員|留學生|編輯|調查)$')
ORG3 = re.compile(r'(局|館|社|院|監|部|處|廳|衙門|公司|書莊|銀號|藥號)$')
PLACEHOLDER = re.compile(r'不詳|不著|名氏|未詳|闕名|佚名')
GARBLE = re.compile(r'..+[撰注註著輯纂修校編删附並評譯述錄訂][^·]*.')   # 名中夹责任方式字（解析粘连）
COUNTRY = re.compile(r'^(日本|朝鮮|高麗|英國|美國|法國|德國|俄國|意大利|葡萄牙|西班牙|荷蘭|比利時|瑞典|印度|天竺)(?=..)')
FOLLOW_OK = set('撰注註著輯纂修校編删刪附並評譯述錄録訂等、;；，,。（(）) |重增補刊刻繪書題箋疏集選審考閱鑒定參批點訓解箋序跋音義圖說說讀釋正記鈔抄演譜輯纂合同口筆篆續自藏菩原傳尊造再降論章授會羅頌直摹编主總承彙句證測詳鑑闡纘覆發女旁所祖排譔別本淺脩節詁述')  # 名后可接之责任方式字（据 p5 统计）
CTRY_IN_AI = '日本|朝鮮|高麗|英國|美國|法國|德國|俄國|意大利|義大利|葡萄牙|西班牙|荷蘭|比利時|瑞典|瑞士|奧國|奧地利|丹麥|印度|天竺|英|美|法|德|俄|日'
DEITY = re.compile(r'(帝君|上帝|真人|天尊|菩薩|仙師|祖師|聖母|娘娘|大帝|真君|天師|仙姑|仙翁|老君|佛祖|元君)$')
DYPFX2 = re.compile(r'^(後魏|北魏|元魏|東魏|西魏|北齊|北周|南齊|劉宋|蕭梁|南朝|北朝|東晉|西晉|東漢|西漢|前漢|後漢|後唐|後晉|後周|後梁|南唐|北宋|南宋|趙宋|南明|三國|十國)(?=..)')
DYPFX = set('周秦漢晉魏隋唐宋遼金元明清梁陳齊吳蜀')
FOREIGN = {'日本', '朝鮮', '高麗', '新羅', '天竺', '外國', '英國', '美國', '法國', '德國', '俄國', '意大利', '葡萄牙', '西班牙', '荷蘭', '比利時', '瑞典', '印度', '安南', '越南', '琉球', '西域', '波斯', '大秦', '阿拉伯', '江戶時代'}
C2 = [('趙宋', '宋'), ('北宋', '宋'), ('南宋', '宋'), ('宋末', '宋'), ('宋', '宋'), ('晋', '晉'), ('西晉', '晉'), ('東晉', '晉'), ('晉', '晉'),
      ('中華民國', '民國'), ('民國', '民國'), ('民国', '民國'), ('南北朝', '南北朝'), ('南朝', '南北朝'), ('北朝', '南北朝'), ('北魏', '南北朝'), ('東魏', '南北朝'), ('西魏', '南北朝'),
      ('北齊', '南北朝'), ('北周', '南北朝'), ('南齊', '南北朝'), ('劉宋', '南北朝'), ('蕭梁', '南北朝'), ('梁', '南北朝'), ('陳', '南北朝'), ('齊', '南北朝'), ('後魏', '南北朝'), ('元魏', '南北朝'),
      ('十六國', '十六國'), ('前秦', '十六國'), ('後秦', '十六國'), ('姚秦', '十六國'), ('苻秦', '十六國'), ('前涼', '十六國'), ('後涼', '十六國'), ('北涼', '十六國'), ('西涼', '十六國'), ('南涼', '十六國'),
      ('前燕', '十六國'), ('後燕', '十六國'), ('南燕', '十六國'), ('北燕', '十六國'), ('前趙', '十六國'), ('後趙', '十六國'), ('成漢', '十六國'), ('西秦', '十六國'), ('夏', '十六國'),
      ('五代', '五代'), ('後唐', '五代'), ('後晉', '五代'), ('後漢', '五代'), ('後周', '五代'), ('後梁', '五代'), ('南唐', '五代'), ('吳越', '五代'), ('前蜀', '五代'), ('後蜀', '五代'), ('十國', '五代'), ('閩', '五代'), ('南漢', '五代'), ('北漢', '五代'), ('楚', '五代'),
      ('西漢', '漢'), ('東漢', '漢'), ('兩漢', '漢'), ('前漢', '漢'), ('漢', '漢'), ('新', '漢'), ('三國', '三國'), ('魏', '三國'), ('蜀', '三國'), ('吳', '三國'),
      ('隋', '隋'), ('唐', '唐'), ('遼', '遼'), ('金', '金'), ('西夏', '金'), ('元', '元'), ('北元', '元'), ('明', '明'), ('南明', '明'), ('清', '清'), ('秦', '秦'),
      ('西周', '先秦'), ('東周', '先秦'), ('周', '先秦'), ('春秋', '先秦'), ('戰國', '先秦'), ('先秦', '先秦'), ('商', '先秦'), ('殷', '先秦'), ('夏', '先秦'), ('上古', '先秦')]
ADJ = {frozenset(x) for x in [('先秦', '秦'), ('秦', '漢'), ('先秦', '漢'), ('漢', '三國'), ('三國', '晉'), ('晉', '十六國'), ('晉', '南北朝'), ('十六國', '南北朝'), ('南北朝', '隋'), ('隋', '唐'),
                              ('唐', '五代'), ('五代', '宋'), ('五代', '遼'), ('宋', '遼'), ('宋', '金'), ('遼', '金'), ('宋', '元'), ('金', '元'), ('元', '明'), ('明', '清'), ('清', '民國')]}


def coarse2(d):
    if not d: return None
    d = d.strip().replace('张', '張')
    if d in FOREIGN: return 'F:' + d
    for k, v in C2:
        if d.startswith(k): return v
    return '?' + d


def rel2(a, b):
    ca, cb = coarse2(a), coarse2(b)
    if ca is None or cb is None: return 'unk'
    if ca == cb: return 'same'
    if ca.startswith(('F:', '?')) or cb.startswith(('F:', '?')): return 'unk'
    return 'adj' if frozenset((ca, cb)) in ADJ else 'incompat'


def loose(s):
    s = T2S.convert((s or '').translate(VARIANTS).translate(EXTRA)).replace('惠', '慧').replace('志', '志')
    return s[1:] if s.startswith('释') and len(s) >= 3 else s   # 释某＝某（惠然＝釋慧然）


def rel2_c(ca, cb):
    """rel2 之粗朝代版（参数已是 coarse2 的结果）。"""
    if ca == cb: return 'same'
    if ca.startswith(('F:', '?')) or cb.startswith(('F:', '?')): return 'unk'
    return 'adj' if frozenset((ca, cb)) in ADJ else 'incompat'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out')
    ap.add_argument('--cbdb', default='/home/claude/cbdb-archive/20260919/cbdb_20260919.sqlite3')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)

    # 1 人物 Entity 名字表（含墓碑；墓碑解到 keeper）
    ent = {}
    for f in glob.glob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')):
        d = json.load(open(f, encoding='utf-8')); ent[d['id']] = d
    people = {k: d for k, d in ent.items() if d.get('subtype') == 'people'}
    print('载入 Entity %d 条，其中人物 %d（live %d）' % (len(ent), len(people), sum(1 for d in people.values() if not d.get('merged_into'))))
    assert people
    def keeper(e):
        n = 0
        while people.get(e, {}).get('merged_into'):
            e = people[e]['merged_into']; n += 1; assert n < 8
        return e
    nameidx = collections.defaultdict(set)   # loose 名 -> {eid}
    for k, d in people.items():
        ns = {d.get('primary_name')} | {x.get('name') for x in d.get('alt_names') or [] if isinstance(x, dict)}
        for n in ns:
            if n: nameidx[loose(n)].add(keeper(k))
        pn = d.get('primary_name') or ''
        for x in d.get('alt_names') or []:   # 姓＋字号（石天基＝石成金字天基；抽检 spot2）
            if isinstance(x, dict) and x.get('name') and len(pn) >= 2 and not x['name'].startswith(pn[0]) and len(x['name']) <= 3:
                nameidx[loose(pn[0] + x['name'])].add(keeper(k))
    # 非人物 Entity 名（机构等），撞到也不建
    othernames = {loose(d.get('primary_name')) for d in ent.values() if d.get('subtype') in ('collective', 'publisher', 'office') and d.get('primary_name')}

    # 2 Work 作者位
    slots = []; nw = 0
    for f in glob.glob(os.path.join(ROOT, 'Work', '*', '*', '*', '*.json')):
        d = json.load(open(f, encoding='utf-8'))
        if d.get('merged_into'): continue
        nw += 1
        for i, au in enumerate(d.get('authors') or []):
            if not isinstance(au, dict) or au.get('entity_id') or not au.get('name'): continue
            m = URI.search(json.dumps(au.get('source'), ensure_ascii=False))
            slots.append({'path': os.path.relpath(f, ROOT), 'id': d['id'], 'title': d.get('title'), 'slot': i, 'name': au['name'],
                          # dynasty 不取 Work.dynasty 兜底：次位责任者常与作品异代（唐□□撰;清陳運溶輯）
                          'dynasty': au.get('dynasty'), 'role': au.get('role'), 'uri': m.group(1) if m else None,
                          'summary': ' | '.join((x.get('summary') or '') for x in d.get('indexed_by') or [] if isinstance(x, dict))[:600],
                          'author_info': ' | '.join((x.get('author_info') or '') for x in d.get('indexed_by') or [] if isinstance(x, dict))})
    print('载入 live Work %d 条；无 entity_id 作者位 %d' % (nw, len(slots)))
    assert nw and slots

    for s in slots:   # 抽检 b01v2：「葛延瑛、吳元祿修」解析成 dynasty=吳
        dy = s['dynasty'] or ''
        if len(dy) == 1 and s['name'].startswith(dy) and (dy + s['name']) not in s['author_info']:
            s['dynasty'] = None
    held = []; st = collections.Counter()
    def hold(s, why, detail=''):
        held.append((s['path'], s['slot'], s['name'], s['dynasty'] or '', why, detail)); st['不建:' + why] += 1

    primaries = {d.get('primary_name') for d in people.values()}
    suffixidx = collections.defaultdict(set)
    for k in nameidx:
        if len(k) >= 4: suffixidx[k[-3:]].add(k)
    slotnames = {s['name'] for s in slots}
    # 3 逐位分流
    cand = []
    for s in slots:
        n = s['name']
        if ANON.search(n): st['占位名(不计)'] += 1; continue
        if PLACEHOLDER.search(n): st['占位名(不计)'] += 1; continue
        if n != n.strip() or BROKEN.search(n) or len(n) < 2: hold(s, '名字含缺字/分隔/括注或单字'); continue
        if (len(n) >= 4 and ORG4.search(n)) or (len(n) == 3 and ORG3.search(n)) or loose(n) in othernames: hold(s, '机构或非人物专名'); continue
        if len(n) >= 4 and '·' not in n and GARBLE.fullmatch(n) and not n.startswith('釋'): hold(s, '疑名字粘连责任方式'); continue
        if len(n) >= 3 and n[-1] in '藏並等' or (len(n) >= 5 and re.search(r'(局制|鹽使|運使|按察使|布政使)$', n)):   # 乙01 抽检：上海巡警總局制
            hold(s, '疑名字粘连责任方式'); continue
        if DEITY.search(n): hold(s, '神号或托名'); continue
        if '囗' in n: hold(s, '名字含缺字/分隔/括注或单字'); continue   # 丙01 抽检：沈囗（囗 U+56D7 作缺字用）
        if re.search(re.escape(n) + r'[（(][^）)]{1,6}[）)]', s['author_info']):
            hold(s, '原文括注另名待核'); continue   # 丙01 抽检：徐太室（學謨）＝已有徐學謨；括注多为本名／字，归 2.2 核
        if len(n) <= 3 and n.endswith('公'): hold(s, '神号或托名'); continue   # 丙01 抽检：題宋漁陽公撰
        if re.search('(宋宋|唐唐|明明|元元|金金|漢漢|晉晉|魏魏|梁梁|陳陳|周周|齊齊|吳吳)' + re.escape(n), s['author_info']):
            hold(s, '朝代字与姓重叠被切'); continue   # 抽检 b02：「宋宋爲仁撰」切成爲仁
        if len(n) >= 3 and any(len(k) > len(loose(n)) and k.endswith(loose(n)) for k in suffixidx.get(loose(n)[-3:], ())):
            hold(s, '名为已有人物名之后缀待核'); continue   # 抽检 b01v2：赤心子＜起北赤心子
        if '囗' in n: hold(s, '名字含缺字/分隔/括注或单字'); continue   # 丙01 抽检：沈囗（囗 U+56D7 作缺字用）
        if re.search(re.escape(n) + r'[（(][^）)]{1,6}[）)]', s['author_info']):
            hold(s, '原文括注另名待核'); continue   # 丙01 抽检：徐太室（學謨）＝已有徐學謨；括注多为本名／字，归 2.2 核
        if len(n) <= 3 and n.endswith('公'): hold(s, '神号或托名'); continue   # 丙01 抽检：題宋漁陽公撰
        if (re.search(r'(軒|齋|斋|堂|閣|樓|館|室|廬|園|山房|書屋|居|亭|庵|菴)(主人)?$', n) or n.endswith('氏')) and re.search('題[^;；|]{0,3}' + re.escape(n), s['author_info']):   # 抽检 b02：題清掄花館主人
            hold(s, '题署室名'); continue
        if DYPFX2.match(n): hold(s, '疑名前粘朝代'); continue
        ai = s['author_info']
        if not s['dynasty'] and len(n) >= 4 and n[0] in DYPFX and n not in primaries:
            hold(s, '疑名前粘朝代'); continue   # 抽检 b01v3：金祿昭聞
        PREV_OK = set('、;；,，|（(　 題等及與和') | DYPFX | set('國人釋代吴洋宗帝后本利羅竺麗朝漢晉宋夏）)□祖')
        st_ = [m.start() for m in re.finditer(re.escape(n), ai)]
        if st_ and all(i > 0 and ai[i - 1] not in PREV_OK for i in st_):
            hold(s, '名字疑被截断', ai[:40]); continue   # 抽检 b01v3：傷心人＜天下第一傷心人
        occ = [m.end() for m in re.finditer(re.escape(n), ai)]
        if occ and all(e < len(ai) and ai[e] not in FOLLOW_OK for e in occ):
            hold(s, '名字疑被截断', ai[:40]); continue   # 抽检 b01：潘慎＜美國潘慎文等輯
        if re.search('(%s)' % CTRY_IN_AI + re.escape(n), ai) or (s['dynasty'] or '') in FOREIGN or '·' in n:
            hold(s, '外国人名(另作专项)'); continue   # 抽检 b01：斯賓塞／斯賓塞爾、巴那比克理等译名异写多、粘连多
        if COUNTRY.match(n): hold(s, '名前带国别待规范'); continue
        if len(n) == 2 and n.endswith('氏'): hold(s, '仅姓氏（某氏）'); continue
        hits = nameidx.get(loose(n), set())
        if hits:
            comp = [e for e in hits if rel2(s['dynasty'], people[e].get('dynasty')) != 'incompat']
            if comp:
                hold(s, '撞已有人物Entity(归2.2补挂)', ','.join(sorted(comp))); continue
            # 朝代不兼容也不建：总目著录朝代常被解析器从前一责任者带过来（衡山圖經「唐□□撰;唐陳運溶輯」），照建会造重
            hold(s, '撞已有人物Entity但朝代不同(待核)', ','.join(sorted(hits))); continue
        if len(n) >= 3 and n[0] in DYPFX and (n[1:] in primaries or n[1:] in slotnames):
            hold(s, '疑名前粘朝代', n[1:]); continue
        s['cd'] = coarse2(s['dynasty'])
        cand.append(s)

    # 4 聚类：原名＋粗朝代
    byname = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in cand: byname[s['name']][s['cd']].append(s)
    # 异体同名（宽归一相同、原名不同）且朝代兼容 → 全部登记
    lz = collections.defaultdict(set)
    for n in byname: lz[loose(n)].add(n)
    groups = []
    for n, bd in byname.items():
        sib = lz[loose(n)] - {n}
        dated = [c for c in bd if c]
        for c, ss in bd.items():
            if sib and any((c is None or c2 is None or rel2_c(c, c2) != 'incompat') for s2 in sib for c2 in byname[s2]):
                for s in ss: hold(s, '异体同名待核', '/'.join(sorted(sib)))
                continue
            if c is None and dated:
                for s in ss: hold(s, '无朝代而同名另有定代者', '/'.join(map(str, dated)))
                continue
            if c and any(c2 and c2 != c and rel2_c(c, c2) != 'incompat' for c2 in dated):
                for s in ss: hold(s, '同名跨相邻或未定朝代待核', '/'.join(dated))
                continue
            groups.append((n, c, ss))

    # 5 CBDB
    db = sqlite3.connect(a.cbdb)
    dyname = dict(db.execute('select c_dy,c_dynasty_chn from DYNASTIES'))
    cb = collections.defaultdict(list)
    for pid, nm, dy, iy, by, dy_ in db.execute('select c_personid,c_name_chn,c_dy,c_index_year,c_birthyear,c_deathyear from BIOG_MAIN'):
        if nm: cb[nm].append({'id': pid, 'dy': dyname.get(dy), 'iy': iy, 'by': by, 'dd': dy_})
    print('载入 CBDB 人物名 %d' % len(cb)); assert cb
    CM = {'漢前': '先秦', '秦漢': '漢', '西漢': '漢', '東漢': '漢', '新': '漢', '三國魏': '三國', '三國吳': '三國', '三國蜀': '三國', '西晉': '晉', '東晉': '晉',
          '宋(劉)': '南北朝', '南齊': '南北朝', '南梁': '南北朝', '陳': '南北朝', '北魏': '南北朝', '北周': '南北朝', '北齊': '南北朝', '西魏': '南北朝', '東魏': '南北朝', '西梁': '南北朝',
          '中華民國': '民國', '南明': '明', '北元': '元', '後梁': '五代', '後唐': '五代', '後晉': '五代', '後漢': '五代', '後周': '五代', '南唐': '五代', '吳越': '五代',
          '前蜀': '五代', '後蜀': '五代', '閩國': '五代', '南漢': '五代', '吳(楊)': '五代', '楚(馬)': '五代', '南平': '五代', '北漢': '五代', '未詳': None}
    plan = []
    for n, c, ss in groups:
        cbc = [p for p in cb.get(n, []) if coarse2(CM.get(p['dy'], p['dy'])) == c] if c and not c.startswith(('F:', '?')) else []
        if len(cbc) >= 2 and len(ss) >= 2:
            for s in ss: hold(s, '同名同代CBDB多人且本组多位', ','.join(str(p['id']) for p in cbc[:6]))
            continue
        if len(ss) >= 2:
            ts = [s['title'] or '' for s in ss]
            EXAM = re.compile(r'硃卷|貢卷|試卷|闈墨')   # 乙01 抽检：彭飛熊、季學英等「優貢卷」＋族谱，同硃卷
            if any(EXAM.search(t) for t in ts) and not all(EXAM.search(t) for t in ts):
                for s in ss: hold(s, '硃卷与他书同名待核')   # 抽检 spot1：张二铭、张家俊皆硃卷＋谱／志异人
                continue
            pu = [s for s in ss if '譜' in (s['title'] or '') or '乘' in (s['title'] or '')]
            if len(pu) >= 2:
                prov = {m.group(1)[:2] for m in (re.match(r'^\[([^\]]+)\]', s['title']) for s in pu) if m}
                py = [min(y) for y in (eras.years(s['title'] + ' ' + s['summary']) for s in pu) if y]
                if len(prov) >= 2 or (len(py) >= 2 and max(py) - min(py) > 40):
                    for s in ss: hold(s, '谱牒异地或刊年相距逾40年', '/'.join(sorted(prov)))   # 抽检 spot2：左逢原山西／湖南
                    continue
            yrs = [min(y) for y in (eras.years(s['title'] + ' ' + s['summary']) for s in ss) if y]
            lim = 60 if any(re.search(r'譜|志|乘', t) for t in ts) else 80   # 抽检 b02：張元澧 1765 谱／1834 志
            if len(yrs) >= 2 and max(yrs) - min(yrs) > lim:
                for s in ss: hold(s, '组内著作年代相距逾80年', '%d-%d' % (min(yrs), max(yrs)))   # 抽检 spot1：孙谦康熙／乾隆
                continue
        dys = collections.Counter(s['dynasty'] for s in ss if s['dynasty'])
        plan.append({'name': n, 'dynasty': dys.most_common(1)[0][0] if dys else None, 'cd': c,
                     'cbdb': None, 'cbdb_cand': cbc[0]['id'] if len(cbc) == 1 else None, 'cbdb_n': len(cbc),
                     'uris': sorted({s['uri'] for s in ss if s['uri']}),
                     'namesakes': sorted({e for s in ss for e in s.get('namesakes', [])}),
                     'slots': [{k: s[k] for k in ('path', 'id', 'title', 'slot', 'name', 'dynasty', 'role', 'author_info', 'summary')} for s in ss]})
    plan.sort(key=lambda g: (str(g['cd']), g['name']))
    st['新建人数'] = len(plan); st['新建涉及作者位'] = sum(len(g['slots']) for g in plan)
    st['其中写cbdb_id'] = sum(1 for g in plan if g['cbdb'])
    st['其中撞名但朝代不兼容照建'] = sum(1 for g in plan if g['namesakes'])
    json.dump(plan, open(os.path.join(a.out, 'plan.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    with open(os.path.join(a.out, 'held.tsv'), 'w', encoding='utf-8') as f:
        f.write('path\tslot\tname\tdynasty\treason\tdetail\n')
        for r in held: f.write('\t'.join(map(str, r)) + '\n')
    json.dump(st, open(os.path.join(a.out, 'stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in sorted(st.items()): print(k, v)


if __name__ == '__main__':
    main()
