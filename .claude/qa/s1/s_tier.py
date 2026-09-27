"""S 级：四库总目类目 -> book-index Work.classification 候选。"""
import json, glob, re, collections, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import siku

# 词表原样匹配不上的 5 处，按任务书 §一 归属规则处理
def remap_l2(l1, l2raw, title):
    if l2raw == "小說家類":
        return "集部", "小說類", ""
    if l2raw == "詩文評類":
        l3 = ""
        if re.search(r"詩話|詩評|詩品", title): l3 = "詩評之屬"
        elif re.search(r"文心|文則|文章|論文", title): l3 = "文評之屬"
        elif re.search(r"詞話|詞評", title): l3 = "詞評之屬"
        elif re.search(r"曲話|曲品|曲律", title): l3 = "曲讕之屬"
        return "集部", "集評類", l3
    if l2raw == "詔令奏議類":
        if re.search(r"詔|制|誥|敕|諭|冊|訓", title):
            return "史部", "詔令類", ""
        if re.search(r"奏|疏|議|章|封事|劄子", title):
            return "史部", "奏議類", ""
        return "史部", "", ""  # 判不了，只到部
    if l2raw == "五經總義類":
        return "經部", "群經總義類", ""
    if l2raw == "天文演算法類":
        return "子部", "天文算法類", ""
    return l1, l2raw, ""

def build_siku_map():
    """title -> list of (l1,l2,l3)"""
    raw, _ = siku.parse()
    out = {}
    for title, occs in raw.items():
        vals = []
        for l1, l2raw, summ, f in occs:
            l2raw_c = (l2raw or "").strip()
            l1c, l2c, l3c = remap_l2(l1, l2raw_c, title)
            vals.append((l1c, l2c, l3c, summ))
        out[title] = vals
    return out

def main():
    import vocab
    V = vocab.load_vocab()
    smap = build_siku_map()
    bad = collections.Counter()
    ok = collections.Counter()
    for title, vals in smap.items():
        for l1, l2, l3, summ in vals:
            c = {"l1": l1 or "", "l2": l2 or "", "l3": l3 or "", "l4": ""}
            if vocab.valid_classification(c, V):
                ok[(l1, l2)] += 1
            else:
                bad[(l1, l2, l3)] += 1
    print("valid combos", sum(ok.values()), "distinct", len(ok))
    print("INVALID combos:", sum(bad.values()))
    for k, n in bad.most_common(30):
        print(" ", n, k)

if __name__ == "__main__":
    main()
