#!/usr/bin/env python3
"""簇人读稿：每簇列成员（丛书、撰人、题录、版本摘要）与连边依据。
用法：python3 review_cl.py <feat.json> <clusters.json> <out.txt>"""
import json, sys
F = json.load(open(sys.argv[1], encoding='utf-8'))
W = {w['id']: w for g in F for w in g['works']}
CL = json.load(open(sys.argv[2], encoding='utf-8'))
with open(sys.argv[3], 'w', encoding='utf-8') as f:
    for ci, c in enumerate(CL):
        print(f'## c{ci} g{c["group"]} {c["title"]} ({len(c["members"])})', file=f)
        for i in c['members']:
            w = W[i]
            au = '；'.join(f'{a[2] or ""}{a[0]}{a[1] or ""}' for a in w['authors']) or '—'
            if w['butu']: au += '(补)'
            col = '／'.join(f'《{x["title"]}》' for x in w['cols'])
            print(f'  {i} 撰:{au} {"子目" + col if w["congshu"] or w["cols"] else "单行"}', file=f)
            for ti, ai, sec, sm in w['ib'][:3]:
                print(f'     · {ti}｜{ai}｜{sec}｜{sm[:110]}', file=f)
        for e in c['edges']:
            print(f'  = {e[0][-4:]}~{e[1][-4:]} {e[2]} {e[3][:80]}', file=f)
        print(file=f)
