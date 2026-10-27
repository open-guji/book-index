#!/usr/bin/env python3
"""把 判定.tsv 中不并的对写成 ../dedup-judged/新-同姓异名余.tsv（X→C，D→D；S／S2 而簇被剔出者→D）。
用法：mkjudged.py <batch.json>（本批实际并的组）"""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
G = json.load(open(sys.argv[1], encoding='utf-8'))['groups']
done = {}
for g in G:
    for i in [g['keeper']] + g['losers']:
        done[i] = g['cluster_id']
import mkbatch  # noqa: E402
rows = list(csv.DictReader(open(os.path.join(HERE, '判定.tsv'), encoding='utf-8'), delimiter='\t'))
out = ['# 新-同姓异名余（去重第二轮细拆，同题、首位责任者同姓异名）判为分立（C）或存疑（D）的对，不并；列：Work甲 Work乙 判定 理由。全部判定见 .claude/qa/dedup-tongxing/判定.tsv。']
for r in rows:
    a, b = r['Work甲'], r['Work乙']
    if a in done and done.get(a) == done.get(b):
        continue
    v = r['判定']
    why = r['理由']
    if v in ('S', 'S2'):
        cid = next((c for c in mkbatch.EXCL if c == 'txy-%03d' % int(r['序'])), None)
        v, why = 'D', why + '；簇未并（核验存疑或卷数不相容）'
    out.append('\t'.join([a, b, 'C' if v == 'X' else 'D', '《%s》%s／%s：%s（新-同姓异名余 序 %s）' % (r['题名键'], r['撰人甲'], r['撰人乙'], why, r['序'])]))
open(os.path.join(HERE, '..', 'dedup-judged', '新-同姓异名余.tsv'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('登记 %d 对' % (len(out) - 1))
