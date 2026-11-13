#!/usr/bin/env python3
"""R1：Kanripo 目录（kanripo/KR-Catalog）→ Work 挂全文链接。只乾跑出台账，写入见 apply.py。
用法：git clone --depth 1 https://github.com/kanripo/KR-Catalog <dir>；python3 -I match.py <dir> out.tsv
分档：A 撰人两侧都有且相合、同题 Work 唯一；B 题名≥4字、同题 Work 唯一且 Work 无撰人；其余不挂。
KR 条目标题形如「题名-朝代-撰人」，括注（正文）等被去掉。已有 kanripo 资源的 Work 跳过。"""
import re, glob, sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'newwork-guard'))
import guard

cat, out = sys.argv[1], sys.argv[2]
ents = []
for f in glob.glob(os.path.join(cat, '**/*.txt'), recursive=True):
    for ln in open(f, encoding='utf-8'):
        m = re.match(r'\*\*\* (KR\w+) (.+)$', ln.rstrip())
        if m:
            parts = m.group(2).split('-')
            t = re.sub(r'\(.*?\)', '', parts[0])
            au = parts[-1] if len(parts) >= 3 else ''
            ents.append((m.group(1), t, au, m.group(2)))
g = guard.Guard(os.path.abspath(os.path.join(HERE, '..', '..', '..')))
root = g.root if hasattr(g, 'root') else None
C = collections.Counter()
with open(out, 'w', encoding='utf-8') as f:
    for kid, t, a, raw in ents:
        k = guard.norm(t)
        recs = g.idx.get(k, [])
        recs = [r for r in recs if not r[4]]  # 不带 [年号] 前缀者
        ids = {r[0] for r in recs}
        tier = ''
        if len(ids) == 1:
            r = recs[0]
            na = guard.nauth(a)
            if na and r[2] and na in r[2]:
                tier = 'A'
            elif len(k) >= 4 and not r[2]:
                tier = 'B'
        C[tier or '-'] += 1
        f.write('\t'.join([kid, raw, tier, next(iter(ids)) if tier else '']) + '\n')
print(dict(C))
