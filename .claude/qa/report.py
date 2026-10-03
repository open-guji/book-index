#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自 known-issues 與 status 生裁決報告。

**所以立此**：前兩版報告都是臨時拼出來的，一輪過去數就陳舊（上版稱總數 3,130、
P 160、Z 未清，而彼時實際早已不同），使用者讀到的是舊帳。今寫成腳本，每輪重跑即可。

用法：python3 .claude/qa/report.py [--out 路徑]
"""
import json, os, argparse, datetime, collections

KI = ".claude/qa/known-issues"
ST = ".claude/qa/status"
# 2026-09-07 使用者定：待審之物一律出到 overview 之「待审元数据」資料夾。
# 舊路 版本梳理/先秦/24-全库质量复查-待裁清单.md 已 git mv 過去，勿再寫回。
DEFAULT_OUT = ("../overview/项目进展/古籍索引网站/待审元数据/"
               "01-全库质量复查-待裁清单.md")

# kind → （甲乙丙丁戊之序號、標題、說明）
GROUPS = [
    ("重出待併", "甲", "重出待併", "二條（或數條）疑為一書，併與不併須裁"),
    ("誤繫待裁", "乙", "誤繫待裁", "繫連可疑而證未足以逕撤"),
    ("斷代兩可", "丙", "斷代兩可", "史源互異，兩說皆有據"),
    ("撰人存疑", "丁", "撰人存疑", "撰人之名或其人待考"),
    ("其他", "戊", "其他", "工具、流程、資料源之疑，或不入前四類者"),
]
LANE_PERIOD = {
    "shanggu": "pre-qin／qin-han", "weijin": "three-kingdoms／jin",
    "nanbeichao": "nanbeichao", "suitang": "sui-tang／five-dynasties",
    "song": "song", "liaojinyuan": "liao-jin-yuan", "ming": "ming",
    "qing": "qing／modern", "undated": "none", "coordinator": "（跨道）",
}


def load_ki():
    out = []
    for f in sorted(os.listdir(KI)):
        if not f.endswith(".json"):
            continue
        try:
            j = json.load(open(os.path.join(KI, f)))
        except Exception:
            continue
        if isinstance(j, dict):
            j["_file"] = f
            out.append(j)
    return out


def brief(j, n=260):
    """取一段可讀之摘要：優先 evidence，其次 why／說，再次 recommend。"""
    for k in ("evidence", "why", "說", "recommend", "note", "detail"):
        v = j.get(k)
        if isinstance(v, str) and v.strip():
            s = " ".join(v.split())
            return s[:n] + ("…" if len(s) > n else "")
        if isinstance(v, list) and v:
            s = " ".join(str(x) for x in v[:3])
            s = " ".join(s.split())
            return s[:n] + ("…" if len(s) > n else "")
    return ""


# 待人裁之分類：**按「要你決定什麼」分，不按「哪個檢報的」分**（2026-09-07）
# 使用者要的是可以逐條下判斷的清單，而檢之代號對他毫無意義。
OPEN_GROUPS = [
    ("甲", "須覆核志書原文", "庫中無該志之整理本，或原文兩解，非讀原書不能定",
     ("G2-題首之病待覆原文", "G2-承前之又致重出", "G-志書承前之題失落", "G-志書按語誤建為書",
      "G-譯業總計語誤建為書", "G-撰人黏題待人定", "I-秦志入庫題名承上之詞（資料缺陷非重出）",
      "I-秦榮光補晉志入庫重出")),
    ("乙", "二說皆通，須擇一", "兩造之說各有據，機械判不出，須人取捨",
     ("C-真疑待裁", "U-漢魏之際待人裁", "I-同題而證據不足以定其為一書，不併",
      "I-孝經原典與補晉志一條是否同書", "I-秦志同題而兩造皆不著撰人待裁")),
    ("丙", "entity 之分合", "併人或拆人，牽動人物庫之骨架，錯了難回頭",
     ("F-entity重出待併", "U-entity實二人", "F-蔡超與蔡超宗是否一人")),
    ("丁", "須外求：查書、查實物、查外部庫", "庫內證據已窮盡",
     ("U-生卒無據而誤", "U-CBDB回填之誤生卒", "E-題名孤證繫Book待裁", "V-連結待人定",
      "H-故宮善本目撰人可疑", "H-千頃堂撰人可疑", "H-故宮善本目撰人為藏文譯語", "G-巴利函題尾殘")),
    ("戊", "著錄本身壞形", "志書之撰人欄或題名欄本身殘壞，須定一個處置通則",
     ("H-國史經籍志撰人欄壞形",)),
]


def open_section(w):
    """把賬上 verdict=open 者按「要你決定什麼」列出。"""
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import verdicts as _v
    op = [x for x in _v.load().values() if x.get('verdict') == 'open']
    if not op:
        return
    by_rule = collections.defaultdict(list)
    for x in op:
        by_rule[x.get('rule') or '（未具 rule）'].append(x)
    placed = set()
    w("## 四、待人裁之 %d 條——**按「要你決定什麼」分**" % len(op))
    w("")
    w("賬上 `verdict=open` 者。**分類依「為什麼機械判不了」，不依哪個檢報的**"
      "——檢之代號對讀者無意義，要決定什麼才有。每條之逐條理由具 `.claude/qa/verdicts.jsonl`"
      "（`python3 .claude/qa/verdicts.py --rule <判準名>` 可列全）。")
    w("")
    for num, name, why, rules in OPEN_GROUPS:
        rows = [x for r in rules for x in by_rule.get(r, [])]
        if not rows:
            continue
        placed.update(rules)
        w("### %s・%s（%d 條）" % (num, name, len(rows)))
        w("")
        w("> %s" % why)
        w("")
        for r in rules:
            lst = by_rule.get(r, [])
            if not lst:
                continue
            w("- **%s**（%d 條）" % (r, len(lst)))
            ex = lst[0]
            if ex.get('why'):
                w("  <br>　　例：`%s` —— %s" % (ex.get('id'), " ".join(str(ex['why']).split())[:200]))
        w("")
    rest = {k: v for k, v in by_rule.items() if k not in placed}
    if rest:
        w("### 己・未歸類（%d 條）" % sum(len(v) for v in rest.values()))
        w("")
        for k, v in sorted(rest.items(), key=lambda kv: -len(kv[1])):
            w("- **%s**（%d 條）" % (k, len(v)))
        w("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args()

    items = load_ki()
    latest = json.load(open(os.path.join(ST, "_latest.json")))
    lanes = {}
    for f in os.listdir(ST):
        if f.startswith("_") or not f.endswith(".json"):
            continue
        try:
            lanes[f[:-5]] = json.load(open(os.path.join(ST, f)))
        except Exception:
            pass

    mat = latest["matrix"]
    total = latest.get("total") or sum(v["total"] for v in mat.values())
    by_kind = collections.defaultdict(list)
    for j in items:
        k = j.get("kind") or "其他"
        by_kind[k if any(k == g[0] for g in GROUPS) else "其他"].append(j)

    L = []
    w = L.append
    w("# 全庫質量複查：待裁清單（第 %d 輪）" % latest.get("round", 0))
    w("")
    w("生成於 %s。**本檔由 `.claude/qa/report.py` 自 `known-issues/` 與 `status/` 重生，"
      "每輪重跑即新**——前兩版是臨時拼的，一輪過去數就陳舊。"
      % datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    w("")
    done = sorted(k for k, v in lanes.items() if v.get("state") == "done")
    run = sorted(k for k, v in lanes.items() if v.get("state") == "running")
    w("九道之中，**已收工 %d 道**（%s）、**在跑 %d 道**（%s）。"
      % (len(done), "、".join(done), len(run), "、".join(run)))
    w("已收 **%d 檔 known-issues**（`.claude/qa/known-issues/`，每檔內載逐條之證與判語）。" % len(items))
    w("")
    w("## 一、全庫掃描今數")
    w("")
    # **不要拿「排除已裁後之數」去跟「首掃之數」相減**——那是兩把不同的尺，相減即誇大。
    # v2 之後 total 是排除已裁者之後的數，故並列三個數，讓讀者自己看得出差在哪。
    _led = latest.get("ledger")
    if _led:
        w("**尚待處置 %s 條**。此數已**排除賬上判為 `normal` 者**（賬 %s 筆），"
          "非與首掃之約 12,800 同尺——那 12,800 是「掃出多少」，此處是「掃出而尚未有裁決者」。"
          % ("{:,}".format(total), "{:,}".format(_led)))
    else:
        w("**%s**（首掃約 12,800，降 %d%%）。"
          % ("{:,}".format(total), round((12800 - total) / 12800 * 100)))
    w("")
    w("坑本 %d 條（`.claude/qa/PITFALLS.md`）。" % latest.get("pitfalls", 0))
    w("")
    w("| 檢 | 數 | 檢 | 數 | 檢 | 數 |")
    w("|---|---:|---|---:|---|---:|")
    ordered = sorted(mat.items(), key=lambda kv: -kv[1]["total"])
    for i in range(0, len(ordered), 3):
        cells = []
        for chk, row in ordered[i:i + 3]:
            cells += [chk, "{:,}".format(row["total"])]
        while len(cells) < 6:
            cells += ["", ""]
        w("| " + " | ".join(cells) + " |")
    w("")
    if latest.get("y_kinds"):
        yk = latest["y_kinds"]
        norm = yk.get("variant", 0) + yk.get("same_name", 0)
        w("**Y 類之細分**：" + "、".join("`%s %d`" % (k, v) for k, v in yk.items())
          + "。其中 `variant`（佛典異譯，坑 45）與 `same_name`（同名異書，坑 60）**本即不當併**，"
          + "共 %d 條是設計上的常態；真正待辦者 %d 條。" % (norm, sum(yk.values()) - norm))
        w("")
    if latest.get("note"):
        w("> " + latest["note"])
        w("")

    w("## 二、各道之數")
    w("")
    w("| 道 | 期 | 批 | 狀態 | 掃出 | 直修 | 查證後修 | 記疑 | 判常態 |")
    w("|---|---|---:|---|---:|---:|---:|---:|---:|")
    tot = collections.Counter()
    for ln in sorted(lanes):
        v = lanes[ln]
        # counts 是 {檢: {found/fixed/researched/recorded/normal}}，須橫加
        agg = collections.Counter()
        for _chk, c in (v.get("counts") or {}).items():
            if isinstance(c, dict):
                for k2 in ("found", "fixed", "researched", "recorded", "normal"):
                    agg[k2] += c.get(k2) or 0
        tot.update(agg)
        w("| %s | %s | %s | %s | %d | %d | %d | %d | %d |" % (
            ln, LANE_PERIOD.get(ln, ""), v.get("batch", ""), v.get("state", ""),
            agg["found"], agg["fixed"], agg["researched"], agg["recorded"], agg["normal"]))
    w("| **合計** | | | | **%d** | **%d** | **%d** | **%d** | **%d** |" % (
        tot["found"], tot["fixed"], tot["researched"], tot["recorded"], tot["normal"]))
    w("")
    w("「掃出」是各道歷輪掃出之累計（同一條跨輪重複掃出者會重複計），"
      "非全庫當下之數（當下見上表 %s）。" % "{:,}".format(total))
    w("")

    w("## 三、待裁清單")
    w("")
    w("分五類，共 **%d 條**。每條皆有 `.claude/qa/known-issues/<檔名>` 可覆按。" % len(items))
    w("")
    for kind, num, name, desc in GROUPS:
        lst = by_kind.get(kind, [])
        if not lst:
            continue
        w("### %s・%s——%s（%d 檔）" % (num, name, desc, len(lst)))
        w("")
        for j in sorted(lst, key=lambda x: (x.get("lane") or "", x.get("_file"))):
            w("- **[%s]** %s" % (j.get("lane", "?"), j.get("title", "（無題）")))
            b = brief(j)
            if b:
                w("  <br>　　%s" % b)
            rec = j.get("recommend")
            if isinstance(rec, str) and len(rec.strip()) > 6:   # 「甲」「乙」之類只是分類字，非建議
                w("  <br>　　**建議**：%s" % " ".join(rec.split())[:180])
            w("  <br>　　`%s`" % j["_file"])
        w("")

    open_section(w)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("已生成 %s（%d 行，%d 檔 known-issues，全庫 %d）" % (a.out, len(L), len(items), total))


if __name__ == "__main__":
    main()
