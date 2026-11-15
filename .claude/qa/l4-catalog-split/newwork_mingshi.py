#!/usr/bin/env python3
"""明史藝文志 N 档 → 新建 Work。撰人须在人物库里有唯一的宋及以前同名 Entity（前缀最长匹配，余≤2字当作字号）；否则不建。
用法：newwork_junzhai.py [--apply]"""
import os, re, sys, json, pickle, importlib.util, collections, random
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("nw", os.path.join(here, "newwork.py"))
src = open(os.path.join(here, "newwork.py"), encoding="utf-8").read().rsplit("\nmain()", 1)[0]
ns = {"__file__": os.path.join(here, "newwork.py")}; exec(compile(src, "newwork", "exec"), ns)
sp, near_dup, cn, mintid = ns["sp"], ns["near_dup"], ns["cn"], ns["mintid"]
ENTS = pickle.load(open("/tmp/claude-0/ents.pkl", "rb"))
OK_OLD = {"pre-qin", "qin-han", "three-kingdoms", "jin", "nanbeichao", "sui-tang", "five-dynasties", "song", None}
OK = {'ming'}
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

PER = {"唐": "sui-tang", "隋": "sui-tang", "宋": "song", "晉": "jin", "梁": "nanbeichao", "陳": "nanbeichao", "齊": "nanbeichao", "北魏": "nanbeichao",
       "漢": "qin-han", "東漢": "qin-han", "魏": "three-kingdoms", "吳": "three-kingdoms", "南唐": "five-dynasties", "周": "sui-tang", "秦": "qin-han"}

def main():
    apply = "--apply" in sys.argv
    idx, by = sp.load_idx(); ents = sp.parse_songshi("mingshi")
    new = []; seen = set()
    for e in ents:
        if sp.match(e, idx, by, "ming")[0] != "N": continue
        t = e["title"]; nm = e["author_raw"]
        if not nm or not re.fullmatch(r"[一-鿿]{2,4}", nm): continue
        if len(t) < 4 or t[0] in "又續後" or SEC_BAD.search(t) or "解題" in t or len(t) > 14 or re.search(r"[^一-鿿]", t): continue
        c = [x for x in ENTS.get(nm, []) if x[1] in OK]
        if len(c) != 1: continue
        if not re.fullmatch(r"[一二三四五六七八九十百千]+卷", e["juan"].replace("巻", "卷")): continue
        if near_dup(t, nm, idx) or "南軒" in t: continue
        if (sp.norm(t), nm) in seen: continue
        seen.add((sp.norm(t), nm)); new.append((e, nm, c[0][0]))
    print("可建 Work", len(new))
    if not apply:
        random.seed(7)
        for e, n, i in random.sample(new, min(40, len(new))): print(e["sec"], "|", e["head"], "|", n, i)
        return
    ids = mintid.mint("Work", "l4", len(new))
    for (e, name, eid), i in zip(new, ids):
        ju = e["juan"].replace("巻", "卷")
        d = {"schema_version": 1, "id": i, "type": "work", "title": e["title"],
             "authors": [{"name": name, "role": "撰", "entity_id": eid, "dynasty": "明", "role_basis": "明史藝文志著錄未標責任方式，暫作撰"}],
             "measures": [{"unit": "卷", "number": cn(ju)}], "measure_info": ju,
             "indexed_by": [{k: v for k, v in {"source": "明史藝文志", "source_bid": "d59f2mox0000", "title_info": e["head"], "author_info": e["author_raw"], "section": e["sec"]}.items() if v}],
             "period_upper": "qing",
             "period_upper_basis": "catalog_bound：所繫著錄為《明史》藝文志（清張廷玉等，1739），故不晚於 qing",
             "ai_note": "2026-11-15 L4 目錄書拆分：據《明史》藝文志著錄新建（庫內無同題 Work）。撰人為人物庫中唯一同名明人 Entity，未覆核。",
             "revision": "1.0.0", "revised_at": "2026-11-15"}
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, e["title"])
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("新建 Work", len(new))
main()
