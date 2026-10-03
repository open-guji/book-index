#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""甲道 74 条画像：把每条 Work 及其所繫 Book 的资源／藏所情况盘出来。"""
import json, os, sys, csv

REPO = os.environ.get("BOOK_INDEX_REPO", "/home/user/book-index")
TSV = "/home/user/overview/项目进展/古籍索引网站/进度/先秦收官/清单/甲-傳世版本74.tsv"

def path_of(kind, oid):
    """按 ID 尾三字符三级散列定位档案。"""
    d = os.path.join(REPO, kind, oid[-3], oid[-2], oid[-1])
    if not os.path.isdir(d):
        return None
    for fn in os.listdir(d):
        if fn.startswith(oid + "-") and fn.endswith(".json"):
            return os.path.join(d, fn)
    return None

def load(kind, oid):
    p = path_of(kind, oid)
    if not p:
        return None, None
    with open(p, encoding="utf-8") as f:
        return json.load(f), p

def main():
    with open(TSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = []
    for r in rows:
        wid = r["id"]
        w, wp = load("Work", wid)
        if w is None:
            out.append({"work_id": wid, "title": r["title"], "错": "Work 档未找到"})
            continue
        books = []
        for bid in w.get("books", []) or []:
            b, bp = load("Book", bid)
            if b is None:
                books.append({"book_id": bid, "错": "Book 档未找到"})
                continue
            books.append({
                "book_id": bid,
                "title": b.get("title"),
                "edition": (b.get("edition") or "")[:60],
                "n_res": len(b.get("resources") or []),
                "contained_in": b.get("contained_in") or [],
                "path": os.path.relpath(bp, REPO),
            })
        out.append({
            "work_id": wid,
            "title": w.get("title"),
            "loss_status": w.get("loss_status"),
            "n_work_res": len(w.get("resources") or []),
            "work_res_ids": [x.get("id") for x in (w.get("resources") or [])],
            "n_rel": len(w.get("related_works") or []),
            "n_books": len(books),
            "books": books,
            "path": os.path.relpath(wp, REPO),
        })
    json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 汇总
    nb_nores = sum(1 for e in out for b in e.get("books", []) if b.get("n_res") == 0)
    nb_noloc = sum(1 for e in out for b in e.get("books", []) if not b.get("contained_in") and "错" not in b)
    nw_nores = sum(1 for e in out if e.get("n_work_res") == 0)
    nw_nobook = sum(1 for e in out if e.get("n_books") == 0)
    nw_norel = sum(1 for e in out if e.get("n_rel") == 0)
    nb_total = sum(e.get("n_books", 0) for e in out)
    print(f"Work 条数            {len(out)}")
    print(f"所繫 Book 总数        {nb_total}")
    print(f"Book 无 resources     {nb_nores}")
    print(f"Book 无 contained_in  {nb_noloc}")
    print(f"Work 无 resources     {nw_nores}")
    print(f"Work 无 Book          {nw_nobook}")
    print(f"Work 无 related_works {nw_norel}")

main()
