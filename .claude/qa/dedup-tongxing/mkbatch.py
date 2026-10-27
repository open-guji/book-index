#!/usr/bin/env python3
"""新-同姓异名余 并条簇与批次规格（改自 dedup-3b0/mkbatch.py）：读 判定.tsv（S 同人并、S2 原文同列并、D 存疑、X 分立），
S／S2 对连成簇，簇内不得有 D／X 对、卷数极差≤1；规范名取 判定.tsv「规范名」栏（簇内多数），keeper 取用规范名者。

    python3 mkbatch.py <批次目录> [--only 簇号,…] [--limit N] [--skip 簇号,…] [--list]
"""
import argparse, collections, csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location('dc', os.path.join(ROOT, 'scripts', 'dedup-census.py'))
dc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(dc)

PREFIX = re.compile(r'^(\[[^\]]*\]|新刊|新刻|新鐫|新鍥|重刊|重刻|欽定|御定|御纂)')
EXCEPT = set()
# 卷数极差＞1 而逐条复核判同书者（丛书卷次误入、残本／辑本条目已在 keeper、他志异记）
JUAN_OK = {'txy-183', 'txy-256', 'txy-306', 'txy-336', 'txy-346', 'txy-445', 'txy-455', 'txy-518', 'txy-746', 'txy-747',
           'txy-781', 'txy-784', 'txy-810', 'txy-236', 'txy-773'}
PRE = re.compile(r'(齊|周|陳|燕|吳|呉|晉|晋|梁|魏|日|日本|美|英|光禄勳|光祿勳)')
SUF = re.compile(r'(讚|輯|修|撰|等|公|氏|攷)')
# 独立核验判存疑而剔出者（簇号 → 理由），登 dedup-judged 为 D
EXCL = {'txy-357': '李充《四部》为晋代目录，李彤《四部》入小学类、佚文讲鸟兽，二书（独立核验 BAD）',
    'txy-491': '靜菴条系元代、记九帙，与胡世寧十八卷是否同书证据不足（独立核验 UNSURE）',
    'txy-167': '被并条 d59f2neqw26a 有 book-text 整理本，需先迁移文本再并',
    'txy-223': '被并条 d59f2mpj5ukh 有 book-text 文本，需先迁移文本再并',
    'txy-268': '被并条 d59f2gnaepz5 有 book-text 文本，需先迁移文本再并',
    'txy-402': '两条皆有 book-text 文本，需先迁移文本再并',
    'txy-254': '第二条为附周玄暐《涇林續記》的合刻本，首位责任者取续记作者（独立核验 UNSURE）'}
ALIAS_EV = re.compile(r'CBDB|别名|字號|异体|同entity|原文')


def wpath(i):
    h = glob.glob(os.path.join(ROOT, 'Work', i[-3], i[-2], i[-1], i + '-*.json'))
    assert len(h) == 1, (i, h)
    return h[0]


def load(i):
    return json.load(open(wpath(i), encoding='utf-8'))


def ent(eid):
    if not eid:
        return None
    h = glob.glob(os.path.join(ROOT, 'Entity', eid[-3], eid[-2], eid[-1], eid + '-*.json'))
    return json.load(open(h[0], encoding='utf-8')) if h else None


def nbooks():
    n = collections.Counter()
    for p in glob.iglob(os.path.join(ROOT, 'Book', '*', '*', '*', '*.json')):
        try:
            d = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        if not d.get('merged_into') and d.get('work_id'):
            n[d['work_id']] += 1
    return n


def first(d):
    a = [x for x in d.get('authors') or [] if isinstance(x, dict)]
    return a[0] if a else {}


CN = dict(zip('〇一二三四五六七八九', range(10)))


def cn2i(t):
    """一百二十 → 120；只认常见卷数写法"""
    n, cur = 0, 0
    for ch in t:
        if ch in CN:
            cur = CN[ch]
        elif ch == '十':
            n += (cur or 1) * 10; cur = 0
        elif ch == '百':
            n += (cur or 1) * 100; cur = 0
    return n + cur


def juans(d):
    """juan_count 与各著录 title_info 里的「N卷」（取每条首个），供卷数相容核对"""
    out = set()
    j = d.get('juan_count') or {}
    if isinstance(j, dict) and j.get('number'):
        out.add(j['number'])
    for x in d.get('indexed_by') or []:
        m = re.search(r'([〇一二三四五六七八九十百]+)卷', x.get('title_info') or '')
        if m:
            out.add(cn2i(m.group(1)))
    return out - {0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir'); ap.add_argument('--only'); ap.add_argument('--skip'); ap.add_argument('--limit', type=int)
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    rows = list(csv.DictReader(open(os.path.join(HERE, '判定.tsv'), encoding='utf-8'), delimiter='\t'))
    par = {}

    def f(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for r in rows:
        if r['判定'] in ('S', 'S2'):
            par[f(r['Work甲'])] = f(r['Work乙'])
    cl = collections.defaultdict(set)
    for r in rows:
        if r['判定'] in ('S', 'S2'):
            cl[f(r['Work甲'])] |= {r['Work甲'], r['Work乙']}
    W = {}
    for ids in cl.values():
        for i in ids:
            W[i] = load(i)
    NB = nbooks()
    print('载入 Work %d、Book 挂接 %d' % (len(W), sum(NB.values())), file=sys.stderr)
    assert W and NB
    groups, bad = [], []
    for root, ids in sorted(cl.items(), key=lambda kv: min(int(r['序']) for r in rows if r['Work甲'] in kv[1] and r['判定'] in ('S', 'S2'))):
        ids = sorted(ids)
        prs = [r for r in rows if r['Work甲'] in ids and r['Work乙'] in ids]
        seqs = sorted(int(r['序']) for r in prs if r['判定'] in ('S', 'S2'))
        cid = 'txy-%03d' % seqs[0]
        # 已墓碑（别的单元先并了）则整簇跳过，下轮重算
        if any(W[i].get('merged_into') for i in ids):
            bad.append((cid, '有成员已成墓碑')); continue
        if cid in EXCL:
            bad.append((cid, '核验存疑：' + EXCL[cid])); continue
        neg = [r for r in prs if r['判定'] in ('D', 'X', 'K')]
        if neg:
            bad.append((cid, '簇内有 %s 对' % '/'.join(r['判定'] + r['序'] for r in neg))); continue
        js = set().union(*(juans(W[i]) for i in ids))
        if js and max(js) - min(js) > 1 and not (set(seqs) & EXCEPT) and cid not in JUAN_OK:
            bad.append((cid, '卷数不相容 %s' % sorted(js))); continue
        # 规范名（keeper 取用此名者）：人工指定（CANON）＞CBDB 本名＞名互含里去掉朝代／官称前缀、去掉误入的角色字，或补全脱字者
        # ＞所繫 Entity 主名＞著录原文 author_info 最常见之形
        names = {i: dc.norm_name(first(W[i]).get('name')) for i in ids}
        vals = set(names.values())
        txt = ' '.join(x.get('author_info') or '' for i in ids for x in W[i].get('indexed_by') or [])
        sc = {n: txt.count(n) - sum(txt.count(m) for m in vals if m != n and n in m) for n in vals}
        for r in prs:
            for m in re.finditer(r'CBDB:([^(]+)\(', r['机器证据']):
                if m.group(1) in sc:
                    sc[m.group(1)] += 100
        for x in vals:
            for y in vals:
                if x != y and y in x:
                    pre, suf = x[:x.index(y)], x[x.index(y) + len(y):]
                    if (pre and PRE.fullmatch(pre) and not suf) or (suf and SUF.fullmatch(suf) and not pre):
                        sc[y] += 50
                    elif not pre and suf and len(suf) <= 2:
                        sc[x] += 50
        for i in ids:
            e = ent(first(W[i]).get('entity_id'))
            if e and dc.norm_name(e.get('primary_name')) in sc:
                sc[dc.norm_name(e.get('primary_name'))] += 5
        cv = collections.Counter(dc.norm_name(r['规范名']) for r in prs if r['判定'] in ('S', 'S2') and dc.norm_name(r['规范名']) in vals)
        canon = cv.most_common(1)[0][0] if cv else max(sc, key=lambda n: (sc[n], len(n)))
        assert canon in vals, (cid, canon, vals)
        ceid = None
        cands = [i for i in ids if names[i] == canon] or ids
        keeper = sorted(cands, key=lambda i: (bool(PREFIX.match(W[i].get('title') or '')), -NB[i], -len(W[i].get('indexed_by') or []), i))[0]
        losers = [i for i in ids if i != keeper]
        kf = first(W[keeper])
        # keeper 撰人无 entity 而簇内他条有（且是同一人）：补繫；别名形（字號／异写）补进 Entity alt_names
        kdyn = W[keeper].get('dynasty') or kf.get('dynasty')
        eid = kf.get('entity_id') or ceid or next((first(W[i]).get('entity_id') for i in ids if first(W[i]).get('entity_id')
                                                   and ent(first(W[i]).get('entity_id'))
                                                   and (not kdyn or not ent(first(W[i]).get('entity_id')).get('dynasty')
                                                        or ent(first(W[i]).get('entity_id')).get('dynasty') == kdyn)
                                                   and canon in {dc.norm_name(x if isinstance(x, str) else x.get('name')) for x in [ent(first(W[i]).get('entity_id')).get('primary_name')] + (ent(first(W[i]).get('entity_id')).get('alt_names') or [])}), None)
        e = ent(eid)
        known = {dc.norm_name(e.get('primary_name'))} | {dc.norm_name(x if isinstance(x, str) else x.get('name')) for x in e.get('alt_names') or []} if e else set()
        alias = []
        for r in prs:
            if r['判定'] != 'S' or not ALIAS_EV.search(r['机器证据'] + r['理由']) or re.search(r'衍字|脱|误切|前缀|连写|泛称', r['理由']):
                continue
            for n in (r['撰人甲'], r['撰人乙']):
                if e and dc.norm_name(n) not in known and n not in [x['name'] for x in alias]:
                    alias.append({'name': n, 'seq': int(r['序']), 'why': r['理由']})
        ev = '；'.join('《%s》%s／%s：%s' % (r['题名键'], r['撰人甲'], r['撰人乙'], r['理由']) for r in prs if r['判定'] in ('S', 'S2'))
        g = {'case_id': cid, 'cluster_id': cid, 'type': 'work', 'keeper': keeper, 'losers': losers,
             'keeper_source': '去重第二轮细拆单元 新-同姓异名余（dedup-tongxing/判定.tsv 序 %s）' % ','.join(map(str, seqs)),
             'evidence': '署名异写同书：' + ev, 'rule': '去重第二轮细拆单元 新-同姓异名余（3b-0 口径）：题名相同、首位责任者同姓异名而判为同一人（名／字／號异写、形近讹字、署名残缺）或著录同列，B 档并',
             'why': '署名异写同书：' + ev,
             'loser_original_notes': {l: {k: W[l].get(k) for k in ('description', 'ai_note') if W[l].get(k)} for l in losers},
             'author_fix': {'canon': canon, 'entity_id': eid if not kf.get('entity_id') else None,
                            'rename': kf.get('name') if dc.norm_name(kf.get('name')) != canon else None},
             'alias_add': {'entity_id': eid, 'names': alias} if e and alias else None,
             'bulei': next(r['部类'] for r in prs)}
        groups.append(g)
    for c, why in bad:
        print('跳过', c, why, file=sys.stderr)
    if a.only:
        groups = [g for g in groups if g['cluster_id'] in a.only.split(',')]
    if a.skip:
        groups = [g for g in groups if g['cluster_id'] not in a.skip.split(',')]
    if a.limit:
        groups = groups[:a.limit]
    print('成簇 %d，跳过 %d，本批 %d 组、被并 %d 条' % (len(groups) + len(bad), len(bad), len(groups), sum(len(g['losers']) for g in groups)), file=sys.stderr)
    if a.list:
        for g in groups:
            kf = first(W[g['keeper']])
            print('%s\t%s\t%s(%s)\t%s\t%s\t%s' % (g['cluster_id'], W[g['keeper']].get('title'), kf.get('name'), g['keeper'],
                  '、'.join('%s(%s)' % (first(W[l]).get('name'), l) for l in g['losers']), json.dumps(g['author_fix'], ensure_ascii=False),
                  '、'.join(x['name'] for x in (g['alias_add'] or {}).get('names', []))))
        return
    os.makedirs(a.outdir, exist_ok=True)
    json.dump({'groups': groups}, open(os.path.join(a.outdir, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
