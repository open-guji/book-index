#!/usr/bin/env python3
"""check_v2.py —— 新格式（schema-v2）殘留檢查。只讀，不改任何檔。

查源檔裡還留著的舊格式寫法（SCHEMA.md〈源數據與構建產物〉、附錄〈新舊欄位對照〉）：

  代碼  檢的是什麼                                   對應遷移步（F2-7）
  V01  源檔頂層出現 `_` 起首欄位（派生欄手寫）        M3
       （`_has_text`／`_has_collated` 豁免：暫留源欄，待文本總管給出穩定來源，#459）
  V02  無底線之舊派生欄（has_text／promoted_to…）    M3
  V03  Work.books                                    M3
  V04  related_works 用反向詞（has_part 等）          M3（M2 先在規範側補寫，M3 刪反向項）
  V05  related_works 用詞表外舊詞（commentary_on 等） M2
  V06  related_works／related_* 項帶 title 副本       M2
  V07  related 存在 id 較大一側                       M1⑤＋M3
  V08  Work／Book／Collection.authors[] 缺 role      M1②（Entity 回填；兩側皆缺者補「撰」）；Book／Collection 自 2026-10-07 起（overview#468）
  V09  舊分類欄 classification                         M4
  V10  Collection.books／contained_works              M1①＋M3
  V11  Entity.works                                   M3
  V12  sidecar（Collection 目錄下非記錄之 .json）      M1⓪＋M6（M6 才刪表）
  V13  relation 未識別（不在新詞表、亦非已知舊詞）    M2（「未識別形態」清單）
  V14  對稱 id 陣列（related_books／related_collections）之項不是字符串  M2
  V15  缺 schema_version，或其值不是整數 1（必填，SCHEMA〈字段表〉）   2026-10-07 起（overview#473）

M0（打 tag）、M5（build）、M6（index/ 重生）不產生源檔殘留，故無代碼。

**專名子類型（dynasty／reign／office／place，overview#464 F6-5）另有一組代碼**：
E1、D1–D3、R1、A1、O01–O05／O09–O12、P01–P11、I01–I12（官署＝collective_kind 為官署之 collective，及官職 institution_ref）（V01 對新子類型亦加嚴）。實現在
`.claude/qa/entity_subtypes.py`（verify.py 共用同一份，不寫兩份），碼義見該文件頭與 SCHEMA〈專名子類型〉。
**級別**：V 系列與專名之 ERROR 計入殘留、決定退出碼；**WARN／INFO 只報不計**——明細 CSV 多一列 `level`，
summary 分「ERROR」「WARN」「INFO」三段列出，退出碼只看 ERROR。`--errors-only` 令明細也不出 WARN／INFO。
上下級區間不合、年號越出所屬朝代區間一律 WARN（S 預審口徑）。
審 PR 用 `--paths` 時，專名之引用與唯一性仍對**全庫**查（索引用全庫建），只輸出所指檔之結果。

用法：
  python3 .claude/qa/check_v2.py                     # 全庫（當前倉根）
  python3 .claude/qa/check_v2.py --root ../book-index-draft
  python3 .claude/qa/check_v2.py --paths Work/a.json Book/b.json   # 只查這些檔（審 PR 用）
  git diff --name-only origin/main... | python3 .claude/qa/check_v2.py --paths -
  python3 .claude/qa/check_v2.py --csv out.csv       # 逐條明細寫 CSV（預設寫 stdout）
  python3 .claude/qa/check_v2.py --summary           # 只出計數

退出碼：0＝無殘留（ERROR）；1＝有殘留；2＝用法錯誤。WARN／INFO 不影響退出碼。
**遷移前的存量會大量報出，這是預期**；審數據 PR 時用 `--paths` 只看改動的檔。
"""
import argparse
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import entity_subtypes as es  # noqa: E402  專名子類型校驗（與 verify.py 共用）

RECORD_DIRS = ("Work", "Book", "Collection", "Entity")
# 記錄目錄之下而非記錄者：整理本、輯佚檔
SKIP_SUBDIRS = ("collated_edition", "fragments")

# 新詞表：源檔可寫的 relation（存儲方向）
STORE_RELATIONS = {
    "part_of", "studies", "contains_text_of", "preceded_by",  # 成對關係之規範方向
    "related",                                                 # 對稱，存 id 較小一側
    "collected_in", "derived_from", "adapted_from", "excerpted_from",
    "source_of", "suspected_same", "same_entry", "pseudepigraph_of",  # 單向
}
# 反向詞：只在 build 產物裡出現，源檔不寫 → 規範方向
REVERSE_RELATIONS = {
    "has_part": "part_of",
    "studied_by": "studies",
    "text_carried_by": "contains_text_of",
    "followed_by": "preceded_by",
    "has_pseudepigraph": "pseudepigraph_of",
    "has_adaptation": "adapted_from",
}
# 詞表外舊詞 → 歸併後之詞（用戶 10-07 定）
DEPRECATED_RELATIONS = {
    "commentary_on": "studies",
    "related_to": "related",
}
# 暫留源欄之 `_` 欄（目錄總管 10-07 定，#459）：V01 不報
UNDERSCORE_EXEMPT = {"_has_text", "_has_collated"}
# 無底線之舊派生欄
OLD_DERIVED = ("has_text", "has_image", "has_collated", "has_full_text",
               "has_digitalization", "promoted_to", "promoted_at")
# 對稱關係（只存 id 較小一側）的 id 陣列欄
SYMMETRIC_ID_LISTS = {
    "Book": ("related_books",),
    "Collection": ("related_books", "related_collections"),
}

CODES = {
    "V01": ("源檔有 _ 起首欄位", "M3"),
    "V02": ("無底線之舊派生欄", "M3"),
    "V03": ("Work.books", "M3"),
    "V04": ("related_works 用反向詞", "M3"),
    "V05": ("related_works 用詞表外舊詞", "M2"),
    "V06": ("關聯項帶 title 副本", "M2"),
    "V07": ("related 存在 id 較大一側", "M1⑤+M3"),
    "V08": ("authors[] 缺 role（Work／Book／Collection）", "M1②"),
    "V09": ("舊分類欄 classification", "M4"),
    "V10": ("Collection.books／contained_works", "M1①+M3"),
    "V11": ("Entity.works", "M3"),
    "V12": ("sidecar 對照表", "M1⓪+M6"),
    "V13": ("relation 未識別", "M2"),
    "V14": ("對稱 id 陣列項非字符串", "M2"),
    "V15": ("缺 schema_version 或值非 1", "#473"),
    # 專名子類型（#464）：第二欄＝所屬檢查族（無遷移步）
    "E1": ("專名：禁外部 id／翻譯欄位", "專名"),
    "D1": ("dynasty 規範名枚舉／唯一", "專名"),
    "D2": ("dynasty 上級／區間", "專名"),
    "D3": ("dates 鍵、整數、無 0 年、period", "專名"),
    "R1": ("reign 所屬朝代／帝王／唯一／區間", "專名"),
    "A1": ("alt_names／ambiguous", "專名"),
    "O01": ("office_level", "專名"), "O02": ("office 必填／概念條禁欄", "專名"),
    "O03": ("office_class", "專名"), "O04": ("office parent_id", "專名"),
    "O05": ("office 複合 base／qualifier", "專名"), "O09": ("office start／end", "專名"),
    "O10": ("office 簡稱 ≤2", "專名"), "O11": ("office 同概念同朝重複", "專名"),
    "O12": ("alt_names.type 枚舉", "專名"),
    "P01": ("place 必填／level", "專名"), "P02": ("place 沿革項時段", "專名"),
    "P03": ("place parent_id", "專名"), "P04": ("place dynasty_ids", "專名"),
    "P06": ("place modern", "專名"), "P07": ("place predecessors", "專名"),
    "P08": ("place coords", "專名"), "P09": ("place 同名異地／疑重複", "專名"),
    "P10": ("place 沿革段之上級於該段年份內不存在", "專名"),
    "P11": ("place 沿革段年份超出所掛朝代起訖", "專名"),
    "I01": ("官署 collective_kind／institution_level", "專名"), "I02": ("官署 必填／分層禁欄", "專名"),
    "I03": ("官署 parent_id", "專名"), "I04": ("官署 superiors", "專名"),
    "I05": ("官署 group_ids", "專名"), "I06": ("官署 start／end", "專名"),
    "I07": ("官署 同概念同朝重複", "專名"), "I08": ("官署 禁外部 id／官職欄", "專名"),
    "I09": ("官署 location_id／succeeds", "專名"), "I10": ("官署 同名朝代重疊", "專名"),
    "I11": ("官署 派生欄", "專名"), "I12": ("官職 institution_ref（含 O14 占位）", "專名"),
}


def kind_of(relpath):
    """回 (記錄類, 是否該查)。relpath 以 / 分隔、相對倉根。"""
    parts = relpath.replace("\\", "/").split("/")
    if not parts or parts[0] not in RECORD_DIRS:
        return None, False
    if any(p in SKIP_SUBDIRS for p in parts[1:-1]):
        return parts[0], False
    if not parts[-1].endswith(".json"):
        return parts[0], False
    return parts[0], True


def rel_target(item):
    """related_works 項之目標 id（舊資料有 `work_id` 一形，backrefs「坑 54」）。"""
    if not isinstance(item, dict):
        return None
    return item.get("id") or item.get("work_id")


def check_record(kind, rec):
    """回 [(code, field, detail)]。rec 是已解析之記錄 dict。"""
    out = []
    rid = rec.get("id", "")

    for k in rec:
        if k.startswith("_") and k not in UNDERSCORE_EXEMPT:
            out.append(("V01", k, ""))
    for k in OLD_DERIVED:
        if k in rec:
            out.append(("V02", k, ""))

    if kind == "Work" and "books" in rec:
        out.append(("V03", "books", "%d 項" % len(rec["books"] or [])))

    rw = rec.get("related_works")
    if isinstance(rw, list):
        for i, it in enumerate(rw):
            if not isinstance(it, dict):
                out.append(("V13", "related_works[%d]" % i, "非物件：%r" % (it,)))
                continue
            rel = it.get("relation")
            tgt = rel_target(it) or ""
            f = "related_works[%d]" % i
            if rel in REVERSE_RELATIONS:
                out.append(("V04", f + ".relation",
                            "%s→%s 應改在 %s 一側寫 %s" % (rel, tgt, tgt, REVERSE_RELATIONS[rel])))
            elif rel in DEPRECATED_RELATIONS:
                out.append(("V05", f + ".relation",
                            "%s 改 %s" % (rel, DEPRECATED_RELATIONS[rel])))
            elif rel not in STORE_RELATIONS:
                out.append(("V13", f + ".relation", repr(rel)))
            if "title" in it:
                out.append(("V06", f + ".title", tgt))
            if rel in ("related", "related_to") and tgt and rid > tgt:
                out.append(("V07", f, "related→%s：%s > %s，應存於 %s 一側" % (tgt, rid, tgt, tgt)))

    for fld in SYMMETRIC_ID_LISTS.get(kind, ()):
        v = rec.get(fld)
        if not isinstance(v, list):
            continue
        for i, it in enumerate(v):
            tgt = it if isinstance(it, str) else rel_target(it)
            if not isinstance(it, str):
                out.append(("V14", "%s[%d]" % (fld, i), json.dumps(it, ensure_ascii=False)[:80]))
            if tgt and rid > tgt:
                out.append(("V07", "%s[%d]" % (fld, i), "%s：%s > %s，應存於 %s 一側" % (fld, rid, tgt, tgt)))

    if kind in ("Work", "Book", "Collection"):
        au = rec.get("authors")
        if isinstance(au, list):
            for i, a in enumerate(au):
                if isinstance(a, dict) and not (isinstance(a.get("role"), str) and a["role"].strip()):
                    out.append(("V08", "authors[%d].role" % i, a.get("name", "")))

    if kind in ("Work", "Collection") and "classification" in rec:
        out.append(("V09", "classification", ""))

    if kind == "Collection":
        for k in ("books", "contained_works"):
            if k in rec:
                out.append(("V10", k, "%d 項" % len(rec[k] or [])))

    if kind == "Entity" and "works" in rec:
        out.append(("V11", "works", "%d 項" % len(rec["works"] or [])))

    sv = rec.get("schema_version")
    if type(sv) is not int or sv != 1:
        out.append(("V15", "schema_version", "缺" if "schema_version" not in rec else repr(sv)))

    return out


def check_file(root, relpath, registry=None):
    """回 [(relpath, id, kind, code, field, detail, level)]；非記錄檔回 []。
    registry：es.Registry（專名引用索引）；None 則不做專名檢查。"""
    kind, ok = kind_of(relpath)
    if not ok:
        return []
    full = os.path.join(root, relpath)
    if not os.path.isfile(full):  # PR 裡刪掉的檔
        return []
    try:
        with open(full, encoding="utf-8") as fh:
            rec = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        return [(relpath, "", kind, "V13", "", "JSON 解析失敗：%s" % e, es.ERROR)]
    if not (isinstance(rec, dict) and "id" in rec and "type" in rec):
        if kind == "Collection":
            return [(relpath, "", kind, "V12", "", os.path.basename(relpath), es.ERROR)]
        return []
    rows = [(relpath, rec.get("id", ""), kind, c, f, d, es.ERROR) for c, f, d in check_record(kind, rec)]
    if kind == "Entity" and es.applies(rec) and registry is not None:
        rows += [(relpath, rec.get("id", ""), kind, c, f, d, lv)
                 for c, lv, f, d in es.check_record(rec, registry)]
    return rows


def walk(root):
    for d in RECORD_DIRS:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for dp, dn, fn in os.walk(base):
            dn[:] = sorted(x for x in dn if x not in SKIP_SUBDIRS)
            for f in sorted(fn):
                if f.endswith(".json"):
                    yield os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")


def read_paths(args_paths):
    if args_paths == ["-"]:
        return [ln.strip() for ln in sys.stdin if ln.strip()]
    out = []
    for p in args_paths:
        if p.startswith("@"):
            with open(p[1:], encoding="utf-8") as fh:
                out.extend(ln.strip() for ln in fh if ln.strip())
        else:
            out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="schema-v2 舊格式殘留檢查（只讀）")
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
                    help="數據倉根目錄（預設：本腳本所在之倉）")
    ap.add_argument("--ref-root", action="append", default=[], metavar="DIR",
                    help="只讀參照倉（可多次）：專名引用（dynasty_ids 等）可解析到該倉之 Entity；草稿庫查時指正式庫")
    ap.add_argument("--paths", nargs="+", metavar="PATH",
                    help="只查這些檔（相對倉根）；`-` 自 stdin 讀，`@檔` 自檔讀")
    ap.add_argument("--csv", metavar="OUT", help="明細 CSV 寫到此檔（預設 stdout）")
    ap.add_argument("--summary", action="store_true", help="只出計數，不出明細")
    ap.add_argument("--codes", help="只報這些代碼，逗號分隔，如 V03,V08")
    ap.add_argument("--errors-only", action="store_true", help="明細只出 ERROR（WARN／INFO 不出；summary 仍分列）")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        print("--root 不存在：%s" % root, file=sys.stderr)
        return 2
    only = set(a.codes.split(",")) if a.codes else None
    if only and not only <= set(CODES):
        print("未知代碼：%s" % ",".join(sorted(only - set(CODES))), file=sys.stderr)
        return 2

    files = read_paths(a.paths) if a.paths else walk(root)
    registry = es.Registry.from_root(root)          # 本倉：跨條目檢查用
    resolver = es.Registry.from_root(root, a.ref_root) if a.ref_root else registry   # 引用解析用
    rows, n_files, sel_ids = [], 0, set()
    for rp in files:
        rp = rp.replace("\\", "/")
        if os.path.isabs(rp):
            rp = os.path.relpath(rp, root).replace(os.sep, "/")
        if kind_of(rp)[1]:
            n_files += 1
        for r in check_file(root, rp, resolver):
            if only is None or r[3] in only:
                rows.append(r)
        if rp.startswith("Entity/"):
            sel_ids.add(os.path.splitext(os.path.basename(rp))[0].split("-")[0])
    # 專名跨條目檢查（唯一性、ambiguous 聲稱數、重疊…）；--paths 時只留所指條目之結果
    for i, c, lv, f, d in es.check_global(registry):
        if a.paths and i not in sel_ids and registry.path.get(i, "") not in {x.replace("\\", "/") for x in files}:
            continue
        if only is None or c in only:
            rows.append((registry.path.get(i, ""), i, "Entity", c, f, d, lv))
    if a.errors_only:
        shown = [r for r in rows if r[6] == es.ERROR]
    else:
        shown = rows

    if not a.summary:
        fh = open(a.csv, "w", encoding="utf-8", newline="") if a.csv else sys.stdout
        w = csv.writer(fh)
        w.writerow(["path", "id", "kind", "code", "field", "detail", "level"])
        w.writerows(shown)
        if a.csv:
            fh.close()

    errs = [r for r in rows if r[6] == es.ERROR]
    err = sys.stderr if not a.summary else sys.stdout
    print("# check_v2：查 %d 檔，殘留（ERROR）%d 處／%d 檔；WARN %d 處；INFO %d 處" % (
        n_files, len(errs), len({r[0] for r in errs}),
        sum(1 for r in rows if r[6] == es.WARN), sum(1 for r in rows if r[6] == es.INFO)), file=err)
    for lv in (es.ERROR, es.WARN, es.INFO):
        sub = [r for r in rows if r[6] == lv]
        cnt = collections.Counter(r[3] for r in sub)
        recs = collections.defaultdict(set)
        for r in sub:
            recs[r[3]].add(r[0])
        if sub:
            print("## %s" % lv, file=err)
        for c in sorted(cnt):
            print("%s\t%s\t%d 處\t%d 檔\t%s" % (c, CODES[c][1], cnt[c], len(recs[c]), CODES[c][0]), file=err)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
