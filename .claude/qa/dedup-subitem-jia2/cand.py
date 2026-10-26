"""子目-甲2 候选：同名丛书不同版次里的同题叢書子目 Work 互并（子部、集部、未分类）。
叢書线（GUJI-526）按《總目》丛书版本记录各建一条子目 Work，同一丛书的几个版次里同一子目被建成多条。
簇＝同题组（dedup-census 口径）里所屬叢書題名去卷種數後相同的子目 Work；跳过 4a-α 清单里的 Work。
用法：P4WORK=<目录> python3 cand.py   （先跑 ../dedup-part4/load.py 与 scripts/dedup-census.py --out $P4WORK/census）
产出 $P4WORK/jia2.json（可并簇）（tier=B 为同名丛书而各版次丛书撰者写法不同、经核同一部书者）与 $P4WORK/jia2-judged.tsv（存疑／分立，入 ../dedup-judged/子目-甲2.tsv）。"""
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
YI = set()  # 子目-乙 判 A/B/B? 的对由子目-甲1 串执行（10-25 两串约定），这里跳过
for p in glob.glob(HERE + '/../dedup-subitem-yi/judged-*.tsv'):
    for line in open(p, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) > 6 and c[6] in ('A', 'B', 'B?'):
            YI |= {c[4], c[5]}
print('载入 子目-乙 A/B 跳过 Work', len(YI))
AX |= YI
assert AX
DYN_OK = lambda ds: len(ds) <= 1
# 同一丛书、各版次著录的编者写法不同（据《總目》叢書部著录与通行书目），不同编者属同一部书
ALIAS = {
    '文淵閣四庫全書': ({'永瑢', '紀昀'}, '文淵閣四庫全書各版次著录编者或作永瑢（总裁）或作紀昀（总纂），同一部书'),
    '說郛': ({'陶宗儀', '張宗祥'}, '說郛一百卷各版次著录编者或作陶宗儀（原编）或作張宗祥（重校），同一部书'),
    '唐人說薈唐代叢書': ({'陳世熙', '王文誥'}, '唐人說薈（唐代叢書）陳世熙辑、王文誥重编，同一部书'),
    '藝海珠塵': ({'吳省蘭', '錢熙輔'}, '藝海珠塵吳省蘭辑、錢熙輔续辑，同一部书'),
    '知不足齋叢書': ({'鮑廷博', '鮑志祖'}, '知不足齋叢書鮑廷博辑、鮑志祖续辑，同一部书'),
    '唐宋叢書': ({'鍾人傑', '張遂辰'}, '唐宋叢書鍾人傑、張遂辰同辑，同一部书'),
    '摛藻堂四庫全書薈要': ({'于敏中', '於敏中', '于敏中等', '於敏中等'}, '摛藻堂四庫全書薈要各版次编者著录作于敏中或於敏中（于／於异写），同一部书'),
    '檀几叢書餘集附政': ({'王晫', '張潮'}, '檀几叢書王晫、張潮同辑，同一部书'),
}


def pkey(t):
    return norm(NUM.sub('', t))


out, judged, skip = [], [], collections.Counter()
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
        tier = 'A'
        if len(ca_all) > 1:
            full = [set().union(*[{norm_name(a.get('name')) for a in C[c[0]].get('authors') or [] if isinstance(a, dict)} for c in fs[i]['cols']]) - {''}
                    for i in fs]
            common = set.intersection(*full) if full and all(full) else set()
            if common:
                tier = 'B'; cnote = '各版次丛书撰者皆有%s' % '、'.join(sorted(common))
            elif k in ALIAS and ca_all <= ALIAS[k][0]:
                tier = 'B'; cnote = ALIAS[k][1]
            else:
                d('同名丛书而丛书撰者不同（%s，疑为异编）' % '／'.join(sorted(ca_all))); continue
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
        if tier == 'B':
            ev.append('丛书撰者写法不同：%s' % cnote)
        out.append(dict(tier=tier, bulei=g['部类'], key=g['题名键'], congshu=k, keeper=keeper, keeper_title=W[keeper]['title'],
                        author=fs[keeper]['fa'], dyn=next(iter(ds), ''), juan=sorted(js), losers=losers, evidence=ev))
print(len(out), '簇', sum(len(o['losers']) for o in out), '条被并')
print(skip.most_common())
print(collections.Counter((o['tier'], o['bulei']) for o in out))
json.dump(out, open(OUT + '/jia2.json', 'w'), ensure_ascii=False, indent=1)
with open(OUT + '/jia2-judged.tsv', 'w') as f:
    for r in judged:
        f.write('\t'.join(r) + '\n')
