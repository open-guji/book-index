#!/usr/bin/env python3
"""3a-2乙「先拆后并」：把混挂不同编次的 Work 按编次组拆开，能并的组直接并进对方 Work。

方案 plan.json（逐对研究所得，见同目录 README.md）：works[wid].groups[] 每组 {name, stay, books, indexed_by}；
merges[] {from: "wid:组名" | "wid", into: wid}。本脚本只做「组」的拆与并；整个 Work 并 Work（from 无组名）
交 dedup-confirmed-163/apply_batch.py，另出 batch.json。

- 留原 Work 的组：Work 去掉其余组的 indexed_by；卷数（juan_count／measures／measure_info）按组名、再按本组著录重算，
  都没有时原卷数若出自被拆走的组则去掉；description 的来源全在被拆走的著录里才去掉，并移给收走那些著录且没有说明的一条。
- resources／resource_groups 一律留原 Work（按版次分资源另做）。
- 并入对方 Work 的组：Book 改挂对方，著录条目移到对方 indexed_by。
- 其余组新建 Work：抄题名、责任者、朝代等；不抄 resources／related_works／description／merged_*；
  卷数按组名或本组著录；分类照原 Work 所在节点补登。
- 改动的 Work、Book：revision 升 major，ai_note 记一行。

用法（cwd 正式库根）：split_works.py --plan plan.json --out <目录> [--apply]
"""
import argparse, collections, copy, json, os, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.claude/qa'))
sys.path.insert(0, str(ROOT / 'build'))
import mintid  # noqa: E402

MACHINE = 2027
TODAY = '2026-10-26'
NOTE = '混记录拆分（{d}，去重：ncltw／3a-2丙 混记录）：'.format(d=TODAY)
DIG = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '〇': 0, '零': 0, '兩': 2}


def cn2int(s):
    n, cur = 0, 0
    for ch in s:
        if ch in DIG:
            cur = DIG[ch]
        elif ch in '十百千':
            u = {'十': 10, '百': 100, '千': 1000}[ch]
            n += (cur or 1) * u; cur = 0
        else:
            return None
    return n + cur


NUM = '[一二三四五六七八九十百千〇零兩]+'


def juan_of(ti):
    """正卷数与整段卷数著录（连附錄、首末卷等，如「六卷附錄一卷」）。"""
    m = re.search(f'({NUM})卷(?:[^（(）)\\s、，；。]{{0,4}}?{NUM}卷)*', ti or '')
    return (cn2int(m.group(1)), m.group(0)) if m else (None, None)


def desc_juan(d):
    t = (d or {}).get('text') or ''
    m = re.search(f'^(?:[^。]{{0,30}}。)?({NUM})卷。', t) or re.search(f'^《[^》]+》({NUM})卷', t)
    return (cn2int(m.group(1)), m.group(1)) if m else (None, None)


def jdump(o):
    return json.dumps(o, ensure_ascii=False, indent=2) + '\n'


def bump(rv):
    return f'{int((rv or "1.0.0").split(".")[0]) + 1}.0.0'


def note(r, s):
    r['ai_note'] = (r.get('ai_note', '') + '\n' if r.get('ai_note') else '') + NOTE + s


def set_juan(r, name, ib, gone=()):
    """卷数先按组名，再按本组著录；都没有时，原卷数若来自被拆走的组就去掉，否则留着。"""
    for t in [name] + [x.get('title_info') for x in ib]:
        n, s = juan_of(t)
        if n:
            other = [m for m in r.get('measures') or [] if m.get('unit') != '卷']  # 冊數等照留
            oi = r.get('measure_info') or ''
            r['juan_count'] = {'number': n}; r['measures'] = [{'unit': '卷', 'number': n}] + other
            r['measure_info'] = s + (' ' + oi if other and '卷' not in oi else '')
            return
    old = (r.get('juan_count') or {}).get('number')
    if old and old in {juan_of(t)[0] for t in gone}:
        for k in ('juan_count', 'measures', 'measure_info'):
            r.pop(k, None)


def ibkey(x):
    return (x.get('source'), x.get('title_info'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    os.chdir(ROOT)
    P = json.load(open(a.plan, encoding='utf-8'))
    widx, bidx = {}, {}
    for h in '0123456789abcdef':
        widx.update(json.load(open(f'index/works/{h}.json', encoding='utf-8')))
        bidx.update(json.load(open(f'index/books/{h}.json', encoding='utf-8')))
    # index/books 可能缺新近导入的 Book（既有漂移）：按 Book 文件补齐涉及本方案 Work 的条目
    wanted = set(P['works']) | {m['into'] for m in P['merges']}
    hits = subprocess.run(['grep', '-rlE', '"work_id": "(' + '|'.join(sorted(wanted)) + ')"', 'Book'], capture_output=True, text=True).stdout.split()
    for hp in hits:
        bd = json.loads(open(hp, encoding='utf-8').read())
        if bd.get('merged_into') or bd.get('work_id') not in wanted:
            continue
        bidx[bd['id']] = dict(bidx.get(bd['id'], {}), path=hp, work_id=bd['work_id'], title=bd.get('title'))
    cls = {}
    for p in sorted(pathlib.Path('classification').rglob('members/*.json')):
        for wid, src in json.load(open(p, encoding='utf-8'))['members']:
            if wid in P['works']:
                cls[wid] = (str(p), src)
    into = {}
    whole = []
    for m in P['merges']:
        if ':' in m['from']:
            into[tuple(m['from'].split(':', 1))] = m['into']
        else:
            whole.append(m)
    used = set(widx) | set(bidx)
    ts = int(time.time()); seq = 0

    def mint():
        nonlocal ts, seq
        while True:
            if seq > 255:
                ts += 1; seq = 0
            raw = (0 << 62) | (3 << 59) | ((ts & ((1 << 40) - 1)) << 19) | (MACHINE << 8) | seq
            seq += 1
            i = mintid.b36(raw)
            if mintid.dec(i) == raw and mintid.idtype(i) == 'Work' and i not in used:
                used.add(i); return i

    recs = {}

    def W(i):
        if i not in recs:
            p = widx[i]['path']
            recs[i] = {'path': p, 'rec': json.loads(open(p, encoding='utf-8').read()), 'orig': open(p, encoding='utf-8').read()}
        return recs[i]['rec']
    books, new, problems, stat, ledger = {}, [], [], collections.Counter(), []

    def give(o, d, entry):
        T = recs[o['to']]['rec'] if o['to'] in recs else next(n['record'] for n in new if n['id'] == o['to'])
        if 'description' not in T:
            T['description'] = d; T['_touched'] = True; entry['description_moved_to'] = o['to']
    for wid, spec in P['works'].items():
        gs = spec['groups']
        if spec.get('uncertain') or len(gs) < 2:
            continue
        if wid not in widx:
            problems.append({'work': wid, 'why': 'Work 不在索引'}); continue
        R = W(wid)
        if 'merged_into' in R:
            problems.append({'work': wid, 'why': 'Work 已是墓碑'}); continue
        have = {i for i, e in bidx.items() if e.get('work_id') == wid}
        planned = {b for g in gs for b in g['books']}
        live_planned = {b for b in planned if b in bidx}
        if have != {b for b in live_planned if bidx[b].get('work_id') == wid} or have - planned:
            problems.append({'work': wid, 'why': 'Book 集合与方案不符（main 已变）', 'extra': sorted(have - planned),
                             'gone': sorted(live_planned - have)}); continue
        ibs = R.get('indexed_by') or []
        stay = [g for g in gs if g['stay']][0]
        moved_ib = set()
        entry = {'work': wid, 'stay': stay['name'], 'out': []}
        for g in gs:
            if g['stay']:
                continue
            gib = [x for x in ibs if ibkey(x) in {ibkey(y) for y in g['indexed_by']}]
            moved_ib |= {ibkey(x) for x in gib}
            tgt = into.get((wid, g['name']))
            if tgt:
                T = W(tgt)
                T['indexed_by'] = (T.get('indexed_by') or []) + [copy.deepcopy(x) for x in gib if ibkey(x) not in {ibkey(y) for y in T.get('indexed_by') or []}]
                note(T, f'由 {wid}（{R["title"]}）拆出的「{g["name"]}」一组并入本条（Book {",".join(g["books"]) or "无"}）')
                T['_touched'] = True
                nid = tgt; stat['组并入已有 Work'] += 1
            else:
                nid = mint()
                nw = {k: copy.deepcopy(v) for k, v in R.items() if k not in (
                    'indexed_by', 'merged_from', 'merged_in', 'merged_into', 'related_works', 'ai_note', 'resources',
                    'resource_groups', 'description', 'juan_count', 'measures', 'measure_info', 'updated_at',
                    # 依原 Work 著录推出的字段不抄（新 Work 不一定有那些著录）
                    'period_upper', 'period_upper_basis', 'loss_status', 'loss_status_basis', 'emendated_by')}
                nw['id'] = nid
                bt = {bidx[b].get('title') for b in g['books'] if b in bidx}
                if len(bt) == 1 and None not in bt and bt != {R['title']}:
                    nw['title'] = bt.pop()   # 本组 Book 题名一致且与原 Work 不同（如「眉山唐先生文集」），取 Book 题名
                nw['indexed_by'] = [copy.deepcopy(x) for x in gib]
                if not nw['indexed_by']:
                    nw.pop('indexed_by')
                set_juan(nw, g['name'], gib)
                nw['ai_note'] = NOTE + f'原 Work {wid} 混挂不同编次，按编次拆出「{g["name"]}」另立'
                nw['revision'] = '1.0.0'; nw['revised_at'] = TODAY
                name = nw['title'] if nw['title'] != R['title'] else pathlib.Path(widx[wid]['path']).name.split('-', 1)[1][:-5]
                new.append({'id': nid, 'path': mintid.path_for(nid, name, 'Work'), 'record': nw, 'from': wid})
                stat['新建 Work'] += 1
            for b in g['books']:
                if b not in bidx:
                    continue
                books[b] = (nid, wid, g['name'])
            entry['out'].append({'group': g['name'], 'to': nid, 'new': not tgt, 'books': g['books'],
                                 'indexed_by': [list(ibkey(x)) for x in gib]})
        R['indexed_by'] = [x for x in ibs if ibkey(x) not in moved_ib]
        if not R['indexed_by']:
            R.pop('indexed_by')
        gone = [g['name'] for g in gs if not g['stay']] + [x.get('title_info') for x in ibs if ibkey(x) in moved_ib]
        set_juan(R, stay['name'], R.get('indexed_by') or [], gone)
        # 说明的来源全在被拆走的著录里、留下的著录一条不沾，才去掉（馆藏、资源来源的说明随资源留在原条）
        d = R.get('description'); ds = set((d or {}).get('sources') or [])
        if ds and ds <= {x.get('source') for x in ibs if ibkey(x) in moved_ib} and not ds & {x.get('source') for x in R.get('indexed_by') or []}:
            R.pop('description')
            entry['description_dropped'] = d.get('text')
            # 移给收走这些著录的那条（它没有说明时）
            for o in entry['out']:
                if ds <= {x[0] for x in o['indexed_by']}:
                    give(o, d, entry)
                    break
        # 说明出自 Book 层（如再造善本、故宫的馆藏说明）而那部 Book 随别组拆走：移过去
        d = R.get('description'); ds = set((d or {}).get('sources') or [])
        if d and ds and not ds & {x.get('source') for x in ibs}:
            def bt_(bs):
                return ''.join(open(bidx[b]['path'], encoding='utf-8').read() for b in bs if b in bidx)
            st = bt_(stay['books'])
            # 说明里的藏品编号（如 ZHSY000727、平圖012296）比来源名更准
            keys = re.findall(r'[A-Z]{2,}\d{4,}|平圖\d{6}', d.get('text') or '') or sorted(ds)
            hit = [o for o in entry['out'] if all(x in bt_(o['books']) for x in keys)]
            if len(hit) == 1 and not any(x in st for x in keys):
                R.pop('description'); entry['description_dropped'] = d.get('text')
                give(hit[0], d, entry)
                # 冊數也出自那部 Book，一并去掉
                if any(m.get('unit') != '卷' for m in R.get('measures') or []):
                    R['measures'] = [m for m in R['measures'] if m.get('unit') == '卷']
                    R['measure_info'] = juan_of(R.get('measure_info'))[1]
                    for k in ('measures', 'measure_info'):
                        if not R.get(k):
                            R.pop(k, None)
        # 说明开头的卷数与留下的编次不符：合某拆出组的就移过去，否则改成现卷数
        d = R.get('description'); dj, dc = desc_juan(d)
        nj = (R.get('juan_count') or {}).get('number')
        if dj and nj and dj != nj:
            hit = [o for o in entry['out'] if juan_of(o['group'])[0] == dj]
            if hit:
                R.pop('description'); entry['description_dropped'] = d.get('text')
                give(hit[0], d, entry)
            else:
                R['description'] = dict(d, text=d['text'].replace(f'。{dc}卷。', f'。{juan_of(R["measure_info"])[1]}。', 1)
                                        if f'。{dc}卷。' in d['text'] else d['text'].replace(f'{dc}卷。', f'{juan_of(R["measure_info"])[1]}。', 1))
                entry['description_juan_fixed'] = f'{dc}卷→{R["measure_info"]}'
        note(R, f'本条混挂不同编次，留「{stay["name"]}」，其余拆出：' + '；'.join(
            f'「{o["group"]}」→{o["to"]}' for o in entry['out']))
        R['_touched'] = True
        ledger.append(entry); stat['拆的 Work'] += 1
    for b, (nid, wid, gname) in books.items():
        stat['改挂 Book'] += 1

    # 整个 Work 并 Work：出 apply_batch 规格
    batch = {'groups': [{'cluster_id': f'mixsplit-{i + 1}', 'type': 'work', 'keeper': m['into'], 'losers': [m['from']],
                         'rule': '混记录先拆后并', 'why': m['why'], 'evidence': m['why']} for i, m in enumerate(whole)]}
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'splits.json').write_text(jdump({'stat': stat, 'problems': problems, 'works': ledger,
                                            'new_works': [{'id': n['id'], 'from': n['from']} for n in new]}), encoding='utf-8')
    (out / 'batch-whole.json').write_text(jdump(batch), encoding='utf-8')
    print(dict(stat)); print('问题', problems)
    if not a.apply:
        return
    import build_derived as B
    shards = {}

    def put(rel, i, e):
        if rel not in shards:
            shards[rel] = json.load(open(rel, encoding='utf-8'))
        shards[rel][i] = e
    for i, c in recs.items():
        r = c['rec']
        if not r.pop('_touched', False):
            continue
        r['revision'] = bump(r.get('revision')); r['revised_at'] = TODAY
        open(c['path'], 'w', encoding='utf-8').write(jdump(r))
        put(f'index/works/{mintid.shard(i)}.json', i, B.index_entry(r, 'Work', c['path']))
    addcls = collections.defaultdict(list)
    for n in new:
        n['record'].pop('_touched', None)
        p = pathlib.Path(n['path']); p.parent.mkdir(parents=True, exist_ok=True)
        assert not p.exists(), p
        p.write_text(jdump(n['record']), encoding='utf-8')
        put(f'index/works/{mintid.shard(n["id"])}.json', n['id'], B.index_entry(n['record'], 'Work', n['path']))
        if n['from'] in cls:
            addcls[cls[n['from']][0]].append([n['id'], cls[n['from']][1]])
    for b, (nid, wid, gname) in books.items():
        p = bidx[b]['path']; r = json.loads(open(p, encoding='utf-8').read())
        r['work_id'] = nid; r['revision'] = bump(r.get('revision')); r['revised_at'] = TODAY
        note(r, f'原挂 {wid}（混挂不同编次），按编次「{gname}」改挂 {nid}')
        open(p, 'w', encoding='utf-8').write(jdump(r))
        put(f'index/books/{mintid.shard(b)}.json', b, B.index_entry(r, 'Book', p))
    B.write_index(str(ROOT), shards)
    for p, add in addcls.items():
        raw = open(p, encoding='utf-8').read(); d = json.loads(raw)
        d['members'] = sorted(d['members'] + add, key=lambda x: x[0])
        head = {k: v for k, v in d.items() if k != 'members'}
        s = json.dumps(head, ensure_ascii=False, indent=2)[:-2]
        s += ',\n  "members": [\n' + ',\n'.join('    ' + json.dumps(m, ensure_ascii=False) for m in d['members']) + '\n  ]\n}' + ('\n' if raw.endswith('\n') else '')
        open(p, 'w', encoding='utf-8').write(s)
    print('已写：Work', sum(1 for c in recs.values()), '新 Work', len(new), 'Book', len(books), '分类节点', len(addcls))


if __name__ == '__main__':
    main()
