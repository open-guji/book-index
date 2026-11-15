#!/usr/bin/env python3
"""郡齋讀書志 N 档 → 新建 Work。撰人须在人物库里有唯一的宋及以前同名 Entity（前缀最长匹配，余≤2字当作字号）；否则不建。
用法：newwork_junzhai.py [--apply]"""
import os, re, sys, json, pickle, importlib.util, collections, random
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("nw", os.path.join(here, "newwork.py"))
src = open(os.path.join(here, "newwork.py"), encoding="utf-8").read().rsplit("\nmain()", 1)[0]
ns = {"__file__": os.path.join(here, "newwork.py")}; exec(compile(src, "newwork", "exec"), ns)
sp, near_dup, cn, mintid = ns["sp"], ns["near_dup"], ns["cn"], ns["mintid"]
ENTS = pickle.load(open("/tmp/claude-0/ents.pkl", "rb"))
OK = {"pre-qin", "qin-han", "three-kingdoms", "jin", "nanbeichao", "sui-tang", "five-dynasties", "song", None}
SEC_BAD = re.compile(r"[一二三四五六七八九十]$")

def resolve(raw):
    a = re.sub(r"^(?:宋朝|後魏|後周|偽唐|後漢|周|梁|唐|晉|宋|魏|吳|漢|隋|齊|陳|秦|本朝|國朝)", "", raw.strip())
    a = re.sub(r"[等撰注編集纂述著]+$", "", a)
    for n in (3, 2, 4):
        nm = a[:n]
        if len(a) - n not in (0, 2) or nm not in ENTS: continue
        c = [x for x in ENTS[nm] if x[1] in OK]
        if len(c) == 1: return nm, c[0][0], c[0][2]
        return None
    return None

DYNRE = r"(宋朝|後魏|後周|偽唐|後漢|周|梁|唐|晉|宋|魏|吳|漢|隋|齊|陳|秦|本朝|國朝)"
DYN2 = {"宋朝": "宋", "本朝": "宋", "國朝": "宋", "後魏": "北魏", "偽唐": "南唐", "後漢": "東漢"}
ANON = {"", "不題", "或人", "闕名", "失名", "不著名氏", "未詳"}
def newperson(raw):
    """人物库里没有唯一同名者：返回 (name, dynasty, True)；无撰人返回 None 表佚名；无法可靠切分返回 False。"""
    raw = raw.strip()
    if raw in ANON: return None
    m = re.match(r"^" + DYNRE + r"(?=[一-鿿]{2})", raw)
    dyn = DYN2.get(m.group(1), m.group(1)) if m else None
    a = raw[m.end():] if m else raw
    a = re.sub(r"[等撰注編集纂述著]+$", "", a)
    if not re.fullmatch(r"[一-鿿]{2,5}", a): return False
    n = {2: 2, 3: 3, 4: 2, 5: 3}[len(a)] if len(a) in (2, 3, 4, 5) else 0
    nm = a[:n]
    if re.search(r"[府卿郎史使太守夫書監師君見氏母妃僧釋]", nm) or nm.endswith(("人", "子")) or nm in ("歐陽", "司馬", "諸葛", "令狐", "上官", "宇文", "慕容", "皇甫"): return False
    if dyn in ("周","梁","宋","魏","吳","漢","齊","陳","秦","唐","隋","晉") and len(a) == 2: return False
    return nm, dyn, True

def main():
    apply = "--apply" in sys.argv
    idx, by = sp.load_idx(); ents = sp.parse_junzhai()
    new = []; seen = set()
    for e in ents:
        if sp.match(e, idx, by, "song")[0] != "N" or not e["author_raw"]: continue
        t = e["title"]
        if len(t) < 4 or t[0] in "又續後" or SEC_BAD.search(t) or "解題" in t or len(t) > 14 or not e["juan"]: continue
        if not re.fullmatch(r"[一二三四五六七八九十百千]+[卷巻]", e["juan"].replace("卷數", "")): continue
        r = resolve(e["author_raw"])
        if not r or near_dup(t, r[0], idx): continue
        if (sp.norm(t), r[0]) in seen: continue
        seen.add((sp.norm(t), r[0])); new.append((e, r))
    print("可建", len(new))
    if not apply:
        random.seed(5)
        for e, r in random.sample(new, min(60, len(new))): print(e["sec"], "|", e["head"], "|", e["author_raw"], "->", r)
        return
    ids = mintid.mint("Work", "l4", len(new))
    for (e, (name, eid, dyn)), i in zip(new, ids):
        a = {"name": name, "role": "撰", "entity_id": eid, "role_basis": "郡齋讀書志著錄未標責任方式，暫作撰"}
        if dyn: a["dynasty"] = dyn
        ju = e["juan"].replace("巻", "卷")
        d = {"schema_version": 1, "id": i, "type": "work", "title": e["title"], "authors": [a],
             "measures": [{"unit": "卷", "number": cn(ju)}], "measure_info": ju,
             "indexed_by": [{"source": "郡齋讀書志", "source_bid": "d59f2hpm3myp", "title_info": e["head"], "author_info": e["author_raw"], "section": e["sec"], "summary": e["summary"][:400]}],
             "period_upper": "song",
             "period_upper_basis": "catalog_bound：所繫著錄為《郡齋讀書志》（南宋晁公武），故不晚於 song",
             "ai_note": "2026-11-15 L4 目錄書拆分：據《郡齋讀書志》著錄新建（庫內無同題 Work）。撰人以人物庫唯一同名 Entity 掛接，未覆核。",
             "revision": "1.0.0", "revised_at": "2026-11-15"}
        d["indexed_by"][0] = {k: v for k, v in d["indexed_by"][0].items() if v}
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, e["title"])
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("新建", len(new))
main()
