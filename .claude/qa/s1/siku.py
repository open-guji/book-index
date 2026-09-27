"""解析 book-text 的《欽定四庫全書總目》整理本（Work d59dh3vo9af4），
按卷内顺序把类目带到其下各书条目，产出 title -> [(l1, l2raw, summary, file), ...]。
"""
import json, glob, os, re, collections

# book-text 是独立只读仓（open-guji/book-text），本道不写它；路径可用环境变量覆盖，
# 默认假定与本仓同一 sessions 的常见 clone 位置（见任务书 §三「只读 book-text」）。
BOOK_TEXT_ROOT = os.environ.get("BOOK_TEXT_ROOT", "/home/user/open-guji/book-text")
SIKU_WORK_ID = "d59dh3vo9af4"  # 《欽定四庫全書總目》整理本（book-text 一侧的 Work id）
BASE = os.path.join(BOOK_TEXT_ROOT, "Work/a/f/4", SIKU_WORK_ID, "collated_edition/juan")

L1_NAMES = ["經部", "史部", "子部", "集部"]

# 卷152 页眉缺「楚辭類」——集部第一卷，实际是楚辭類（35 卡 §四·1 已知误差，约 23 部）
FILE_L2_OVERRIDE = {
    "152.json": "楚辭類",
}

def strip_l2_raw(name):
    name = name.strip()
    name = name.lstrip("○△")
    # category 首条把 l1 与序号也写进 title，如「經部一 《易類》」
    name = re.sub(r"^(經部|史部|子部|集部)[一二三四五六七八九十百]*\s*", "", name)
    name = name.strip("《》 ")
    name = re.sub(r"^補編[·／/]?(子編|經編|史編)?", "", name)
    name = re.sub(r"(存目)?[一二三四五六七八九十百]*$", "", name)
    name = name.strip()
    return name

def parse_page_header_content(content):
    """返回 (l1 or None, l2raw or None)。content 形如
    '卷N 部N\\n\\n○類名\\n\\n序文……' 或只有 '卷N 部N'（无类变）。"""
    if not content:
        return None, None
    lines = [l for l in content.split("\n") if l.strip()]
    l1 = None
    if lines:
        m = re.search(r"(經部|史部|子部|集部)", lines[0])
        if m:
            l1 = m.group(1)
    l2 = None
    for l in lines[1:]:
        l = l.strip()
        if l.startswith("○") or l.startswith("△"):
            l2 = strip_l2_raw(l)
            break
        if l.startswith("《四庫全書總目提要》"):
            continue
        # 不是类目行（序文、集部總敘等），停止查找
        break
    return l1, l2

def parse():
    """returns: title -> list of (l1, l2raw, summary, file)"""
    files = sorted(glob.glob(os.path.join(BASE, "*.json")), key=lambda p: int(os.path.basename(p)[:3]))
    cur_l1, cur_l2raw = None, None
    out = collections.defaultdict(list)
    stats = collections.Counter()
    for fp in files:
        fname = os.path.basename(fp)
        d = json.load(open(fp, encoding="utf-8"))
        for s in d.get("sections", []):
            t = s.get("type")
            if t == "page_header":
                content = s.get("content") or ""
                if content.startswith("附錄") and not re.match(r"^卷", content):
                    # 卷末附录（如「附錄•四庫抽毀書提要」）另编次序，不承袭正文部类——
                    # 承袭会把附录里跨四部的书全部误记成前一正文类目最后一类
                    cur_l1, cur_l2raw = None, None
                    continue
                l1, l2 = parse_page_header_content(content)
                if l1: cur_l1 = l1
                if fname in FILE_L2_OVERRIDE:
                    cur_l2raw = FILE_L2_OVERRIDE[fname]
                elif l2:
                    cur_l2raw = l2
            elif t == "preface":
                m = re.search(r"(經部|史部|子部|集部)", s.get("title") or "")
                if m: cur_l1 = m.group(1)
            elif t == "category":
                title = s.get("title") or ""
                cur_l2raw = strip_l2_raw(title)
            elif t == "book":
                title = (s.get("title") or "").strip()
                if not title:
                    continue
                stats["book"] += 1
                out[title].append((cur_l1, cur_l2raw, s.get("summary") or "", fname))
    return out, stats

if __name__ == "__main__":
    out, stats = parse()
    print(stats)
    print("distinct titles", len(out))
    dup = sum(1 for v in out.values() if len(v) > 1)
    print("titles with >1 occurrence", dup)
    # sanity: 楚辭 override
    for t, v in out.items():
        if "楚辭章句" in t:
            print(t, v)
    # l2raw distribution sanity
    import collections as c2
    cnt = c2.Counter()
    for v in out.values():
        for l1, l2raw, summ, f in v:
            cnt[(l1, l2raw)] += 1
    for k, n in cnt.most_common(80):
        print(n, k)
