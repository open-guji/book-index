#!/usr/bin/env python3
"""entity_subtypes.py —— Entity 專名子類型（dynasty／reign／office／place）之校驗，
check_v2.py 與 verify.py **共用這一份**（不得各寫一份）。

依據：overview `項目進展/古籍目錄/整體設計/專名建檔/給S-字段清單.md` §四，及 D／O／P 設計檔；
字段形狀見 schema/entity.md。overview#464（F6-5）。

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
  I01–I12  官署（collective 且 collective_kind=官署，P3c 設計稿 §六／§十二，S 10-07 定）；
       I12 兼管官職條之 institution_ref（O14 第二步：`COL:` 占位一律 ERROR）。
       collective_kind 缺省＝未分，舊 collective 不受約束。
  V01  源檔出現 `_` 起首或 children／reigns／index_in_reign 等派生／反向欄位           ERROR
       （`_` 起首者仍由 check_v2 自身之 V01 報；本模塊只補非底線之派生名，並在新子類型內
       把 `_has_text`／`_has_collated` 之豁免收回。）
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

NEW_SUBTYPES = ("dynasty", "reign", "office", "place")
ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

PERIODS = {"pre-qin", "qin-han", "three-kingdoms", "jin", "nanbeichao", "sui-tang",
           "five-dynasties", "song", "liao-jin-yuan", "ming", "qing", "modern"}

# alt_names.type 枚舉（SCHEMA〈alt_names.type 枚舉〉；新增十項依 #464 清單 §三·1）
ALT_TYPES = {
    "字", "號", "諡號", "賜號", "別名", "常用名", "簡體", "行第", "廟號", "訛名", "異體", "封爵", "俗姓",
    "簡稱", "合稱", "避諱", "別稱", "雅稱", "全稱", "異寫", "舊稱", "異稱", "今名",
}
ALT_TYPES_NEW_ONLY = ALT_TYPES  # 新子類型暫與全表同；人物之長尾罕見值不在此限（由 qa_entity 判 WARN）

# 各子類型可用 dates 鍵（清單 §三·3）；office／place 不用 dates
DATES_KEYS = {
    "people": {"birth", "death", "floruit", "chinese", "basis"},
    "dynasty": {"start", "end", "basis", "chinese"},
    "reign": {"start", "end", "basis", "chinese"},
    "office": set(),
    "place": set(),
}
# 源檔不許寫之派生／反向欄（無底線者；`_` 起首者由 check_v2 V01 報）
DERIVED_NAMES = ("children", "reigns", "index_in_reign", "successors", "people", "holders",
                 "compounds", "ancestors", "span", "same_name")
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
PRED_KINDS = {"析出", "並入"}
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


class Registry:
    """全庫 Entity 之輕量索引：id → (subtype, 記錄)。只留新子類型之整條記錄，其餘只留 subtype。"""

    def __init__(self):
        self.sub = {}      # id -> subtype
        self.rec = {}      # id -> record（僅 NEW_SUBTYPES）
        self.path = {}     # id -> relpath

    @classmethod
    def from_root(cls, root, ref_roots=()):
        """ref_roots：只讀參照倉（草稿庫查時指正式庫），其 Entity 只供引用解析（如 dynasty_ids 指正式 id）；
        同 id 以 root 為準。跨條目之全庫檢查（check_global）應另用不帶 ref_roots 之索引，免把兩倉同名條當重複。"""
        reg = cls()
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
        if st in NEW_SUBTYPES or st == "collective":
            self.rec[i] = d

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
    if st in ("office", "place"):
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
                if k != "wikidata_id":
                    out.append(("E1", ERROR, "external_ids." + k, "新子類型只許 wikidata_id"))
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
                if dids and bd and not (set(dids) & set(bd)):
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
        if dids and td and not (set(dids) & set(td)):
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
                if dids and sd and not (set(dids) & set(sd)):
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
            out.append(("P07", ERROR, f + ".kind", "須為 析出／並入：%r" % (p.get("kind"),)))
    if "coords" in rec:
        out.append(("P08", ERROR, "coords", "第一期禁出現"))
    return out


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
            "office": _check_office, "place": _check_place}[st](rec, reg)
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
    # P09：同名異地組（INFO）、同名同上級疑重複（WARN）
    names = {}
    for i, r in reg.of("place"):
        names.setdefault(r.get("primary_name"), []).append(i)
    for n, ids in names.items():
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
