#!/usr/bin/env python3
"""S1-Work分类吸收：主管线。

用法（在 book-index 根目录下跑）：
  python3 .claude/qa/s1/build_classification.py build    # 只计算，写 .claude/qa/s1/out/*.json，不改 Work 档
  python3 .claude/qa/s1/build_classification.py write [--l1 經部|史部|子部|集部] [--limit N]
                                                          # 把 build 的结果写进 Work 档的 classification 字段
                                                          # （只写这一个字段，不动其他字段），可按部分批

依据：任务书 overview `项目进展/总调度/古籍索引三块/任务书/S1-Work分类吸收.md`。
三级依据优先序 S＞A＞B＞C；各源冲突（不同来源判定的 l1 不同）者一律不写，见
out/conflicts.json；对照表判不了、拿不准的行见 out/skipped_sections.json。
"""
import argparse, collections, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vocab, siku, s_tier, crosswalk

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'out')
SIKU_BID = siku.SIKU_WORK_ID


def match_siku(title_info, summary, smap):
    occs = smap.get(title_info)
    if not occs:
        return None
    if len(occs) == 1:
        return occs[0][:3]
    key = (summary or "")[:30]
    cands = [o for o in occs if key and (o[3] or "")[:30] == key]
    if len(cands) == 1:
        return cands[0][:3]
    return None  # 多个同题又消歧不了：宁缺不错


def build():
    V = vocab.load_vocab()
    smap = s_tier.build_siku_map()
    files = sorted(glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')))
    results = {}
    conflicts = []
    tier_count = collections.Counter()
    n_total = 0
    for fp in files:
        d = json.load(open(fp, encoding='utf-8'))
        if d.get('merged_into'):
            continue
        n_total += 1
        wid = d['id']
        cands = []  # (l1, l2, l3, tier, source_desc)
        for e in (d.get('indexed_by') or []):
            if e.get('misattached'):
                continue
            src, sec, sbid = e.get('source'), e.get('section'), e.get('source_bid')
            if sbid == SIKU_BID:
                m = match_siku(e.get('title_info'), e.get('summary'), smap)
                if m:
                    l1, l2, l3 = m
                    cands.append((l1, l2 or '', l3 or '', 'S', src))
            if sec:
                r = crosswalk.classify_section(src, sec)
                if r[0] == 'SKIP':
                    continue
                l1, l2, l3, tier, why = r
                if l2 == '__ZHAOLING__':
                    ttl = d.get('title') or ''
                    if re.search(r'詔|制|誥|敕|諭|冊|訓', ttl):
                        l2f = '詔令類'
                    elif re.search(r'奏|疏|議|章|封事|劄子', ttl):
                        l2f = '奏議類'
                    else:
                        l2f = ''
                    cands.append((l1, l2f, '', tier, f'{src}/{sec}'))
                else:
                    cands.append((l1, l2 or '', l3 or '', tier, f'{src}/{sec}'))
        if not cands:
            continue
        specific = [c for c in cands if c[1]]
        l1s_specific = {c[0] for c in specific if c[0]}
        l1s_all = {c[0] for c in cands if c[0]}
        if len(l1s_specific) > 1:
            conflicts.append({'id': wid, 'title': d.get('title'),
                               'l1s': sorted(l1s_specific), 'cands': cands})
            continue
        if not specific and len(l1s_all) > 1:
            conflicts.append({'id': wid, 'title': d.get('title'),
                               'l1s': sorted(l1s_all), 'cands': cands})
            continue
        best = None
        for pref in ('S', 'A', 'B'):
            for c in cands:
                if c[3] == pref and c[1]:
                    best = c; break
            if best:
                break
        if best:
            tier_count['l2_' + best[3]] += 1
            results[wid] = {'l1': best[0], 'l2': best[1], 'l3': best[2] or '',
                             'basis': best[3], 'source': best[4], 'path': os.path.relpath(fp, ROOT)}
        elif l1s_all:
            l1 = next(iter(l1s_all))
            tier_count['l1only'] += 1
            results[wid] = {'l1': l1, 'l2': '', 'l3': '', 'basis': 'C',
                             'source': ';'.join(sorted({c[4] for c in cands})),
                             'path': os.path.relpath(fp, ROOT)}

    bad = []
    for wid, r in results.items():
        c = {'l1': r['l1'], 'l2': r['l2'], 'l3': r['l3'], 'l4': ''}
        if not vocab.valid_classification(c, V):
            bad.append((wid, r))
    if bad:
        print(f'词表校验不过 {len(bad)} 条——不应发生，先修 crosswalk 再 build', file=sys.stderr)
        for wid, r in bad[:10]:
            print('  ', wid, r, file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUT, exist_ok=True)
    # results.json 是可重算的工作缓存（.gitignore 排除），冲突清单与未用对照行是
    # 报告要用的审计产物，落在 .claude/qa/ 顶层，随本道一并提交
    json.dump(results, open(os.path.join(OUT, 'results.json'), 'w', encoding='utf-8'),
               ensure_ascii=False, indent=1)
    qa_dir = os.path.join(ROOT, '.claude', 'qa')
    json.dump(conflicts, open(os.path.join(qa_dir, 'S1-分类冲突清单.json'), 'w', encoding='utf-8'),
               ensure_ascii=False, indent=1)

    skip_rows = []
    for (src, sec), n in crosswalk.scan_sections().items():
        r = crosswalk.classify_section(src, sec)
        if r[0] == 'SKIP':
            skip_rows.append({'source': src, 'section': sec, 'count': n, 'why': r[1]})
    skip_rows.sort(key=lambda x: -x['count'])
    json.dump(skip_rows, open(os.path.join(qa_dir, 'S1-未用对照行清单.json'), 'w', encoding='utf-8'),
               ensure_ascii=False, indent=1)

    print('works(非墓碑)', n_total, '有分类线索', len(results), '冲突', len(conflicts))
    print(dict(tier_count))
    print('到类合计', sum(v for k, v in tier_count.items() if k.startswith('l2')))
    print('未用 section 行数', len(skip_rows), '条目数合计', sum(r['count'] for r in skip_rows))
    print('写入', OUT)


def _dump(obj, fmt=(2, '\n')):
    ind, nl = fmt
    return json.dumps(obj, ensure_ascii=False, indent=ind) + nl


def _fmt_of(raw, d):
    for ind in (2, 1, 4):
        for nl in ('\n', ''):
            if raw == json.dumps(d, ensure_ascii=False, indent=ind) + nl:
                return ind, nl
    return 2, '\n'


def write(l1_filter=None, limit=None):
    results = json.load(open(os.path.join(OUT, 'results.json'), encoding='utf-8'))
    items = [(wid, r) for wid, r in results.items() if not l1_filter or r['l1'] == l1_filter]
    if limit:
        items = items[:limit]
    n_written = 0
    for wid, r in items:
        p = os.path.join(ROOT, r['path'])
        raw = open(p, encoding='utf-8').read()
        d = json.loads(raw)
        if d.get('classification'):
            continue  # 已写过（重跑幂等），不重复覆盖
        d['classification'] = {'l1': r['l1'], 'l2': r['l2'], 'l3': r['l3'], 'l4': '',
                                'basis': r['basis'], 'source': r['source']}
        fmt = _fmt_of(raw, json.loads(raw))
        open(p, 'w', encoding='utf-8').write(_dump(d, fmt))
        n_written += 1
    print(f'写入 {n_written} 条' + (f'（部＝{l1_filter}）' if l1_filter else '（全部）'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['build', 'write'])
    ap.add_argument('--l1', default=None)
    ap.add_argument('--limit', type=int, default=None)
    a = ap.parse_args()
    if a.cmd == 'build':
        build()
    else:
        write(a.l1, a.limit)
