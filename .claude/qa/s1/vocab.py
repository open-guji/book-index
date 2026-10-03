import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
VOCAB_PATH = os.path.join(ROOT, "classific.json")

def load_vocab():
    rows = json.load(open(VOCAB_PATH, encoding="utf-8"))
    l1s = set()
    l2_by_l1 = {}       # l1 -> set(l2)
    l1_of_l2 = {}       # l2 -> set(l1)  (should mostly be singleton)
    l3_set = set()      # (l1,l2,l3)
    l3_by_l1l2 = {}      # (l1,l2) -> set(l3)
    l4_set = set()
    for r in rows:
        l1 = r["cata_l1"]; l2 = r["cata_l2"]; l3 = r.get("cata_l3"); l4 = r.get("cata_l4")
        l1s.add(l1)
        l2_by_l1.setdefault(l1, set()).add(l2)
        l1_of_l2.setdefault(l2, set()).add(l1)
        if l3:
            l3_set.add((l1, l2, l3))
            l3_by_l1l2.setdefault((l1, l2), set()).add(l3)
        if l4:
            l4_set.add((l1, l2, l3, l4))
    return dict(l1s=l1s, l2_by_l1=l2_by_l1, l1_of_l2=l1_of_l2, l3_set=l3_set,
                l3_by_l1l2=l3_by_l1l2, l4_set=l4_set)

def valid_classification(c, V):
    """c: dict with l1/l2/l3/l4 (may have '' for unset). Returns True if a valid
    prefix of some vocab row."""
    l1 = c.get("l1") or ""
    l2 = c.get("l2") or ""
    l3 = c.get("l3") or ""
    l4 = c.get("l4") or ""
    if not l1:
        return l2 == "" and l3 == "" and l4 == ""  # 全空视为未分类，允许（但不应该出现在写入数据里）
    if l1 not in V["l1s"]:
        return False
    if not l2:
        return l3 == "" and l4 == ""
    if l2 not in V["l2_by_l1"].get(l1, set()):
        return False
    if not l3:
        return l4 == ""
    if (l1, l2, l3) not in V["l3_set"]:
        return False
    if not l4:
        return True
    return (l1, l2, l3, l4) in V["l4_set"]

if __name__ == "__main__":
    V = load_vocab()
    print("l1", V["l1s"])
    print("l2 count", sum(len(v) for v in V["l2_by_l1"].values()))
    print("l3 count", len(V["l3_set"]))
    print("l4 count", len(V["l4_set"]))
