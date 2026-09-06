#!/usr/bin/env python3
"""全庫品質掃描電池（qa-sweep）。

用法：
  python3 .claude/qa/scan.py                      # 全庫，按 period 分組計數
  python3 .claude/qa/scan.py --period song        # 只報 song 之條（宇宙仍是全庫）
  python3 .claude/qa/scan.py --period none        # period 缺值者
  python3 .claude/qa/scan.py --period ming --show F --limit 50   # 印某一項之明細
  python3 .claude/qa/scan.py --period ming --out /tmp/ming.json  # 明細全數落檔

各項檢查（字母即報表之鍵）：
  A basis_stale      period_basis 句首稱「據 authors[i].dynasty「X」」而實錄非 X／無此鍵
  B dangling         related_works / books / authors.entity_id / contained_in / source_bid 指向不存在之 ID
  C entity_period    撰人 entity 之 period 與 work 之 period 不同（附役，注疏類自行判）
  D upper_conflict   period_upper 早於 period
  E lost_but_text    loss_status=lost 而有 Book／_has_text／_has_image
  F name_mismatch    撰人名不在所繫 entity 之 primary_name／alt_names（容「X等」「X氏」）
  G title_catalog    題名夾雜卷數／撰人／殘語；附 clash＝剝殘語所得之淨題撞庫者（撞庫型信度遠高於孤例，優先處置）
  H author_odd       撰人名可疑：單字、含數字／標點／「等」「撰」「注」
  I dup_title        同題且撰人集合相同（或俱無撰人）之組
  J desc_gap         著錄 ≥4 源而 description 全缺
  K entity_oneway    work→entity 無回指；entity.works 懸空；entity→work 無回指（人指書而書之 authors 不指人）
  L lone_outlier     一 entity 名下諸 work 之 period，n−1 同而恰一異（磁鐵／誤繫徵候）
  M index_drift      索引 period/loss_status/title/subtype/author/dynasty/role 與記錄檔不符（dynasty 取頂層，無則 authors[0]）
  N source_no_bid    indexed_by 有 source 而無 source_bid（來源為 Collection 者豁免：其本無 work-space 之 bid）
  O dyn_transitional 撰人 entity 之 dynasty 作「元末明初」類跨代標籤而生卒與之相斥（L5 循環論據之遺）
  P bogus_alias      ai_note 載「撰人異稱……同指一人」而 X、Y 全無共字（補南北史志「深覈」偽註）
  Q propagate_conflict period_basis 自稱「據 entity 之 period 傳播」而所繫 entity 之 period 與本條不同（C 之高精子集）
  R upper_selfcontra  period_basis 自稱「上限 X 覆驗不相斥」而 X 實早於 period（覆驗方向反了）
  S upper_ghost      period_upper_basis 之 catalog_bound 所引之志不在本條 indexed_by（引不存在之著錄為據）
  T l5_circular      entity 之 dynasty_basis 以「L5 斷代歸一」起首而其「確證」（名下 work 分居諸桶）不成立
  U dyn_vs_life      entity 之 dynasty 與其自載生卒相斥（O 之推廣，不限跨代標籤）
  W claimed_not_done ai_note 稱某欄已「清除／卸除／已刪」而該欄仍在

H 之 kind 另有 residue：頂真格斷鏈之殘語與括注注記被取作撰人（「十集」「，一名」「二譯」
「廣卷帙」），及罕用部件字致脫姓（「𰖍拙」實「陳拙」）——suitang 道所報，H 收窄後方現形。

H 之 kind：num 數字（明人排行字常態，已收窄）／split 拆字缺字描述式／role 役字結尾／
prefix 身分官銜前綴／bracket 括號按語／single 單字／punct 其他標點。

判準與踩坑見 PROTOCOL.md、PITFALLS.md。本檔只掃不改。
"""
import argparse, collections, glob, json, os, re, sys, urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ORD = ['pre-qin','qin-han','three-kingdoms','jin','nanbeichao','sui-tang','five-dynasties',
       'song','liao-jin-yuan','ming','qing','modern']

def _load_idx(fam):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')):
        out.update(json.load(open(f)))
    return out

def load_universe():
    IW, IB, IE = _load_idx('works'), _load_idx('books'), _load_idx('entities')
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json')))
    return IW, IB, IE, IC

def read(path):
    return json.load(open(os.path.join(ROOT, path)))

def period_key(p):
    return 'none' if p is None else p

# ---------------------------------------------------------------- checks
BASIS_RE = re.compile(r'^據 authors\[(\d+)\]\.dynasty[「『"]([^」』"]+)[」』"]')
TITLE_RE = re.compile(r'[一二三四五六七八九十百]+卷|\d+卷|\(存|（存|原目|[，,：:]| 題$|卷首$| 著$')
# G 之淨題：剝去題末之卷數／存卷／撰人括注／殘綴
CLEAN_RE = [re.compile(x) for x in (
    r'[（(](存[^）)]*|[一二三四五六七八九十百]+卷[^）)]*)[）)]\s*$',
    r'[（(][^）)]{0,8}[）)]\s*(著|撰|注|傳|題|編)?\s*$',
    r'\s*(著|撰|注|傳|題|編)\s*$',
    r'[一二三四五六七八九十百]+卷.*$', r'\d+卷.*$', r'\s*卷首\s*$', r'\s*原目\s*$')]
def clean_title(t):
    prev = None
    while prev != t:
        prev = t
        for r in CLEAN_RE:
            t = r.sub('', t).strip()
    return t
NUM_CH = '〇一二三四五六七八九十百千'
SPLIT_RE = re.compile(r'\[[^\]]*\+[^\]]*\]|《[^》]{1,3}》|[?？□]')
# 只取名末幾乎不可能是人名用字者：修（歐陽修）、述、校、疏、傳、解皆常見於名，故不列
ROLE_SUF = re.compile(r'(撰|注|編|輯|纂|等)$|(上人|居士|道人)$')
# 釋／僧／道士是本庫僧道之常例（非缺陷），不列；只取著錄語黏連之身分與帝號
PREFIX_RE = re.compile(r'^(西洋人|泰西|西洋|大學士|太監|尚書|侍郎|禦史|御史|翰林|明太祖|太祖高皇帝|世宗|神宗|熹宗|思宗)')
PUNCT_RE = re.compile(r'[卷篇、，。\[\]（）()]')
# 頂真格斷鏈之殘語、注記誤作人名、罕用部件字脫姓（suitang 所報，坑 26）
# 收窄記：初稿之 ^廣.{1,3}$ 誤收廣成子、廣德先生、廣治、廣學、廣化、廣衍、廣夷等真名（假陽性
# 七成八），依坑 21 之訓改為「決不入人名之書志語／校勘語」白名單，現全庫零假陽性。
RESIDUE_RE = re.compile(
    r'^[，。、；]'                                    # 一、標點起首者為斷鏈殘語
    r'|^(一名|又名|原名|亦名)$'                        # 二、異名引導語單獨成名
    r'|^[一二三四五六七八九十百千]+(卷|篇|集|冊|譯)$'    # 三、「二譯」「十集」之數量殘語
    r'|(卷帙|卷首|原目|存卷|闕卷)'                      # 四、書志用語，不入人名
)
# 校勘語殘留（「廣作中作」）。名中已有括注者另有 punct 型收之，此處不重報。
COLLATE_RE = re.compile(r'(一作|或作|題作|中作|作中|原作)')
RADICAL_RE = re.compile(r'^[\u2e80-\u2fff\u31c0-\u31ef]')
# X 檢（撰人／書名切分之誤）之字表，移植自 entity-cbdb 道之 scan_author_title_split.py
# 回溯重建之志：補X書藝文志／經籍志之屬，成書在清末民初而非其所補之代
# 回溯重建之志：成書在清末民初而非其所補之代。名目不止「補X書藝文志」一種——
# 《元史藝文志》（錢大昕補元）《三國藝文志》《後漢藝文志》（姚振宗）《宋史藝文志補》
# 皆是，其 basis 之括注每每自陳「清人補」「清某某補X，斷代」。故兼認名目與自陳（坑 55）。
RETRO_RE = re.compile(r'補[^》，,。\s]{1,4}(書)?(藝文志|经籍志|經籍志)|(藝文志|經籍志)補|元史藝文志|三國藝文志|後漢藝文志')
# basis 之括注自陳為清人所補者（「清人補」「清錢大昕補元，斷代」「清姚振宗考證隋志」）
RETRO_NOTE_RE = re.compile(r'清人補|清[^）]{0,6}補[^）]{0,4}[，,]?\s*斷代|補[^）]{0,4}[，,]\s*斷代')
M_POS = re.compile(r'(今存|今尚存|原文賴[^，。]{0,12}以存|全文見於|全文賴|完帙尚存|今有傳本)')
M_BARE = re.compile(r'尚存')
M_PAST = re.compile(r'(時|代|志|世|初|末|間|前|後)$')   # 「梁時尚存」是存至某代而後亡
M_NEG = re.compile(r'(之目賴|目錄賴|其目賴|原書已佚|已佚|佚文|輯本|殘卷|亡佚|不存|未見傳本|而亡|已亡|全亡)')
# 撰人小傳式之小注：字／號／諡／籍貫／科第／官職——編目者確知有此人，是原分法之正證
BIO_RE = re.compile(r'[字號号諡谥]\s*[^\s，,。]|[縣县州府郡]人|進士|舉人|貢生|生員|知[縣県府州]|訓導|教諭|通判|同知|按察|布政|御史|翰林')
# 帝號／諡號式之異稱（元帝＝蕭繹、武帝＝梁武帝）本無共字，非偽稱
# 「王」「公」單字結尾在人名中太常見（顧野王、王儉），不可作帝號之徵；
# 只收帝／后／太子／世子之結尾與明確之廟號年號式起首。
TITLE_RE_IMPERIAL = re.compile(r'(帝|后|太子|世子|皇后)$|^(梁|陳|齊|周|隋|魏|宋|晉|漢|唐|後梁)?(高祖|太祖|世祖|太宗|文帝|武帝|明帝|元帝|宣帝|簡文帝|孝武帝|後主|煬帝|昭明)')
JUAN_RE = re.compile(r'([〇一二三四五六七八九十百千]+|\d+)\s*卷')
_NUM = {c: i for i, c in enumerate('〇一二三四五六七八九')}
def _cn2int(x):
    if x.isdigit(): return int(x)
    if x == '十': return 10
    n = 0; unit = 1; tot = 0
    for c in reversed(x):
        if c == '十': unit = 10; n = 0 if n else 1; tot += n * unit; n = 0
        elif c == '百': unit = 100; n = 0 if n else 1; tot += n * unit; n = 0
        elif c == '千': unit = 1000; n = 0 if n else 1; tot += n * unit; n = 0
        elif c in _NUM: tot += _NUM[c] * (unit if unit > 1 and n == 0 else 1); n = 1; unit = 1
    return tot or None
def desc_text(w):
    """取 description 之正文，容其為 dict／str／None 三型。"""
    d = w.get('description')
    if isinstance(d, dict): return d.get('text') or ''
    if isinstance(d, str): return d
    return ''

def juan_of(w):
    """自本條諸著錄之引文抽卷數（可多，諸志所記本有異同）。無者回空集。"""
    out = set()
    for ib in (w.get('indexed_by') or []):
        for fld in ('title_info', 'summary'):
            for m in JUAN_RE.finditer(ib.get(fld) or ''):
                v = _cn2int(m.group(1))
                if v: out.add(v)
    return out
BOUND_RE = re.compile(r'最緊者為[^，,。]{0,30}')
# 異譯之明證（Y 之 variant 型；坑 45）
TRANSL_RE = re.compile(r'(第[二三四五]出|所譯之本|所出[一二三四五六七八九十百]+部|出者[大小]同|小異|異譯|重譯|別譯)')
Y_NORM = re.compile(r'[《》〈〉「」『』（）()⟨⟩\s、，。]')
SPLIT_NOTE_RE = re.compile(r'[⟨（(【\[].*?[⟩）)】\]]')
ZHAI = set('齋斋軒轩堂山谷溪雲云亭樓楼園园庵菴洲峯峰石竹松梅居舍館馆廬庐窩窝村塘湖江河潭')
BAD_HEAD = set('論论門门經经傳传注疏解義义記记志史書书子語语詩诗文集稿編编錄录鈔钞')
TITLE_TAIL = ('集','志','録','錄','稿','編','傳','考','記','譜','論','解','注','圖','說','説',
              '書','鑑','鑒','略','畧','要','鈔','钞','草','詩','文','卷','篇','典','經','史','談','話')
def odd_kinds(nm):
    """撰人名之可疑型。數字一則已收窄：明人排行字（數字在名之中段）是常態，不報。"""
    ks = []
    if SPLIT_RE.search(nm): ks.append('split')
    if ROLE_SUF.search(nm) and len(nm) >= 2: ks.append('role')
    if PREFIX_RE.match(nm): ks.append('prefix')
    if PUNCT_RE.search(nm): ks.append('punct')
    if len(nm) == 1: ks.append('single')
    if (RESIDUE_RE.search(nm) or RADICAL_RE.match(nm)
            or (COLLATE_RE.search(nm) and not PUNCT_RE.search(nm))): ks.append('residue')
    if any(c in NUM_CH for c in nm):
        # 排行字（楊一清、劉三吾）與名末之數（黃式三、尹會一）皆明清常態，不報。
        # 只報：名以數字起（多為僧號／殘名）、或長逾四字者。
        if nm[0] in NUM_CH or len(nm) >= 5:
            ks.append('num')
    return ks
ALIAS_RE = re.compile(r'撰人異稱——本志作[「『]([^」』]+)[」』]而庫中作[「『]([^」』]+)[」』]，同指一人')
# F 之正俗異體歸一（只作比對，禁止寫盤；nanbeichao 道所列，坑 19）
VARIANTS = str.maketrans('温云舍冲吴隠禇衞鈃隂邱楊煜檝𣶬', '溫雲捨沖吳隱褚衛銒陰丘揚曄楫沈')
# 朝代→年代區間（U 檢用；粗界，只作「相斥」之判，不作定代）
DYN_SPAN = {
 '先秦': (-1100, -221), '春秋': (-770, -476), '戰國': (-475, -221), '秦': (-221, -206),
 '西漢': (-206, 8), '東漢': (25, 220), '漢': (-206, 220), '三國魏': (220, 265), '三國吳': (222, 280),
 '三國蜀': (221, 263), '魏': (220, 265), '西晉': (265, 317), '東晉': (317, 420), '晉': (265, 420),
 '南朝宋': (420, 479), '南朝齊': (479, 502), '南朝梁': (502, 557), '南朝陳': (557, 589),
 '北魏': (386, 534), '後魏': (386, 534), '東魏': (534, 550), '西魏': (535, 556),
 '北齊': (550, 577), '北周': (557, 581), '隋': (581, 618), '唐': (618, 907),
 '五代': (907, 960), '後梁': (907, 923), '後唐': (923, 936), '後晉': (936, 947),
 '後漢': (947, 951), '後周': (951, 960), '北宋': (960, 1127), '南宋': (1127, 1279), '宋': (960, 1279),
 '遼': (916, 1125), '金': (1115, 1234),
 # 元：下限用蒙古建國之 1206 而非忽必烈建元之 1271。《元史》為耶律楚材、劉祁諸人立傳，
 # 本庫與一般典籍皆稱蒙古國時期（1206–1271）人物為「元人」，以 1271 為界則逢卒必報。
 # liaojinyuan 道 18 個 U 類 entity 有 14 個由此而來（坑 27）。
 '元': (1206, 1368), '明': (1368, 1644), '清': (1644, 1912),
 '民國': (1912, 1949), '中華民國': (1912, 1949),
}
LATE_ROLE = {'注','疏','箋','訓詁','音','音義','集解','集注','校','校注','輯','輯佚','輯錄','補','補注','釋','正義','章句','解','箋注','纂','編','刊','訂','評','批','校刊','校訂','增補','續'}

def run_checks(works, IW, IB, IE, IC, ents):
    """works: dict id->record (全庫)。回傳 {check: [row,...]}。row 皆含 id,title,period。"""
    ALL = set(IW) | set(IB) | set(IE) | set(IC)
    COLL_TITLES = {v.get('title') for v in IC.values()}
    R = collections.defaultdict(list)
    # P 之「先問庫」用表：名 → 同一 entity 之全部名（primary_name ＋ alt_names）。
    # 二名若同屬一個 entity，其「同指一人」之說即有本庫自身之證。此法把帝號式異稱
    # （元帝＝蕭繹、簡文帝＝蕭綱、梁武帝＝蕭衍）與偽稱（武帝／熊安生、范岫／文帝）
    # 一刀分開，勝過任何字面之判（坑 52）。
    alias_of = collections.defaultdict(set)
    for _e in ents.values():
        _ns = {(_e.get('primary_name') or '').strip()}
        for _a in (_e.get('alt_names') or []):
            _n = _a.get('name') if isinstance(_a, dict) else _a
            if _n: _ns.add(str(_n).strip())
        _ns = {n for n in _ns if n}
        for _n in _ns: alias_of[_n] |= _ns
    def row(w, **kw):
        d = {'id': w['id'], 'title': w.get('title'), 'period': period_key(w.get('period'))}
        d.update(kw); return d

    # 反向表：entity -> works 實繫（自 work 側）
    w2e = collections.defaultdict(set)
    for w in works.values():
        for a in (w.get('authors') or []):
            if a.get('entity_id'): w2e[a['entity_id']].add(w['id'])

    for w in works.values():
        a_list = w.get('authors') or []
        # A
        m = BASIS_RE.match((w.get('period_basis') or '').strip())
        if m:
            i, claim = int(m.group(1)), m.group(2)
            real = a_list[i].get('dynasty') if i < len(a_list) else '<無此撰人>'
            if real != claim:
                R['A'].append(row(w, claim=claim, real=real, author=(a_list[i].get('name') if i < len(a_list) else None)))
        # B
        for r in (w.get('related_works') or []):
            if r.get('id') and r['id'] not in ALL: R['B'].append(row(w, field='related_works', ref=r['id'], ref_title=r.get('title')))
        for b in (w.get('books') or []):
            if b not in ALL: R['B'].append(row(w, field='books', ref=b))
        for a in a_list:
            if a.get('entity_id') and a['entity_id'] not in IE: R['B'].append(row(w, field='authors.entity_id', ref=a['entity_id'], author=a.get('name')))
        for k in ('contained_in', 'additional_works'):
            for r in (w.get(k) or []):
                rid = r.get('id') if isinstance(r, dict) else r
                if rid and rid not in ALL: R['B'].append(row(w, field=k, ref=rid))
        for ib in (w.get('indexed_by') or []) + (w.get('emendated_by') or []):
            if ib.get('source_bid') and ib['source_bid'] not in ALL: R['B'].append(row(w, field='source_bid', ref=ib['source_bid'], source=ib.get('source')))
            if ib.get('source') and not ib.get('source_bid') and ib.get('source') not in COLL_TITLES: R['N'].append(row(w, source=ib.get('source')))
        # C / F / K(oneway)
        for a in a_list:
            eid = a.get('entity_id')
            if not eid or eid not in IE: continue
            e = ents.get(eid)
            ie = IE[eid]
            ep = ie.get('period')
            if ep and w.get('period') and ep != w['period']:
                R['C'].append(row(w, author=a.get('name'), role=a.get('role'), entity=eid, entity_name=ie.get('primary_name'),
                                  entity_dynasty=ie.get('dynasty'), entity_period=ep,
                                  annot=(a.get('role') in LATE_ROLE)))
            nm = a.get('name') or ''
            if e is not None:
                names = {e.get('primary_name')} | {x.get('name') for x in (e.get('alt_names') or []) if isinstance(x, dict)}
                vn = {(n or '').translate(VARIANTS) for n in names}; nmv = nm.translate(VARIANTS)
                ok = nmv in vn or (nmv.endswith('等') and nmv[:-1] in vn) or (nmv.endswith('氏') and any(n.startswith(nmv[:-1]) for n in vn))
                if not ok:
                    R['F'].append(row(w, author=nm, entity=eid, entity_name=e.get('primary_name'),
                                      alt=[x.get('name') for x in (e.get('alt_names') or []) if isinstance(x, dict)], entity_dynasty=e.get('dynasty')))
                if not any(x.get('work_id') == w['id'] for x in (e.get('works') or [])):
                    R['K'].append(row(w, kind='work->entity 無回指', author=nm, entity=eid, entity_name=e.get('primary_name')))
        # D
        pu, p = w.get('period_upper'), w.get('period')
        if pu in ORD and p in ORD and ORD.index(pu) < ORD.index(p):
            R['D'].append(row(w, period_upper=pu))
        # E
        if w.get('loss_status') == 'lost' and (w.get('books') or w.get('_has_text') or w.get('_has_image')):
            R['E'].append(row(w, books=len(w.get('books') or []), has_text=bool(w.get('_has_text')), has_image=bool(w.get('_has_image'))))
        # G（clash 於迴圈後補）
        if TITLE_RE.search(w.get('title') or ''): R['G'].append(row(w, clean=clean_title(w.get('title') or '')))
        # H
        for a in a_list:
            nm = a.get('name') or ''
            ks = odd_kinds(nm) if nm else []
            if ks:
                R['H'].append(row(w, author=nm, kind='+'.join(ks), dynasty=a.get('dynasty'), entity=a.get('entity_id'), note=(a.get('note') or '')[:60]))
        # Q / R / S
        pb = w.get('period_basis') or ''
        if 'period 傳播' in pb or 'entity_propagation' in pb:
            for a in a_list:
                e2 = IE.get(a.get('entity_id') or '')
                if e2 and e2.get('period') and w.get('period') and e2['period'] != w['period']:
                    R['Q'].append(row(w, entity=a.get('entity_id'), entity_name=e2.get('primary_name'),
                                      entity_period=e2['period'], role=a.get('role'), annot=(a.get('role') in LATE_ROLE)))
        mu = re.search(r'上限\s*([a-z\-]+)\s*覆驗不相斥', pb)
        if mu and w.get('period') in ORD and mu.group(1) in ORD and ORD.index(mu.group(1)) < ORD.index(w['period']):
            R['R'].append(row(w, claimed_upper=mu.group(1)))
        pub = w.get('period_upper_basis') or ''
        if pub.startswith('catalog_bound'):
            ms = re.search(r'最緊者為《(.+?)》', pub)
            if ms and not any((x.get('source') or '') == ms.group(1) for x in (w.get('indexed_by') or [])):
                R['S'].append(row(w, cited=ms.group(1), sources=[x.get('source') for x in (w.get('indexed_by') or [])]))
        # W：宣稱已清而該欄仍在
        for fld, verb in (('birth_year', '生卒'), ('death_year', '生卒'), ('cbdb_id', 'cbdb')):
            pass
        # P
        # P 之分型（坑 52）：ai_note 自稱「本志作 X 而庫中作 Y，同指一人」，其可信度分四等。
        # 全無共字者未必皆偽——帝號／諡號式之異稱（元帝＝蕭繹、武帝＝梁武帝）本就無共字，
        # 故先以 TITLE_RE_IMPERIAL 別之；扣去帝號一路，餘下之「全無共字」才是偽稱之大宗。
        for m in ALIAS_RE.finditer(w.get('ai_note') or ''):
            x, y = m.group(1), m.group(2)
            sx, sy = set(x), set(y)
            # **先問庫**：二名若同屬一個 entity（primary_name／alt_names 相通），
            # 其「同指一人」之說即有本庫自身之證，不必再疑。此法把帝號式異稱
            # （元帝＝蕭繹、簡文帝＝蕭綱、梁武帝＝蕭衍）與偽稱（武帝／熊安生、
            # 范岫／文帝）一刀分開，勝過任何字面之判（坑 52）。
            if y in alias_of.get(x, ()) or x in alias_of.get(y, ()):
                k = 'confirmed'
            elif x == y: k = 'same'
            elif len(sx & sy) >= min(len(sx), len(sy)): k = 'variant_char'
            elif sx & sy: k = 'partial'
            elif TITLE_RE_IMPERIAL.search(x) or TITLE_RE_IMPERIAL.search(y): k = 'imperial'
            else: k = 'no_common'
            R['P'].append(row(w, kind=k, x=x, y=y, no_common=not (sx & sy)))
        # J
        d = w.get('description'); dt = (d.get('text') if isinstance(d, dict) else d) or ''
        if not dt and len(w.get('indexed_by') or []) >= 4:
            R['J'].append(row(w, sources=len(w['indexed_by'])))
        # M
        ie = IW.get(w['id']) or {}
        nz = lambda v: None if v in ('', None) else v
        a0 = a_list[0] if a_list else {}
        want = {f: nz(w.get(f)) for f in ('period', 'loss_status', 'title', 'subtype')}
        want.update({'author': nz(a0.get('name')), 'role': nz(a0.get('role')),
                     'dynasty': nz(w.get('dynasty')) if nz(w.get('dynasty')) is not None else nz(a0.get('dynasty'))})
        for f, b_ in want.items():
            a_ = nz(ie.get(f))
            if a_ != b_: R['M'].append(row(w, field=f, index=a_, record=b_))

    # G clash：以淨題撞全庫之題（排除自身與墓碑）
    # 墓碑（merged_into 不空之被併條）之索引項依先例仍留 title 欄（供人知其去向），
    # 若不排除，已併之組每次重掃都再報一次 clash（ming 道所報，坑 37）。
    by_title = collections.defaultdict(list)
    for w in works.values():
        if w.get('merged_into'): continue
        by_title[(w.get('title') or '').strip()].append(w['id'])
    for r in R['G']:
        c = r.get('clean') or ''
        hits = [x for x in by_title.get(c, []) if x != r['id']]
        r['clash'] = bool(hits)
        if hits: r['clash_ids'] = hits[:5]

    # I 同題同撰人。**卷數異即異書**（skill〈同名異書識別判準〉）——undated 道逐組裁
    # 142 組，其中 119 組卷數互異（如《毛詩義疏》一組五條作 20／10／29／11／28 卷，
    # 皆繫隋志，正是隋志所著錄之五家義疏，斷不可併）。志書裸條之題又多是截斷之形
    # （《雜傳》《義疏》《詩》《書》《經》），同題本不足為據。故卷數互異者降為
    # kind='juan_differ' 而不作重出候選（坑 47）。墓碑不入組（坑 37 同理）。
    groups = collections.defaultdict(list)
    for w in works.values():
        if w.get('merged_into'): continue
        au = tuple(sorted((a.get('name') or '') for a in (w.get('authors') or [])))
        groups[(w.get('title'), au)].append(w)
    for (t, au), ws in groups.items():
        if len(ws) < 2: continue
        juans = {frozenset(juan_of(w)) for w in ws}
        known = [j for j in juans if j]
        differ = len(known) > 1 and not set.intersection(*[set(j) for j in known])
        kind = 'juan_differ' if differ else 'same_juan'
        for w in ws:
            R['I'].append(row(w, kind=kind, group_title=t, authors=list(au),
                              group_ids=[x['id'] for x in ws], juan=sorted(juan_of(w)),
                              sources=[i.get('source') for i in (w.get('indexed_by') or [])]))

    # K(entity side) / L / O
    for eid, e in ents.items():
        per = collections.Counter()
        for x in (e.get('works') or []):
            wid = x.get('work_id')
            if wid not in IW:
                R['K'].append({'id': wid, 'title': None, 'period': 'none', 'kind': 'entity.works 懸空',
                               'entity': eid, 'entity_name': e.get('primary_name')})
                continue
            if wid in works and eid not in w2e.get(eid, set()) and not any(a.get('entity_id') == eid for a in (works[wid].get('authors') or [])):
                R['K'].append(row(works[wid], kind='entity->work 無回指（人指書而書不指人）', entity=eid, entity_name=e.get('primary_name'),
                                  work_authors=[a.get('name') for a in (works[wid].get('authors') or [])]))
            per[period_key(IW[wid].get('period'))] += 1
        # T：L5 斷代歸一之循環確證
        if (e.get('dynasty_basis') or '').startswith('L5 斷代歸一'):
            pp = {period_key(IW[x['work_id']].get('period')) for x in (e.get('works') or [])
                  if x.get('work_id') in IW and IW[x['work_id']].get('period')}
            if len(pp) <= 1:
                for x in (e.get('works') or []):
                    if x.get('work_id') in works:
                        R['T'].append(row(works[x['work_id']], entity=eid, entity_name=e.get('primary_name'),
                                          entity_dynasty=e.get('dynasty'), buckets=sorted(pp)))
        # U：entity 之 dynasty 與自載生卒相斥（O 之推廣）
        by_, dy_ = e.get('birth_year'), e.get('death_year')
        span = DYN_SPAN.get((e.get('dynasty') or '').strip())
        if span and (by_ or dy_):
            lo, hi = span
            bad = (by_ and by_ > hi) or (dy_ and dy_ < lo) or (by_ and by_ < lo - 120) or (dy_ and dy_ > hi + 120)
            if bad:
                for x in (e.get('works') or []):
                    if x.get('work_id') in works:
                        R['U'].append(row(works[x['work_id']], entity=eid, entity_name=e.get('primary_name'),
                                          entity_dynasty=e.get('dynasty'), span=list(span), birth=by_, death=dy_))
        # W：ai_note 稱已清除而欄仍在
        an = e.get('ai_note') or ''
        for fld, pat in (('birth_year', r'birth_year[^。]{0,20}(清除|卸除|已刪)'),
                         ('cbdb_id', r'cbdb_id[^。]{0,20}(清除|卸除|已刪)')):
            if e.get(fld) is not None or (fld == 'cbdb_id' and (e.get('external_ids') or {}).get('cbdb_id') is not None):
                if re.search(pat, an):
                    R['W'].append({'id': eid, 'title': e.get('primary_name'), 'period': period_key(e.get('period')),
                                   'field': fld, 'still': e.get(fld) or (e.get('external_ids') or {}).get('cbdb_id')})
        dy = e.get('dynasty') or ''
        if ('末' in dy and '初' in dy) or dy in ('宋元', '元明', '明清', '金元'):
            by, dyr = e.get('birth_year'), e.get('death_year')
            # 跨代標籤所跨之後一代起年：元末明初→1368；宋末元初→1279；明末清初→1644；金元→1234
            start = {'明': 1368, '元': 1279, '清': 1644}.get(dy[dy.index('初')-1] if '初' in dy else dy[-1], None)
            bogus = bool(start and ((by and by >= start + 2) or (dyr and dyr >= start + 82)))
            if bogus:
                for x in (e.get('works') or []):
                    wid = x.get('work_id')
                    if wid in works:
                        R['O'].append(row(works[wid], entity=eid, entity_name=e.get('primary_name'), entity_dynasty=dy,
                                          birth=by, death=dyr, basis=(e.get('dynasty_basis') or '')[:80]))
        dated = {k: v for k, v in per.items() if k != 'none'}
        if len(dated) >= 2:
            top, n = max(dated.items(), key=lambda kv: kv[1])
            rest = sum(v for k, v in dated.items() if k != top)
            if rest == 1 and n >= 2:
                odd = [k for k in dated if k != top][0]
                odd_w = [x['work_id'] for x in e['works'] if x.get('work_id') in IW and period_key(IW[x['work_id']].get('period')) == odd]
                for wid in odd_w:
                    wrec = works.get(wid)
                    R['L'].append({'id': wid, 'title': IW[wid].get('title'), 'period': odd, 'entity': eid,
                                   'entity_name': e.get('primary_name'), 'entity_dynasty': e.get('dynasty'),
                                   'majority_period': top, 'majority_n': n,
                                   'role': next((a.get('role') for a in ((wrec or {}).get('authors') or []) if a.get('entity_id') == eid), None)})

    # ── X：撰人／書名切分之誤（entity-cbdb 道所發，坑 30）──────────────────
    # 志書著錄之體例是「撰人＋書名⟨小注⟩」，匯入時要在二者之間切一刀。切錯一格就
    # 憑空造出一個人，而拼起來與原文一字不差——字串比對查不出，CBDB 也驗不出
    # （這輩多是方志別集之作者，無官無科第，本不在 CBDB）。判準移植自該道
    # overview/scripts/cbdb-sync/scan_author_title_split.py（已經三輪抽核打磨）。
    in_name, head_title, name_all, title_all = (collections.Counter() for _ in range(4))
    bg_name, bg_title = collections.Counter(), collections.Counter()
    for w in works.values():
        t = (w.get('title') or '').strip()
        if t:
            head_title[t[0]] += 1; title_all[t] += 1
            for i in range(len(t)-1): bg_title[t[i:i+2]] += 1
        for x in (w.get('authors') or []):
            nm = (x.get('name') or '').strip()
            name_all[nm] += 1
            for ch in nm[1:]: in_name[ch] += 1
            for i in range(len(nm)-1): bg_name[nm[i:i+2]] += 1
    nworks = {eid: len(d.get('works') or []) for eid, d in ents.items()}
    for wid, w in works.items():
        title = (w.get('title') or '').strip()
        if len(title) < 3: continue
        c, rest = title[0], title[1:]
        for a_ in (w.get('authors') or []):
            nm, eid = (a_.get('name') or '').strip(), a_.get('entity_id')
            if len(nm) != 2: continue
            hits = [ib for ib in (w.get('indexed_by') or [])
                    if SPLIT_NOTE_RE.sub('', (ib.get('title_info') or ib.get('summary') or '')).strip().startswith(nm + c)]
            if not hits: continue
            ratio = in_name[c] / (head_title[c] + 1)
            if ratio < 1.0: continue
            ib0 = hits[0]
            note0 = ' '.join(SPLIT_NOTE_RE.findall(ib0.get('summary') or ib0.get('title_info') or ''))
            sc = 2 if ratio >= 4 else (1 if ratio >= 2 else 0.5)
            sc += 1 if rest[-1] in TITLE_TAIL else 0
            sc += 1 if (eid and nworks.get(eid, 0) <= 1) else 0
            if note0 and re.search(r'[字號号]\s*[^人\s]{0,3}' + re.escape(c), note0): sc -= 3   # 以字名集
            if set(title[1:4]) & ZHAI: sc -= 2                                                  # 齋號切進書名
            if rest and rest[0] in BAD_HEAD: sc -= 2                                            # 去首字不成詞
            # 小注若為現撰人之小傳（「字某某，號某某，某地人」「某年進士」），
            # 即是編目者確知有此二字之人——**是原分法之正證，非猜法之正證**。
            # 原判準在此加分，方向反了：抽驗 undated 桶 12 條，僅 1 條真缺陷（八分之一），
            # 九條皆帶此型小注而現撰人無誤（呉䎖《升恒堂集》、潘章《力田餘稿》、
            # 傅梅《簡翁詩集》、鄭渭《望川存稿》、呉沉《應酬稿》……）。今改為減分（坑 48）。
            if note0 and BIO_RE.search(note0): sc -= 2
            strong = ''
            if rest.startswith(nm[0]) and len(rest) > 2:                                        # 書名以姓＋字／諡／官起
                mid = rest[1:]
                for key in re.findall(r'[字號号諡谥]\s*([^\s，,。]{2})', note0):
                    if mid.startswith(key): strong = f'書名以姓＋{key}起'; break
                if not strong and re.match(r'^(文|忠|孝|莊|庄|端|恭|簡|简|靖|貞|贞|定|懿|襄|節|节|毅|裕|憲|宪|清|敏|肅|肃|安)', mid):
                    strong = '書名以姓＋諡字起'
                if not strong and re.search(r'(公|先生|府君)', rest[:5]): strong = '書名以姓＋尊稱起'
            if strong: sc += 3
            left, right = nm[1] + c, (c + rest[0] if rest else '')
            ln, lt, rn, rt = bg_name[left], bg_title[left], bg_name[right], bg_title[right]
            bg = ''
            if ln >= 3 and ln > lt * 2: sc += 1.5; bg = f'「{left}」入人名{ln}次'
            if rt >= 3 and rt > rn * 2: sc -= 2; bg = (bg + '；' if bg else '') + f'「{right}」入書名{rt}次'
            if lt >= 3 and lt > ln * 2: sc -= 1.5; bg = (bg + '；' if bg else '') + f'「{left}」入書名{lt}次'
            sc += 1 if name_all.get(nm + c, 0) > 0 else 0
            # 論體之三字書名（氏姓論、昕天論、才性論、聲類論）易被誤縮為二字。凡剝後只剩
            # 二字、而猜出之三字名全庫無徵、原二字名卻另有其書者，偏向原分法（weijin 所報，坑 38）
            if len(rest) <= 2 and name_all.get(nm + c, 0) == 0:
                sc -= 2
                if name_all.get(nm, 0) > 1: sc -= 1
            if title_all.get(title, 0) > 1: sc -= 2                                             # 同題他處亦見
            if re.match(r'^[鄉縣州府都里]?(縣志|州志|府志|志)$', rest): sc -= 2                    # 通名成詞
            if sc < 3.0: continue
            bare = SPLIT_NOTE_RE.sub('', (ib0.get('title_info') or ib0.get('summary') or '')).strip()
            R['X'].append(row(w, score=round(sc, 1), kind=strong or '撰人切短', author=nm,
                              guess_name=nm + c, guess_title=rest, entity=eid,
                              source=ib0.get('source', ''), raw=bare[:50], note=note0[:36], bigram=bg))

    # ── Y：一節著錄分居二條（shanggu 道所發之疑，坑 35）──────────────────────
    # 一部志之一節著錄，若原文（source_bid＋title_info＋summary 全同）同時掛在二條
    # 同題之 work 上，非重出即誤繫。三道收窄以除假陽性：
    #   (a) 諸條之題須同——合刊條拆分者（「東夷圖說二卷嶺海異聞一卷」）題必異，是正辦；
    #   (b) summary 須非裸題——「孝經注一卷」不足以辨條，志中五家孝經注文字全同；
    #   (c) 撰人各異而著錄文不點名者抑制——同上，是志書同文著錄之常，非缺陷。
    # 分二型：著錄文點名某條之撰人而他條亦掛之 → misattached（著錄誤繫，該條不當有此志）；
    #         諸條撰人全同（或皆空）→ dup（重出待併）。
    ykey = collections.defaultdict(set)
    for wid, w in works.items():
        nt = Y_NORM.sub('', (w.get('title') or ''))
        for ib in (w.get('indexed_by') or []):
            sb, ti, su = ib.get('source_bid'), ib.get('title_info') or '', ib.get('summary') or ''
            if not (sb and ti and su): continue
            nsu = Y_NORM.sub('', su)
            if nsu == nt or len(nsu) <= len(nt) + 1: continue          # (b)
            ykey[(sb, Y_NORM.sub('', ti), nsu)].add(wid)
    for k, v in ykey.items():
        if len(v) < 2: continue
        v = sorted(v)
        if len({(works[x].get('title') or '') for x in v}) != 1: continue   # (a)
        su = k[2]
        aus = {x: [(a.get('name') or '').strip() for a in (works[x].get('authors') or [])] for x in v}
        owners = [x for x in v if any(a and a in su for a in aus[x])]
        # (d) 同經異譯之防（坑 45）：佛典之譯人多不著錄，兩造 authors 皆空，只憑撰人判不出。
        # 其別載在 author_info——「第二出」「與某某出者小異」「此為某某所譯之本」
        # 「某某所出十部之一」皆是異譯之明證。故 author_info 相異者一律不判 dup。
        ai = {x: Y_NORM.sub('', ' '.join(
            (ib.get('author_info') or '') for ib in (works[x].get('indexed_by') or [])
            if (ib.get('source_bid') == k[0]))) for x in v}
        transl = any(TRANSL_RE.search(t) for t in ai.values())
        if owners and len(owners) < len(v):
            kind, extra = 'misattached', {'owner': owners}
        elif len(set(ai.values())) > 1 or transl:
            # 著錄之 author_info 有別（或明言異譯）：非重出，報作 variant——**不可併**
            kind, extra = 'variant', {'author_info': {x: ai[x][:40] for x in v}}
        elif len({frozenset(a for a in aus[x] if a) for x in v}) == 1:
            kind, extra = 'dup', {}
        else:
            continue                                                   # (c)
        for x in v:
            R['Y'].append(row(works[x], kind=kind, source_bid=k[0], entry=su[:44],
                              group=v, authors=aus[x], **extra))

    # ── Y 之三型 twin_edition：同撰人同題而分繫同名異本之志（weijin 所報，坑 39）──
    # 《補晉書藝文志》有丁國鈞本與文廷式本二整理本，source_bid 各異、著錄文字亦各異，
    # 故上兩型（須 summary 全同）掃不出。判準用 weijin 道所定：撰人全同＋正規化題全同
    # ＋各自 indexed_by 恰一節＋二節出自同名而異本之志。
    solo = collections.defaultdict(list)
    for wid, w in works.items():
        ib = w.get('indexed_by') or []
        if len(ib) != 1: continue
        src = (ib[0].get('source') or '').strip()
        if not src: continue
        nsrc = src.replace('晋', '晉').replace('経', '經')
        au = tuple(sorted((a.get('name') or '').strip() for a in (w.get('authors') or [])))
        nt = Y_NORM.sub('', (w.get('title') or ''))
        if not nt: continue
        solo[(nsrc, au, nt)].append((wid, ib[0].get('source_bid')))
    for (nsrc, au, nt), lst in solo.items():
        if len(lst) < 2: continue
        if len({b for _, b in lst}) < 2: continue          # 須真出自異本，同本之重出上型已收
        ids = sorted(w for w, _ in lst)
        for wid in ids:
            R['Y'].append(row(works[wid], kind='twin_edition', source=nsrc,
                              group=ids, authors=list(au)))

    # ── Z：catalog_bound 誤取志名裡的朝代為界（nanbeichao 所報，坑 40）────────
    # 「補X書藝文志」是清末民初人對 X 代書目之回溯重建，**成書在清而非 X 代**。
    # catalog_bound 的原意是以志書自身之成書年代為界（《隋志》唐人成，故所著錄不晚於隋唐），
    # 取志名裡的「晉」作界，等於說「凡補晉志著錄之書必不晚於晉」——對整類回溯重建之志皆誤。
    # 此類之界對本庫斷代幾無收窄之用，當自 basis 中剔除，另尋實有之志立界。
    for wid, w in works.items():
        b = w.get('period_upper_basis') or ''
        if 'catalog_bound' not in b: continue
        # 只報「該回溯志正是所取之界」者。basis 中順帶提及而非取以為界者不算——
        # 邏輯之誤只在它被當作 catalog_bound 之界時才傷人（455 → 72）。
        m = BOUND_RE.search(b)
        if not m: continue
        seg = m.group(0)
        mm = RETRO_RE.search(seg) or RETRO_NOTE_RE.search(b)
        if not mm: continue
        m = mm
        others = sorted({(ib.get('source') or '') for ib in (w.get('indexed_by') or [])
                         if ib.get('source') and not RETRO_RE.search(ib.get('source') or '')})
        R['Z'].append(row(w, retro=m.group(0), period_upper=w.get('period_upper'),
                          contradict=bool(w.get('period') and w.get('period_upper')
                                          and w.get('period') != w.get('period_upper')),
                          other_sources=others[:4], basis=b[:90]))

    # ── M：loss_status 與 description 不相覆核（weijin 所報，坑 43）──────────
    # 二型：contra＝loss 明作 lost 之屬而 desc 稱今存（真矛盾）；blank＝loss 未填而 desc 稱今存。
    # 「尚存」前若有時間限定（梁時尚存、唐志尚存、校書時尚存）是「存至某代而後亡」，非今存——
    # 初稿不辨此，11 條裡 10 條假陽性（坑 21 之訓），今以 M_PAST 排除。
    for wid, w in works.items():
        ls = w.get('loss_status')
        if ls in ('extant', 'partially_extant'): continue
        # description 之型不一：多數是 {"text":…} 物件，而庫中確有存純字串者
        # （`d59f28k3vbwl`，weijin 桶）。`.get` 施於 str 即 AttributeError，
        # 全庫任何 --period 皆崩，九道盡廢。**掃描器讀資料一律要容型**（坑 54）。
        t = desc_text(w)
        if not t: continue
        m = M_POS.search(t)
        if not m:
            for b in M_BARE.finditer(t):
                if not M_PAST.search(t[max(0, b.start()-1):b.start()]): m = b; break
        if not m: continue
        seg = t[max(0, m.start()-16):m.end()+16]
        if M_NEG.search(seg): continue
        R['M'].append(row(w, kind='contra' if ls else 'blank', loss_status=ls, evidence=seg.strip()[:52]))

    # ── V：維基文庫之題名孤證連結（weijin 所報，坑 44）──────────────────────
    # resources 之 url 形如 zh.wikisource.org/wiki/<題名>（頁名恰等題名、無消歧義後綴），
    # 而題僅二至四字者，最易撞上「明星同名書」——謝沈《晉書》連到房玄齡官修正史、
    # 阮籍《樂論》連到蘇洵、陸機《晉紀》連到干寶輯本，皆此。
    # 只報候選，須逐一 WebFetch 覆核頁面之撰人／朝代；以「庫中同題之數」為危度。
    same_title = collections.Counter((w.get('title') or '').strip() for w in works.values())
    for wid, w in works.items():
        t = (w.get('title') or '').strip()
        if not (2 <= len(t) <= 4): continue
        for r_ in (w.get('resources') or []):
            u = r_.get('url') or ''
            if 'zh.wikisource.org/wiki/' not in u: continue
            page = urllib.parse.unquote(u.split('/wiki/', 1)[1])
            if '(' in page or '（' in page or '/' in page: continue   # 帶消歧義後綴或子頁者不報
            if page.strip() != t: continue
            n = same_title[t]
            if n < 3: continue                                        # 庫中同題不足三見者危度低
            R['V'].append(row(w, page=page, same_title=n, url=u[:90]))
            break
    return R

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', help='逗號分隔；none 表缺值', default=None)
    ap.add_argument('--show', help='印某一檢查之明細，如 F', default=None)
    ap.add_argument('--limit', type=int, default=40)
    ap.add_argument('--out', help='明細落檔（JSON）', default=None)
    ap.add_argument('--summary-out', help='計數落檔（JSON）', default=None)
    a = ap.parse_args()
    want = set(a.period.split(',')) if a.period else None

    IW, IB, IE, IC = load_universe()
    works = {}
    for wid, ie in IW.items():
        try: works[wid] = read(ie['path'])
        except Exception as ex: print('讀檔失敗', wid, ex, file=sys.stderr)
    ents = {}
    for eid, ie in IE.items():
        try: ents[eid] = read(ie['path'])
        except Exception as ex: print('讀檔失敗', eid, ex, file=sys.stderr)
    print(f'宇宙：works {len(works)} books {len(IB)} entities {len(ents)} collections {len(IC)}', file=sys.stderr)

    R = run_checks(works, IW, IB, IE, IC, ents)
    if want:
        R = {k: [r for r in v if r.get('period') in want] for k, v in R.items()}

    # 計數表：check × period
    table = collections.defaultdict(lambda: collections.Counter())
    for k, rows in R.items():
        for r in rows: table[k][r.get('period')] += 1
    periods = [p for p in ORD + ['none'] if (not want or p in want)]
    print('check ' + ' '.join(f'{p[:6]:>6}' for p in periods) + '   total')
    for k in sorted(table):
        print(f'{k:5s} ' + ' '.join(f'{table[k].get(p,0):6d}' for p in periods) + f'   {sum(table[k].values()):6d}')
    if a.show:
        rows = R.get(a.show, [])
        print(f'\n== {a.show}: {len(rows)} ==')
        for r in rows[:a.limit]: print(json.dumps(r, ensure_ascii=False))
    if a.out:
        json.dump(R, open(a.out, 'w'), ensure_ascii=False, indent=1)
        print('明細已寫', a.out, file=sys.stderr)
    if a.summary_out:
        json.dump({'periods': {p: sum(1 for w in works.values() if period_key(w.get('period')) == p) for p in ORD + ['none']},
                   'checks': {k: dict(v) for k, v in table.items()}},
                  open(a.summary_out, 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
