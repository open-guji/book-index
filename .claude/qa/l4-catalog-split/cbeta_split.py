#!/usr/bin/env python3
"""CBETA 经录（T55 n2146/2148/2151/2152）→ 条目 → 匹配 Work → indexed_by。
用法：cbeta_split.py <2146|2148|2151|2152> [--apply]   环境变量 CB=CBETA xml-p5 的 T55 目录。
条目来自 CBETA 语义标记：cb:jl_title（经题）、cb:jl_juan（卷数）、cb:jl_byline（译者／朝代）。
匹配：题名（去「佛說」前缀、简繁异写折叠）同＋译者名与候选 Work 作者名有 2 字相连重合，时代不晚于志书 → A；
      无译者可核时题名唯一且 Work 已有≥2 处著录 → B；其余不写。"""
import os, re, sys, json, collections, difflib, importlib.util
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sp", os.path.join(here, "split.py")); sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
CB = os.environ.get("CB", "/tmp/claude-0/cbeta/xml-p5/T/T55")
BOOKS = {
    "2146": ("眾經目錄", "d59fyt4wtfk0"),      # 隋法經
    "2148": ("眾經目錄", "d59fyiq2zpxc"),      # 唐靜泰
    "2151": ("古今譯經圖紀", "d59f28lx3xfn"),
    "2152": ("續古今譯經圖紀", "d59f28k1dfk2"),
}
F = str.maketrans({"彥": "彦", "徳": "德", "隠": "隱", "寗": "寧", "衞": "衛", "彌": "弥", "釋": "", "竺": "", "支": "支"})
def fold(s): return s.translate(F).replace("沙門", "").replace("三藏", "").replace("法師", "")
def tx(s): return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", re.sub(r"<anchor[^>]*/>|<lb[^>]*/>|<pb[^>]*/>", "", s)))

def tkey(t):
    t = sp.norm(t)
    return re.sub(r"^(佛說|佛说)", "", t)

def parse(n):
    t = open(os.path.join(CB, "T55n%s.xml" % n), encoding="utf-8").read()
    b = t[t.index("<body>"):]
    b = re.sub(r"<anchor[^>]*/>|<lb[^>]*/>|<pb[^>]*/>|<space[^>]*/>|<milestone[^>]*/>", "", b)
    out = []
    if n in ("2146", "2148"):
        sec = ""
        for m in re.finditer(r"(<cb:mulu[^>]*>([^<]*)</cb:mulu>)|(<item [^>]*>(.*?)</item>)", b, re.S):
            if m.group(1):
                sec = m.group(2).strip() or sec; continue
            it = m.group(4)
            ti = re.search(r"<cb:jl_title>(.*?)</cb:jl_title>", it, re.S)
            if not ti: continue
            ju = re.search(r"<cb:jl_juan[^>]*>(.*?)</cb:jl_juan>", it, re.S)
            by = re.search(r"<cb:jl_byline>(.*?)</cb:jl_byline>", it, re.S)
            out.append(dict(sec=sec, title=tx(ti.group(1)), juan=tx(ju.group(1)) if ju else "", byline=tx(by.group(1)) if by else "", text=tx(it)))
    else:
        sec = ""
        for m in re.finditer(r"(<cb:mulu level=\"1\"[^>]*>([^<]*)</cb:mulu>)|(<p [^>]*>(.*?)</p>)", b, re.S):
            if m.group(1):
                sec = m.group(2).strip(); continue
            p = m.group(4)
            by = re.search(r"<cb:jl_byline>(.*?)</cb:jl_byline>", p, re.S)
            person = tx(by.group(1)) if by else ""
            for tm in re.finditer(r"<cb:jl_title>(.*?)</cb:jl_title>(?:<note[^>]*><cb:jl_juan[^>]*>(.*?)</cb:jl_juan>)?", p, re.S):
                # 所在句
                s0 = p.rfind("。", 0, tm.start()); s1 = p.find("。", tm.end())
                sent = tx(p[s0 + 1: s1 + 1 if s1 >= 0 else len(p)])
                out.append(dict(sec=sec, title=tx(tm.group(1)), juan=tx(tm.group(2) or ""), byline=person, text=sent))
    return out

def main():
    n = sys.argv[1]; apply = "--apply" in sys.argv
    src, sbid = BOOKS[n]
    idx, by = sp.load_idx()
    tk = collections.defaultdict(list)
    for w, v in idx.items():
        for t in [v["t"]] + list(v["at"] or []):
            if isinstance(t, str) and t: tk[tkey(t)].append(w)
    ents = parse(n); cnt = collections.Counter(); props = collections.defaultdict(list); rows = []
    for e in ents:
        k = tkey(e["title"])
        allc = tk.get(k, [])
        cands = [w for w in allc if idx[w]["p"] is None or sp.RANK.index(idx[w]["p"]) <= sp.RANK.index("sui-tang")]
        g, c = "N", []
        if allc:
            b = fold(e["byline"]) if e["byline"] else ""
            def ok(w):
                for nm in idx[w]["a"]:
                    nm = fold(nm)
                    if len(nm) >= 2 and difflib.SequenceMatcher(None, nm, b, autojunk=False).find_longest_match(0, len(nm), 0, len(b)).size >= min(3, len(nm)): return True
                return False
            if b:
                hit = [w for w in cands if ok(w)]
                g, c = ("A", hit) if len(hit) == 1 else ("C", hit or allc[:6])
            else:
                g, c = "C", allc[:6]   # 无译者不写（同题异卷的单品经易错挂，如「大寶積經一卷」）
        cnt[g] += 1; rows.append((g, e["sec"], e["title"], e["juan"], e["byline"], ",".join(c)))
        if g in "AB": props[c[0]].append(e)
    led = os.path.join(sp.SC, "cbeta%s-ledger.tsv" % n)
    open(led, "w", encoding="utf-8").write("\n".join("\t".join(r) for r in rows))
    print(n, src, "条目", len(ents), dict(cnt), "台账", led)
    if apply:
        w_n = 0
        for wid, es in props.items():
            if wid == sbid: continue
            p = os.path.join(sp.BI, idx[wid]["path"]); raw = open(p, encoding="utf-8").read(); d = json.loads(raw)
            lines = raw.split("\n"); ind = len(lines[1]) - len(lines[1].lstrip(" ")) if len(lines) > 2 and lines[0] == "{" else 2
            ib = d.setdefault("indexed_by", [])
            for e in es:
                ti = e["title"] + e["juan"]
                if any(x.get("source") == src and x.get("source_bid") == sbid and x.get("title_info") == ti for x in ib): continue
                ent = {"source": src, "source_bid": sbid, "title_info": ti}
                if e["text"]: ent["summary"] = e["text"]
                if e["byline"]: ent["author_info"] = e["byline"]
                if e["juan"]: ent["juan_count"] = e["juan"]
                if e["sec"]: ent["section"] = e["sec"]
                ib.append(ent); w_n += 1
            open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=ind) + ("\n" if raw.endswith("\n") else ""))
        print("写入", w_n)
main()
