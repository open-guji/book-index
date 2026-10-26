#!/usr/bin/env python3
"""拆回 10-19「查重线 Book 层」错并的叢書子目 Book（去重方案部分 6 第四节第 1 条）。

成因：草稿库提交 449d40913f2「跨部查重 Book 层：同 Work 同版本重复 Book 并条」把各叢書版次里的同一子目
（同 Work、edition 同为空或同写「道光本」之类）当成同版本并成一条，被并者留草稿墓碑，keeper 随后升格；
于是一个正式 Book 同时挂在同一丛书的几个版次（或几部不同丛书）下。一个 Book 是一个具体版本，应拆。

做法（只拆「被并者所属 Collection 与 keeper 不同」者；同 Collection 或都无 Collection 的并条不动）：
- 被并草稿的原记录取自 449d40913f2^（git 历史完整），草稿 id 按 promotions 译成正式 id（work_id 用 keeper 现值），
  铸新正式 id 建 Book，ai_note 记来历；promotions 加「被并草稿 → 新 Book」。
- keeper 减法复原：只删掉来自被并者的 provenance／indexed_by／sources／contained_in 项与 merged_from 项、改写
  ai_note 里的查重线说明；keeper 10-19 之后的其他改动原样保留。减完与 keeper 自身原记录（译后）逐项核对。
- 草稿库：被并草稿墓碑改成已升格残档（去 work_id／merged_into），keeper 草稿残档的 merged_from 去掉它。

用法：split.py --draft ../book-index-draft [--only <keeper 正式 id 文件>] [--limit N] [--out <批目录>] [--apply]
乾跑默认，只写 <批目录>/plan.json；--apply 才改两库文件。启动打印载入条数，为 0 报错。
"""
import argparse, collections, copy, glob, hashlib, json, os, pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.claude/qa'))
import mintid  # noqa: E402

COMMIT = '449d40913f24cff79a1a515bfa9dca6599ccdde3'
MACHINE = 2027          # 本串铸 id 用；全库 Book 实测未用（2026-10-25）
TODAY = '2026-10-25'
CHA = '查重线（Book 层 2026-10-19）'
# 同一实物的跨源 Collection（总目叢書线录的 vs 早期手建的；10-25 抽检发现），查「已有同丛书 Book」时视同一个
# 武英殿聚珍版書一百三十八種五个版次（子目 edition 自注用的简称）
JUZHEN = {'8rldonorf7cw': '殿本', '8rldonor3yte': '福建本', '8rldomtfn94x': '廣東本',
          '8rldonorf7cx': '浙江本', '8rldonorf7cy': '江西本'}
SAME_COL = [{'8rldp1yeqrk0', '8rlb6yi1ecqo'},   # 文淵閣四庫全書（臺北故宮）
            {'8rldo48qtsld', '8rlb6yk66qdc'}]   # 摛藻堂四庫全書薈要


def die(msg):
    sys.exit('错误：' + msg)


def git(args, cwd, inp=None):
    return subprocess.run(['git', '-c', 'core.quotePath=false'] + args, cwd=cwd, input=inp,
                          capture_output=True, check=True).stdout


def cat_batch(cwd, specs):
    out = git(['cat-file', '--batch'], cwd, ('\n'.join(specs) + '\n').encode())
    res, i = [], 0
    while i < len(out):
        nl = out.index(b'\n', i)
        hdr = out[i:nl].decode().split()
        if hdr[-1] == 'missing':
            res.append(None); i = nl + 1; continue
        sz = int(hdr[2]); res.append(json.loads(out[nl + 1:nl + 1 + sz])); i = nl + 2 + sz
    return res


def load_commit(draft):
    names = [n for n in git(['show', COMMIT, '--name-only', '--format='], draft).decode().split('\n')
             if n.startswith('Book/')]
    before = cat_batch(draft, [f'{COMMIT}^:{n}' for n in names])
    after = cat_batch(draft, [f'{COMMIT}:{n}' for n in names])
    rec = {}
    for n, b, a in zip(names, before, after):
        if b is None or a is None:
            die('提交里有新增或删除的 Book 档：' + n)
        rec[a['id']] = {'path': n, 'before': b, 'after': a}
    return rec


def load_promotions():
    P = {}
    for f in sorted(glob.glob(str(ROOT / 'promotions/*.json'))):
        P.update(json.load(open(f, encoding='utf-8'))['promotions'])
    return P


def book_index():
    """→ (id→路径, work_id→[(活 Book id, 所挂 Collection 集)])。"""
    idx, byw = {}, collections.defaultdict(list)
    for root, _d, fs in os.walk(ROOT / 'Book'):
        for fn in fs:
            if fn.endswith('.json'):
                p = pathlib.Path(root) / fn
                idx[fn.split('-', 1)[0]] = p
                d = json.loads(p.read_text(encoding='utf-8'))
                if 'merged_into' not in d and d.get('work_id'):
                    byw[d['work_id']].append((d['id'], {c.get('id') for c in d.get('contained_in') or []}))
    return idx, byw


def tr_rec(r, P, miss):
    """整条记录译 id：顶层 id／work_id 不译（另行赋值），其余草稿 id 按 promotions 译成正式 id。"""
    return {k: (x if k in ('id', 'work_id') else tr(x, P, miss)) for k, x in r.items()}


def tr(v, P, miss):
    """把草稿 id 按 promotions 译成正式 id（只译恰为一个草稿 id 的字符串值）。"""
    if isinstance(v, dict):
        return {k: tr(x, P, miss) for k, x in v.items()}
    if isinstance(v, list):
        return [tr(x, P, miss) for x in v]
    if isinstance(v, str) and len(v) == 13 and v.startswith('1') and mintid.idtype(v) and mintid.parse(v)['status'] == 1:
        if v in P:
            return P[v]['production_id']
        miss.append(v)
    return v


def ci_ids(rec):
    return [c.get('id') for c in rec.get('contained_in') or []]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def remove_once(lst, items, key):
    """从 lst 里按 key 每个 item 删一次；回 (新列表, 删不到的 item)。"""
    out = list(lst); missing = []
    for it in items:
        k = key(it)
        for j, x in enumerate(out):
            if key(x) == k:
                del out[j]; break
        else:
            missing.append(it)
    return out, missing


def jdump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--draft', required=True)
    ap.add_argument('--only')
    ap.add_argument('--skip', help='跳过这些 keeper 正式 id（文件，一行一个）')
    ap.add_argument('--limit', type=int, help='本批最多新建多少个 Book（按 keeper 正式 id 排序取前面的组）')
    ap.add_argument('--out', default=str(pathlib.Path(__file__).parent / 'plan'))
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--merge-existing', action='store_true',
                    help='只做「同 Work 已有同丛书活 Book」的组：剥离照常，被并者并入那个已有 Book，不新建')
    a = ap.parse_args()
    draft = pathlib.Path(a.draft).resolve()

    rec = load_commit(draft)
    P = load_promotions()
    idx, byw = book_index()
    cols = {}
    for f in glob.glob(str(ROOT / 'Collection/*/*/*/*.json')):
        c = json.load(open(f, encoding='utf-8')); cols[c['id']] = c

    def colfix(c):
        """Collection 墓碑（部分 6 并了 Collection 后）沿 merged_into 走到 keeper。"""
        seen = set()
        while c in cols and cols[c].get('merged_into') and c not in seen:
            seen.add(c); c = cols[c]['merged_into']
        return c

    def tr_ci(r):
        """译过 id 的记录：contained_in 再沿 Collection 墓碑走到 keeper，并去重。"""
        if r.get('contained_in'):
            out, have = [], set()
            for x in r['contained_in']:
                y = dict(x, id=colfix(x.get('id')))
                if y['id'] not in have:
                    have.add(y['id']); out.append(y)
            r['contained_in'] = out
        return r
    print(f'载入：449d409 Book 档 {len(rec)}、promotions {len(P)}、正式 Book {len(idx)}')
    if not rec or not P or not idx:
        die('载入条数为 0')

    groups = collections.defaultdict(list)
    for i, r in rec.items():
        if 'merged_into' in r['after']:
            groups[r['after']['merged_into']].append(i)
    only = set(open(a.only).read().split()) if a.only else None
    skip = set(open(a.skip).read().split()) if a.skip else set()

    plan, stat, problems = [], collections.Counter(), []
    tcache = {}                 # --merge-existing：被并入的已有 Book
    targets_used_as_keeper = set()
    for kd in sorted(groups, key=lambda k: P.get(k, {}).get('production_id') or 'zzzz' + k):
        losers = sorted(groups[kd])
        kb = rec[kd]['before']
        def tci(r):
            return frozenset(colfix(P[c]['production_id'] if c in P else c) for c in ci_ids(r))
        kci = tci(kb)
        split = [l for l in losers if tci(rec[l]['before']) != kci]
        # 抽检（10-26 batch-04）：总目把聚珍版书子目在五个版次下都登了一遍，子目 edition 自注实际所收版次
        # （如「殿本、福建本、廣東本」）；自注不含的版次下那条是幽灵子目，不新建，照旧并在 keeper，只删 keeper 上那个 Collection
        ghosts = {}
        for l in split:
            ed = rec[l]['before'].get('edition') or ''
            if any(x in ed for x in JUZHEN.values()):
                g = [c for c in tci(rec[l]['before']) if c in JUZHEN and JUZHEN[c] not in ed]
                if g:
                    ghosts[l] = g
        if ghosts:
            split = [l for l in split if l not in ghosts]
            if not split:
                problems.append({'keeper_draft': kd, 'why': '被并者都是聚珍幽灵子目，不新建；keeper 上的幽灵 Collection 留人工删',
                                 'ghosts': ghosts}); continue
        if not split:
            stat['同 Collection 或都无，不动'] += 1; continue
        if not kci or any(not tci(rec[l]['before']) for l in split):
            # 抽检（10-25）：这类多是总目「叢編之屬」单条与该丛书子目，实为同一版本，10-19 并对了，不拆
            stat['一侧无 Collection，不拆'] += 1
            problems.append({'keeper_draft': kd, 'why': '一侧无 Collection，不拆（待人工核馆藏，可能应补挂）'}); continue
        prom = P.get(kd, {}).get('production_id')
        if not prom or prom not in idx:
            stat['keeper 未升格／正式档不在'] += 1
            problems.append({'keeper_draft': kd, 'why': 'keeper 未升格或正式档不在', 'prod': prom}); continue
        if (only is not None and prom not in only) or prom in skip:
            continue
        kpath = idx[prom]
        K = json.loads(kpath.read_text(encoding='utf-8'))
        if 'merged_into' in K:
            problems.append({'keeper': prom, 'why': 'keeper 已是墓碑 → ' + K['merged_into']}); continue
        if any(l in P for l in split):
            problems.append({'keeper': prom, 'why': '被并者已另行升格', 'drafts': [l for l in split if l in P]}); continue
        # 同 Work 已有别的活 Book 挂在同一 Collection 或同题同版本名的 Collection（如两个文淵閣本 Collection）：
        # 新建会多一份重复，整组跳过，交部分 5 判
        def ckey(c):
            x = cols.get(c) or {}
            ib = x.get('indexed_by') or [{}]
            return (ib[0].get('title_info') or x.get('title'), x.get('edition'))
        other = [(i, cs) for i, cs in byw.get(K['work_id'], []) if i != prom]
        hit = []
        for l in split:
            for c in tci(rec[l]['before']):
                for i, cs in other:
                    eq = set().union(*[g for g in SAME_COL if c in g]) | {c}
                    if eq & cs or (cols.get(c, {}).get('edition') and ckey(c) in {ckey(x) for x in cs if x != c}):
                        hit.append((l, c, i))
        target = None
        if hit:
            tg = {h[2] for h in hit}
            if (a.merge_existing and len(tg) == 1 and {h[0] for h in hit} == set(split)
                    and len({tci(rec[l]['before']) for l in split}) == 1 and next(iter(tg)) not in targets_used_as_keeper):
                target = next(iter(tg))
            else:
                stat['同 Work 已有同丛书 Book，跳过组'] += 1
                problems.append({'keeper': prom, 'why': '同 Work 已有挂同一／同版本丛书的活 Book，新建会重复'
                                 + ('；候选不唯一或只部分命中，留人工' if a.merge_existing else '，交 --merge-existing'),
                                 'hits': hit[:5]}); continue
        elif a.merge_existing:
            continue
        miss = []
        kb_t = tr_ci(tr_rec(kb, P, miss))
        item = {'keeper': prom, 'keeper_draft': kd, 'keeper_path': str(kpath.relative_to(ROOT)),
                'keeper_sha256': sha(kpath), 'stays_merged': [l for l in losers if l not in split],
                'split': [], 'warnings': []}
        newK = copy.deepcopy(K)
        lts = {}
        for l in split + sorted(ghosts):   # 幽灵子目也做减法（馆藏／著录是整套丛书照抄，不属 keeper 版次），只是不新建
            lb = rec[l]['before']
            lmiss = []
            lt = lts[l] = tr_ci(tr_rec(lb, P, lmiss))
            if lmiss:
                item['warnings'].append(f'{l}：草稿 id 未升格，原样保留 {sorted(set(lmiss))}')
            # 减法：只删 keeper 原记录里没有的项
            kprov = [x.get('source') for x in kb_t.get('provenance') or []]
            rm_prov = [x for x in lt.get('provenance') or [] if x.get('source') not in kprov]
            newK['provenance'], m1 = remove_once(newK.get('provenance') or [], rm_prov, lambda x: x.get('source'))
            kib = [json.dumps(x, ensure_ascii=False, sort_keys=True) for x in kb_t.get('indexed_by') or []]
            rm_ib = [x for x in lt.get('indexed_by') or [] if json.dumps(x, ensure_ascii=False, sort_keys=True) not in kib]
            newK['indexed_by'], m2 = remove_once(newK.get('indexed_by') or [], rm_ib,
                                                 lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True))
            ksrc = [x.get('id') for x in kb_t.get('sources') or []]
            rm_src = [x for x in lt.get('sources') or [] if x.get('id') not in ksrc]
            newK['sources'], m3 = remove_once(newK.get('sources') or [], rm_src, lambda x: x.get('id'))
            rm_ci = [c for c in lt.get('contained_in') or [] if c.get('id') not in kci]
            newK['contained_in'], m4 = remove_once(newK.get('contained_in') or [], rm_ci, lambda x: x.get('id'))
            mf = newK.get('merged_from') or []
            if l in ghosts:
                if l not in mf:
                    item['warnings'].append(f'merged_from 里无 {l}')
            elif l in mf:
                newK['merged_from'] = [x for x in mf if x != l]
            elif 'merged_from' in newK:
                item['warnings'].append(f'merged_from 里无 {l}')
            for nm, m in (('provenance', m1), ('indexed_by', m2), ('sources', m3)):
                if m:
                    item['warnings'].append(f'{l}：keeper 里找不到 {len(m)} 条 {nm}（升格时未带入，照拆）')
            if m4:
                item['warnings'].append(f'{l}：keeper contained_in 里无 {[c.get("id") for c in m4]}（升格时未带入）')
        for l, g in ghosts.items():
            rm = [c for c in g if c not in kci]
            if rm:
                item['warnings'].append(f'{l}：聚珍幽灵子目（edition 自注不含 {[JUZHEN[c] for c in rm]}），不新建，仍并在 keeper；keeper 删其所挂 {rm} 与带来的馆藏／著录／源记录')
        # 新 Book：被并者按所挂 Collection 分组，同一 Collection 的几条（同一丛书版次的同一子目）并成一个
        sub = collections.defaultdict(list)
        for l in split:
            sub[tci(rec[l]['before'])].append(l)
        for cset in sorted(sub, key=lambda c: sorted(sub[c])[0]):
            ls = sorted(sub[cset]); l = ls[0]; lb = rec[l]['before']
            if target:
                # 并入已有活 Book：只并馆藏／著录／源记录，contained_in 已同（或同一实物的跨源 Collection），不动
                if target not in tcache:
                    tp = idx[target]
                    tcache[target] = {'path': str(tp.relative_to(ROOT)), 'sha256': sha(tp),
                                      'record': json.loads(tp.read_text(encoding='utf-8')), 'from': []}
                T = tcache[target]['record']
                for x in ls:
                    xt = lts[x]
                    for k, key in (('provenance', lambda y: y.get('source')), ('sources', lambda y: y.get('id')),
                                   ('indexed_by', lambda y: json.dumps(y, ensure_ascii=False, sort_keys=True))):
                        have = {key(y) for y in T.get(k) or []}
                        add = [y for y in xt.get(k) or [] if key(y) not in have]
                        if add:
                            T[k] = (T.get(k) or []) + add
                    T['merged_from'] = (T.get('merged_from') or []) + [x]
                    tcache[target]['from'].append(x)
                item['split'].append({'draft': l, 'also': ls[1:], 'draft_path': rec[l]['path'],
                                      'also_paths': [rec[x]['path'] for x in ls[1:]], 'merge_into': target, 'srcs': [lts[x] for x in ls],
                                      'id': target, 'path': tcache[target]['path'], 'collections': sorted(cset)})
                continue
            nb = copy.deepcopy(lts[l])
            for x in ls[1:]:
                xt = lts[x]
                for k, key in (('provenance', lambda y: y.get('source')), ('sources', lambda y: y.get('id')),
                               ('indexed_by', lambda y: json.dumps(y, ensure_ascii=False, sort_keys=True))):
                    have = {key(y) for y in nb.get(k) or []}
                    add = [y for y in xt.get(k) or [] if key(y) not in have]
                    if add:
                        nb[k] = (nb.get(k) or []) + add
            nb['work_id'] = K['work_id']
            nb['revision'] = '1.0.0'
            nb['revised_at'] = TODAY
            for k in ('merged_into', 'merged_from'):
                nb.pop(k, None)
            extra = ''
            if ls[1:]:
                nb['merged_from'] = ls[1:]
                extra = f'；同挂此叢書版次的草稿 {",".join(ls[1:])} 同一子目，并入本条（馆藏/著录取并集）'
            nb['ai_note'] = (lb.get('ai_note', '') + '\n' if lb.get('ai_note') else '') + (
                f'拆分（2026-10-25，去重方案部分 6 附）：10-19 查重线 Book 层误把不同叢書版次的子目并入 {prom}，'
                f'按草稿 {l} 并前原记录（草稿库 {COMMIT[:11]}^）复原为独立 Book' + extra)
            name = pathlib.Path(rec[l]['path']).name.split('-', 1)[1][:-5]
            item['split'].append({'draft': l, 'also': ls[1:], 'draft_path': rec[l]['path'],
                                  'also_paths': [rec[x]['path'] for x in ls[1:]], 'record': nb, 'name': name,
                                  'collections': ci_ids(nb)})
        # ai_note
        note = newK.get('ai_note', '')
        lines = note.split('\n')
        keep_lines = list(lines)   # 10-19 查重线原说明保留作留痕
        if target:
            keep_lines.append(f'拆分（2026-10-26，去重方案部分 6 附）：10-19 查重线误并的不同叢書版次子目（{",".join(sorted(x for s in item["split"] for x in [s["draft"]] + s["also"]))}）'
                              f'已剥出，并入同 Work 已挂该叢書版次的 Book {target}')
        else:
            keep_lines.append(f'拆分（2026-10-25，去重方案部分 6 附）：10-19 查重线误并的不同叢書版次子目已拆出另立 Book（{",".join(sorted(x for s in item["split"] for x in [s["draft"]] + s["also"]))}）')
        gci = sorted({c for g in ghosts.values() for c in g if c not in kci})
        if gci:
            keep_lines[-1] += f'；聚珍版书子目 edition 自注不收的版次 {",".join(gci)} 为总目重登的幽灵条目，不另立，删去所挂及其带来的馆藏／著录／源记录（草稿仍并于本条）'
        newK['ai_note'] = '\n'.join(keep_lines)
        if not newK.get('merged_from'):
            newK.pop('merged_from', None)
        for k in ('provenance', 'indexed_by', 'sources', 'contained_in'):
            if k in newK and not newK[k]:
                newK.pop(k)
        # keeper 自身原挂的 Collection 若升格时没带进正式库（当时该 Collection 未升格），补回
        have_ci = set(ci_ids(newK))
        back = [c for c in kb_t.get('contained_in') or [] if c.get('id') not in have_ci and mintid.parse(c['id'])['status'] == 0]
        if back:
            newK['contained_in'] = (newK.get('contained_in') or []) + back
            item['warnings'].append(f'keeper 自身原挂 {[c["id"] for c in back]} 升格时未带入，补回')
        # 核对：剩下的 provenance/sources/contained_in 应 ⊇ keeper 原记录，且不含已拆出者独有项
        for k, key in (('provenance', 'source'), ('sources', 'id'), ('contained_in', 'id')):
            own = {x.get(key) for x in kb_t.get(k) or []}
            have = {x.get(key) for x in newK.get(k) or []}
            if not own <= have:
                item['warnings'].append(f'减后 {k} 缺 keeper 原有项 {sorted(own - have)[:3]}')
            for s in item['split']:
                extra = {x.get(key) for r in ([s['record']] if 'record' in s else s['srcs']) for x in r.get(k) or []} - own
                if extra & have:
                    item['warnings'].append(f'减后 {k} 仍含 {s["draft"]} 独有项')
        rv = K.get('revision', '1.0.0').split('.')
        newK['revision'] = f'{int(rv[0]) + 1}.0.0'   # schema/common.md：同 Work 下并／拆 Book 属 major
        newK['revised_at'] = TODAY
        item['keeper_record'] = newK
        if item['split'] and a.limit and stat['新建 Book'] + len(item['split']) > a.limit:
            break
        if item['split']:
            plan.append(item)
            stat['拆的组'] += 1
            stat['聚珍幽灵子目（不新建）'] += len(ghosts)
            stat['并入已有 Book' if target else '新建 Book'] += len(item['split'])
            if item['warnings']:
                stat['有警告的组'] += 1
        if a.limit and stat['新建 Book'] >= a.limit:
            break

    # 查新 Book 的源记录是否已在正式库另有 Book（他人已补建）
    want = {s['record']['sources'][0]['id']: (it['keeper'], s['draft'])
            for it in plan for s in it['split'] if 'record' in s and s['record'].get('sources')}
    hits = subprocess.run(['rg', '-l', '-F', '-f', '/dev/stdin', '--glob', '*.json', 'Book'], cwd=ROOT,
                          input='\n'.join(want) + '\n', text=True, capture_output=True).stdout.split()
    kset = {it['keeper_path'] for it in plan}
    dup = [h for h in hits if h not in kset]
    if dup:
        bad = set()
        for h in dup:
            d = json.loads((ROOT / h).read_text(encoding='utf-8'))
            for x in d.get('sources') or []:
                if x.get('id') in want:
                    bad.add(want[x['id']][0])
                    problems.append({'why': '新 Book 的源记录在正式库已有别的 Book，整组跳过待人工',
                                     'keeper': want[x['id']][0], 'draft': want[x['id']][1], 'other': h})
        plan = [it for it in plan if it['keeper'] not in bad]
        stat['源记录撞别的正式 Book，跳过组'] = len(bad)
        stat['拆的组'] = len(plan); stat['新建 Book'] = sum(len(it['split']) for it in plan)
    # 铸 id
    used = set(idx)
    ts = int(time.time()); seq = 0
    keepers = {it['keeper'] for it in plan}
    bad_t = [t for t in tcache if t in keepers]
    if bad_t:
        plan = [it for it in plan if not any(s.get('merge_into') in bad_t for s in it['split'])]
        for t in bad_t:
            tcache.pop(t)
        problems.append({'why': '并入目标本身是本批 keeper，跳过', 'targets': bad_t})
    for t, c in tcache.items():
        r = c['record']
        r['ai_note'] = (r.get('ai_note', '') + '\n' if r.get('ai_note') else '') + (
            f'并入（2026-10-26，去重方案部分 6 附）：10-19 查重线误并入别条的同丛书同子目草稿 {",".join(c["from"])}'
            f'（并前原记录见草稿库 {COMMIT[:11]}^）与本条同一实物，馆藏／著录／源记录并入本条')
        rv = r.get('revision', '1.0.0').split('.')
        r['revision'] = f'{int(rv[0]) + 1}.0.0'
        r['revised_at'] = TODAY
    for it in plan:
        for s in it['split']:
            if s.get('merge_into'):
                continue
            while True:
                if seq > 255:
                    ts += 1; seq = 0
                raw = (0 << 62) | (0 << 59) | ((ts & ((1 << 40) - 1)) << 19) | (MACHINE << 8) | seq
                seq += 1
                i = mintid.b36(raw)
                if mintid.dec(i) == raw and i not in used:
                    break
            used.add(i)
            s['id'] = i
            r = s['record']; r['id'] = i
            s['record'] = {k: r[k] for k in ['schema_version', 'id'] + [k for k in r if k not in ('schema_version', 'id')]}
            s['path'] = mintid.path_for(i, s['name'], 'Book')

    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ledger = [{'keeper': it['keeper'], 'keeper_draft': it['keeper_draft'], 'keeper_path': it['keeper_path'],
               'keeper_sha256_before': it['keeper_sha256'], 'stays_merged': it['stays_merged'],
               'split': [{'draft': s['draft'], 'also_merged': s['also'], 'new_id': s['id'], 'path': s['path'], 'contained_in': s['collections'],
                          'merge_into_existing': bool(s.get('merge_into')),
                          'edition': (s.get('record') or {}).get('edition', ''),
                          'sources': [x.get('id') for x in (s.get('record') or {}).get('sources') or []]} for s in it['split']],
               'warnings': [w for w in it['warnings'] if '草稿 id 未升格' not in w or 'contained_in' in w]}
              for it in plan]
    (out / 'splits.json').write_text(json.dumps({'commit': COMMIT, 'base': git(['rev-parse', 'HEAD'], ROOT).decode().strip(),
                                                'stat': stat, 'problems': problems, 'splits': ledger},
                                               ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (out / 'plan.json').write_text(json.dumps({'commit': COMMIT, 'base': git(['rev-parse', 'HEAD'], ROOT).decode().strip(),
                                              'stat': stat, 'problems': problems, 'groups': plan,
                                              'targets': tcache},
                                             ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(dict(stat)); print('问题', len(problems))
    if not a.apply:
        return
    # 写正式库
    promo_add = collections.defaultdict(dict)
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    for it in plan:
        kp = ROOT / it['keeper_path']
        if sha(kp) != it['keeper_sha256']:
            die('keeper 已变：' + it['keeper_path'])
        kp.write_text(jdump(it['keeper_record']), encoding='utf-8')
        for s in it['split']:
            if s.get('merge_into'):
                continue
            p = ROOT / s['path']; p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists():
                die('新档已存在：' + s['path'])
            p.write_text(jdump(s['record']), encoding='utf-8')
            promo_add[s['draft'][-2:]][s['draft']] = {'production_id': s['id'], 'type': 'book', 'promoted_at': now}
    for t, c in tcache.items():
        tp = ROOT / c['path']
        if sha(tp) != c['sha256']:
            die('并入目标已变：' + c['path'])
        tp.write_text(jdump(c['record']), encoding='utf-8')
    for sh, add in promo_add.items():
        f = ROOT / f'promotions/{sh}.json'
        d = json.loads(f.read_text(encoding='utf-8'))
        for k in add:
            if k in d['promotions']:
                die('promotions 已有 ' + k)
        d['promotions'].update(add)
        f.write_text(jdump(d), encoding='utf-8')
    # 写草稿库
    for it in plan:
        kdp = draft / rec[it['keeper_draft']]['path']
        kd = json.loads(kdp.read_text(encoding='utf-8'))
        gone = {x for s in it['split'] for x in [s['draft']] + s['also']}
        if 'merged_from' in kd:
            kd['merged_from'] = [x for x in kd['merged_from'] if x not in gone]
            if not kd['merged_from']:
                kd.pop('merged_from')
            kdp.write_text(jdump(kd), encoding='utf-8')
        for s in it['split']:
            for ap_ in s['also_paths']:
                xp = draft / ap_
                xd = json.loads(xp.read_text(encoding='utf-8'))
                if xd.get('merged_into') not in (it['keeper'], it['keeper_draft']):
                    die(f'草稿 {xd["id"]} merged_into 已变：{xd.get("merged_into")}')
                xd['merged_into'] = s['id']
                xp.write_text(jdump(xd), encoding='utf-8')
            lp = draft / s['draft_path']
            ld = json.loads(lp.read_text(encoding='utf-8'))
            if ld.get('merged_into') not in (it['keeper'], it['keeper_draft']):
                die(f'草稿 {s["draft"]} merged_into 已变：{ld.get("merged_into")}')
            if s.get('merge_into'):
                ld['merged_into'] = s['id']
                lp.write_text(jdump(ld), encoding='utf-8')
                continue
            stub = {'schema_version': ld['schema_version'], 'id': ld['id'], 'type': ld['type'], 'title': ld['title']}
            lp.write_text(jdump(stub), encoding='utf-8')
    sys.path.insert(0, str(ROOT / 'build'))
    import build_derived as B
    shards = {}
    for it in plan:
        for s in it['split']:
            if s.get('merge_into'):
                continue
            rel = f"index/books/{B.shard_of(s['id']):x}.json"
            if rel not in shards:
                shards[rel] = json.loads((ROOT / rel).read_text(encoding='utf-8'))
            shards[rel][s['id']] = B.index_entry(s['record'], 'Book', s['path'])
    shards = {k: dict(sorted(v.items())) for k, v in shards.items()}
    B.write_index(str(ROOT), shards)
    print('已写：keeper', len(plan), '新 Book', sum(len(it['split']) for it in plan), 'promotions 分片', len(promo_add))


if __name__ == '__main__':
    main()
