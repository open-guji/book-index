#!/usr/bin/env python3
"""拆开族谱多修聚合 Work（去重方案部分 6 附-族谱）。

F 道把题名行、责任者行全同的多条上图记录并成一个 Work，族谱里常把同题异修、异支（堂号不同）挂在一起。
研-族谱口径（10-26 定甲）：各修各算一个 Work。本脚本把这类 Work 下的 Book 按「修」分组：

- 只拆题名是族谱（族譜／宗譜／家譜／支譜……）的；清单里混入的谱录（說文諧聲譜、十友譜等）不动。
- 组键：刊年（publication_info.year 为四位数字时）＋堂号（edition 里「某某堂」）；两样都没有的，以 edition 原文为键。
- 同键的 Book 同组（同一修的不同藏本）；键不同即不同组。只差年份或只差堂号也分开——
  口径「不并的方向错了只是多一条 Work，以后可补并」，宁分不混。
- Book 最多的组留原 Work（并列取年份最早），其余每组新建一个 Work：抄原 Work 的题名、责任者等，
  不抄 indexed_by（总目那条记录一条著录全部版本，留在原 Work）；分类照原 Work 所在节点补登。
- Book：work_id 改指新 Work，revision 升 major，ai_note 记一行。

用法（cwd 正式库根）：split_zupu.py --list <多修聚合Work.tsv> --out <目录> [--apply]
"""
import argparse, collections, copy, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.claude/qa'))
sys.path.insert(0, str(ROOT / 'build'))
import mintid  # noqa: E402

MACHINE = 2027          # 与拆回丛书版次同串
TODAY = '2026-10-26'
HALL = re.compile(r'([^\s\d年月]{2})堂')
ZUPU = re.compile(r'(族譜|宗譜|家譜|支譜|世譜|房譜|通譜|續譜|家乘|族志|宗志|世系|譜牒|祠譜|聯譜|合譜|分譜|會譜|統譜)')
MANUAL = {'d59fy68u06bk': '人工：山東文獻集成本是民國二十六年鉛印本（同 108 卷）的影印本，同一修，不拆'}
DYN = re.compile(r'^(清|明|民國|元|宋)')


def jdump(o):
    return json.dumps(o, ensure_ascii=False, indent=2) + '\n'


VAR = str.maketrans({'献': '獻', '礼': '禮', '宝': '寶', '义': '義', '庄': '莊', '万': '萬', '敎': '教', '啓': '啟'})
ERA = re.compile(r'([^\s\d年月清明民國]{2}[元一二三四五六七八九十]+年)')
REPAIR = re.compile(r'補修|遞修|增修|補刻|重修|續修|增刻|重印|補印')


def attrs(b):
    """一个 Book 的「修」特征：地望、卷数、刊年、堂号、藏馆、版本里提到的年号年。"""
    ed = (b.get('edition') or '').translate(VAR)
    y = str((b.get('publication_info') or {}).get('year') or '')
    y = y if re.fullmatch(r'\d{4}', y) else None
    if REPAIR.search(ed) and len(ERA.findall(ed)) >= 2:
        y = None            # 递修本：publication_info.year 取的是修年，不是印年，不作键
    h = HALL.findall(DYN.sub('', ed))
    h = h[-1] + '堂' if h else None
    t = (b.get('title') or '').translate(VAR)
    m = re.match(r'^[\[〔]([^\]〕]+)[\]〕]', t)
    place = m.group(1) if m else None
    ib = (b.get('indexed_by') or [{}])[0]
    ti = (ib.get('title_info') or '').translate(VAR)
    juan = ti[len(t):] if ti.startswith(t) else None
    juan = juan or None    # 「□卷」「存卷N」照留：与「不分卷」不相容（不分卷的谱不会有卷五）
    summ = ib.get('summary') or ''
    hold = set(summ.split('｜')[-1].split('、')) if summ.count('｜') >= 3 else set()
    return {'place': place, 'juan': juan, 'year': y, 'hall': h, 'ed': ed, 'hold': hold, 'eras': set(ERA.findall(ed))}


def key(a, bid):
    if a['year'] or a['hall']:
        return (a['place'], a['juan'], a['year'], a['hall'])
    return (a['place'], a['juan'], 'ed', a['ed'] or bid)


def same_xiu(a, b):
    """两组是否同一修（抽检 10-26：异体字、一侧缺堂号、递修本的修年／印年曾把同一修拆开）：
    藏馆有交集；地望、卷数、堂号都相容（同，或一侧缺；卷数一侧为另一侧前段也算，如「二十卷」与「二十卷首一卷末一卷」）；
    年份相容（同、一侧缺、或一侧版本里写着另一侧的年号年）；且刊年相同、或共有年号年、或版本原文全同。"""
    if not (a['hold'] & b['hold']):
        return False
    if a['place'] and b['place'] and a['place'] != b['place']:
        return False
    if not juan_ok(a['juan'], b['juan']):
        return False
    if a['hall'] and b['hall'] and a['hall'] != b['hall']:
        return False
    ey = a['year'] and b['year'] and a['year'] == b['year']
    if not (a['year'] or b['year']):
        return False        # 两侧都无确切刊年：研-族谱口径判 D，不并
    if a['year'] and b['year'] and not ey and not (a['eras'] & b['eras']):
        return False
    # 只凭堂号同、一侧无年份不并（研-族谱口径判 D，宁分不混）；版本原文（异体归一后）全同才算
    return bool(ey or (a['eras'] & b['eras']) or (a['ed'] and a['ed'] == b['ed']))


def juan_ok(x, y):
    if not x or not y:
        return True
    return x.startswith(y) or y.startswith(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    os.chdir(ROOT)
    W = [l.split('\t')[0] for l in open(a.list, encoding='utf-8') if l.strip() and not l.startswith(('#', 'Work\t'))]
    widx, bidx = {}, {}
    for h in '0123456789abcdef':
        widx.update(json.load(open(f'index/works/{h}.json', encoding='utf-8')))
        bidx.update(json.load(open(f'index/books/{h}.json', encoding='utf-8')))
    byw = collections.defaultdict(list)
    want = set(W)
    for i, e in bidx.items():
        if e.get('work_id') in want:
            byw[e['work_id']].append(i)
    # 分类：Work → (节点文件, 来源标签)
    cls = {}
    for p in sorted(pathlib.Path('classification').rglob('members/*.json')):
        for wid, src in json.load(open(p, encoding='utf-8'))['members']:
            if wid in want:
                cls[wid] = (str(p), src)

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

    stat, plan, problems = collections.Counter(), [], []
    for wid in W:
        if wid not in widx:
            problems.append({'work': wid, 'why': 'Work 不在索引（已并或已删）'}); continue
        wp = pathlib.Path(widx[wid]['path'])
        Wr = json.loads(wp.read_text(encoding='utf-8'))
        if wid in MANUAL:
            problems.append({'work': wid, 'why': MANUAL[wid]}); continue
        if not ZUPU.search(Wr.get('title', '')) or not re.search('氏|族|宗|世家', Wr.get('title', '')):
            problems.append({'work': wid, 'why': '题名不是族谱（谱录、年谱等），不按修拆', 'title': Wr.get('title')}); continue
        if 'merged_into' in Wr:
            problems.append({'work': wid, 'why': 'Work 已是墓碑'}); continue
        books = {i: json.loads(pathlib.Path(bidx[i]['path']).read_text(encoding='utf-8')) for i in byw.get(wid, [])}
        A = {i: attrs(b) for i, b in books.items()}
        g = collections.defaultdict(list)
        for i in books:
            # 键相同且有确切刊年的直接同组；否则每个 Book 自成一组，下面按 same_xiu 合（复检 10-26：无年份同堂号曾绕过藏馆条件）
            k = key(A[i], i)
            g[k if A[i]['year'] else k + (i,)].append(i)
        # 合并同一修的组（并查）
        ks = list(g)
        par = {k: k for k in ks}

        def find(k):
            while par[k] != k:
                k = par[k]
            return k
        for x in range(len(ks)):
            for y in range(x + 1, len(ks)):
                if any(same_xiu(A[i], A[j]) for i in g[ks[x]] for j in g[ks[y]]):
                    par[find(ks[y])] = find(ks[x])
        g2 = collections.defaultdict(list)
        for k in ks:
            g2[find(k)] += g[k]
        g = g2
        if len(g) < 2:
            stat['只一修，不拆'] += 1
            problems.append({'work': wid, 'why': f'Work 下 {len(books)} 个 Book 同属一修，不拆', 'keys': [list(k) for k in g]}); continue
        def yr(k):
            ys = [A[i]['year'] for i in g[k] if A[i]['year']]
            return min(ys) if ys else '9999'
        order = sorted(g, key=lambda k: (-len(g[k]), yr(k), str(k)))
        item = {'work': wid, 'work_path': str(wp), 'stay': {'key': list(order[0]), 'books': sorted(g[order[0]])}, 'new': []}
        for k in order[1:]:
            nid = mint()
            nw = {x: copy.deepcopy(v) for x, v in Wr.items() if x not in ('indexed_by', 'merged_from', 'merged_in', 'related_works', 'ai_note',
                                                                   'resources', 'resource_groups', 'period', 'period_basis')}
            nw['id'] = nid
            eds = '、'.join(sorted({books[i].get('edition') or '' for i in g[k]}))
            nw['ai_note'] = (f'拆分（{TODAY}，去重方案部分 6 附-族谱）：F 道把同题同责任者的各修族谱并成 Work {wid}；'
                             f'按研-族谱口径「各修各算一个 Work」，把 {eds} 一修拆出另立。著录（总目一条记全部版本）见原 Work。')
            nw['revision'] = '1.0.0'; nw['revised_at'] = TODAY
            name = pathlib.Path(widx[wid]['path']).name.split('-', 1)[1][:-5]
            npath = mintid.path_for(nid, name, 'Work')
            moved = []
            for i in sorted(g[k]):
                b = copy.deepcopy(books[i])
                b['work_id'] = nid
                rv = b.get('revision', '1.0.0').split('.')
                b['revision'] = f'{int(rv[0]) + 1}.0.0'; b['revised_at'] = TODAY
                b['ai_note'] = (b.get('ai_note', '') + '\n' if b.get('ai_note') else '') + (
                    f'拆分（{TODAY}，去重方案部分 6 附-族谱）：原挂 {wid}（F 道多修聚合 Work），按「各修各算」改挂本修 Work {nid}')
                moved.append({'id': i, 'path': bidx[i]['path'], 'record': b})
            item['new'].append({'id': nid, 'path': npath, 'key': list(k), 'record': nw, 'books': moved})
            stat['新建 Work'] += 1; stat['改挂 Book'] += len(moved)
        W2 = copy.deepcopy(Wr)
        W2['ai_note'] = (W2.get('ai_note', '') + '\n' if W2.get('ai_note') else '') + (
            f'拆分（{TODAY}，去重方案部分 6 附-族谱）：本条原把同题各修族谱聚在一起，按「各修各算一个 Work」'
            f'把其余各修拆出另立 {",".join(n["id"] for n in item["new"])}；本条留 Book 最多的一修')
        rv = W2.get('revision', '1.0.0').split('.')
        W2['revision'] = f'{int(rv[0]) + 1}.0.0'; W2['revised_at'] = TODAY
        item['work_record'] = W2
        plan.append(item); stat['拆的 Work'] += 1

    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ledger = [{'work': it['work'], 'stay': it['stay'],
               'new': [{'id': n['id'], 'key': n['key'], 'books': [b['id'] for b in n['books']],
                        'editions': [b['record'].get('edition') for b in n['books']]} for n in it['new']]} for it in plan]
    (out / 'splits.json').write_text(jdump({'stat': stat, 'problems': problems, 'splits': ledger}), encoding='utf-8')
    print(dict(stat)); print('问题', len(problems))
    if not a.apply:
        return
    import build_derived as B
    shards = {}

    def put(rel, i, e):
        if rel not in shards:
            shards[rel] = json.load(open(rel, encoding='utf-8'))
        shards[rel][i] = e
    addcls = collections.defaultdict(list)
    for it in plan:
        pathlib.Path(it['work_path']).write_text(jdump(it['work_record']), encoding='utf-8')
        for n in it['new']:
            p = pathlib.Path(n['path']); p.parent.mkdir(parents=True, exist_ok=True)
            assert not p.exists(), p
            p.write_text(jdump(n['record']), encoding='utf-8')
            put(f'index/works/{mintid.shard(n["id"])}.json', n['id'], B.index_entry(n['record'], 'Work', n['path']))
            for b in n['books']:
                pathlib.Path(b['path']).write_text(jdump(b['record']), encoding='utf-8')
                put(f'index/books/{mintid.shard(b["id"])}.json', b['id'], B.index_entry(b['record'], 'Book', b['path']))
            if it['work'] in cls:
                addcls[cls[it['work']][0]].append([n['id'], cls[it['work']][1]])
    B.write_index(str(ROOT), shards)
    for p, add in addcls.items():
        d = json.load(open(p, encoding='utf-8'))
        d['members'] = sorted(d['members'] + add, key=lambda x: x[0])
        raw = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(dump_members(d, raw))
    print('已写：Work', len(plan), '新 Work', sum(len(it['new']) for it in plan), '分类节点', len(addcls))


def dump_members(d, raw):
    # 照原文件排版：members 一项一行
    head = {k: v for k, v in d.items() if k != 'members'}
    s = json.dumps(head, ensure_ascii=False, indent=2)[:-2]
    lines = ',\n'.join('    ' + json.dumps(m, ensure_ascii=False) for m in d['members'])
    s += ',\n  "members": [\n' + lines + '\n  ]\n}' + ('\n' if raw.endswith('\n') else '')
    return s


if __name__ == '__main__':
    main()
