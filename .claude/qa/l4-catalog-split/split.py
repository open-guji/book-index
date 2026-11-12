#!/usr/bin/env python3
"""L4 目录书拆分：book-text 转录 → 条目 → 匹配 Work → 提议 indexed_by。

用法（先乾跑，默认不写库）：
  python3 split.py junzhai            # 郡齋讀書志（衢本，維基文庫転录）
  python3 split.py suichu             # 遂初堂書目（Kanripo 文淵閣四庫本）
  python3 split.py wenyuan            # 文淵閣書目（Kanripo）
  加 --apply 把「匹配」档写进 Work 的 indexed_by（幂等：同 source+title_info 已有则跳过）
输出：scratch/<book>-ledger.tsv（逐条：档、条目、候选）。

匹配分档：
  A 作者+朝代吻合的唯一候选   → 写
  B 无撰人可核、题名全库唯一、题名≥4字、该 Work 已有≥2处著录、朝代不晚于志书 → 写（遂初堂/文渊阁只有这档）
  C 题名同、撰人不合或候选多  → 不写，进清单（人核/新建候选）
  N 无同题                    → 不写（新建候选）
"""
import os, re, sys, json, pickle, collections

BI = os.environ.get("BI", "/home/user/book-index")
BT = os.environ.get("BT", "/home/user/open-guji/book-text/Work")
SC = os.environ.get("SC", "/tmp/claude-0/-home-user/6391c0cf-8f64-5490-8408-a53b15323acd/scratchpad/")

RANK = ["pre-qin", "qin-han", "three-kingdoms", "jin", "nanbeichao", "sui-tang",
        "five-dynasties", "song", "liao-jin-yuan", "ming", "qing", "modern"]
BOOKS = {
    # key: (source 名, source_bid, 志书时代上限, 文本目录)
    "junzhai": ("郡齋讀書志", "d59f2hpm3myp", "song", "m/y/p/d59f2hpm3myp/default"),
    "suichu": ("遂初堂書目", "d59f2hs9m96q", "song", "9/6/q/d59f2hs9m96q/kanripo"),
    "wenyuan": ("文淵閣書目", "d59f2njb2w3m", "ming", "w/3/m/d59f2njb2w3m/default"),
}
FOLD = str.maketrans({"爲": "為", "録": "錄", "説": "說", "裏": "裡", "並": "并", "歴": "歷", "厯": "歷",
                      "註": "注", "於": "于", "羣": "群", "衆": "眾", "着": "著", "後": "后", "傳": "傳"})
DYN = r"(?:皇朝|本朝|國朝|偽蜀|僞蜀|偽唐|僞唐|偽|僞|後漢|前漢|西漢|東漢|後魏|北魏|北齊|北周|後周|後唐|後晉|石晉|南唐|吳越|前蜀|後蜀|蜀|吳|魏|晉|宋|齊|梁|陳|隋|唐|漢|秦|楚|周|遼|金|元|明|清|唐末|宋初|五代)"
ROLE = r"(?:撰|著|編|編次|編集|集|纂|纂集|述|作|輯|註|注|箋|疏|解|釋|校|訂|書|錄|記|修|譔|等)"


def norm(t):
    t = re.sub(r"[《》〈〉「」『』\[\]（）()<>△\s·，。、；：]", "", t)
    t = re.sub(r"[一二三四五六七八九十百千]+[卷篇冊册部]$", "", t)
    return t.translate(FOLD)


def load_idx():
    idx = pickle.load(open(SC + "idx.pkl", "rb"))
    by = collections.defaultdict(list)
    for wid, v in idx.items():
        for t in [v["t"]] + list(v["at"] or []):
            if isinstance(t, str) and t:
                by[norm(t)].append(wid)
    return idx, by


def clean_author(s):
    s = re.sub(r"^" + DYN + "+", "", s)
    s = re.sub(r"[等]$", "", s)
    return s


def parse_junzhai():
    """維基文庫衢本：`## 類` 为 section；`△?《題》卷數` 或 `作者《題》卷數` 为条首；其后 `右…` 为提要。"""
    d = os.path.join(BT, BOOKS["junzhai"][3])
    out = []
    sec = ""
    for fn in sorted(f for f in os.listdir(d) if re.fullmatch(r"\d{3}\.md", f)):
        cur = None
        for ln in open(os.path.join(d, fn), encoding="utf-8").read().split("\n"):
            ln = ln.rstrip()
            if not ln:
                continue
            m = re.match(r"^## (.+)$", ln)
            if m:
                h = m.group(1)
                if h.startswith("卷"):
                    continue
                if h.startswith("△") or "《" in h:  # 維基把部分条首误作标题
                    ln = h
                else:
                    sec = h
                    cur = None
                    continue
            m = re.match(r"^(△?)(?:([^《》，。：「」\s]{1,6}))?《([^》]+)》([^《》，。]*)(.*)$", ln)
            if m and not ln.startswith("右") and len(ln) < 120:
                pre, au, title, juan, rest = m.groups()
                cur = dict(sec=sec, title=title, juan=juan.strip(), head=ln, summary=[], pre_author=au or "", tri=pre,
                           file=fn)
                out.append(cur)
                continue
            if cur is not None:
                cur["summary"].append(ln)
    for e in out:
        s = "\n".join(e["summary"])
        e["summary"] = s
        a = e["pre_author"]
        if not a:
            m = re.match(r"^右(?:" + DYN + r"|[^，。]{0,0})*([^，。：；]{2,12}?)(?:" + ROLE + r")", s)
            if m:
                a = m.group(1)
        e["author_raw"] = a
        e["author"] = clean_author(a) if a else ""
    return out


def parse_listbook(key):
    """遂初堂／文淵閣：只有题名行（Kanripo 竖排）。遂初堂：一行一书，部类标题行；文淵閣：两栏。"""
    d = os.path.join(BT, BOOKS[key][3])
    out = []
    sec = ""
    for fn in sorted(f for f in os.listdir(d) if re.fullmatch(r"\d{3}\.md", f)):
        for ln in open(os.path.join(d, fn), encoding="utf-8").read().split("\n"):
            ln = ln.rstrip()
            if not ln.strip() or ln.startswith("##"):
                continue
            if key == "wenyuan":
                body = re.sub(r"[<>|]", "", ln.strip())
                for m in re.finditer(r"([^\u3000]+?)((?:[一二三四五六七八九十百千萬]+[部匣片冊册卷套]+)+)", body):
                    t, jn = m.group(1).strip(), m.group(2)
                    if 1 < len(t) <= 24:
                        out.append(dict(sec=sec, title=t, juan=jn, head=t + jn, summary="",
                                        author_raw="", author="", file=fn))
            else:
                if key == "suichu" and fn != "003.md":
                    continue
                if ln.startswith("\u3000\u3000") and not re.search(r"\u3000{2}\S+\u3000{2,}\S", ln.strip("\n")):
                    h = ln.strip("\u3000 ")
                    if "撰" not in h and len(h) <= 8:
                        sec = h
                        continue
                for p in [p for p in re.split(r"\u3000{2,}", ln.strip("\u3000 ")) if p]:
                    if p in ("欽定四庫全書", "遂初堂書目") or len(p) > 14:
                        continue
                    out.append(dict(sec=sec, title=p, juan="", head=p, summary="", author_raw="", author="", file=fn))
    return out


def match(e, idx, by, era):
    k = norm(e["title"])
    if len(k) < 2:
        return "N", []
    cands = [w for w in by.get(k, []) if (idx[w]["p"] is None or RANK.index(idx[w]["p"]) <= RANK.index(era))]
    allc = by.get(k, [])
    if not allc:
        return "N", []
    if e["author"]:
        a = e["author"]
        hit = [w for w in cands if any(len(n) >= 2 and (n in a or a in n) for n in idx[w]["a"])]
        if len(hit) == 1:
            return "A", hit
        if len(hit) > 1:
            return "C", hit
        return "C", allc[:6]
    # 无撰人：全库同题唯一且朝代合
    if len(allc) == 1 and len(cands) == 1 and idx[cands[0]]["p"] is not None:
        # 无撰人只凭题名：需题名≥4字且该 Work 已有≥2处独立著录（石刻孝經→李師徳 之类单源弱对应不写）
        if len(k) >= 4 and len(idx[cands[0]]["src"]) >= 2:
            return "B", cands
        return "C", cands
    return "C", allc[:6]


def main():
    key = sys.argv[1]
    apply = "--apply" in sys.argv
    src, sbid, era, _ = BOOKS[key]
    ents = parse_junzhai() if key == "junzhai" else parse_listbook(key)
    idx, by = load_idx()
    cnt = collections.Counter()
    rows = []
    props = collections.defaultdict(list)
    for e in ents:
        g, c = match(e, idx, by, era)
        cnt[g] += 1
        rows.append((g, e["file"], e["sec"], e["title"], e["juan"], e["author"], ",".join(c)))
        if g in "AB":
            props[c[0]].append(e)
    led = os.path.join(SC, f"{key}-ledger.tsv")
    with open(led, "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(r) + "\n")
    print(key, "条目", len(ents), dict(cnt), "→ 台账", led)
    if apply:
        n = 0
        for wid, es in props.items():
            if wid == sbid:
                continue
            p = os.path.join(BI, idx[wid]["path"])
            raw = open(p, encoding="utf-8").read()
            d = json.loads(raw)
            lines = raw.split("\n")
            ind = len(lines[1]) - len(lines[1].lstrip(" ")) if len(lines) > 2 and lines[0] == "{" else 2
            nl = raw.endswith("\n")
            ib = d.setdefault("indexed_by", [])
            for e in es:
                ti = e["head"] if key != "junzhai" else (e["head"])
                if any(x.get("source") == src and x.get("title_info") == ti for x in ib):
                    continue
                ent = {"source": src, "source_bid": sbid, "title_info": ti}
                if e["summary"]:
                    ent["summary"] = e["summary"]
                if e["author_raw"]:
                    ent["author_info"] = e["author_raw"]
                if e["sec"]:
                    ent["section"] = e["sec"]
                if e["juan"]:
                    ent["juan_count"] = e["juan"]
                ib.append(ent)
                n += 1
            with open(p, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=ind)
                if nl:
                    f.write("\n")
        print("写入 indexed_by", n)


if __name__ == "__main__":
    main()
