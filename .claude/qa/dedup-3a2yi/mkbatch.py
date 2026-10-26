#!/usr/bin/env python3
"""去重方案 3a-2乙（集部别集名异写）：由 判定.tsv 的「并」对成簇，生成 apply_batch 用的 batch.json。

    mkbatch.py <批次目录> [--sample N] [--skip 已做批次目录,...] [--max 300]

成簇规则：只取判「并」的边做并查集；簇内任两条之间若另有「分立／存疑」边，整簇不并（防 詩集—集—文集 串并）。
每簇成员须在当前工作树里仍活（无 merged_into），否则跳过。
keeper：版本（Book）多＞有《中國古籍總目》著录＞著录多＞id 早。
"""
import argparse, collections, csv, glob, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def load(i):
    hits = glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json'))
    return json.load(open(hits[0], encoding='utf-8')) if len(hits) == 1 else None


def book_counts(ids):
    ids = set(ids); n = collections.Counter()
    for p in glob.glob(os.path.join(ROOT, 'Book', '*', '*', '*', '*.json')):
        try:
            d = json.load(open(p, encoding='utf-8'))
        except ValueError:
            continue
        if d.get('work_id') in ids and not d.get('merged_into'):
            n[d['work_id']] += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--sample', type=int); ap.add_argument('--max', type=int, default=300)
    ap.add_argument('--skip', default=''); ap.add_argument('--seed', type=int, default=25)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(os.path.join(HERE, '判定.tsv'), encoding='utf-8'), delimiter='\t'))
    print('载入判定', len(rows), '对'); assert rows
    par = {}
    def f(x):
        while par.setdefault(x, x) != x:
            x = par[x]
        return x
    for r in rows:
        if r['判定'] == '并':
            par[f(r['a_id'])] = f(r['b_id'])
    comp = collections.defaultdict(set)
    for x in list(par):
        comp[f(x)].add(x)
    done = set()
    for d in filter(None, a.skip.split(',')):
        for g in json.load(open(os.path.join(d, 'batch.json'), encoding='utf-8'))['groups']:
            done.update([g['keeper']] + g['losers'])
    clusters, blocked, dead = [], 0, 0
    for mem in comp.values():
        if len(mem) < 2 or mem & done:
            continue
        edges = [r for r in rows if r['a_id'] in mem and r['b_id'] in mem]
        if any(r['判定'] != '并' for r in edges):
            blocked += 1; continue
        recs = {i: load(i) for i in mem}
        if any(v is None or v.get('merged_into') for v in recs.values()):
            dead += 1; continue
        clusters.append((sorted(mem), edges, recs))
    print('可并簇', len(clusters), '簇内冲突不并', blocked, '成员已失活跳过', dead)
    clusters.sort(key=lambda c: c[0][0])
    if a.sample:
        random.seed(a.seed); clusters = random.sample(clusters, a.sample)
    clusters = clusters[:a.max]
    nb = book_counts([i for c in clusters for i in c[0]])
    groups = []
    for mem, edges, recs in clusters:
        def key(i):
            ib = [x for x in recs[i].get('indexed_by') or [] if isinstance(x, dict)]
            return (-nb[i], -any(x.get('source') == '中國古籍總目' for x in ib), -len(ib), i)
        keeper = min(mem, key=key); losers = [i for i in mem if i != keeper]
        def desc(i):
            r = recs[i]; au = (r.get('authors') or [{}])[0]
            return '《%s》%s(%s,%d版本)' % (r.get('title'), au.get('name'), r.get('dynasty') or '朝代缺', nb[i])
        ev = '集部别集名异写（同首位责任者，题名只差集名后缀）：%s；逐条子 agent 判并——%s' % (
            '／'.join(desc(i) for i in mem), '；'.join('%s|%s：%s' % (e['a_title'], e['b_title'], e['依据']) for e in edges))
        groups.append({
            'case_id': 'Y%04d' % (len(groups) + 1), 'cluster_id': '3a2yi-' + keeper, 'type': 'work',
            'keeper': keeper, 'losers': losers,
            'keeper_source': '去重方案 3a-2乙 集部别集名异写候选（细拆脚本 near_title_alias.py）＋逐条子 agent 判定（.claude/qa/dedup-3a2yi/判定.tsv）',
            'evidence': ev, 'rule': '去重方案 3a-2乙：别集名异写 B 档证据并（口径见 ai-team 3a-2乙-别集名异写口径.md）', 'why': ev,
            'loser_original_notes': {l: {k: recs[l][k] for k in ('description', 'ai_note') if recs[l].get(k)} for l in losers}})
    os.makedirs(a.out, exist_ok=True)
    json.dump({'groups': groups}, open(os.path.join(a.out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('写出', len(groups), '组', sum(len(g['losers']) for g in groups), '个被并者')


if __name__ == '__main__':
    main()
