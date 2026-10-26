#!/usr/bin/env python3
"""3a-3：汇总子 agent 判定 → 簇 → batch.json（供 ../dedup-3a/apply_3a.py 同款 apply_batch 使用）与 dedup-judged 登记。

    python3 build_batch.py <packets_dir> <verdicts_dir> <out_dir> [--name b-01] [--limit N] [--skip-done 已并台账...]

判定文件：A_id  B_id  同书|分立|存疑  A|B|-  理由
簇＝同书边的连通分量；keeper：题名不带撰人尾／坊刻前缀＞子 agent 保留建议票数＞著录多＞id 早；簇内任两点有「分立」边则整簇转存疑；簇大于 4 留人工。
"""
import argparse, collections, glob, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def path_of(i):
    h = glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json'))
    return h[0] if len(h) == 1 else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('packets'); ap.add_argument('verdicts'); ap.add_argument('out')
    ap.add_argument('--name', default='b-01'); ap.add_argument('--limit', type=int, default=300)
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--skip-done', action='append', default=[])
    a = ap.parse_args()
    info, ev = {}, {}
    for f in sorted(glob.glob(os.path.join(a.packets, '*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            info[r['A']['id']] = r['A']; info[r['B']['id']] = r['B']
            ev[tuple(sorted(r['pair'].split('|')))] = r['evidence']
    V = {}
    for f in sorted(glob.glob(os.path.join(a.verdicts, '*.tsv'))):
        for line in open(f, encoding='utf-8'):
            x = line.rstrip('\n').split('\t')
            if len(x) < 5 or x[2] not in ('同书', '分立', '存疑'):
                continue
            V[tuple(sorted(x[:2]))] = (x[2], {'A': x[0], 'B': x[1]}.get(x[3]), x[4])
    print('载入判定', len(V), collections.Counter(v[0] for v in V.values()), file=sys.stderr)
    assert V
    done = set()
    for f in a.skip_done:
        for m in json.load(open(f, encoding='utf-8'))['merges']:
            done.update([m['keeper']] + m['losers'])
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for (p, q), (v, k, r) in V.items():
        if v == '同书': par[find(p)] = find(q)
    cl = collections.defaultdict(set)
    for x in list(par): cl[find(x)].add(x)
    groups, held = [], []
    for root, mem in cl.items():
        if len(mem) < 2: continue
        bad = [pq for pq, (v, k, r) in V.items() if v == '分立' and pq[0] in mem and pq[1] in mem]
        if bad:
            held.append((mem, '簇内有分立边')); continue
        if len(mem) > 4:
            held.append((mem, '簇过大')); continue
        if mem & done:
            continue
        recs = {}
        for i in mem:
            p = path_of(i)
            if not p: break
            d = json.load(open(p, encoding='utf-8'))
            if d.get('merged_into'): break
            recs[i] = d
        if len(recs) != len(mem):
            held.append((mem, '已有成员被并或缺')); continue
        edges = [(pq, V[pq]) for pq in V if pq[0] in mem and pq[1] in mem and V[pq][0] == '同书']
        votes = collections.Counter(k for _, (v, k, r) in edges if k)
        keeper = sorted(mem, key=lambda i: (bool(re.search(r'[撰著編輯]$|^(新刊|新刻|新鐫|重刻|重刊|刻)', recs[i].get('title') or '')), -votes[i], -len(recs[i].get('indexed_by') or []), i))[0]
        losers = sorted(mem - {keeper})
        def lab(i):
            d = recs[i]; au = '/'.join(str(x.get('name')) for x in (d.get('authors') or [])[:1] if isinstance(x, dict))
            return '《%s》%s' % (d.get('title'), au)
        reasons = '；'.join(r for _, (v, k, r) in edges)
        cites = '；'.join('%s「%s」' % (e.get('mark', '其他题名'), e.get('context') or e.get('alias')) for pq, _ in edges for e in ev.get(pq, [])[:1])
        kind = '著录原文自证' if any(e.get('mark') for pq, _ in edges for e in ev.get(pq, [])) else '总目题名括注／其他题名互见'
        why = '异题名同书（%s）：%s／%s；依据：%s；两道子 agent 逐条复核：%s' % (kind, lab(keeper), '、'.join(lab(l) for l in losers), cites, reasons)
        notes = {}
        for l in losers:
            n = {k: recs[l].get(k) for k in ('ai_note', 'description') if recs[l].get(k)}
            if n: notes[l] = n
        groups.append({'case_id': 'A3-%s' % keeper, 'cluster_id': '3a3-%s' % keeper, 'type': 'work', 'keeper': keeper, 'losers': losers,
                       'keeper_source': '去重方案 3a-3 一名／又名自证扫描（.claude/qa/dedup-3a3/scan_alias.py）',
                       'evidence': why, 'rule': '去重方案3a-3：异题名同书，著录原文自证（一名／又名／原名／即）B 档逐条复核并', 'why': why,
                       'loser_original_notes': notes})
    groups.sort(key=lambda g: g['keeper'])
    sel = groups[a.offset:a.offset + a.limit]
    od = os.path.join(a.out, a.name); os.makedirs(od, exist_ok=True)
    json.dump({'groups': sel}, open(os.path.join(od, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('同书簇', len(groups), '本批', len(sel), '留人工', len(held), file=sys.stderr)
    with open(os.path.join(a.out, '留人工.tsv'), 'w', encoding='utf-8') as f:
        for mem, why in held:
            f.write('%s\t%s\t%s\n' % (why, ','.join(sorted(mem)), '、'.join(info.get(i, {}).get('title') or '' for i in sorted(mem))))
    # dedup-judged 登记：分立→C，存疑→D
    with open(os.path.join(a.out, 'judged-3a-3.tsv'), 'w', encoding='utf-8') as f:
        for (p, q), (v, k, r) in sorted(V.items()):
            if v != '同书':
                f.write('%s\t%s\t%s\t%s\n' % (p, q, {'分立': 'C-分立', '存疑': 'D-存疑'}[v], r.replace('\t', ' ')))

if __name__ == '__main__':
    main()
