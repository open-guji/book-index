#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""為新建之 Book 補 index/books 分片——reindex.py 不管 Book（其 scan_files 只掃
Work/Entity，且 REC_RE 要求 12–13 位 id 而 Book id 為 10 位），故本道自補這一段。

**以記錄為真**，欄位生成規則自既有索引條目逆推並抽樣驗過：
  id/title/type/path/edition/work_id 恆有
  author←authors[0].name  role←authors[0].role  dynasty←authors[0].dynasty
  era←dating.era  sort_year←dating.year  holder←current_location.name
  juan_count←juan_count.number  has_image←resources 任一 types 含 image
  **值為空者不寫該鍵**（非寫 null）
冪等：已在索引中且內容相同則跳過。
"""
import json, os, sys, glob
sys.path.insert(0, ".claude/qa")
import mintid

def build(bid):
    d0 = os.path.join("Book", bid[-3], bid[-2], bid[-1])
    fn = [f for f in os.listdir(d0) if f.startswith(bid + "-")][0]
    p = os.path.join(d0, fn)
    d = json.load(open(p, encoding="utf-8"))
    e = {"id": bid, "title": d.get("title"), "type": "Book", "path": p}
    au = (d.get("authors") or [{}])[0]
    dt = d.get("dating") or {}
    cl = d.get("current_location") or {}
    jc = d.get("juan_count") or {}
    img = any("image" in (r.get("types") or ([r["type"]] if r.get("type") else []))
              for r in (d.get("resources") or []))
    for k, v in (("author", au.get("name")), ("era", dt.get("era")),
                 ("sort_year", dt.get("year")), ("holder", cl.get("name")),
                 ("dynasty", au.get("dynasty")), ("role", au.get("role")),
                 ("juan_count", jc.get("number"))):
        if v not in (None, ""):
            e[k] = v
    if img:
        e["has_image"] = True
    e["edition"] = d.get("edition")
    e["work_id"] = d.get("work_id")
    return e

ids = [l.strip() for l in open("/tmp/claude-0/-home-user/c7adbf54-09a2-51e4-b45a-ed05a549863d/scratchpad/xq/new_book_ids.txt") if l.strip()]
dry = "--run" not in sys.argv
byshard = {}
for bid in ids:
    byshard.setdefault(mintid.shard(bid), []).append(bid)
for sh, bids in sorted(byshard.items()):
    fp = os.path.join("index", "books", f"{sh}.json")
    raw = open(fp, encoding="utf-8").read()
    idx = json.loads(raw)
    tail = "\n" if raw.endswith("\n") else ""
    if raw != json.dumps(idx, ensure_ascii=False, indent=2) + tail:
        # 索引檔格式另有其樣，探明再寫
        for ind in (None, 1, 2, 4):
            for sep in (None, (",", ": ")):
                if raw == json.dumps(idx, ensure_ascii=False, indent=ind, separators=sep) + tail:
                    fmt = (ind, sep); break
            else: continue
            break
        else:
            print(f"  ! {fp} 格式未識別，未改"); continue
    else:
        fmt = (2, None)
    changed = 0
    for bid in bids:
        e = build(bid)
        if idx.get(bid) == e:
            print(f"  – {bid} 已在 {fp}，內容相同"); continue
        idx[bid] = e; changed += 1
        print(f"  {'[干跑] ' if dry else '  ✓ '}{bid} → {fp}   {json.dumps(e, ensure_ascii=False)[:150]}")
    if changed and not dry:
        open(fp, "w", encoding="utf-8").write(
            json.dumps(idx, ensure_ascii=False, indent=fmt[0], separators=fmt[1]) + tail)
        print(f"     寫回 {fp}（新增 {changed} 鍵，共 {len(idx)} 鍵）")
