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
    a = re.sub(r"^(?:宋朝|後魏|後周|偽唐|後漢|周|梁|唐|晉|宋|魏|吳|漢|隋|齊|陳|秦|本朝|國朝|皇朝)", "", raw.strip())
    a = re.sub(r"[等撰注編集纂述著]+$", "", a)
    for n in (3, 2, 4):
        nm = a[:n]
        if len(a) - n not in (0, 2) or nm not in ENTS: continue
        c = [x for x in ENTS[nm] if x[1] in OK]
        if len(c) == 1: return nm, c[0][0], c[0][2]
        return None
    return None

DYNRE = r"(宋朝|後魏|後周|偽唐|後漢|周|梁|唐|晉|宋|魏|吳|漢|隋|齊|陳|秦|本朝|國朝|皇朝)"
DYN2 = {"宋朝": "宋", "本朝": "宋", "國朝": "宋", "後魏": "北魏", "偽唐": "南唐", "後漢": "東漢", "皇朝": "宋"}
ANON = {"", "不題", "或人", "闕名", "失名", "不著名氏", "未詳"}
SUR = set("王李張劉陳楊黃趙吳周徐孫馬朱胡郭何高林羅鄭梁謝宋唐許韓馮鄧曹彭曾蕭田董袁潘于蔣蔡余杜葉程蘇魏呂丁任沈姚盧姜崔鍾譚陸汪范金石廖賈夏韋傅方白鄒孟熊秦邱江尹薛閻段雷侯龍史陶黎賀顧毛郝龔邵萬錢嚴賴覃洪武莫孔湯向常溫康施文牛樊葛邢安齊易喬伍龐顏倪莊聶章魯嵇祝苗裴焦滕狄邊晏歐陽司馬諸葛上官令狐宇文慕容皇甫獨孤長孫鮮於".replace("歐陽","").replace("司馬","").replace("諸葛","").replace("上官","").replace("令狐","").replace("宇文","").replace("慕容","").replace("皇甫","").replace("獨孤","").replace("長孫","").replace("鮮於",""))
BADN = ("江南", "淮南", "河南", "河東", "西蜀", "東吳")
SUR2 = {"歐陽", "司馬", "諸葛", "上官", "令狐", "宇文", "慕容", "皇甫", "獨孤", "長孫", "鮮於"}
def fold(x): return x.replace("範", "范").replace("徳", "德")
def surname_ok(nm): return nm[:2] in SUR2 or nm[0] in SUR
def title_author(t):
    for n in (3, 2):
        nm = fold(t[:n])
        if t[n:] in ("集", "詩", "文集", "歌詩", "詩集", "奏議", "詩話") and nm in ENTS and surname_ok(nm):
            c = [x for x in ENTS[nm] if x[1] in OK]
            if len(c) == 1: return nm, c[0][0], c[0][2]
    return None
def newperson(raw):
    """人物库里没有唯一同名者：返回 (name, dynasty, True)；无撰人返回 None 表佚名；无法可靠切分返回 False。"""
    raw = raw.strip()
    if raw in ANON: return None
    m = re.match(r"^" + DYNRE + r"(?=[一-鿿]{2})", raw)
    dyn = DYN2.get(m.group(1), m.group(1)) if m else None
    a = raw[m.end():] if m else raw
    a = re.sub(r"[等撰注編集纂述著所]+$", "", a)
    if "字" in a: a = a.split("字")[0]
    if not re.fullmatch(r"[一-鿿]{2,5}", a): return False
    n = {2: 2, 3: 3, 4: 2, 5: 3}[len(a)] if len(a) in (2, 3, 4, 5) else 0
    nm = a[:n]
    nm = fold(nm)
    if nm.startswith(BADN) or not surname_ok(nm) or re.search(r"[府卿郎史使太守夫書監師君見氏母妃僧釋中何按皇朝從父公]", nm) or nm.endswith(("人", "子")) or nm in ("歐陽", "司馬", "諸葛", "令狐", "上官", "宇文", "慕容", "皇甫"): return False
    if dyn in ("周","梁","宋","魏","吳","漢","齊","陳","秦","唐","隋","晉") and len(a) == 2: return False
    return nm, dyn, True

SUMONLY = False
SKIP = {"嘉祐時政記", "三劉漢書"}   # 多人合撰，只取首位会错
ALIAS = {"唐玄宗": ("唐玄宗", "hixhd2f8wam8", "唐"), "宋徽宗": ("宋徽宗", "hixhd2h9btiy", "宋")}
# 逐条人工判定（读原文解题）：题名 → 撰人原文（带朝代前缀）
MANUAL = {"陸龜笠澤叢書": "唐陸龜蒙字魯望", "遊氏中庸解": "皇朝遊酢字定夫", "太常禮書": "皇朝陳祥道字用之", "蔡邕獨斷": "漢蔡邕",
          "智永千字文": "梁周興嗣", "英公字源": "皇朝釋夢英", "武陵法帖": "皇朝王若谷", "富公語錄": "皇朝富弼", "張浮休使遼錄": "皇朝張舜民",
          "虜廷雜記": "皇朝趙志忠", "蜀三神祠碑文": "皇朝井度", "吳氏西齊書目": "唐吳兢", "明皇老子註二卷疏": "唐唐玄宗", "唐明皇註孝經": "唐唐玄宗",
          "聖宋茶論": "皇朝宋徽宗", "三十家註老子": "唐張君相", "阮逸註中說": "皇朝阮逸"}
PER = {"唐": "sui-tang", "隋": "sui-tang", "宋": "song", "晉": "jin", "梁": "nanbeichao", "陳": "nanbeichao", "齊": "nanbeichao", "北魏": "nanbeichao",
       "漢": "qin-han", "東漢": "qin-han", "魏": "three-kingdoms", "吳": "three-kingdoms", "南唐": "five-dynasties", "周": "sui-tang", "秦": "qin-han"}

DY = r"(皇朝|本朝|國朝|宋朝|唐|宋|晉|梁|陳|隋|齊|周|魏|吳|漢|後漢|後魏|後周|偽唐|南唐|偽蜀|前蜀|後蜀|西晉|東晉|北齊|北周)"
def sumauthor(sm):
    """从提要首句取撰人：返回 raw 字符串（带朝代前缀）、"" 表示未取到。"""
    if re.match(r"^右(不記|不著|不見|不題|未詳|闕|無撰|失名|不知)", sm): return "不題"
    m = re.match(r"^右" + DY + r"?([一-鿿]{2,5}?)(?:字([一-鿿]{1,3}))?(?:也|，|。|、|所?[撰著集編纂述譔注註解作輯錄校]|等)", sm)
    if not m: return ""
    dy, nm, zi = m.groups()
    if re.search(r"[初年中間時代世朝]", nm): return ""
    return (dy or "") + nm + (("字" + zi) if zi else "")

def main():
    apply = "--apply" in sys.argv
    idx, by = sp.load_idx(); ents = sp.parse_junzhai()
    new = []; seen = set(); ent_pre = {}
    for e in ents:
        if sp.match(e, idx, by, "song")[0] != "N": continue
        t = e["title"]
        if len(t) < 4 or t[0] in "又續後" or SEC_BAD.search(t) or "解題" in t or len(t) > 14 or re.search(r"[^一-鿿]", t): continue
        if not e["author_raw"] and not SUMONLY: pass
        if t in SKIP: continue
        e["author_raw"] = MANUAL.get(t) or sumauthor(e["summary"]) or e["author_raw"]
        r = resolve(fold(e["author_raw"])) if e["author_raw"] else None
        rr = re.sub(r"^(?:皇朝|唐|宋)", "", e["author_raw"]); r = ALIAS.get(rr) or r
        p = (r[0], r[2]) if r else newperson(e["author_raw"])
        if r: ent_pre[r[0]] = r[1]
        if p is False or re.search(r"[，、；？]《|》.*《", e["head"]): continue
        if p and p[0] and t[0] in SUR and fold(p[0])[0] != fold(t)[0] and t not in MANUAL: continue
        ta = None
        if p is None:   # 无撰人：题名带人名者（某某集）取题名前缀的唯一 Entity；别集／总集类取不到则不建
            ta = title_author(t)
            if not ta and re.search(r"別集|總集|詩", e["sec"] + t): continue
        if ta: name, dyn = ta[0], ta[2]; ent_pre[name] = ta[1]
        else:
            name, dyn = (p[0], p[1]) if p else ("佚名", None)
            if name == "佚名" and (t[0] in SUR or t[:2] in SUR2 or re.search(r"[公氏相卿]", t[:3])): continue
        if near_dup(t, name, idx): continue
        if (sp.norm(t), name) in seen: continue
        seen.add((sp.norm(t), name)); new.append((e, name, dyn))
    people = sorted({(n, d) for _, n, d in new if n != "佚名" and n not in ent_pre}, key=lambda x: x[0])
    print("可建 Work", len(new), "新建人物", len(people), "佚名", sum(1 for _, n, _d in new if n == "佚名"))
    if not apply:
        random.seed(7)
        for e, n, d in random.sample(new, min(70, len(new))): print(e["sec"], "|", e["head"], "|", e["author_raw"], "->", n, d)
        return
    pids = mintid.mint("Entity", "l4", len(people)); pid = {}
    for (n, d), i in zip(people, pids):
        pid[n] = i
        o = {"schema_version": 1, "id": i, "type": "entity", "subtype": "people", "primary_name": n}
        if d:
            o["dynasty"] = d; o["dynasty_basis"] = "據《郡齋讀書志》責任者著錄"
            if d in PER: o["period"] = PER[d]; o["period_basis"] = "據 dynasty「%s」歸併" % d
        o["ai_note"] = "2026-11-15 L4 目錄書拆分：據《郡齋讀書志》責任者新建；人物庫中無可確認同人的同名條（用戶 11-02 口徑：無佐證不掛舊條）。"
        o["revision"] = "1.0.0"; o["revised_at"] = "2026-11-15"
        p = "Entity/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, n)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(json.dumps(o, ensure_ascii=False, indent=2) + "\n")
    ids = mintid.mint("Work", "l4", len(new))
    for (e, name, dyn), i in zip(new, ids):
        a = {"name": name, "role": "撰"}
        if name != "佚名":
            a["entity_id"] = ent_pre.get(name) or pid[name]; a["role_basis"] = "郡齋讀書志著錄未標責任方式，暫作撰"
            if dyn: a["dynasty"] = dyn
        ju = e["juan"].replace("巻", "卷").replace("卷數", "")
        d = {"schema_version": 1, "id": i, "type": "work", "title": e["title"], "authors": [a]}
        if re.fullmatch(r"[一二三四五六七八九十百千]+卷", ju):
            d["measures"] = [{"unit": "卷", "number": cn(ju)}]; d["measure_info"] = ju
        d.update({"indexed_by": [{k: v for k, v in {"source": "郡齋讀書志", "source_bid": "d59f2hpm3myp", "title_info": e["head"], "author_info": e["author_raw"], "section": e["sec"], "summary": e["summary"][:400]}.items() if v}],
             "period_upper": "song",
             "period_upper_basis": "catalog_bound：所繫著錄為《郡齋讀書志》（南宋晁公武），故不晚於 song",
             "ai_note": "2026-11-15 L4 目錄書拆分：據《郡齋讀書志》著錄新建（庫內無同題 Work）。" + ("無撰人者署佚名。" if name == "佚名" else "撰人新建人物條，未覆核。"),
             "revision": "1.0.0", "revised_at": "2026-11-15"})
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, e["title"])
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("新建 Work", len(new), "人物", len(people))
main()
