#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""鑄 id 與辨 id 之型。

**所以立此**：兩事久卡諸道——
1. 立新 work（nanbeichao G 類「串條待拆」5 條、undated「倪思八題」6 條）皆須新 id，
   而真正之生成器在庫外（`book-index-manager`，使用者機上 D:/workspace），車道取不到。
2. 坑 61：本座曾把 `related_works` 裡的 id 一概當作 Work，險刪 84 條有效之
   Collection 引用（8rlcsybg2hhm 十三經、8rlcsybg2hhi 二十四史……）。
   **而 id 自己就寫著它是什麼型**——bit 61-59 即 type。一行可辨，卻靠肉眼猜。

規範見 overview/设计文档/古籍索引/索引ID.md（v2.0，2026-05-14），本檔只是其 64 位
布局之忠實實作，非另立一套：

    bit 63 Sign(固定0) │ bit 62 Status(0=Official,1=Draft) │ bit 61-59 Type
    bit 58-19 Timestamp(40 位；Official 用秒，Draft 用毫秒) │ bit 18-8 MachineID │ bit 7-0 Sequence

已以庫中現有之 id 反驗：d59f2pwcbh1d→type=3(Work) ts=2026-08-25T15:21:23、
hixhd2h9be75→type=4(Entity)、8rlcsybg2hhm→type=2(Collection)，皆合。

**MachineID 之分配**：2000–2047 全庫未用（實測 119 個在用者最大 1977），
故取 2000 予協調者、2001–2009 予九道。如此鑄出之 id 與上游生成器**永不相撞**，
且日後一望而知何者出自複查期間。
"""
import os, sys, time, json, argparse

A = "0123456789abcdefghijklmnopqrstuvwxyz"
TYPE = {0: "Book", 2: "Collection", 3: "Work", 4: "Entity"}
FAMILY = {"Book": "Book", "Collection": "Collection", "Work": "Work", "Entity": "Entity"}
LANE_MACHINE = {
    "coordinator": 2000, "shanggu": 2001, "weijin": 2002, "nanbeichao": 2003,
    "suitang": 2004, "song": 2005, "liaojinyuan": 2006, "ming": 2007,
    "qing": 2008, "undated": 2009,
}


def b36(n):
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = A[r] + s
    return s


def dec(s):
    n = 0
    for c in s:
        if c not in A:
            raise ValueError("非 base36 之字：%r（id 不得含大寫）" % c)
        n = n * 36 + A.index(c)
    return n


def parse(i):
    """拆一個 id。回 dict；type_name 為 None 表落在保留位（0/1/5/6/7 之保留者）。"""
    raw = dec(i)
    if raw >= 2 ** 63:
        raise ValueError("raw >= 2^63，sign bit 被置位：%s" % i)
    t = (raw >> 59) & 7
    return {
        "id": i, "raw": raw, "status": (raw >> 62) & 1, "type": t,
        "type_name": TYPE.get(t), "ts": (raw >> 19) & ((1 << 40) - 1),
        "machine": (raw >> 8) & 2047, "seq": raw & 255,
    }


def idtype(i):
    """**坑 61 之解**：一個 id 是 Work 還是 Collection、Entity、Book，id 自己說了算。

    凡欲對一串 id 做「查不到就刪」之事者，**先叫這個函式**——
    庫有五個 id 空間，「不在 Work 表裡」不等於「不存在」。
    回 'Work'/'Book'/'Collection'/'Entity'，或 None（保留位／不可解）。
    """
    try:
        return parse(i)["type_name"]
    except Exception:
        return None


def _existing_ids():
    seen = set()
    for fam in ("Work", "Entity", "Book", "Collection"):
        if not os.path.isdir(fam):
            continue
        for root, _d, files in os.walk(fam):
            for f in files:
                if f.endswith(".json") and "-" in f:
                    seen.add(f.split("-", 1)[0])
    return seen


def mint(kind="Work", lane="coordinator", n=1, status=0):
    """鑄 n 個新 id。同一秒之內以 sequence 遞增，逾 255 則等下一秒。"""
    ty = {v: k for k, v in TYPE.items()}[kind]
    machine = LANE_MACHINE.get(lane)
    if machine is None:
        raise SystemExit("未知車道 %r；可用：%s" % (lane, "、".join(LANE_MACHINE)))
    used = _existing_ids()
    out, seq = [], 0
    ts = int(time.time())
    while len(out) < n:
        if seq > 255:
            time.sleep(1.0)
            ts = int(time.time())
            seq = 0
        raw = (status << 62) | (ty << 59) | ((ts & ((1 << 40) - 1)) << 19) | (machine << 8) | seq
        seq += 1
        i = b36(raw)
        if len(i) != 12:
            raise SystemExit("鑄出之 id 非 12 位（%s），時戳或有異，中止" % i)
        if i in used:          # 理論上不可能（machine 段獨佔），仍驗
            continue
        used.add(i)
        out.append(i)
    return out


def path_for(i, name, family=None):
    """記錄檔之路徑：<Family>/<倒三>/<倒二>/<倒一>/<id>-<name>.json（非索引之分片規則！）"""
    fam = family or idtype(i)
    if not fam:
        raise ValueError("無法自 id 判其型：%s" % i)
    return os.path.join(FAMILY[fam], i[-3], i[-2], i[-1], "%s-%s.json" % (i, name))


def shard(i):
    """索引分片鍵：h=0; h=(h*31+ord(c))&0xFFFFFFFF; '0123456789abcdef'[h%16]

    **與 path_for 之「倒三位」是兩條不同之規則，切勿混用**（坑 42、坑 50）。"""
    h = 0
    for c in i:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return "0123456789abcdef"[h % 16]


def main():
    ap = argparse.ArgumentParser(description="鑄 id／辨 id 之型")
    ap.add_argument("--type", default="Work", choices=sorted(TYPE.values()))
    ap.add_argument("--lane", default="coordinator")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--parse", metavar="ID", nargs="+", help="拆已有之 id，印其型與時戳")
    a = ap.parse_args()
    if a.parse:
        import datetime
        for i in a.parse:
            try:
                p = parse(i)
                unit = "ms" if p["status"] else "s"
                t = (datetime.datetime.utcfromtimestamp(p["ts"] / (1000.0 if p["status"] else 1.0))
                     .isoformat())
            except Exception as e:
                print("%-14s 解不開：%s" % (i, e)); continue
            print("%-14s %-11s %-8s ts=%s(%s) machine=%-5d seq=%-3d 檔=%s 索引分片=%s"
                  % (i, p["type_name"] or "保留位%d" % p["type"],
                     "Draft" if p["status"] else "Official", t, unit,
                     p["machine"], p["seq"],
                     "%s/%s/%s/%s/" % (p["type_name"], i[-3], i[-2], i[-1]) if p["type_name"] else "?",
                     shard(i)))
        return
    for i in mint(a.type, a.lane, a.n):
        print(i)


if __name__ == "__main__":
    main()
