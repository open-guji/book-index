#!/usr/bin/env python3
"""entity_subtypes.py —— Entity 專名子類型（dynasty／reign／office／place）之校驗，
check_v2.py 與 verify.py **共用這一份**（不得各寫一份）。

依據：overview `項目進展/古籍目錄/整體設計/專名建檔/給S-字段清單.md` §四，及 D／O／P 設計檔；
字段形狀見 schema/entity.md（總覽）與 schema/entity/（各子類型）。overview#464（F6-5）。

碼與級別（沿用清單）：
  E1   四子類型不許有 cbdb_*／chgis_id／dila_*／translation／c_office_trans／cbdb_alt_names，
       external_ids 只許 wikidata_id（非 place 之 coords 亦在此）                      ERROR
  D1   dynasty primary_name 須在 SCHEMA〈規範朝代名完整枚舉〉內；dynasty 名全庫唯一      ERROR
  D2   dynasty parent_id 存在、是 dynasty、無環、深度≤3（上溯跳數）；
       子朝代 dates 落在上級之內（容差 1 年）                                          ERROR／WARN
  D3   dates 鍵按 subtype 放行；start≤end；整數；無 0 年；dynasty 有 period 而缺 start     ERROR／WARN
  R1   reign：dynasty_id 必填且指向 dynasty（缺而 ai_note 有說明則 WARN）、dates.start 必填、
       (primary_name, dynasty_id, start) 唯一、同朝同名年號區間不重疊、
       dates ⊂ dynasty.dates（容差 5 年，越界 WARN）、ruler.name 非空、
       ruler.entity_id 若有則為 people                                                ERROR／WARN
  A1   alt_names：type 在枚舉內、ambiguous 為 bool；帶 ambiguous 之名全庫至少 2 條聲稱
       （否則 WARN）；無 ambiguous 之 dynasty 別名在 dynasty 內全局唯一（ERROR）        ERROR／WARN
  O01–O05、O09–O12  官職，見各函數註；O06（CBDB 碼防重）已刪；O07 併入 V01；O08 併入 E1。
  P01–P11  地名，見各函數註；P05 併入 V01、P08 coords 單獨出碼；P10 沿革段之上級於該段年份內須存在（WARN）；P11 沿革段年份須為所掛朝代起訖覆蓋（WARN）。
  P12–P14  地名兩層（跨朝條 concept／朝代條 concrete）：P12 place_level 枚舉；P13 朝代條頂層 dynasty_ids 必填、
       各段不換名不換級、段之朝代不出頂層所掛；P14 上級同層（朝代條之上級須朝代條且朝代相交，跨朝條之上級須跨朝條）、
       concept_id 只許朝代條且須指跨朝條。place_level 缺省＝concept（舊「一地一條＋沿革」條）。
  I01–I12  官署（collective 且 collective_kind=官署，P3c 設計稿 §六／§十二，S 10-07 定）；
       I12 兼管官職條之 institution_ref（O14 第二步：`COL:` 占位一律 ERROR）。
       collective_kind 缺省＝未分，舊 collective 不受約束。
  V01  源檔出現 `_` 起首或 children／reigns／index_in_reign 等派生／反向欄位           ERROR
       （`_` 起首者仍由 check_v2 自身之 V01 報；本模塊只補非底線之派生名，並在新子類型內
       把 `_has_text`／`_has_collated` 之豁免收回。）
  N01–N03  人物籍貫 `native_place_entity_id`（people 可選；值為地名 Entity id；舊 `native_place` 自由文本照留）：
       N01  只許 people 有此欄；值須為非空字符串                                  ERROR
       N02  須指向本庫（或 --ref-root 之正式庫）中 subtype=place 的 Entity，不存在或非 place   ERROR
       N03  指向的地名是墓碑（有 merged_into）：只警告，提示跟 merged_into          WARN
  S01–S06  印章（seal，GUJI-538）：
       S01  seal_text（印文）非空、seal_kind 在枚舉內、primary_name 非空、description.sources 非空   ERROR
       S02  dynasty_ids 非空且各指 dynasty；start／end 為整數且 start ≤ end；                      ERROR
            seal_style／seal_form 若有須在枚舉內                                                 ERROR
       S03  owner_ids／institution_ids 各指本庫存在的 Entity（people／collective／office／reign 之外
            不得指 seal 與 dynasty）；指墓碑 WARN                                               ERROR／WARN
       S04  appears_in ≤20 條、ref_type ∈ Book／Work、id 存在於本庫（或 --ref-root）對應目錄；     ERROR
            不得重複
       S05  images 每項有 file／credit／license／source_url（≤8、license 閉集、file 路徑規範）；S06 file 在 book-index-asset 存在；禁人物／朝代／地名／年號專屬欄位                         ERROR
  K01–K09  出版社／刻書機構（publisher，GUJI-539 v3；官署／書院一律 collective，不入此）：
       K01  publisher_kind 在 6 值內（家刻｜坊刻｜寺觀｜藩府｜現代出版社｜未分）、kind_also／status 枚舉、
            primary_name 非空、description.sources 非空                                          ERROR
       K02  古代類 dynasty_ids 必填且各指 dynasty；現代出版社不得寫 dynasty_ids                       ERROR
       K03  start／end 為非 0 整數且 start ≤ end                                                  ERROR
       K04  locations[]：{place_id?, name, start?, end?, note?}，place_id 須指 place；墓碑 WARN      ERROR／WARN
       K05  owners[]={id, role}（id 指 people／collective）；parent_id 指 publisher／collective、
            不自指、publisher 上級鏈無環；指墓碑 WARN                                             ERROR／WARN
       K06  禁欄（predecessors、publisher_sub、legal_name、representative、books、其他子類型專屬欄）  ERROR
       K07  external_ids 只許 wikidata_id／isbn_publisher_code                                   ERROR
       K08  寫了 start／end 而缺 dates_basis                                                     WARN
       K09  同名＋同類別＋同朝代集之 publisher 重複                                               WARN
  級別 INFO：P09 同名異地清單，不計入 ERROR／WARN。

口徑（S 預審）：上下級區間不合（戰國止年晚於東周、北朝起年早於南北朝）、年號越出所屬朝代區間，
一律 WARN，不是 ERROR。

用法：  problems = scan(root)  →  [(relpath, id, subtype, code, level, field, detail)]
        check_record(rec, reg)  →  單條（局部＋引用）檢查；全庫唯一性等見 check_global(reg)。
"""
import glob
import json
import os
import re

NEW_SUBTYPES = ("dynasty", "reign", "office", "place", "seal", "publisher")
ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

PERIODS = {"pre-qin", "qin-han", "three-kingdoms", "jin", "nanbeichao", "sui-tang",
           "five-dynasties", "song", "liao-jin-yuan", "ming", "qing", "modern"}

# alt_names.type 枚舉（SCHEMA〈alt_names.type 枚舉〉；新增十項依 #464 清單 §三·1）
ALT_TYPES = {
    "字", "號", "諡號", "賜號", "別名", "常用名", "簡體", "行第", "廟號", "訛名", "異體", "封爵", "俗姓",
    "簡稱", "合稱", "避諱", "別稱", "雅稱", "全稱", "異寫", "舊稱", "異稱", "今名",
    "堂號", "牌記名",   # publisher 用（GUJI-539 v3）
}
ALT_TYPES_NEW_ONLY = ALT_TYPES  # 新子類型暫與全表同；人物之長尾罕見值不在此限（由 qa_entity 判 WARN）

# 各子類型可用 dates 鍵（清單 §三·3）；office／place 不用 dates
DATES_KEYS = {
    "people": {"birth", "death", "floruit", "chinese", "basis"},
    "dynasty": {"start", "end", "basis", "chinese"},
    "reign": {"start", "end", "basis", "chinese"},
    "office": set(),
    "place": set(),
    "seal": set(),
    "publisher": set(),
}
# 源檔不許寫之派生／反向欄（無底線者；`_` 起首者由 check_v2 V01 報）
DERIVED_NAMES = ("children", "reigns", "index_in_reign", "successors", "people", "holders",
                 "compounds", "ancestors", "span", "same_name", "concretes")
FORBIDDEN_TOP = ("translation", "c_office_trans", "cbdb_alt_names")
FORBIDDEN_PREFIXES = ("cbdb_", "dila_", "chgis")

OFFICE_LEVELS = {"concept", "concrete"}
OFFICE_CLASSES = {"職事官", "差遣", "散官", "階官", "加官", "貼職", "寄祿官", "祠祿官", "勳", "爵",
                  "本官", "試秩", "憲官", "兼職差遣", "未詳"}
QUALIFIER_KINDS = {"institution", "place", "mode", "mode+institution"}
CONCEPT_FORBIDDEN = ("dynasty_ids", "rank", "salary", "office_class", "base_office_id", "parent_id")
# 官署（collective_kind=官署）
COLLECTIVE_KINDS = {"官署", "書院學校", "館局", "民間", "未分"}
INST_LEVELS = {"concept", "concrete", "group"}
INST_CONCRETE_ONLY = ("dynasty_ids", "function", "superiors", "start", "end", "basis")
INST_OFFICE_FIELDS = ("office_level", "office_class", "rank", "salary", "base_office_id", "qualifier",
                      "institution_ref")
INST_DERIVED = ("subordinates", "members", "offices", "_subordinates", "_members", "_children", "_offices")
INST_WARN_RANGE = 5
# O14 第二步（替換 PR draft#97 合入後，S 10-07 收緊）：凍結名單清空，`COL:` 占位一律 ERROR。
COL_PLACEHOLDERS = frozenset()
PLACE_LEVELS = {"國", "郡", "州", "府", "軍", "監", "路", "道", "省", "縣", "廳", "都"}
MODERN_RELATIONS = {"同名同地", "治所今在", "轄域約當", "沿用其名而異地", "無對應"}
PRED_KINDS = {"析出", "並入", "改置"}
PLACE_TIERS = {"concept", "concrete"}   # place_level：跨朝條／朝代條；缺省＝concept
MAX_DYNASTY_DEPTH = 3
PLACE_END_MAX = 1912


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def nonempty_str(v):
    return isinstance(v, str) and bool(v.strip())


def load_canonical_dynasties(schema_path=None):
    """讀 schema/common.md〈规范朝代名全表〉與〈域外朝代〉兩表之首列（本腳本所在倉之 schema，非 --root 之倉）。
    D1 之枚舉只此一份：權威在 schema/common.md（overview#496）。讀不到或解析為空即拋 RuntimeError——
    不再靜默跳過 D1（吻合度報告 §六-14）。"""
    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "schema", "common.md")
    try:
        txt = open(schema_path, encoding="utf-8").read()
    except OSError as e:
        raise RuntimeError("D1 讀不到朝代規範名表：%s（%s）" % (schema_path, e))

    def table(head, nxt):
        a = txt.find(head)
        b = txt.find(nxt, a + len(head)) if a >= 0 else -1
        if a < 0 or b < 0:
            raise RuntimeError("D1 在 %s 找不到表〈%s〉" % (schema_path, head.strip("# ")))
        names = set()
        for ln in txt[a:b].splitlines():
            if not ln.startswith("|") or ln.startswith("|-"):
                continue
            cell = ln.split("|")[1].strip()
            if cell and cell != "规范名":
                names.add(cell)
        return names

    names = table("#### 规范朝代名全表", "#### 域外朝代") | table("#### 域外朝代", "#### 需拆分的歧义朝代")
    if not names:
        raise RuntimeError("D1 朝代規範名表解析為空：%s" % schema_path)
    return names


SEAL_IMG_MAX = 8
SEAL_IMG_LICENSES = ("公有領域", "CC0")


def _find_asset_root():
    """book-index-asset 本地根：環境變量 BOOK_INDEX_ASSET_ROOT，或與本倉並列之 ../book-index-asset；都無則 None。"""
    c = [os.environ.get("BOOK_INDEX_ASSET_ROOT", "")]
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    c.append(os.path.join(os.path.dirname(here), "book-index-asset"))
    for x in c:
        if x and os.path.isdir(os.path.join(x, "entity")):
            return x
    return None


class Registry:
    """全庫 Entity 之輕量索引：id → (subtype, 記錄)。只留新子類型之整條記錄，其餘只留 subtype。"""

    def __init__(self):
        self.sub = {}      # id -> subtype
        self.rec = {}      # id -> record（僅 NEW_SUBTYPES）
        self.path = {}     # id -> relpath
        self.roots = []     # 參與索引之倉根（供 Book／Work 存在性查詢）
        self._bw = {}       # (ref_type, id) 查詢快取：ref_type -> {id}
        self.asset_root = _find_asset_root()   # book-index-asset 根；無則 S06 跳過（不硬依賴另一倉）
        self.dyn_name = {}  # dynasty id -> primary_name（草稿／正式庫朝代 ID 為兩套，跨倉按名字比，GUJI-528）

    @classmethod
    def from_root(cls, root, ref_roots=()):
        """ref_roots：只讀參照倉（草稿庫查時指正式庫），其 Entity 只供引用解析（如 dynasty_ids 指正式 id）；
        同 id 以 root 為準。跨條目之全庫檢查（check_global）應另用不帶 ref_roots 之索引，免把兩倉同名條當重複。"""
        reg = cls()
        reg.roots = list(ref_roots) + [root]
        for r in list(ref_roots) + [root]:
            for f in glob.glob(os.path.join(r, "Entity", "**", "*.json"), recursive=True):
                try:
                    d = json.load(open(f, encoding="utf-8"))
                except (ValueError, UnicodeDecodeError):
                    continue
                if not (isinstance(d, dict) and d.get("id") and d.get("type") == "entity"):
                    continue
                reg.add(d, os.path.relpath(f, r).replace(os.sep, "/"))
        return reg

    def add(self, d, relpath=""):
        i = d.get("id")
        st = d.get("subtype") or "people"
        self.sub[i] = st
        self.path[i] = relpath
        if st == "dynasty" and d.get("primary_name"):
            self.dyn_name[i] = d["primary_name"]
        if st in NEW_SUBTYPES or st == "collective":
            self.rec[i] = d

    def dyn_overlap(self, a, b):
        """兩組 dynasty_ids 是否相交：ID 相交，或（跨倉 ID 兩套時）朝代主名相交。"""
        a, b = set(a or []), set(b or [])
        if a & b:
            return True
        na = {self.dyn_name[x] for x in a if x in self.dyn_name}
        nb = {self.dyn_name[x] for x in b if x in self.dyn_name}
        return bool(na & nb)

    def has_record(self, ref_type, i):
        """Book／Work 記錄檔是否存在（按 {id}-*.json 檔名，各倉根任一有即可）。"""
        if ref_type not in self._bw:
            ids = set()
            for r in self.roots:
                for f in glob.glob(os.path.join(r, ref_type, "*", "*", "*", "*.json")):
                    ids.add(os.path.basename(f).split("-", 1)[0].split(".json")[0])
            self._bw[ref_type] = ids
        return i in self._bw[ref_type]

    def is_inst(self, i):
        r = self.rec.get(i) or {}
        return r.get("subtype") == "collective" and r.get("collective_kind") == "官署"

    def of(self, subtype):
        return [(i, r) for i, r in self.rec.items() if r.get("subtype") == subtype]


# ----------------------------------------------------------------------------- 局部檢查

def _dates_problems(rec, st):
    out = []
    dt = rec.get("dates")
    if dt is None:
        return out
    if not isinstance(dt, dict):
        return [("D3", ERROR, "dates", "非物件")]
    allowed = DATES_KEYS.get(st, set())
    if st in ("office", "place", "seal", "publisher"):
        return [("D3", ERROR, "dates", "%s 不用 dates（起訖在 start／end 或沿革項）" % st)]
    for k in dt:
        if k not in allowed:
            out.append(("D3", ERROR, "dates." + k, "%s 不放行此鍵" % st))
    if st in ("dynasty", "reign"):
        for k in ("start", "end"):
            v = dt.get(k)
            if v is None:
                continue
            if not is_int(v):
                out.append(("D3", ERROR, "dates." + k, "非整數：%r" % (v,)))
            elif v == 0:
                out.append(("D3", ERROR, "dates." + k, "無 0 年"))
        s, e = dt.get("start"), dt.get("end")
        if is_int(s) and is_int(e) and s > e:
            out.append(("D3", ERROR, "dates", "start > end：%s > %s" % (s, e)))
    return out


def _alt_problems(rec):
    out = []
    alts = rec.get("alt_names")
    if alts is None:
        return out
    if not isinstance(alts, list):
        return [("A1", ERROR, "alt_names", "非數組")]
    for i, a in enumerate(alts):
        f = "alt_names[%d]" % i
        if not isinstance(a, dict) or not nonempty_str(a.get("name")):
            out.append(("A1", ERROR, f, "缺 name"))
            continue
        t = a.get("type")
        if t is not None and t not in ALT_TYPES_NEW_ONLY:
            out.append(("O12", ERROR, f + ".type", "不在枚舉：%r" % (t,)))
        if "ambiguous" in a and not isinstance(a["ambiguous"], bool):
            out.append(("A1", ERROR, f + ".ambiguous", "非布爾：%r" % (a["ambiguous"],)))
    return out


def _forbidden_problems(rec, st):
    out = []
    ext = rec.get("external_ids")
    if ext is not None:
        if not isinstance(ext, dict):
            out.append(("E1", ERROR, "external_ids", "非物件"))
        else:
            for k, v in ext.items():
                if k == "isbn_publisher_code" and st == "publisher":
                    if not nonempty_str(v):
                        out.append(("K07", ERROR, "external_ids.isbn_publisher_code", "須非空字符串：%r" % (v,)))
                elif k != "wikidata_id":
                    out.append(("E1", ERROR, "external_ids." + k, "新子類型只許 wikidata_id"
                                + ("（publisher 另許 isbn_publisher_code）" if st == "publisher" else "")))
                elif v is not None and not (isinstance(v, str) and re.match(r"^Q\d+$", v)):
                    out.append(("E1", ERROR, "external_ids.wikidata_id", "須 Q\\d+：%r" % (v,)))
    for k in rec:
        if k in FORBIDDEN_TOP or k.startswith(FORBIDDEN_PREFIXES):
            out.append(("E1", ERROR, k, "新子類型禁此欄"))
        if k in DERIVED_NAMES:
            out.append(("V01", ERROR, k, "派生／反向欄位不入源檔"))
        if k.startswith("_"):
            # `_` 起首：check_v2 自身之 V01 已報（豁免 _has_text／_has_collated）；新子類型收回豁免
            if k in ("_has_text", "_has_collated"):
                out.append(("V01", ERROR, k, "新子類型不留此豁免欄"))
    if "coords" in rec and st != "place":
        out.append(("E1", ERROR, "coords", "只 place 預留，且第一期禁出現"))
    return out


def _check_dynasty(rec, reg):
    out = []
    pid = rec.get("parent_id")
    dt = rec.get("dates") or {}
    if pid is not None:
        if reg.sub.get(pid) != "dynasty":
            out.append(("D2", ERROR, "parent_id", "不存在或非 dynasty：%r" % (pid,)))
        else:
            seen, cur, hops = {rec["id"]}, pid, 1
            while True:
                if cur in seen:
                    out.append(("D2", ERROR, "parent_id", "成環"))
                    break
                seen.add(cur)
                nxt = (reg.rec.get(cur) or {}).get("parent_id")
                if nxt is None or reg.sub.get(nxt) != "dynasty":
                    break
                cur, hops = nxt, hops + 1
            else:
                pass
            if hops > MAX_DYNASTY_DEPTH and not any(c == "D2" and "環" in d for c, _, _, d in out):
                out.append(("D2", ERROR, "parent_id", "深度 %d > %d" % (hops, MAX_DYNASTY_DEPTH)))
            par = (reg.rec.get(pid) or {}).get("dates") or {}
            s, e = dt.get("start"), dt.get("end")
            ps, pe = par.get("start"), par.get("end")
            if is_int(s) and is_int(ps) and s < ps - 1:
                out.append(("D2", WARN, "dates.start", "起 %d 早於上級 %s 之起 %d（容差 1 年）" %
                            (s, (reg.rec[pid]).get("primary_name"), ps)))
            if is_int(pe) and (e is None and is_int(s) or is_int(e)) and (e is None or e > pe + 1):
                out.append(("D2", WARN, "dates.end", "止 %s 晚於上級 %s 之止 %d（容差 1 年）" %
                            (e, (reg.rec[pid]).get("primary_name"), pe)))
    per = rec.get("period")
    if per is not None and per not in PERIODS:
        out.append(("D3", ERROR, "period", "非現有 period slug：%r" % (per,)))
    if per is not None and not is_int(dt.get("start")):
        out.append(("D3", WARN, "dates.start", "中國朝代（有 period）應有 start"))
    if not nonempty_str(rec.get("primary_name")):
        out.append(("D1", ERROR, "primary_name", "缺"))
    return out


def _span(rec):
    dt = rec.get("dates") or {}
    return dt.get("start"), dt.get("end")


def _check_reign(rec, reg):
    out = []
    did = rec.get("dynasty_id")
    dyn = reg.rec.get(did) if did else None
    if did is None:
        if nonempty_str(rec.get("ai_note")):
            out.append(("R1", WARN, "dynasty_id", "缺，ai_note 已說明"))
        else:
            out.append(("R1", ERROR, "dynasty_id", "必填（所屬政權無條目時須在 ai_note 說明）"))
    elif reg.sub.get(did) != "dynasty":
        out.append(("R1", ERROR, "dynasty_id", "不存在或非 dynasty：%r" % (did,)))
    ruler = rec.get("ruler")
    if not (isinstance(ruler, dict) and nonempty_str(ruler.get("name"))):
        out.append(("R1", ERROR, "ruler.name", "必填"))
    elif ruler.get("entity_id") is not None:
        eid = ruler["entity_id"]
        if reg.sub.get(eid) != "people":
            out.append(("R1", ERROR, "ruler.entity_id", "須為 people 條：%r" % (eid,)))
    s, e = _span(rec)
    if not is_int(s):
        out.append(("R1", ERROR, "dates.start", "必填整數"))
    elif dyn is not None:
        ds, de = _span(dyn)
        if is_int(ds) and s < ds - 5:
            out.append(("R1", WARN, "dates.start", "起 %d 早於朝代 %s 之起 %d（容差 5 年）" %
                        (s, dyn.get("primary_name"), ds)))
        if is_int(de):
            end = e if is_int(e) else s
            if end > de + 5:
                out.append(("R1", WARN, "dates.end", "止 %d 晚於朝代 %s 之止 %d（容差 5 年）" %
                            (end, dyn.get("primary_name"), de)))
    return out


def _chain_cycle(start, nxt_of):
    seen, cur = {start}, nxt_of(start)
    while cur is not None:
        if cur in seen:
            return True
        seen.add(cur)
        cur = nxt_of(cur)
    return False


def _check_office(rec, reg):
    out = []
    if rec.get("merged_into"):   # 墓碑只留 _common.md〈merged_into〉規定的欄位，不查 office 欄位
        return out
    lvl = rec.get("office_level")
    if lvl not in OFFICE_LEVELS:
        out.append(("O01", ERROR, "office_level", "須為 concept／concrete：%r" % (lvl,)))
        return out
    pid = rec.get("parent_id")
    if lvl == "concept":
        for k in CONCEPT_FORBIDDEN:
            if k in rec:
                out.append(("O02" if k != "parent_id" else "O04", ERROR, k, "概念條不得有"))
        return out
    # 具體條
    dids = rec.get("dynasty_ids")
    if not (isinstance(dids, list) and dids):
        out.append(("O02", ERROR, "dynasty_ids", "具體條必有非空數組"))
        dids = []
    for d in dids:
        if reg.sub.get(d) != "dynasty":
            out.append(("O02", ERROR, "dynasty_ids", "不存在或非 dynasty：%r" % (d,)))
    for k in ("function", "basis"):
        if not nonempty_str(rec.get(k)):
            out.append(("O02", ERROR, k, "具體條必填"))
    oc = rec.get("office_class")
    if oc is not None and oc not in OFFICE_CLASSES:
        out.append(("O03", ERROR, "office_class", "不在枚舉：%r" % (oc,)))
    if pid is not None and (reg.sub.get(pid) != "office" or
                            (reg.rec.get(pid) or {}).get("office_level") != "concept"):
        out.append(("O04", ERROR, "parent_id", "須指向 office 概念條：%r" % (pid,)))
    s, e = rec.get("start"), rec.get("end")
    for k, v in (("start", s), ("end", e)):
        if v is not None and not is_int(v):
            out.append(("O09", ERROR, k, "非整數：%r" % (v,)))
    if is_int(s) and is_int(e) and s > e:
        out.append(("O09", ERROR, "start/end", "start > end：%s > %s" % (s, e)))
    bid = rec.get("base_office_id")
    q = rec.get("qualifier")
    if bid is not None:
        base = reg.rec.get(bid)
        if bid == rec["id"]:
            out.append(("O05", ERROR, "base_office_id", "自指"))
        elif base is None or base.get("subtype") != "office":
            out.append(("O05", ERROR, "base_office_id", "不存在或非 office：%r" % (bid,)))
        else:
            if base.get("office_level") == "concept":
                if not nonempty_str(rec.get("ai_note")):
                    out.append(("O05", WARN, "base_office_id", "指向概念條而 ai_note 未標注"))
            else:
                if _chain_cycle(rec["id"], lambda x: (reg.rec.get(x) or {}).get("base_office_id")):
                    out.append(("O05", ERROR, "base_office_id", "成環"))
                bd = base.get("dynasty_ids") or []
                if dids and bd and not reg.dyn_overlap(dids, bd):
                    out.append(("O05", ERROR, "dynasty_ids", "複合條與其 base 之 dynasty_ids 不相交"))
        if not isinstance(q, dict):
            out.append(("O05", ERROR, "qualifier", "有 base_office_id 則 qualifier 必有"))
    if q is not None:
        if not isinstance(q, dict) or q.get("kind") not in QUALIFIER_KINDS or not nonempty_str(q.get("name")):
            out.append(("O05", ERROR, "qualifier", "kind 須在枚舉內、name 非空：%r" % (q,)))
    out += _institution_ref_problems(rec, reg, dids)
    for i, a in enumerate(rec.get("alt_names") or []):
        if isinstance(a, dict) and a.get("type") == "簡稱" and nonempty_str(a.get("name")) and len(a["name"]) <= 2:
            out.append(("O10", WARN, "alt_names[%d]" % i, "簡稱 %r 長度 ≤2，須確認不與他概念重名" % a["name"]))
    return out


def _institution_ref_problems(rec, reg, dids):
    """I12：官職具體條之 institution_ref。`COL:<名>` 占位只許凍結名單內（O14 第一步，WARN）；
    真 id 須為官署條；指 concrete 須與官職 dynasty_ids 相交；指 concept 須 ai_note 標「待補」；
    指 group 而官職名含部名 WARN。id 不在本庫（草稿指正式庫）時只 WARN，由 build 之懸空檢查兜底。"""
    out = []
    ref = rec.get("institution_ref")
    if ref is None:
        return out
    if not nonempty_str(ref):
        return [("I12", ERROR, "institution_ref", "非空字符串：%r" % (ref,))]
    if ref.startswith("COL:"):
        name = ref[4:].strip()
        if name in COL_PLACEHOLDERS:
            out.append(("I12", WARN, "institution_ref", "占位 %r 待換真 id" % ref))
        else:
            out.append(("I12", ERROR, "institution_ref", "占位 %r：官署條已建，須指真 id（O14 第二步，新官署先建條）" % ref))
        return out
    if ref not in reg.sub:
        return [("I12", WARN, "institution_ref", "%r 不在本庫（若指正式庫須確認存在）" % ref)]
    if not reg.is_inst(ref):
        return [("I12", ERROR, "institution_ref", "須指 collective_kind=官署 之條：%r" % ref)]
    t = reg.rec[ref]
    lv = t.get("institution_level")
    if lv == "concrete":
        td = t.get("dynasty_ids") or []
        if dids and td and not reg.dyn_overlap(dids, td):
            out.append(("I12", ERROR, "institution_ref", "所指官署 %s 之朝代與官職不相交" % t.get("primary_name")))
    elif lv == "concept":
        if "待補" not in (rec.get("ai_note") or ""):
            out.append(("I12", WARN, "institution_ref", "指概念條而 ai_note 未標「待補具體條」"))
    elif lv == "group":
        pn = rec.get("primary_name") or ""
        if re.search(r"[吏戶禮兵刑工]部", pn):
            out.append(("I12", WARN, "institution_ref", "官名含部名而指合稱條，宜指該部同朝具體條"))
    return out


def _check_institution(rec, reg):
    """I01–I11（局部＋引用）。只對 collective_kind=官署。"""
    out = []
    i = rec["id"]
    lvl = rec.get("institution_level")
    if lvl not in INST_LEVELS:
        return [("I01", ERROR, "institution_level", "官署須為 concept／concrete／group：%r" % (lvl,))]
    # I08：外部 id、官職專有欄；I11：派生欄
    for c, lv, f, d in _forbidden_problems(rec, "collective"):
        out.append(("I08" if c == "E1" else ("I11" if c == "V01" else c), lv, f, d))
    for k in INST_OFFICE_FIELDS:
        if k in rec:
            out.append(("I08", ERROR, k, "官署條不得有官職專有欄"))
    for k in INST_DERIVED:
        if k in rec and not k.startswith("_"):
            out.append(("I11", ERROR, k, "派生欄不入源檔"))
    pid = rec.get("parent_id")
    if lvl in ("concept", "group"):
        for k in INST_CONCRETE_ONLY:
            if k in rec:
                out.append(("I02", ERROR, k, "%s 條不得有" % ("概念" if lvl == "concept" else "合稱")))
        if pid is not None:
            out.append(("I03", ERROR, "parent_id", "概念條、合稱條不得有"))
        if lvl == "group" and "group_ids" in rec:
            out.append(("I02", ERROR, "group_ids", "合稱條不得有（合稱不嵌套）"))
        if not (nonempty_str(rec.get("description")) or
                (isinstance(rec.get("description"), dict) and nonempty_str(rec["description"].get("text")))):
            out.append(("I02", ERROR, "description", "概念條、合稱條必填"))
    dids = []
    if lvl == "concrete":
        dids = rec.get("dynasty_ids")
        if not (isinstance(dids, list) and dids):
            out.append(("I02", ERROR, "dynasty_ids", "具體條必有非空數組"))
            dids = []
        for d in dids:
            if reg.sub.get(d) != "dynasty":
                out.append(("I02", ERROR, "dynasty_ids", "不存在或非 dynasty：%r" % (d,)))
        for k in ("function", "basis"):
            if not nonempty_str(rec.get(k)):
                out.append(("I02", ERROR, k, "具體條必填"))
        if "待核" in (rec.get("basis") or ""):
            out.append(("I02", ERROR, "basis", "不得含「待核」"))
        if pid is not None and not (reg.is_inst(pid) and reg.rec[pid].get("institution_level") == "concept"):
            out.append(("I03", ERROR, "parent_id", "須指向官署概念條：%r" % (pid,)))
        # I04 superiors
        sup = rec.get("superiors")
        if sup is not None:
            if not isinstance(sup, list):
                out.append(("I04", ERROR, "superiors", "非數組"))
                sup = []
            for k, x in enumerate(sup):
                f = "superiors[%d]" % k
                sid = x.get("id") if isinstance(x, dict) else None
                if sid == i:
                    out.append(("I04", ERROR, f, "自指"))
                    continue
                if not (reg.is_inst(sid) and reg.rec[sid].get("institution_level") == "concrete"):
                    out.append(("I04", ERROR, f, "須指官署具體條：%r" % (sid,)))
                    continue
                sd = reg.rec[sid].get("dynasty_ids") or []
                if dids and sd and not reg.dyn_overlap(dids, sd):
                    out.append(("I04", WARN, f, "上級 %s 與本條朝代不相交" % reg.rec[sid].get("primary_name")))
                for kk in ("start", "end"):
                    if kk in x and not is_int(x[kk]):
                        out.append(("I04", ERROR, f + "." + kk, "非整數：%r" % (x[kk],)))
                if is_int(x.get("start")) and is_int(x.get("end")) and x["start"] > x["end"]:
                    out.append(("I04", ERROR, f, "start > end"))
            # 環：沿任一 superiors 上溯
            stack, seen = [x.get("id") for x in sup if isinstance(x, dict)], set()
            while stack:
                x = stack.pop()
                if x == i:
                    out.append(("I04", ERROR, "superiors", "隸屬成環"))
                    break
                if x in seen or x not in reg.rec:
                    continue
                seen.add(x)
                stack.extend(y.get("id") for y in (reg.rec[x].get("superiors") or []) if isinstance(y, dict))
        # I06 起訖
        s, e = rec.get("start"), rec.get("end")
        for k, v in (("start", s), ("end", e)):
            if v is not None and not is_int(v):
                out.append(("I06", ERROR, k, "非整數：%r" % (v,)))
            elif v == 0:
                out.append(("I06", ERROR, k, "無 0 年"))
        if is_int(s) and is_int(e) and s > e:
            out.append(("I06", ERROR, "start/end", "start > end：%s > %s" % (s, e)))
        spans = [_span(reg.rec[d]) for d in dids if d in reg.rec]
        lo = [a for a, _ in spans if is_int(a)]
        hi = [b for _, b in spans if is_int(b)]
        if is_int(s) and lo and s < min(lo) - INST_WARN_RANGE:
            out.append(("I06", WARN, "start", "早於所屬朝代（容差 %d 年）" % INST_WARN_RANGE))
        if is_int(e) and hi and e > max(hi) + INST_WARN_RANGE:
            out.append(("I06", WARN, "end", "晚於所屬朝代（容差 %d 年）" % INST_WARN_RANGE))
    # I05 group_ids
    gids = rec.get("group_ids")
    if gids is not None and lvl != "group":
        if not isinstance(gids, list):
            out.append(("I05", ERROR, "group_ids", "非數組"))
            gids = []
        for g in gids:
            if not (reg.is_inst(g) and reg.rec[g].get("institution_level") == "group"):
                out.append(("I05", ERROR, "group_ids", "須指合稱條：%r" % (g,)))
        if lvl == "concrete" and pid and set(gids) & set((reg.rec.get(pid) or {}).get("group_ids") or []):
            out.append(("I05", WARN, "group_ids", "與其概念條重複掛同一合稱"))
    # I09
    if "location_id" in rec:
        out.append(("I09", ERROR, "location_id", "第一期禁出現（place 無條目）"))
    if "succeeds" in rec:
        out.append(("I09", WARN, "succeeds", "第一期只留字段位，不填"))
    return out


def _uncovered(s, e, parent_hist):
    """[s, e] 中不被上級任一沿革段覆蓋之區間（端點相接算覆蓋；s／e 缺則不查）。"""
    if not (is_int(s) and is_int(e)):
        return []
    segs = sorted((h.get("start") if is_int(h.get("start")) else float("-inf"),
                   h.get("end") if is_int(h.get("end")) else float("inf"))
                  for h in parent_hist if isinstance(h, dict))
    gaps, cur = [], s
    for a, b in segs:
        if b < cur:
            continue
        if a > cur:
            gaps.append((cur, min(a, e)))
        cur = max(cur, b)
        if cur >= e:
            break
    if cur < e:
        gaps.append((cur, e))
    return [(a, b) for a, b in gaps if a < b]


SEAL_KINDS = ("官印", "私印", "鑒藏印", "齋館印", "其他")
SEAL_STYLES = ("朱文", "白文", "朱白相間")
SEAL_FORMS = ("方", "圓", "橢圓", "長方", "異形")
SEAL_REF_MAX = 20
SEAL_FORBIDDEN = ("dynasty", "dynasty_basis", "period", "period_basis", "native_place", "native_place_basis",
                  "native_place_entity_id", "title_or_office", "name_basis", "collective_kind",
                  "institution_level", "superiors", "group_ids", "parent_id", "function", "basis", "succeeds",
                  "dynasty_id", "ruler", "office_level", "office_class", "rank", "salary", "institution_ref",
                  "base_office_id", "qualifier", "history", "modern", "predecessors", "dates")


def _check_seal(rec, reg):
    out = []
    if not nonempty_str(rec.get("primary_name")):
        out.append(("S01", ERROR, "primary_name", "缺"))
    if not nonempty_str(rec.get("seal_text")):
        out.append(("S01", ERROR, "seal_text", "印文必填且非空"))
    if rec.get("seal_kind") not in SEAL_KINDS:
        out.append(("S01", ERROR, "seal_kind", "不在枚舉：%r" % (rec.get("seal_kind"),)))
    desc = rec.get("description")
    if not (isinstance(desc, dict) and isinstance(desc.get("sources"), list) and desc["sources"]):
        out.append(("S01", ERROR, "description.sources", "印章條須有來源"))
    if rec.get("seal_style") is not None and rec["seal_style"] not in SEAL_STYLES:
        out.append(("S02", ERROR, "seal_style", "不在枚舉：%r" % (rec["seal_style"],)))
    if rec.get("seal_form") is not None and rec["seal_form"] not in SEAL_FORMS:
        out.append(("S02", ERROR, "seal_form", "不在枚舉：%r" % (rec["seal_form"],)))
    dids = rec.get("dynasty_ids")
    if not (isinstance(dids, list) and dids):
        out.append(("S02", ERROR, "dynasty_ids", "必有非空數組"))
        dids = []
    for d in dids:
        if reg.sub.get(d) != "dynasty":
            out.append(("S02", ERROR, "dynasty_ids", "不存在或非 dynasty：%r" % (d,)))
    s, e = rec.get("start"), rec.get("end")
    for k, v in (("start", s), ("end", e)):
        if v is not None and not is_int(v):
            out.append(("S02", ERROR, k, "非整數：%r" % (v,)))
    if is_int(s) and is_int(e) and s > e:
        out.append(("S02", ERROR, "start", "start > end：%s > %s" % (s, e)))
    for f in ("owner_ids", "institution_ids"):
        v = rec.get(f)
        if v is None:
            continue
        if not (isinstance(v, list) and v and all(nonempty_str(x) for x in v)):
            out.append(("S03", ERROR, f, "須非空 id 數組（不寫裸字符串名）"))
            continue
        for x in v:
            st = reg.sub.get(x)
            if st is None:
                out.append(("S03", ERROR, f, "id 不存在：%r" % (x,)))
            elif st not in (("people", "collective", "office") if f == "owner_ids" else ("collective",)):
                out.append(("S03", ERROR, f, "%s 不得指 %s：%r" % (f, st, x)))
            elif (reg.rec.get(x) or {}).get("merged_into"):
                out.append(("S03", WARN, f, "%r 是墓碑，請改指 merged_into" % (x,)))
    ai = rec.get("appears_in")
    if ai is not None:
        if not isinstance(ai, list):
            out.append(("S04", ERROR, "appears_in", "非數組"))
        else:
            if len(ai) > SEAL_REF_MAX:
                out.append(("S04", ERROR, "appears_in", "本期只作代表例，≤%d 條" % SEAL_REF_MAX))
            seen = set()
            for i, it in enumerate(ai):
                f = "appears_in[%d]" % i
                if not isinstance(it, dict) or it.get("ref_type") not in ("Book", "Work") or not nonempty_str(it.get("id")):
                    out.append(("S04", ERROR, f, "須 {ref_type: Book|Work, id}"))
                    continue
                key = (it["ref_type"], it["id"])
                if key in seen:
                    out.append(("S04", ERROR, f, "重複：%r" % (key,)))
                seen.add(key)
                if not reg.has_record(it["ref_type"], it["id"]):
                    out.append(("S04", ERROR, f + ".id", "%s 不存在：%r" % (it["ref_type"], it["id"])))
    imgs = rec.get("images")
    if imgs is not None:
        if not isinstance(imgs, list) or not imgs:
            out.append(("S05", ERROR, "images", "須非空數組"))
        else:
            if len(imgs) > SEAL_IMG_MAX:
                out.append(("S05", ERROR, "images", "每條 ≤%d 張" % SEAL_IMG_MAX))
            rid = rec.get("id") or ""
            for i, it in enumerate(imgs):
                f = "images[%d]" % i
                if not isinstance(it, dict) or not all(nonempty_str(it.get(k)) for k in ("file", "credit", "license", "source_url")):
                    out.append(("S05", ERROR, f, "須有 file／credit／license／source_url"))
                    continue
                if it["license"] not in SEAL_IMG_LICENSES:
                    out.append(("S05", ERROR, f + ".license", "不在 %s：%r" % ("／".join(SEAL_IMG_LICENSES), it["license"])))
                if not it["source_url"].startswith(("http://", "https://")):
                    out.append(("S05", ERROR, f + ".source_url", "須為 http(s) 網址"))
                fp = it["file"]
                want = "entity/%s/%s/%s/%s/" % (rid[-3:-2], rid[-2:-1], rid[-1:], rid)
                if not (fp.startswith(want) and re.fullmatch(r"[0-9]+\.webp", fp[len(want):])):
                    out.append(("S05", ERROR, f + ".file", "須為 %s{序號}.webp（相對 book-index-asset）：%r" % (want, fp)))
                    continue
                ar = reg.asset_root
                if ar and not os.path.isfile(os.path.join(ar, fp)):
                    out.append(("S06", ERROR, f + ".file", "book-index-asset 中無此文件：%r" % (fp,)))
    for k in SEAL_FORBIDDEN:
        if k in rec:
            out.append(("S05", ERROR, k, "seal 不用此欄"))
    return out

PUBLISHER_KINDS = ("家刻", "坊刻", "寺觀", "藩府", "現代出版社", "未分")
PUBLISHER_STATUS = ("存續", "撤併", "停業", "未詳")
PUBLISHER_LOC_KEYS = {"place_id", "name", "start", "end", "note"}
PUBLISHER_OWNER_ROLES_HINT = ("主人", "創辦", "主持", "經營", "督刻")   # 開放詞表，不在內只提示不報
PUBLISHER_FORBIDDEN = ("dynasty", "dynasty_basis", "period", "period_basis", "native_place", "native_place_basis",
                       "native_place_entity_id", "title_or_office", "collective_kind",
                       "institution_level", "superiors", "group_ids", "function", "basis", "succeeds",
                       "dynasty_id", "ruler", "office_level", "office_class", "rank", "salary", "institution_ref",
                       "base_office_id", "qualifier", "history", "modern", "dates",
                       "seal_text", "seal_kind", "owner_ids", "institution_ids", "appears_in", "images",
                       "predecessors", "publisher_sub", "legal_name", "representative", "books", "subordinates")


def _check_publisher(rec, reg):
    """publisher（出版社／刻書機構，GUJI-539 v3）。K01–K08；K09 在 check_global。"""
    out = []
    if not nonempty_str(rec.get("primary_name")):
        out.append(("K01", ERROR, "primary_name", "缺"))
    kind = rec.get("publisher_kind")
    if kind not in PUBLISHER_KINDS:
        out.append(("K01", ERROR, "publisher_kind", "不在枚舉（%s）：%r" % ("｜".join(PUBLISHER_KINDS), kind)))
    ka = rec.get("kind_also")
    if ka is not None:
        if not (isinstance(ka, list) and ka and all(x in PUBLISHER_KINDS for x in ka)):
            out.append(("K01", ERROR, "kind_also", "須非空數組且取值在 publisher_kind 枚舉內：%r" % (ka,)))
        elif kind in ka:
            out.append(("K01", ERROR, "kind_also", "不得含主類別 %r" % (kind,)))
    st = rec.get("status")
    if st is not None and st not in PUBLISHER_STATUS:
        out.append(("K01", ERROR, "status", "不在枚舉（%s）：%r" % ("｜".join(PUBLISHER_STATUS), st)))
    desc = rec.get("description")
    if not (isinstance(desc, dict) and isinstance(desc.get("sources"), list) and desc["sources"]):
        out.append(("K01", ERROR, "description.sources", "publisher 條須有 description 與非空來源"))
    # K02 dynasty_ids
    dids = rec.get("dynasty_ids")
    if kind == "現代出版社":
        if dids is not None:
            out.append(("K02", ERROR, "dynasty_ids", "現代出版社不得寫 dynasty_ids"))
    elif kind in PUBLISHER_KINDS:
        if not (isinstance(dids, list) and dids):
            out.append(("K02", ERROR, "dynasty_ids", "古代類必有非空數組"))
        else:
            for d in dids:
                if reg.sub.get(d) != "dynasty":
                    out.append(("K02", ERROR, "dynasty_ids", "不存在或非 dynasty：%r" % (d,)))
    # K03 start/end
    s, e = rec.get("start"), rec.get("end")
    for k, v in (("start", s), ("end", e)):
        if v is not None and not is_int(v):
            out.append(("K03", ERROR, k, "非整數：%r" % (v,)))
        elif v == 0:
            out.append(("K03", ERROR, k, "無 0 年"))
    if is_int(s) and is_int(e) and s > e:
        out.append(("K03", ERROR, "start", "start > end：%s > %s" % (s, e)))
    # K04 locations
    locs = rec.get("locations")
    if locs is not None:
        if not (isinstance(locs, list) and locs):
            out.append(("K04", ERROR, "locations", "須非空數組"))
        else:
            for i, it in enumerate(locs):
                f = "locations[%d]" % i
                if not isinstance(it, dict) or not nonempty_str(it.get("name")):
                    out.append(("K04", ERROR, f, "須物件且 name 非空"))
                    continue
                for k in it:
                    if k not in PUBLISHER_LOC_KEYS:
                        out.append(("K04", ERROR, f + "." + k, "不放行此鍵"))
                for k in ("start", "end"):
                    v = it.get(k)
                    if v is not None and (not is_int(v) or v == 0):
                        out.append(("K04", ERROR, f + "." + k, "須非 0 整數：%r" % (v,)))
                if is_int(it.get("start")) and is_int(it.get("end")) and it["start"] > it["end"]:
                    out.append(("K04", ERROR, f, "start > end"))
                pid = it.get("place_id")
                if pid is not None:
                    if reg.sub.get(pid) != "place":
                        out.append(("K04", ERROR, f + ".place_id", "不存在或非 place：%r" % (pid,)))
                    elif (reg.rec.get(pid) or {}).get("merged_into"):
                        out.append(("K04", WARN, f + ".place_id", "%r 是墓碑，請改指 merged_into" % (pid,)))
    # K05 owners / parent_id
    owners = rec.get("owners")
    if owners is not None:
        if not (isinstance(owners, list) and owners):
            out.append(("K05", ERROR, "owners", "須非空數組"))
        else:
            for i, it in enumerate(owners):
                f = "owners[%d]" % i
                if not isinstance(it, dict) or not nonempty_str(it.get("id")) or not nonempty_str(it.get("role")):
                    out.append(("K05", ERROR, f, "須 {id, role}，role 非空"))
                    continue
                for k in ("start", "end"):
                    v = it.get(k)
                    if v is not None and (not is_int(v) or v == 0):
                        out.append(("K05", ERROR, f + "." + k, "須非 0 整數：%r" % (v,)))
                x = it["id"]
                sx = reg.sub.get(x)
                if sx is None:
                    out.append(("K05", ERROR, f + ".id", "id 不存在：%r" % (x,)))
                elif sx not in ("people", "collective"):
                    out.append(("K05", ERROR, f + ".id", "owners 只指 people／collective，不得指 %s：%r" % (sx, x)))
                elif (reg.rec.get(x) or {}).get("merged_into"):
                    out.append(("K05", WARN, f + ".id", "%r 是墓碑，請改指 merged_into" % (x,)))
    pid = rec.get("parent_id")
    if pid is not None:
        if not nonempty_str(pid):
            out.append(("K05", ERROR, "parent_id", "非字符串"))
        elif pid == rec.get("id"):
            out.append(("K05", ERROR, "parent_id", "自指"))
        elif reg.sub.get(pid) not in ("publisher", "collective"):
            out.append(("K05", ERROR, "parent_id", "須指 publisher 或 collective：%r（%s）" % (pid, reg.sub.get(pid))))
        else:
            seen, cur = {rec.get("id")}, pid
            while cur and reg.sub.get(cur) == "publisher":
                if cur in seen:
                    out.append(("K05", ERROR, "parent_id", "上級鏈有環"))
                    break
                seen.add(cur)
                cur = (reg.rec.get(cur) or {}).get("parent_id")
    # K06 禁欄
    for k in PUBLISHER_FORBIDDEN:
        if k in rec:
            out.append(("K06", ERROR, k, "publisher 不用此欄"))
    # K08
    if (s is not None or e is not None) and not nonempty_str(rec.get("dates_basis")):
        out.append(("K08", WARN, "dates_basis", "寫了 start／end 而缺 dates_basis"))
    return out


def _check_place(rec, reg):
    out = []
    if not nonempty_str(rec.get("primary_name")):
        out.append(("P01", ERROR, "primary_name", "缺"))
    hist = rec.get("history")
    if not (isinstance(hist, list) and hist):
        out.append(("P01", ERROR, "history", "須非空數組"))
        hist = []
    spans = []
    for i, h in enumerate(hist):
        f = "history[%d]" % i
        if not isinstance(h, dict):
            out.append(("P01", ERROR, f, "非物件"))
            continue
        if h.get("level") not in PLACE_LEVELS:
            out.append(("P01", ERROR, f + ".level", "不在枚舉：%r" % (h.get("level"),)))
        if not nonempty_str(h.get("name")):
            out.append(("P01", ERROR, f + ".name", "缺"))
        s, e = h.get("start"), h.get("end")
        for k, v in (("start", s), ("end", e)):
            if v is not None and not is_int(v):
                out.append(("P02", ERROR, f + "." + k, "非整數：%r" % (v,)))
        if is_int(s) and is_int(e) and s > e:
            out.append(("P02", ERROR, f, "start > end：%s > %s" % (s, e)))
        if is_int(e) and e > PLACE_END_MAX:
            out.append(("P02", ERROR, f + ".end", "end > %d（其後用 modern 表達）" % PLACE_END_MAX))
        spans.append((s if is_int(s) else float("-inf"), e if is_int(e) else float("inf"), i))
        for d in h.get("dynasty_ids") or []:
            if reg.sub.get(d) != "dynasty":
                out.append(("P04", ERROR, f + ".dynasty_ids", "不存在或非 dynasty：%r" % (d,)))
        dyn_hist = [{"start": _span(reg.rec[d])[0], "end": _span(reg.rec[d])[1]}
                    for d in h.get("dynasty_ids") or [] if reg.sub.get(d) == "dynasty" and d in reg.rec]
        if dyn_hist and all(is_int(x["start"]) and is_int(x["end"]) for x in dyn_hist):
            gaps = _uncovered(s, e, dyn_hist)
            if gaps:
                out.append(("P11", WARN, f + ".dynasty_ids", "所掛朝代未覆蓋本段年份：%s（補掛該時之朝代，或於朝代交替處拆段）" % (
                    "、".join("%s–%s" % g for g in gaps))))
        hp = h.get("parent_id")
        if hp is not None:
            if hp == rec["id"]:
                out.append(("P03", ERROR, f + ".parent_id", "自引用"))
            elif reg.sub.get(hp) != "place":
                out.append(("P03", ERROR, f + ".parent_id", "不存在或非 place：%r" % (hp,)))
            if "parent_text" in h:
                out.append(("P03", WARN, f, "parent_id 與 parent_text 並存，入庫前清掉 parent_text"))
            if reg.sub.get(hp) == "place" and hp != rec["id"]:
                gaps = _uncovered(s, e, reg.rec.get(hp, {}).get("history") or [])
                if gaps:
                    out.append(("P10", WARN, f + ".parent_id", "上級 %s 於本段年份內不存在：%s（拆段、該段上級留空）" % (
                        reg.rec[hp].get("primary_name"), "、".join("%s–%s" % g for g in gaps))))
    spans.sort()
    for (s1, e1, i1), (s2, e2, i2) in zip(spans, spans[1:]):
        if s2 < e1:
            out.append(("P02", ERROR, "history", "第 %d、%d 項時段重疊" % (i1, i2)))
    # 鏈無環：place → 其任一沿革項之 parent_id（含任一 → 圖中有環即報）
    def parents(x):
        r = reg.rec.get(x) or {}
        return [h.get("parent_id") for h in (r.get("history") or []) if isinstance(h, dict) and h.get("parent_id")]
    stack, seen = list(parents(rec["id"])), set()
    while stack:
        x = stack.pop()
        if x == rec["id"]:
            out.append(("P03", ERROR, "history", "parent_id 鏈成環"))
            break
        if x in seen:
            continue
        seen.add(x)
        stack.extend(parents(x))
    m = rec.get("modern")
    if m is not None:
        if not isinstance(m, dict):
            out.append(("P06", ERROR, "modern", "非物件"))
        else:
            if m.get("relation") not in MODERN_RELATIONS:
                out.append(("P06", ERROR, "modern.relation", "必填且在枚舉內：%r" % (m.get("relation"),)))
            ad = m.get("adcode")
            if ad is not None and not (isinstance(ad, str) and re.fullmatch(r"\d{6}", ad)):
                out.append(("P06", ERROR, "modern.adcode", "須六位數字：%r" % (ad,)))
    for i, p in enumerate(rec.get("predecessors") or []):
        f = "predecessors[%d]" % i
        if not isinstance(p, dict) or reg.sub.get(p.get("id")) != "place":
            out.append(("P07", ERROR, f + ".id", "不存在或非 place"))
        if isinstance(p, dict) and p.get("kind") not in PRED_KINDS:
            out.append(("P07", ERROR, f + ".kind", "須為 析出／並入／改置：%r" % (p.get("kind"),)))
    if "coords" in rec:
        out.append(("P08", ERROR, "coords", "第一期禁出現"))
    return out + _check_place_tier(rec, reg, hist)


def place_tier(rec):
    return (rec or {}).get("place_level") or "concept"


def _check_place_tier(rec, reg, hist):
    """P12–P14：兩層。朝代條＝某朝某名某級一條，朝內上級變動拆段；換名、升降另立一條，以 predecessors 改置相接。"""
    out = []
    lv = rec.get("place_level")
    if lv is not None and lv not in PLACE_TIERS:
        return [("P12", ERROR, "place_level", "須為 concept／concrete：%r" % (lv,))]
    tier = place_tier(rec)
    top = rec.get("dynasty_ids")
    if tier == "concept":
        for k in ("dynasty_ids", "concept_id"):
            if k in rec:
                out.append(("P13" if k == "dynasty_ids" else "P14", ERROR, k, "跨朝條不得有（只許朝代條）"))
    else:
        if not (isinstance(top, list) and top):
            out.append(("P13", ERROR, "dynasty_ids", "朝代條必填（非空數組）"))
            top = []
        for d in top:
            if reg.sub.get(d) != "dynasty":
                out.append(("P13", ERROR, "dynasty_ids", "不存在或非 dynasty：%r" % (d,)))
        levels = set()
        for i, h in enumerate(hist):
            if not isinstance(h, dict):
                continue
            f = "history[%d]" % i
            if nonempty_str(h.get("name")) and h["name"] != rec.get("primary_name"):
                out.append(("P13", ERROR, f + ".name", "朝代條各段須同 primary_name（換名另立朝代條）：%r" % (h["name"],)))
            levels.add(h.get("level"))
            extra = [d for d in h.get("dynasty_ids") or [] if d not in top]
            if extra:
                out.append(("P13", ERROR, f + ".dynasty_ids", "不在頂層 dynasty_ids 內：%r" % (extra,)))
        if len(levels) > 1:
            out.append(("P13", ERROR, "history", "朝代條各段須同級（升降另立朝代條）：%s" % "、".join(sorted(map(str, levels)))))
        c = rec.get("concept_id")
        if c is not None:
            r = reg.rec.get(c)
            if reg.sub.get(c) != "place" or place_tier(r) != "concept":
                out.append(("P14", ERROR, "concept_id", "須指跨朝條（place_level=concept）：%r" % (c,)))
    for i, h in enumerate(hist):
        hp = h.get("parent_id") if isinstance(h, dict) else None
        if hp is None or hp == rec["id"] or reg.sub.get(hp) != "place":
            continue
        pr = reg.rec.get(hp) or {}
        f = "history[%d].parent_id" % i
        if place_tier(pr) != tier:
            out.append(("P14", ERROR, f, "上級須同層（%s 條之上級不得為 %s 條）：%r" % (tier, place_tier(pr), hp)))
        elif tier == "concrete" and not set(pr.get("dynasty_ids") or []) & set(top or []):
            out.append(("P14", ERROR, f, "上級朝代條與本條朝代不相交：%r" % (hp,)))
    return out


def check_native_place(rec, reg):
    """人物籍貫 `native_place_entity_id`（N01–N03）。無此欄回 []。與 applies／check_record 無關（people 不屬新子類型）。"""
    if "native_place_entity_id" not in rec:
        return []
    v = rec["native_place_entity_id"]
    st = rec.get("subtype") or "people"
    if st != "people":
        return [("N01", ERROR, "native_place_entity_id", "只許 people 條有此欄，本條為 %s" % st)]
    if not nonempty_str(v):
        return [("N01", ERROR, "native_place_entity_id", "須為非空字符串（地名 Entity id）：%r" % (v,))]
    if reg.sub.get(v) != "place":
        return [("N02", ERROR, "native_place_entity_id",
                 "須指向 place 條：%r %s" % (v, "不存在" if v not in reg.sub else "是 %s" % reg.sub[v]))]
    tomb = (reg.rec.get(v) or {}).get("merged_into")
    if tomb:
        return [("N03", WARN, "native_place_entity_id", "%s 是墓碑，請改指 merged_into：%s" % (v, tomb))]
    return []


def applies(rec):
    """本模塊是否檢查此條：四新子類型，或帶 collective_kind 之 collective。"""
    st = rec.get("subtype")
    return st in NEW_SUBTYPES or (st == "collective" and "collective_kind" in rec)


def check_record(rec, reg):
    """單條新子類型記錄之局部＋引用檢查。回 [(code, level, field, detail)]。
    非新子類型回 []（people、無 collective_kind 之舊 collective 不受影響）。"""
    st = rec.get("subtype")
    if not applies(rec):
        return []
    if st == "collective":
        k = rec.get("collective_kind")
        if k not in COLLECTIVE_KINDS:
            return [("I01", ERROR, "collective_kind", "不在枚舉：%r" % (k,))]
        if k != "官署":
            return []
        return _check_institution(rec, reg) + _alt_problems(rec)
    out = []
    out += _forbidden_problems(rec, st)
    out += _dates_problems(rec, st)
    out += _alt_problems(rec)
    out += {"dynasty": _check_dynasty, "reign": _check_reign,
            "office": _check_office, "place": _check_place,
            "seal": _check_seal, "publisher": _check_publisher}[st](rec, reg)
    return out


# ----------------------------------------------------------------------------- 全庫檢查

def check_global(reg, canonical=None):
    """跨條目之檢查。回 [(id, code, level, field, detail)]。
    canonical：規範朝代名集合（None 則讀本倉 schema/common.md；讀不到即報錯）。"""
    out = []
    if canonical is None:
        canonical = load_canonical_dynasties()
    dyns = reg.of("dynasty")
    # D1 枚舉＋唯一
    byname = {}
    for i, r in dyns:
        n = r.get("primary_name")
        if canonical is not None and n not in canonical:
            out.append((i, "D1", ERROR, "primary_name", "不在規範朝代名枚舉：%r" % (n,)))
        byname.setdefault(n, []).append(i)
    for n, ids in byname.items():
        if len(ids) > 1:
            for i in ids:
                out.append((i, "D1", ERROR, "primary_name", "朝代名重複：%r（%d 條）" % (n, len(ids))))
    # A1：dynasty 內無 ambiguous 之別名全局唯一（也不得與他條 primary_name 撞）
    plain = {}
    for i, r in dyns:
        for a in r.get("alt_names") or []:
            if isinstance(a, dict) and nonempty_str(a.get("name")) and not a.get("ambiguous"):
                plain.setdefault(a["name"], set()).add(i)
    for n, ids in plain.items():
        if len(ids) > 1:
            for i in sorted(ids):
                out.append((i, "A1", ERROR, "alt_names", "未標 ambiguous 之別名 %r 為 %d 條朝代所共用" % (n, len(ids))))
    # A1：ambiguous 之名全庫至少 2 條聲稱（四子類型內計）
    claims = {}
    for i, r in reg.rec.items():
        # 以 primary_name 本身為此名者亦算一條聲稱（如「後漢」為五代後漢之規範名，亦為東漢之別稱）
        if r.get("subtype") == "dynasty" and nonempty_str(r.get("primary_name")):
            claims.setdefault(r["primary_name"], set()).add(i)
        for a in r.get("alt_names") or []:
            if isinstance(a, dict) and a.get("ambiguous") is True and nonempty_str(a.get("name")):
                claims.setdefault(a["name"], set()).add(i)
    amb_names = {a["name"] for r in reg.rec.values() for a in (r.get("alt_names") or [])
                 if isinstance(a, dict) and a.get("ambiguous") is True and nonempty_str(a.get("name"))}
    for n, ids in claims.items():
        if n in amb_names and len(ids) < 2:
            for i in ids:
                out.append((i, "A1", WARN, "alt_names", "ambiguous 之名 %r 全庫僅 %d 條聲稱（標記多餘）" % (n, len(ids))))
    # R1：reign 唯一與重疊
    triples, bydyn = {}, {}
    for i, r in reg.of("reign"):
        s, e = _span(r)
        k = (r.get("primary_name"), r.get("dynasty_id"), s)
        triples.setdefault(k, []).append(i)
        if is_int(s):
            bydyn.setdefault((r.get("dynasty_id"), r.get("primary_name")), []).append(
                (s, e if is_int(e) else s, i))
    for k, ids in triples.items():
        if len(ids) > 1:
            for i in ids:
                out.append((i, "R1", ERROR, "primary_name", "(名, 朝代, 起年) 重複：%r" % (k,)))
    for (d, n), lst in bydyn.items():
        lst.sort()
        for (s1, e1, i1), (s2, e2, i2) in zip(lst, lst[1:]):
            if s2 <= e1 and (s1, i1) != (s2, i2) and not (s1 == s2):  # 起年相同者已由三元組唯一報
                out.append((i2, "R1", ERROR, "dates", "同朝同名年號 %r 區間與 %s 重疊" % (n, i1)))
    # O11：同概念下同朝具體條 dynasty_ids 完全相同
    seen = {}
    for i, r in reg.of("office"):
        if r.get("office_level") == "concrete" and r.get("parent_id"):
            k = (r["parent_id"], tuple(sorted(r.get("dynasty_ids") or [])))
            seen.setdefault(k, []).append(i)
    for k, ids in seen.items():
        if len(ids) > 1 and k[1]:
            for i in ids:
                out.append((i, "O11", WARN, "dynasty_ids", "同概念下同朝已有 %d 條具體條" % len(ids)))
    # I07：同概念下同朝（合併條按展開朝代算）只一條具體條；I10：同名＋朝代重疊之具體條疑重複
    by_concept, by_name = {}, {}
    for i, r in reg.rec.items():
        if not (reg.is_inst(i) and r.get("institution_level") == "concrete"):
            continue
        for d in r.get("dynasty_ids") or []:
            if r.get("parent_id"):
                by_concept.setdefault((r["parent_id"], d), set()).add(i)
            by_name.setdefault((r.get("primary_name"), d), set()).add(i)
    flagged = set()
    for k, ids in by_concept.items():
        if len(ids) > 1:
            for i in sorted(ids):
                if (i, "I07") not in flagged:
                    flagged.add((i, "I07"))
                    out.append((i, "I07", WARN, "dynasty_ids", "同概念下同朝已有 %d 條具體條" % len(ids)))
    for k, ids in by_name.items():
        if len(ids) > 1:
            for i in sorted(ids):
                if (i, "I10") not in flagged:
                    flagged.add((i, "I10"))
                    out.append((i, "I10", WARN, "primary_name", "同名 %r 朝代重疊之具體條 %d 條，疑重複" % (k[0], len(ids))))
    # K09：publisher 同名＋同類別＋同朝代集重複（防重複建檔）
    pubs = {}
    for i, r in reg.of("publisher"):
        if r.get("merged_into"):
            continue
        k = (r.get("primary_name"), r.get("publisher_kind"), tuple(sorted(r.get("dynasty_ids") or [])))
        pubs.setdefault(k, []).append(i)
    for k, ids in pubs.items():
        if len(ids) > 1:
            for i in ids:
                out.append((i, "K09", WARN, "primary_name", "同名同類別同朝代之 publisher %d 條，疑重複：%r" % (len(ids), k[0])))
    # P09：同名異地組（INFO）、同名同上級疑重複（WARN）；朝代條只在同名同朝代內比
    names = {}
    for i, r in reg.of("place"):
        k = (r.get("primary_name"),) if place_tier(r) == "concept" else \
            (r.get("primary_name"), tuple(sorted(r.get("dynasty_ids") or [])))
        names.setdefault(k, []).append(i)
    for (n, *_), ids in names.items():
        if len(ids) > 1:
            def ups(x):
                return frozenset(h.get("parent_id") for h in (reg.rec[x].get("history") or [])
                                 if isinstance(h, dict) and h.get("parent_id"))
            groups = {}
            for i in ids:
                groups.setdefault(ups(i), []).append(i)
            for i in ids:
                out.append((i, "P09", INFO, "primary_name", "同名 %r 共 %d 條（同名異地清單）" % (n, len(ids))))
            for u, g in groups.items():
                if len(g) > 1 and u:
                    for i in g:
                        out.append((i, "P09", WARN, "primary_name", "同名同上級鏈 %r 有 %d 條，疑重複" % (n, len(g))))
    return out


def scan(root, canonical=None, only_ids=None):
    """全庫掃描。回 [(relpath, id, subtype, code, level, field, detail)]。
    only_ids：只回這些 id 之結果（審 PR 用 --paths 時；索引仍用全庫建）。"""
    reg = Registry.from_root(root)
    rows = []
    for i, r in reg.rec.items():
        if only_ids is not None and i not in only_ids:
            continue
        for c, lv, f, d in check_record(r, reg):
            rows.append((reg.path.get(i, ""), i, r.get("subtype"), c, lv, f, d))
    for i, c, lv, f, d in check_global(reg, canonical):
        if only_ids is not None and i not in only_ids:
            continue
        rows.append((reg.path.get(i, ""), i, reg.sub.get(i), c, lv, f, d))
    return rows
