#!/usr/bin/env python3
"""通志藝文略 N 档 → 新建 Work（只建注文里撰人干净的；无撰人者不建）。用法：newwork.py [--apply]"""
import os, re, sys, json, importlib.util, collections
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sp", os.path.join(here, "split.py")); sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
sys.path.insert(0, os.path.join(sp.BI, ".claude/qa"))
import mintid

DIG = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
def cn(s):
    s = s.replace("巻", "卷").rstrip("卷")
    n = 0; cur = 0
    for c in s:
        if c in DIG: cur = DIG[c]
        elif c == "十": n += (cur or 1) * 10; cur = 0
        elif c == "百": n += (cur or 1) * 100; cur = 0
        elif c == "千": n += (cur or 1) * 1000; cur = 0
    return n + cur
DYN_MAP = {"周": "北周", "梁": "梁", "唐": "唐", "晉": "晉", "宋": "宋", "宋朝": "宋", "魏": "魏", "吳": "吳", "漢": "漢", "隋": "隋",
           "齊": "齊", "陳": "陳", "後魏": "北魏", "後周": "後周", "偽唐": "南唐", "秦": "秦", "後漢": "東漢"}
AMBIG = {"周", "梁", "宋", "魏", "吳", "漢", "齊", "陳", "秦", "唐", "隋", "晉"}
BAD = re.compile(r"[府卿郎史使太守夫書監師君見隋志書目一二三四五六七八九十]|等|居士|道人|老君|真人|先生|氏|母|妃|僧|釋|子$")
SUF = {"撰": "撰", "注": "注", "註": "注", "修": "修", "編": "編", "集": "輯", "纂": "纂", "述": "述", "著": "撰", "譔": "撰"}

def extract(note):
    m = re.match(r"^(宋朝|後魏|後周|偽唐|後漢|周|梁|唐|晉|宋|魏|吳|漢|隋|齊|陳|秦)?([一-鿿]{2,3}?)(撰|注|註|修|編|集|纂|述|著|譔)?$", note.strip())
    if not m: return None
    dyn, name, suf = m.groups()
    if BAD.search(name) or name.endswith("人"): return None
    if name in ("歐陽", "司馬", "諸葛", "令狐", "上官", "宇文", "慕容", "皇甫"): return None
    if dyn in AMBIG and len(name) == 2: return None   # 「陳堯佐」類：朝代字与姓难分，不建
    return DYN_MAP.get(dyn), name, SUF.get(suf)

import difflib
_AU = None
def near_dup(title, name, idx):
    """同撰人名下已有题名相近（相似度≥0.6 或互为子串）的 Work → 疑似同书异写，不新建（进人核）。"""
    global _AU
    if _AU is None:
        _AU = collections.defaultdict(list)
        for w, v in idx.items():
            for a in v["a"]: _AU[a].append(v["t"])
    t = sp.norm(title)
    for t2 in _AU.get(name, []):
        t2 = sp.norm(t2)
        if t in t2 or t2 in t or difflib.SequenceMatcher(None, t, t2).ratio() >= 0.6: return True
    return False

def main():
    apply = "--apply" in sys.argv
    idx, by = sp.load_idx(); ents = sp.parse_tongzhi()
    seen = set(); new = []
    for e in ents:
        if sp.match(e, idx, by, "song")[0] != "N" or not e["note"]: continue
        r = extract(e["note"])
        if not r: continue
        if re.search(r"集.+集", e["title"]) or "解題" in e["title"]: continue
        if not r[2] or len(e["title"]) < 5 or e["title"][0] in "又續後": continue  # 只收责任方式明、题名≥5字者（短题易是折行残片）
        if len(e["title"]) < 3 or re.search(r"[一二三四五六七八九十]$", e["title"]): continue
        if re.search(r"[一二三四五六七八九十百]+篇", e["title"]) or len(e["title"]) > 14: continue
        if near_dup(e["title"], r[1], idx): continue
        key = (sp.norm(e["title"]), r[1])
        if key in seen: continue
        seen.add(key); new.append((e, r))
    print("可建", len(new))
    if not apply:
        import random; random.seed(11)
        for e, r in random.sample(new, min(200, len(new))): print(e["sec"], "|", e["head"], "|", r)
        return

    ids = mintid.mint("Work", "l4", len(new))
    for (e, (dyn, name, suf)), i in zip(new, ids):
        m = re.match(r"^(.*?)([一二三四五六七八九十百千]+[卷巻])$", e["head"])
        a = {"name": name, "role": suf or "撰"}
        if dyn: a["dynasty"] = dyn
        if not suf: a["role_basis"] = "通志注文未標責任方式，暫作撰"
        d = {"schema_version": 1, "id": i, "type": "work", "title": e["title"], "authors": [a],
             "measures": [{"unit": "卷", "number": cn(m.group(2))}], "measure_info": m.group(2).replace("巻", "卷"),
             "indexed_by": [{"source": "通志藝文略", "source_bid": "d59gc4hif56o", "title_info": e["head"], "author_info": e["note"], "section": e["sec"]}],
             "period_upper": "song",
             "period_upper_basis": "catalog_bound：所繫著錄為《通志藝文略》（南宋鄭樵（1161）），故不晚於 song",
             "ai_note": "2026-11-12 L4 目錄書拆分：據《通志》藝文略著錄新建（庫內無同題 Work）。撰人取自著錄注文，未覆核，未掛 Entity。",
             "revision": "1.0.0", "revised_at": "2026-11-12"}
        d["indexed_by"][0] = {k: v for k, v in d["indexed_by"][0].items() if v}
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, e["title"])
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("新建", len(new))
main()
