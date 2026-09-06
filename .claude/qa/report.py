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
DEFAULT_OUT = ("../overview/项目进展/古籍索引网站/版本梳理/先秦/"
               "24-全库质量复查-待裁清单.md")

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
    w("**%s**（首掃約 12,800，降 %d%%）。坑本 %d 條（`.claude/qa/PITFALLS.md`）。"
      % ("{:,}".format(total), round((12800 - total) / 12800 * 100), latest.get("pitfalls", 0)))
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

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("已生成 %s（%d 行，%d 檔 known-issues，全庫 %d）" % (a.out, len(L), len(items), total))


if __name__ == "__main__":
    main()
