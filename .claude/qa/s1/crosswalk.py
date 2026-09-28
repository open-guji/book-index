"""A/B/C 级：indexed_by[].section -> classification 候选。
逐行可审：main() 打印全部 390 行的判定，SKIP 的行即「拿不准不用」，进最终报告清单。
"""
import re, sys, os, json, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vocab

CM = str.maketrans({"经": "經", "羣": "群", "术": "術", "礼": "禮", "记": "記",
                     "谱": "譜", "录": "錄", "杂": "雜", "别": "別", "说": "說",
                     "历": "歷", "録": "錄", "雑": "雜"})

L1_NAMES = ("經部", "史部", "子部", "集部")

# 甲乙丙丁部 / 六藝略等古称 -> l1
L1_ALIAS = [
    ("甲部", "經部"), ("乙部", "史部"), ("丙部", "子部"), ("丁部", "集部"),
    ("六藝略", "經部"), ("諸子略", "子部"), ("兵書略", "子部"), ("數術略", "子部"),
    ("方技略", "子部"), ("詩賦略", "集部"), ("經編", "經部"), ("史編", "史部"),
    ("子編", "子部"),
]

# l2raw（去「類」）-> 词表 l2（含「類」）。同名同義／改名，均在此
L2_DIRECT = {
    "易": "易類", "書": "書類", "尚書": "書類", "詩": "詩類", "禮": "禮類", "周禮": "禮類",
    "儀禮": "禮類", "禮記": "禮類", "通禮": "禮類", "三禮總義之屬": "禮類",
    "儀禮之屬": "禮類", "禮記之屬": "禮類", "周官禮": "禮類", "樂": "樂類",
    "春秋": "春秋類", "春秋左氏學": "春秋類", "春秋公羊家學": "春秋類",
    "春秋穀梁家學": "春秋類", "春秋三傳": "春秋類", "孝經": "孝經類",
    "論語": "四書類", "孟子": "四書類", "論語孟子": "四書類", "四書": "四書類",
    "爾雅": "小學類", "小學": "小學類", "字書之屬": "小學類", "韻書之屬": "小學類",
    "訓站之屬": "小學類", "訓詁之屬": "小學類",
    "五經總義": "群經總義類", "五經總類": "群經總義類", "羣經": "群經總義類",
    "五經總議": "群經總義類", "群經總議": "群經總義類", "群經": "群經總義類",
    "正史": "正史類", "編年": "編年類", "起居": "編年類", "起居注": "編年類", "古史": "編年類",
    "紀事本末": "紀事本末類", "別史": "別史類", "霸史": "載記類", "載記": "載記類",
    "雜史": "雜史類", "雜傳": "傳記類", "別傳": "傳記類", "雜傳記": "傳記類",
    "傳記類總錄之屬": "傳記類", "傳記類郡書之屬": "傳記類", "地理": "地理類",
    "總志郡縣志之屬": "地理類", "外紀雜記之屬": "地理類", "河渠之屬": "地理類",
    "職官": "職官類", "儀制": "政書類", "儀注": "政書類", "刑法": "政書類",
    "舊事": "政書類", "簿錄": "目錄類", "目錄": "目錄類", "史評": "史評類",
    "史鈔": "史鈔類", "詔令奏議": None,  # 另走 remap_zhaoling
    "儒": "儒家類", "儒家": "儒家類", "道": "道家類", "道家": "道家類",
    "法": "法家類", "法家": "法家類", "農": "農家類", "農家": "農家類",
    "雜": "雜家類", "雜家": "雜家類", "兵家": "兵家類", "兵書": "兵家類",
    "兵權謀": "兵家類", "兵形勢": "兵家類", "兵技巧": "兵家類", "兵陰陽": "兵家類",
    "醫方": "醫家類", "醫術": "醫家類", "醫書": "醫家類", "醫經": "醫家類",
    "經方": "醫家類", "醫家": "醫家類", "曆數": "天文算法類", "曆算家": "天文算法類",
    "歷算家": "天文算法類", "歷數": "天文算法類", "天文家": "天文算法類",
    "天文": "天文算法類", "天文家": "天文算法類", "曆譜": "天文算法類",
    "算數": "天文算法類", "天文算法": "天文算法類", "層數": "天文算法類",
    "五行": "術數類", "五行家": "術數類", "蓍龜": "術數類", "雜占": "術數類",
    "形法": "術數類", "卜筮": "術數類", "術數": "術數類",
    "藝術": "藝術類", "雜藝術": "藝術類", "雜藝術家": "藝術類",
    "譜錄": "譜錄類", "類書": "類書類",
    # 09-27 23:40Z 修订（overview e2ff3e51／#114）：历代志书之「小説家／小說家類」
    # 收的是笔记（世說新語、酉陽雜俎一類），非通俗小说，归子部／說叢類；本道各
    # 来源（汉志、後漢志、三国志、補晉書志、隋志、宋志、玉函山房、續修四庫）皆是
    # 著录历代典籍的传统目录，无一是「中國通俗小說書目」一类的白话小说专目，
    # 故一律按此归——若日后并入通俗小说专目，需另判
    "小說": "說叢類", "小說家": "說叢類", "小説": "說叢類",
    "別集": "別集類", "總集": "總集類", "詩賦": "別集類",
    "詞曲": "詞曲類", "楚辭": "楚辭類",
    "釋家": "釋家類", "佛經": "釋家類",
    "孟氏易": "易類", "費氏易": "易類", "難義音例并雜論": "易類",
    "道書": "道家類", "墨": "雜家類", "墨家": "雜家類", "名": "雜家類", "名家": "雜家類",
    "從横": "雜家類", "縱橫家": "雜家類",  # 四库自序（見凡例四）：名墨縱橫皆併入雜家
    "隂陽": "術數類", "陰陽": "術數類", "陰陽家": "術數類", "神〓": "醫家類", "房中": "醫家類",
    "醫經": "醫家類",
}

# 已知不可靠 OCR／異寫，先歸一到「去類字之基名」
NORMALIZE = {
    "層數": "曆算家", "識緯": None, "緯書": None, "五經緯": None,  # 讖緯——词表无对应类，只到部
}

# 只到部的「N類」整體別稱
L1_WHOLE = {"經類": "經部", "史類": "史部", "子類": "子部", "集類": "集部"}


def l1_from_prefix(source, section):
    section = re.sub(r"^補編[·／/]?", "", section)
    for alias, l1 in L1_ALIAS:
        if section.startswith(alias):
            return l1
    for l1 in L1_NAMES:
        if section.startswith(l1):
            return l1
    if source == "經義考":
        return "經部"
    return None


def strip_l2(tok):
    tok = tok.strip()
    tok = tok.translate(CM)
    tok = re.sub(r"^(補編[·／/]?)?(子編|經編|史編)?", "", tok)
    tok = tok.strip("·／/ ")
    tok = re.sub(r"類$", "", tok)
    return tok


def remap_zhaoling(l2base, title_hint=""):
    # 詔令奏議：没有属可判时只到部（此处 title_hint 留空，交上层用书名再判）
    return None


_V = vocab.load_vocab()


def classify_section(source, section):
    """returns (l1, l2, l3, tier, why) or ('SKIP', reason)"""
    if source == "國立故宮博物院善本舊籍":
        return ("SKIP", "统一编号非类目")
    if source == "國史經籍志" and "儀注" in section and ("崩" in section or "薨" in section or "卒" in section or "世子" in section):
        return ("SKIP", "具体丧礼条目名混入 section，非类名")
    if source == "三國藝文志" and section.startswith("集部·佛道"):
        return ("SKIP", "该志集部·佛道为自设门类，佛道混编，映射不可靠")
    if source == "舊唐書經籍志" and section == "起居注故事職官類":
        return ("SKIP", "三类合书一 section，无法拆分")
    if source == "新唐書藝文志" and section == "譜牒類":
        return ("SKIP", "谱牒非词表既有类，不臆断")
    if source == "後漢藝文志" and section.startswith("附錄二"):
        return ("SKIP", "附录内具体书名，非类名")
    if source == "玉函山房輯佚書" and section == "附錄／":
        return ("SKIP", "空类名")
    if source == "玉函山房輯佚書" and "十三經漢注" in section:
        return ("SKIP", "该辑佚书自订之「子編」归堆，内容实为經部注疏，前缀部名不可信")
    if source == "玉函山房輯佚書" and "經籍佚文" in section:
        return ("SKIP", "「經籍佚文」是跨部佚书杂编，前缀「子編」不可信（如《十道志佚文》实为史部地理）")
    if source == "崇文總目" and section == "道書類":
        return ("子部", "道家類", None, "B", "道書->道家類")
    if source == "玉函山房輯佚書" and "釋道類" in section:
        return ("SKIP", "釋道合類，无法拆分")
    if source == "玉函山房輯佚書" and "陰陽類" in section:
        return ("子部", "術數類", None, "B", "陰陽類->術數類")
    if source == "國史經籍志" and section in ("子類上", "子類下", "史類", "經類", "集類"):
        l1_ = {"子類上": "子部", "子類下": "子部", "史類": "史部",
               "經類": "經部", "集類": "集部"}[section]
        return (l1_, None, None, "C", "只标部名（上/下）")
    if source == "國史經籍志" and section == "集類・制詔":
        return ("史部", "詔令類", None, "B", "制詔->詔令類")

    raw = section.translate(CM)
    if raw in L1_WHOLE:
        return (L1_WHOLE[raw], None, None, "C", "只标部名")

    parts = re.split(r"[／/]", raw)
    l1 = None
    l2tok = raw
    if len(parts) >= 2:
        l1 = l1_from_prefix(source, parts[0])
        l2tok = parts[-1]
    else:
        # 「经部 春秋類」这类空格分隔（无 ／ 分隔符）——续修四库全书惯用此式
        m = re.match(r"^(經部|史部|子部|集部)\s+(\S+)$", raw)
        if m:
            l1 = m.group(1)
            l2tok = m.group(2)
        else:
            l1 = l1_from_prefix(source, raw)
            l2tok = raw
            if l1 and raw.strip() == l1:
                l2tok = ""

    if source == "經義考":
        l1 = "經部"

    l2tok = l2tok.strip()
    if l2tok in L1_NAMES:
        return (l1 or l2tok, None, None, "C", "只标部名")

    if not l2tok:
        if l1:
            return (l1, None, None, "C", "section 只到部")
        return ("SKIP", f"无法判部：{section!r}")

    base = strip_l2(l2tok)
    if base in NORMALIZE:
        mapped = NORMALIZE[base]
        if mapped is None:
            return (l1, None, None, "C", f"{base} 词表无对应类，只到部") if l1 else ("SKIP", f"{base} 无法判部")
        base = mapped

    if base == "詔令奏議":
        return (l1 or "史部", "__ZHAOLING__", None, "B", "詔令奏議，按書名再判詔令/奏議")

    l2 = L2_DIRECT.get(base)
    if l2 is None:
        alt = base.replace("家", "") if "家" in base else base + "家"
        l2 = L2_DIRECT.get(alt)

    if l2:
        # 词表内每个 l2 只属一个 l1（52 类彼此不重名）——一旦 l2 判定，l1 概以词表为准，
        # 不用来源志书自己的部类归属（如「丁部集録／釋家」「丁部集録／道家」，補晉書志把
        # 佛道书籍系于其自訂之「集部」，但词表釋家類／道家類定為子部，从词表）
        owners = _V["l1_of_l2"].get(l2, set())
        if len(owners) == 1:
            l1 = next(iter(owners))
        tier = "A" if (base + "類" == l2 or base == l2) else "B"
        return (l1, l2, None, tier, f"{l2tok}->{l2}")

    if l1:
        return (l1, None, None, "C", f"未識別 l2：{l2tok!r}，只到部")
    return ("SKIP", f"未識別：{source} / {section!r}")


def scan_sections():
    """全库现行 (source, section) 计数——逐行可审的判定表就是靠这个生成，
    不依赖任何快照文件（35 卡的旧 CSV 不能直接套用，数据已变）。"""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    c = collections.Counter()
    for f in glob.glob(os.path.join(root, 'Work/*/*/*/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        for e in (d.get('indexed_by') or []):
            s = e.get('section')
            if s:
                c[(e.get('source'), s)] += 1
    return c


def main():
    counts = scan_sections()
    rows = [(n, src, sec) for (src, sec), n in sorted(counts.items(), key=lambda x: -x[1])]
    V = vocab.load_vocab()
    skip_n = 0; ok_n = 0; bad_n = 0
    for n, src, sec in rows:
        r = classify_section(src, sec)
        if r[0] == "SKIP":
            skip_n += n
            print(f"SKIP  {n:5d}  {src}\t{sec}\t{r[1]}")
            continue
        l1, l2, l3, tier, why = r
        if l2 == "__ZHAOLING__":
            ok_n += n
            print(f"{tier}     {n:5d}  {src}\t{sec}\t-> {l1}/詔令奏議(按書名判)")
            continue
        c = {"l1": l1 or "", "l2": l2 or "", "l3": l3 or "", "l4": ""}
        valid = vocab.valid_classification(c, V)
        if not valid:
            bad_n += n
            print(f"BAD!  {n:5d}  {src}\t{sec}\t-> {l1}/{l2}  {why}  **不在词表**")
        else:
            ok_n += n
            print(f"{tier}     {n:5d}  {src}\t{sec}\t-> {l1}/{l2 or ''}  {why}")
    print(f"\n合计：OK {ok_n}  SKIP {skip_n}  BAD {bad_n}  总 {ok_n+skip_n+bad_n}")


if __name__ == "__main__":
    main()
