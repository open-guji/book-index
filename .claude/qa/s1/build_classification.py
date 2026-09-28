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


def _norm_title(s):
    return (s or "").replace("《", "").replace("》", "")


def match_siku(title_info, summary, smap_norm):
    """按去括号后的题名比对（book-index 少数条目的 title_info 缺《》，
    如「史記」《史記》均能命中；协调者验收 09-28 所报）。"""
    occs = smap_norm.get(_norm_title(title_info))
    if not occs:
        return None
    if len(occs) == 1:
        return occs[0][:3]
    key = (summary or "")[:30]
    cands = [o for o in occs if key and (o[3] or "")[:30] == key]
    if len(cands) == 1:
        return cands[0][:3]
    return None  # 多个同题又消歧不了：宁缺不错


# 协调者验收所报（09-28）：漢書藝文志早于四部体例，其「六藝略／春秋」把史书
# （史記一类）也收在内——本道 crosswalk 一律映成經部／春秋類是错的。这些是
# 漢志为唯一来源、逐条人工判过的例外（漢志非唯一来源时，S／後出志自然按
# rank() 优先胜出，用不上这张表）。
HANZHI_CHUNQIU_OVERRIDE = {
    '史記': ('史部', '正史類'),           # 太史公一百三十篇——即《史記》本書
    '續太史公': ('史部', '正史類'),        # 馮商所續《太史公》——史記之續作
    '春秋漢著記': ('史部', '編年類'),      # 漢著記一百九十卷——逐年時政記錄，起居注一類
    '太古以來年紀': ('史部', '編年類'),
    '漢大年紀': ('史部', '編年類'),
    '國語': ('史部', '雜史類'),           # 左丘明著，記諸國史事，非解經
    '新國語': ('史部', '雜史類'),         # 劉向分《國語》
    '戰國策': ('史部', '雜史類'),
    '楚漢春秋': ('史部', '雜史類'),        # 陸賈記楚漢之際史事，體例仿春秋而非解經
    '世本': ('史部', '傳記類'),           # 古史官記黃帝以來諸侯大夫世系，近譜牒傳記
    '春秋奏事': ('史部', '奏議類'),        # 秦時大臣奏事及刻石名山文，非解經
}


# 协调者验收所报（09-28）：補晉書藝文志「丁部集録／總集類」绝大多数确是總集
# （詩文合集），但混入了「奏事」「詔」一類公文，按書名關鍵詞另判。
def bujinshu_zongji_override(title_info):
    # 本桶（丁部集録／總集類）里含「奏」「詔」二字者逐一核过，皆是奏事／詔令
    # 之属而非詩文總集（如「魏名臣奏」「隆安直詔」），故此桶内可放宽按字判——
    # 放到其他来源／其他 section 不可作此推廣
    if '奏' in title_info:
        return '奏議類'
    if '詔' in title_info:
        return '詔令類'
    if '故事' in title_info:
        return '政書類'
    return None  # 其余仍归總集類，不改


def _rank(c):
    """S＞後出各志之 A／B＞漢書藝文志之 A／B＞C（协调者验收 09-28 所定：
    漢志早于四部体例，六藝略未必对应经部，与后出志或四库冲突时不该赢）。"""
    tier, src = c[3], c[4]
    is_han = src.startswith('漢書藝文志')
    base = {'S': 0, 'A': 1, 'B': 2}.get(tier, 5)
    return base + (2 if is_han and tier in ('A', 'B') else 0)


def build():
    V = vocab.load_vocab()
    smap = s_tier.build_siku_map()
    smap_norm = collections.defaultdict(list)
    for t, occs in smap.items():
        smap_norm[_norm_title(t)].extend(occs)
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
        title = d.get('title') or ''
        cands = []  # (l1, l2, l3, tier, source_desc)
        for e in (d.get('indexed_by') or []):
            if e.get('misattached'):
                continue
            src, sec, sbid = e.get('source'), e.get('section'), e.get('source_bid')
            if sbid == SIKU_BID:
                m = match_siku(e.get('title_info'), e.get('summary'), smap_norm)
                if m:
                    l1, l2, l3 = m
                    cands.append((l1, l2 or '', l3 or '', 'S', src))
            if sec:
                r = crosswalk.classify_section(src, sec)
                if r[0] == 'SKIP':
                    continue
                l1, l2, l3, tier, why = r
                if l2 == '__ZHAOLING__':
                    if re.search(r'詔|制|誥|敕|諭|冊|訓', title):
                        l2f = '詔令類'
                    elif re.search(r'奏|疏|議|章|封事|劄子', title):
                        l2f = '奏議類'
                    else:
                        l2f = ''
                    cands.append((l1, l2f, '', tier, f'{src}/{sec}'))
                elif l2 == '__BUJINSHU_ZONGJI__':
                    l2f = bujinshu_zongji_override(e.get('title_info') or title) or '總集類'
                    l1f = '史部' if l2f in ('奏議類', '詔令類', '政書類') else '集部'
                    cands.append((l1f, l2f, '', tier, f'{src}/{sec}'))
                else:
                    if src == '漢書藝文志' and sec == '六藝略／春秋' and title in HANZHI_CHUNQIU_OVERRIDE:
                        l1, l2 = HANZHI_CHUNQIU_OVERRIDE[title]
                        l3 = ''
                    cands.append((l1, l2 or '', l3 or '', tier, f'{src}/{sec}'))
        if not cands:
            continue
        specific = [c for c in cands if c[1]]
        l1s_all = {c[0] for c in cands if c[0]}
        best = None
        if specific:
            best_rank = min(_rank(c) for c in specific)
            at_best = [c for c in specific if _rank(c) == best_rank]
            l1s_at_best = {c[0] for c in at_best if c[0]}
            if len(l1s_at_best) > 1:
                conflicts.append({'id': wid, 'title': title,
                                   'l1s': sorted(l1s_at_best), 'cands': cands})
                continue
            best = at_best[0]
        elif len(l1s_all) > 1:
            conflicts.append({'id': wid, 'title': title,
                               'l1s': sorted(l1s_all), 'cands': cands})
            continue
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
