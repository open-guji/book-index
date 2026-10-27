#!/usr/bin/env python3
"""人读稿：逐组列出每条 Work 的丛书、撰人、卷数串、著录部类与版本摘要。
用法：python3 review.py <feat.json> <out.txt> [组号起 止]"""
import json, sys
F = json.load(open(sys.argv[1], encoding='utf-8'))
lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, len(F))
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    for gi in range(lo, min(hi, len(F))):
        g = F[gi]
        print(f'## {gi} {g["key"]} [{g["cat"]}{"·" + g["sub"] if g["sub"] else ""}]', file=f)
        for w in g['works']:
            au = '；'.join(f'{a[2] or ""}{a[0]}{a[1] or ""}{"#" if a[3] else ""}' for a in w['authors']) or '—'
            if w['butu']: au += '(补)'
            col = '／'.join(f'《{c["title"]}》{("[" + "；".join((x[2] or "") + (x[0] or "") + (x[1] or "") for x in c["auth"]) + "]") if c["auth"] else ""}' for c in w['cols'])
            print(f'  {w["id"]} 「{w["title"]}」 撰:{au} {"子目" + col if w["congshu"] else "单行"} res{w["nres"]}', file=f)
            for ti, ai, sec, sm in w['ib'][:4]:
                print(f'     · {ti}｜{ai}｜{sec}｜{sm[:150]}', file=f)
        print(file=f)
