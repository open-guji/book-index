#!/usr/bin/env python3
"""由判定对表生成 batch.json。用法：build_batch.py <pairs.tsv> <批次目录> [--cluster-prefix 3a2c-J01]
pairs.tsv 每行：id1<TAB>id2<TAB>档(A/B)<TAB>依据。同一 Work 出现在多对里的并成一个簇（连通分量）。
keeper：题名用正字者（差字取全库题名中较常见的一形，个别按 OVERRIDE）＞著录多＞id 早。
启动时核对每条仍活（非墓碑），并打印载入条数。"""
import collections, glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# 全库题名用字频率不能定正字的个别字对：值为正字
OVERRIDE = {'與輿': '輿', '元玄': '玄', '删刪': '刪', '場塲': '場', '制製': '制', '孤弧': '弧', '繆謬': '謬',
            '潁穎': '潁', '略畧': '略', '讚贊': '贊', '板版': '版', '劄札': '札', '穀谷': '穀', '榖谷': '榖', '岳獄': '岳',
            '詒貽': '詒', '世代': '世', '冢家': '冢', '禊褉': '禊', '梃挺': '梃', '挺梃': '梃'}


def path(i):
    h = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')
    assert len(h) == 1, (i, h)
    return h[0]


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    prefix = sys.argv[sys.argv.index('--cluster-prefix') + 1] if '--cluster-prefix' in sys.argv else '3a2c'
    rows = [l.rstrip('\n').split('\t') for l in open(src, encoding='utf-8') if l.strip() and not l.startswith('#')]
    print('载入判定对', len(rows))
    assert rows, '判定对为 0'
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
    import backrefs
    fq = collections.Counter()
    for t, _p, d in backrefs.iter_records(ROOT):
        if t == 'Work' and not d.get('merged_into'):
            fq.update(d.get('title') or '')
    print('全库活 Work 题名用字', sum(fq.values()))
    rec = {}
    par = {}
    def f(x):
        while par.setdefault(x, x) != x:
            x = par[x]
        return x
    ev = collections.defaultdict(list)
    for r in rows:
        a, b, grade, why = r[0], r[1], r[2], r[3]
        for i in (a, b):
            if i not in rec:
                rec[i] = json.load(open(path(i), encoding='utf-8'))
        if rec[a].get('merged_into') or rec[b].get('merged_into'):
            print('跳过（已有一侧被并）', a, b); continue
        par[f(a)] = f(b)
        ev[(a, b)] = (grade, why)
    cl = collections.defaultdict(set)
    for (a, b) in ev:
        cl[f(a)] |= {a, b}
    def score(i, members):
        t = rec[i].get('title') or ''
        s = 0
        for j in members:
            if j == i: continue
            u = rec[j].get('title') or ''
            if len(u) != len(t): continue
            for x, y in zip(t, u):
                if x != y:
                    key = ''.join(sorted(x + y))
                    good = OVERRIDE.get(key) or (x if fq.get(x, 0) >= fq.get(y, 0) else y)
                    s += 1 if x == good else -1
        return (s, len(rec[i].get('indexed_by') or []), -int(i, 36))
    groups = []
    for n, (root, mem) in enumerate(sorted(cl.items(), key=lambda kv: min(kv[1]))):
        mem = sorted(mem)
        keeper = max(mem, key=lambda i: score(i, mem))
        losers = [i for i in mem if i != keeper]
        evs = []
        grades = set()
        for (a, b), (g, w) in ev.items():
            if a in mem:
                grades.add(g)
                evs.append(f"《{rec[a].get('title')}》／《{rec[b].get('title')}》：{w}")
        def desc(i):
            d = rec[i]; au = (d.get('authors') or [{}])[0]
            j = (d.get('juan_count') or {}).get('number')
            return f"《{d.get('title')}》{au.get('name')}({d.get('dynasty') or au.get('dynasty') or '—'},{j if j else '—'}卷,{len(d.get('indexed_by') or [])}著录)"
        why = '差一字·經史：' + '／'.join(desc(i) for i in [keeper] + losers) + '；' + '；'.join(evs)
        g = 'B' if 'B' in grades else 'A'
        groups.append({'case_id': f'{prefix}-{n+1:03d}', 'cluster_id': f'{prefix}-{n+1:03d}', 'type': 'work',
                       'keeper': keeper, 'losers': losers,
                       'keeper_source': '去重方案细拆单元 3a-2丙 差一字·經史扫描（near_title_alias.py）',
                       'evidence': why, 'why': why,
                       'rule': f'去重方案3a-2丙：题名差一字（异体／误字／同书异写）{g} 档并',
                       'loser_original_notes': {l: {k: rec[l][k] for k in ('description', 'ai_note') if rec[l].get(k)} for l in losers}})
    os.makedirs(outdir, exist_ok=True)
    json.dump({'groups': groups}, open(os.path.join(outdir, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('簇', len(groups), '被并', sum(len(g['losers']) for g in groups))


if __name__ == '__main__':
    main()
