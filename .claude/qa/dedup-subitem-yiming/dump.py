"""把需人判（有 R 对）的组写成人读稿，按组均分成 N 份，供子 agent 逐组判定。
用法：OUT=... python3 dump.py N"""
import json, os, sys, collections, csv
S = os.environ.get('OUT', '/tmp/yiming')
N = int(sys.argv[1])
feat = json.load(open(S + '/feat.json'))
I = json.load(open(S + '/info.json'))
P = list(csv.DictReader(open(S + '/pairs.tsv'), delimiter='\t'))
need = collections.defaultdict(list)
for p in P: need[int(p['组'])].append(p)
todo = [gi for gi in range(len(feat)) if any(p['判定'] in ('R', 'A') for p in need[gi])]
def line(w):
    i = I[w['id']]
    au = '；'.join('%s%s%s' % (a[2] or '', a[0] or '', a[1] or '') for a in w['authors']) or '—'
    ib = ' ‖ '.join('%s｜%s｜%s%s' % (t or '', ai or '', sec or '', ('｜' + sm[:90]) if sm else '') for t, ai, sec, sm in w['ib'][:3])
    col = ('叢書：%s' % w['col']) + (('（叢書撰者 %s）' % '、'.join(i['inh'])) if i['inh'] else '') if w['col'] else '單行本'
    return '- %s 《%s》 責任者：%s ｜ %s ｜ 著錄：%s' % (w['id'], w['title'], au, col, ib)
chunks = [[] for _ in range(N)]; size = [0] * N
for gi in sorted(todo, key=lambda g: -len(feat[g]['works'])):
    k = size.index(min(size)); chunks[k].append(gi); size[k] += len(feat[gi]['works']) + 3
for k, ch in enumerate(chunks):
    with open(S + '/review-%02d.md' % k, 'w') as f:
        for gi in sorted(ch):
            g = feat[gi]
            a = [(p['Work甲'], p['Work乙']) for p in need[gi] if p['判定'] == 'A']
            f.write('## 组 %d 《%s》（%d 条）\n' % (gi, g['key'], len(g['works'])))
            for w in g['works']: f.write(line(w) + '\n')
            if a: f.write('机判同撰人可并的对：' + '；'.join('%s=%s' % x for x in a) + '\n')
            f.write('\n')
    print(k, len(ch), '组', size[k])
