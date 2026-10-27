"""人读稿：按组列出各条特征与机判对。输出 $P4WORK/zj-read-*.txt（每份 60 组），跳过「纯 C 卷异或缺」组（另抽检）。"""
import os, json, csv, collections
WK = os.environ.get('P4WORK', '/tmp/p4')
F = json.load(open(WK + '/zj-feat.json'))
R = collections.defaultdict(list)
for r in csv.DictReader(open(WK + '/zj-pairs.tsv'), delimiter='\t'): R[int(r['组'])].append(r)
def pure_c(rs): return all(r['机判'] == 'C?' and r['撰人'] == '异' and r['卷'] in ('悬殊', '缺') for r in rs)
blocks = []; skipped = []
for gi, g in enumerate(F):
    rs = R[gi]
    if pure_c(rs): skipped.append(gi); continue
    L = ['#%d %s ［%s／%s］' % (gi, g['key'], g['bulei'], g['cat'])]
    for w in g['works']:
        col = w['col']
        L.append(' %s《%s》撰:%s 卷:%s/%s 丛:%s%s B%d:%s' % (w['id'][-4:], w['title'], '、'.join('%s%s' % (x[1], x[0]) + ('' if x[3] == 'self' else '[' + x[3] + ']') for x in w['eff']) or '—',
            w['juan'], w['bjuan'], (col or {}).get('title', '单行')[:24], ('〔%s〕' % '、'.join((a[0] or '') for a in col['cauth'])) if col and col['cauth'] else '', w['nbooks'], '／'.join(sorted(set(w['eds'])))[:60]))
        for x in w['ib'][:3]: L.append('   [%s] %s｜%s｜%s' % ((x[0] or x[4])[:10], x[1][:30], x[2][:30], x[3][:90]))
    for r in rs:
        L.append(' > %s-%s %s %s卷%s %s' % (r['Work甲'][-4:], r['Work乙'][-4:], r['机判'], r['撰人'], r['卷'], r['证据']))
    blocks.append('\n'.join(L))
n = 0
for i in range(0, len(blocks), 60):
    open(WK + '/zj-read-%02d.txt' % (i // 60), 'w').write('\n'.join(blocks[i:i + 60]) + '\n'); n += 1
open(WK + '/zj-pureC.txt', 'w').write('\n'.join(map(str, skipped)))
print('读稿', len(blocks), '组', n, '份；纯C', len(skipped))
