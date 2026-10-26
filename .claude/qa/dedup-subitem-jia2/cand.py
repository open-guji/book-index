"""子目-甲2 候选：同名丛书不同版次里的同题叢書子目 Work 互并（子部、集部、未分类）。
叢書线（GUJI-526）按《總目》丛书版本记录各建一条子目 Work，同一丛书的几个版次里同一子目被建成多条。
簇＝同题组（dedup-census 口径）里所屬叢書題名去卷種數後相同的子目 Work；跳过 4a-α 清单里的 Work。
用法：P4WORK=<目录> python3 cand.py   （先跑 ../dedup-part4/load.py 与 scripts/dedup-census.py --out $P4WORK/census）
产出 $P4WORK/jia2.json（可并簇）、$P4WORK/jia2-B待核.json（同名丛书而丛书撰者写法不同，待逐条核）与 $P4WORK/jia2-judged.tsv（存疑／分立，入 ../dedup-judged/子目-甲2.tsv）。"""
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__), '../dedup-part4/feat.py')).read())
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('P4WORK', '/tmp/p4')
BULEI = ('子部', '集部', '未分类')
PAR = re.compile(r'所屬叢書記錄 ([0-9a-z]{16})（([^）]+)）')
NUM = re.compile(r'[一二三四五六七八九十百千〇零□]+(種|卷|集|冊)|不分卷')
AX = set()
for p in glob.glob(HERE + '/../dedup-part4/候选/4a-alpha-*.json'):
    for c in json.load(open(p)):
        AX |= {c['keeper'], *c['losers']}
print('载入 4a-α 跳过 Work', len(AX))
assert AX
DYN_OK = lambda ds: len(ds) <= 1


def pkey(t):
    return norm(NUM.sub('', t))


out, judged, bt, skip = [], [], [], collections.Counter()
for g in groups:
    if g['判定'] != '未判' or g['部类'] not in BULEI:
        continue
    ids = g['ids'].split(',')
    cl = collections.defaultdict(list)
    for i in ids:
        m = PAR.search(W[i].get('ai_note') or '')
        if m:
            cl[pkey(m.group(2))].append((i, m.group(1), m.group(2)))
    for k, v in cl.items():
        if len(v) < 2:
            continue
        skip['簇'] += 1
        v = [x for x in v if x[0] not in AX]
        if len(v) < 2:
            skip['4a-α 跳过'] += 1
            continue
        fs = {i: feat(i) for i, _, _ in v}

        def d(reason, kind='D'):
            skip[reason] += 1
            for a in range(len(v)):
                for b in range(a + 1, len(v)):
                    judged.append((v[a][0], v[b][0], kind, '子目-甲2：%s（《%s》，丛书《%s》）' % (reason, g['题名键'], v[0][2])))
        if len(norm(g['题名键'])) <= 1:
            d('泛称题名（单字，多为卷首／卷末／文体分卷，非独立作品）'); continue
        rc = collections.Counter(r for _, r, _ in v)
        if max(rc.values()) > 1:
            d('同一丛书记录内同题两条（疑异篇或重出）'); continue
        fas = {fs[i]['fa'] for i in fs} - {''}
        if len(fas) > 1:
            d('簇内首位责任者不同（%s，疑误字待 3c）' % '／'.join(sorted(fas))); continue
        ds = {fs[i]['dyn'] for i in fs} - {''}
        if not DYN_OK(ds):
            d('簇内朝代不同'); continue
        cas = [{c[2] for c in fs[i]['cols']} for i in fs]
        if any(not x for x in cas):
            skip['_有子目无丛书 Collection 或 Collection 无撰者'] += 1
        ca_all = set().union(*cas) - {''}
        if len(ca_all) > 1:
            skip['B 待核：同名丛书而丛书首位撰者不同（%s）' % '／'.join(sorted(ca_all))] += 1
            bt.append(dict(bulei=g['部类'], key=g['题名键'], congshu=k, ids=[i for i, _, _ in v], col_authors=sorted(ca_all))); continue
        js = set().union(*[({fs[i]['juan']} | fs[i]['bjuan']) for i in fs]) - {None}
        if js and max(js) - min(js) > 1:
            d('卷数差>1'); continue
        if any('敦煌' in (W[i].get('ai_note') or '') for i in fs):
            skip['敦煌'] += 1; continue
        order = sorted(fs, key=lambda i: (not fs[i]['fa'], -fs[i]['nbooks'],
                                          not any(not s.startswith('叢書部') for s in fs[i]['secs']), i))
        keeper, losers = order[0], order[1:]
        rid = {i: (r, t) for i, r, t in v}
        ev = ['《%s》（%s）属《%s》（丛书记录 %s）' % (W[i]['title'], i, rid[i][1], rid[i][0]) for i in order]
        out.append(dict(bulei=g['部类'], key=g['题名键'], congshu=k, keeper=keeper, keeper_title=W[keeper]['title'],
                        author=fs[keeper]['fa'], dyn=next(iter(ds), ''), juan=sorted(js), losers=losers, evidence=ev))
print(len(out), '簇', sum(len(o['losers']) for o in out), '条被并')
print(skip.most_common())
print(collections.Counter(o['bulei'] for o in out))
json.dump(out, open(OUT + '/jia2.json', 'w'), ensure_ascii=False, indent=1)
json.dump(bt, open(OUT + '/jia2-B待核.json', 'w'), ensure_ascii=False, indent=1)
with open(OUT + '/jia2-judged.tsv', 'w') as f:
    for r in judged:
        f.write('\t'.join(r) + '\n')
