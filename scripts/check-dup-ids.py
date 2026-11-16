#!/usr/bin/env python3
"""全库 id 唯一性检查（2026-11-16 起进 CI）。

起因：两个串用同一机器号并行铸号，main 上撞出 1,800 个「一 id 两档」，build_derived 读档失败、正式数据发布中断。
查两件事，任一不过即退出码 1：
  1. Work／Book／Collection／Entity 四目录下，同一 id（文件名首段）只许有一个文件；
  2. mintid.py 车道登记表里，在役车道不得同号且类型相交（见 mintid.lane_conflicts）。
用法：python3 scripts/check-dup-ids.py [--root .]
"""
import argparse, collections, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("--root", default=".")
a = ap.parse_args()

seen = collections.defaultdict(list)
n = 0
for fam in ("Work", "Book", "Collection", "Entity"):
    base = os.path.join(a.root, fam)
    for dp, _dn, fn in os.walk(base):
        for f in fn:
            if f.endswith(".json") and "-" in f:
                n += 1
                seen[f.split("-", 1)[0]].append(os.path.relpath(os.path.join(dp, f), a.root))
dups = {k: v for k, v in seen.items() if len(v) > 1}
rc = 0
print("查 %d 档，重复 id %d 个" % (n, len(dups)))
if dups:
    rc = 1
    for k in sorted(dups)[:50]:
        print("  DUP", k, " | ".join(dups[k]))
    if len(dups) > 50:
        print("  …… 另 %d 个" % (len(dups) - 50))
    print("修法：后合进来的一侧换机器号重铸 id，并同步改所有引用（collected_in、_contents、related_works、promotions 等）。")

sys.path.insert(0, os.path.join(a.root, ".claude", "qa"))
try:
    import mintid
    cf = mintid.lane_conflicts()
except Exception as e:  # 表坏了也算红
    cf = [("?", "?", -1, ["mintid 载入失败：%s" % e])]
print("车道登记冲突 %d 处" % len(cf))
for c in cf:
    rc = 1
    print("  LANE", c)
sys.exit(rc)
