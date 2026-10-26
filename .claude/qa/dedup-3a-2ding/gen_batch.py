#!/usr/bin/env python3
"""去重方案 3a-2丁（子集未分类·题名差一字）：由判定对生成 apply_batch 用的 batch.json。

    gen_batch.py <pairs.tsv> <批次目录> <批名> [--max N] [--rule A|B] [--block 判分立存疑.tsv]

pairs.tsv 每行：idA  idB  类型(异体/通用/误字/简称)  依据字  理由。按对求连通簇；簇内各条须仍活、非敦煌遗书、
彼此未互链（related_works 已互指者视为已判分立，整簇跳过）；两条卷数（juan_count，缺则取各著录 title_info 主卷数）无一对相差 ≤1 的簇在 A 档跳过、B 档照收。
簇内有合刻著录（title_info「某N卷某某N卷」）、多出他人责任者的，整簇跳过（转人工）。
簇内任两条若在 --block 文件里（判分立／存疑的对），整簇跳过，防经第三条串并。
keeper：题名不含异体字＞版本多＞著录多＞id 早。"""
import collections, glob, json, os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
VAR = set('襍厯歴靑禄㫖彚圗緫㑹藳稾藁遯谿磵礀畧嬾虚内謡眞黄緑潜鍼祕窻窓筭灋勛迃僊挍綉碁叅燄')
NUM = '一二三四五六七八九十百'
HEKE = re.compile(r'[%s]卷\s?(?!附|首|末|補|續|録|錄|目|存|殘)[^\s\d，。、；：（）()《》,]{2,}?[%s]+卷' % (NUM, NUM))
def cn(t):
    n, cur = 0, 0
    for ch in t:
        v = NUM.find(ch)
        if ch == '十': cur = (cur or 1) * 10; n += cur; cur = 0
        elif ch == '百': cur = (cur or 1) * 100; n += cur; cur = 0
        else: cur = v + 1
    return n + cur
def juans(d):
    # juan_count；缺则取各著录 title_info 开头的主卷数
    if isinstance(d.get('juan_count'), dict) and isinstance(d['juan_count'].get('number'), int): return [d['juan_count']['number']]
    out = []
    for x in d.get('indexed_by') or []:
        m = re.match(r'^《?[^《》\d]*?》?\s*([%s]+)卷' % NUM, (x.get('title_info') or '') if isinstance(x, dict) else '')
        if m: out.append(cn(m.group(1)))
    return out
def path(i): return glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def load(i): return json.load(open(path(i), encoding='utf-8'))
def main():
    src, outdir, name = sys.argv[1:4]
    mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 10**9
    rule = sys.argv[sys.argv.index('--rule') + 1] if '--rule' in sys.argv else 'A'
    pairs = [l.rstrip('\n').split('\t') for l in open(src, encoding='utf-8') if l.strip()]
    par = {}
    def f(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    why = collections.defaultdict(list)
    block = set()
    if '--block' in sys.argv:
        for l in open(sys.argv[sys.argv.index('--block') + 1], encoding='utf-8'):
            q = l.split('\t')
            if len(q) > 1: block.add(frozenset(q[:2]))
    for p in pairs:
        par[f(p[0])] = f(p[1])
    for p in pairs: why[f(p[0])].append(p)
    base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
    sys.path.insert(0, os.path.join(ROOT, '.claude/qa')); import backrefs
    need = {x for p in pairs for x in p[:2]}; nb = collections.Counter()
    for t, _, d in backrefs.iter_records(ROOT):
        if t == 'Book' and d.get('work_id') in need and not d.get('merged_into'): nb[d['work_id']] += 1
    groups, skipped = [], []
    for r, ps in sorted(why.items(), key=lambda kv: min(min(p[0], p[1]) for p in kv[1])):
        ids = sorted({x for p in ps for x in p[:2]})
        D = {i: load(i) for i in ids}
        if any(frozenset((x, y)) in block for x in ids for y in ids if x < y): skipped.append((ids, '簇内有分立／存疑对')); continue
        if any(HEKE.search(x.get('title_info') or '') for d in D.values() for x in d.get('indexed_by') or [] if isinstance(x, dict)):
            skipped.append((ids, '合刻／附刻著录')); continue
        names = [{a.get('name') for a in d.get('authors') or [] if isinstance(a, dict)} for d in D.values()]
        if any(len(n) > 1 and n - set().union(*[m for j, m in enumerate(names) if j != i]) for i, n in enumerate(names)): skipped.append((ids, '多出他人责任者')); continue
        if any(d.get('merged_into') for d in D.values()): skipped.append((ids, '已并')); continue
        if any('敦煌遺書' in (d.get('ai_note') or '') for d in D.values()): skipped.append((ids, '敦煌')); continue
        rel = any(isinstance(x, dict) and x.get('id') in ids or x in ids for d in D.values() for x in d.get('related_works') or [])
        if rel: skipped.append((ids, '已互链')); continue
        J = [juans(d) for d in D.values()]
        if rule == 'A' and any(a and b and min(abs(x - y) for x in a for y in b) > 1 for i, a in enumerate(J) for b in J[i + 1:]): skipped.append((ids, '卷数差>1 转 B')); continue
        key = lambda i: (any(c in VAR for c in D[i].get('title') or ''), -nb[i], -len(D[i].get('indexed_by') or []), i)
        keeper = min(ids, key=key); losers = [i for i in ids if i != keeper]
        desc = '／'.join(f"《{D[i]['title']}》{'/'.join(a.get('name') or '' for a in (D[i].get('authors') or [])[:1])}({','.join(str(x) for x in [((D[i].get('juan_count') or {}).get('number') if isinstance(D[i].get('juan_count'), dict) else None)] if x)}{'卷' if isinstance(D[i].get('juan_count'), dict) else ''})" for i in ids)
        ev = f"题名只差一字（{'；'.join(p[3] + ' ' + p[2] + '：' + p[4] for p in ps)}）。{desc}；首位责任者同一，朝代兼容，著作领域不冲突"
        if len(groups) >= mx: break
        groups.append({'case_id': f'{name}-{len(groups)+1:03d}', 'cluster_id': f'3a-2丁-{name}-{len(groups)+1:03d}', 'type': 'work', 'keeper': keeper, 'losers': losers,
                       'keeper_source': f'去重方案 3a-2丁 差一字近题扫描（book-index {base[:10]}）', 'evidence': ev,
                       'rule': '去重方案 3a-2丁：题名差一字（异体／通用／误字）同首位责任者，' + ('A 档机械并' if rule == 'A' else 'B 档证据并'), 'why': ev,
                       'loser_original_notes': {l: {k: D[l][k] for k in ('ai_note', 'description') if D[l].get(k)} for l in losers}})
    os.makedirs(outdir, exist_ok=True)
    json.dump({'groups': groups}, open(os.path.join(outdir, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('载入对', len(pairs), '组', len(groups), '跳过', len(skipped))
    if not pairs: sys.exit('载入 0 对')
    for s in skipped: print('跳过', *s)
main()
