#!/usr/bin/env python3
"""由判定表写 dedup-judged/新-待並條.tsv（C 分立、D 存疑两档；供 dedup-census --whitelist）。用法：mk_judged.py <判定.tsv> <out.tsv>"""
import csv, sys
rows = list(csv.DictReader((l for l in open(sys.argv[1], encoding='utf-8') if not l.startswith('#')), delimiter='\t'))
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    f.write('# 新-待並條（related 注「待並條」的链接逐条定论）判为分立 C／存疑 D 的对，不并；链接注已改为「同題異書：…」／「存疑未并：…」。'
            '基线 main ba18f194a7 起；口径见 .claude/qa/dedup-daibingtiao/README.md\n# Work甲\tWork乙\t判定\t理由\n')
    for r in rows:
        if r['判定'][0] in 'CD':
            f.write('\t'.join([r['A'], r['B'], 'C分立' if r['判定'][0] == 'C' else 'D存疑', r['理由']]) + '\n')
