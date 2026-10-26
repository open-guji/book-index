#!/usr/bin/env python3
"""拆回-二：E／F／G 道 Book 跨版次多挂按总目源记录所属丛书实例拆开（去重方案细拆单元「拆回-二」）。

成因：E／F／G 道按「Work＋总目子目版本标注」聚簇，把同一子目在各丛书版次、各丛书里的总目实例记录并成一个 Book，
再挂到所有对应 Collection。一个 Book 是一个具体版本，应拆。研究报告：ai-team 去重方案目录 拆回二/研究报告-20261025.md。

依据：open-guji-core/book_index_json 总目 parsed 数据里每条实例的 series.series_id（＝所属丛书实例＝Collection.sources[].id）
与 holdings[].item_uri（＝provenance[].source 的 item id）。

做法：
- 范围：活 Book，ai_note 以「E 道／F 道／G 道」开头，contained_in ≥2；排除 --exclude（拆回串 keeper）。
- 每条源记录按 series_id 对到本 Book 已挂的 Collection；每个 Collection 一组（同组几条合一个 Book）。
- 无 series 的记录（总目「××本」子目著录，0 馆藏）不进任何组，从 sources 去掉、id 记在保留 Book 的 ai_note；带馆藏者整条存疑。
- provenance 按 item id 分回；分不干净整条存疑。
- 目标 Collection（含同题同版本名、文淵閣／摛藻堂同物两套）已有同 Work 的别的 Book：整条存疑（拆后要另判并）。
- 有源记录所属丛书实例未建 Collection、或有已挂 Collection 无记录对应：整条存疑。
- provenance 最多的一组保留原 id（revision 升 major），其余铸新 id（MachineID 2035，1.0.0）。
- 新档文件名只用题名。
- 版本以所挂 Collection 为准：各组 edition 置空，去掉 edition_type／publication_info／dating（原值是聚簇代表记录的标注，
  拆后多数不对）；原 edition 与各记录的子目版本标注写入 ai_note。indexed_by summary 按本组馆藏与 Collection 版本重写。
- contained_in 若指 Collection 墓碑，沿 merged_into 改指 keeper。

用法：split_efg.py --parsed <parsed 目录> [--exclude keepers.txt] [--only ids.txt] [--limit N] [--out 批目录] [--apply]
乾跑默认只写 <批目录>/plan.json 与 存疑.tsv；--apply 才写正式库与 index。
"""
import argparse, collections, copy, glob, hashlib, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.claude/qa'))
import mintid  # noqa: E402

MACHINE = 2035          # 本单元铸 id 用；全库实测未用（2026-10-25）
TODAY = time.strftime('%Y-%m-%d')
LANE = re.compile(r'^([EFG]) 道')
SAME_COL = [{'8rldp1yeqrk0', '8rlb6yi1ecqo'}, {'8rldo48qtsld', '8rlb6yk66qdc'}]
DROP = ('edition_type', 'publication_info', 'dating')


def die(m):
    sys.exit('错误：' + m)


def jdump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def clean(label):
    """总目子目版本标注去解析杂质（藏经刻版段，与子目无关）。"""
    return ';'.join(x for x in (label or '').split(';') if x and '磧砂' not in x and '延聖院' not in x)


def item(src):
    return (src or '').rsplit('item/', 1)[-1].rsplit('/', 1)[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parsed', required=True)
    ap.add_argument('--exclude')
    ap.add_argument('--only')
    ap.add_argument('--limit', type=int, help='本批最多拆多少个原 Book（按 id 排序）')
    ap.add_argument('--out', default=str(pathlib.Path(__file__).parent / 'plan'))
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    excl = set(open(a.exclude).read().split()) if a.exclude else set()
    only = set(open(a.only).read().split()) if a.only else None

    cols, books, paths = {}, {}, {}
    for f in glob.glob(str(ROOT / 'Collection/**/*.json'), recursive=True):
        c = json.load(open(f, encoding='utf-8')); cols[c['id']] = c
    byw = collections.defaultdict(set)   # (work, collection) -> 活 Book
    for r, _d, fs in os.walk(ROOT / 'Book'):
        for fn in fs:
            if not fn.endswith('.json'):
                continue
            p = pathlib.Path(r) / fn
            d = json.loads(p.read_text(encoding='utf-8'))
            paths[d['id']] = p
            if 'merged_into' in d:
                continue
            for x in d.get('contained_in') or []:
                byw[(d.get('work_id'), x.get('id'))].add(d['id'])
            if LANE.match(d.get('ai_note') or '') and len({x.get('id') for x in d.get('contained_in') or []}) >= 2:
                books[d['id']] = d
    need = {s.get('id') for b in books.values() for s in b.get('sources') or []}
    rec = {}
    for f in sorted(glob.glob(os.path.join(a.parsed, '*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            if r['source_record_id'] in need:
                rec[r['source_record_id']] = r
    print(f'载入：Collection {len(cols)}、正式 Book {len(paths)}、范围 Book {len(books)}、源记录 {len(rec)}')
    if not cols or not books or not rec:
        die('载入条数为 0')

    def live(c):
        seen = set()
        while c in cols and cols[c].get('merged_into') and c not in seen:
            seen.add(c); c = cols[c]['merged_into']
        return c
    inst2col = collections.defaultdict(set)
    for c in cols.values():
        if not c.get('merged_into'):
            for s in c.get('sources') or []:
                if s.get('id'):
                    inst2col[s['id']].add(c['id'])

    def ck(c):
        x = cols.get(c) or {}; ib = x.get('indexed_by') or [{}]
        return (ib[0].get('title_info') or x.get('title'), x.get('edition'))
    byck = collections.defaultdict(set)
    for c, x in cols.items():
        if not x.get('merged_into') and x.get('edition'):
            byck[ck(c)].add(c)

    def eq(c):
        e = {c} | set().union(*[g for g in SAME_COL if c in g])
        if (cols.get(c) or {}).get('edition'):
            e |= byck[ck(c)]
        return {live(x) for x in e} | e

    plan, hold, stat = [], [], collections.Counter()
    for bid in sorted(books):
        b = books[bid]
        if bid in excl:
            continue
        if only is not None and bid not in only:
            continue
        lane = LANE.match(b['ai_note']).group(1)

        def H(why):
            hold.append({'book': bid, 'lane': lane, 'why': why, 'title': b.get('title')}); stat['存疑：' + why] += 1
        ci = list(dict.fromkeys(live(x['id']) for x in b['contained_in']))
        if len(ci) < 2:
            stat['挂的 Collection 归一后 <2，不动'] += 1; continue
        srcs = [s.get('id') for s in b.get('sources') or []]
        if any(s not in rec for s in srcs):
            H('源记录不在总目解析数据'); continue
        groups = collections.OrderedDict((c, []) for c in ci); virt = []; bad = None
        for s in srcs:
            sid = rec[s]['series']['series_id']
            if not sid:
                if rec[s]['holdings']:
                    bad = '无丛书源记录带馆藏（疑单行本混入）'; break
                virt.append(s); continue
            hit = [c for c in {live(x) for x in inst2col.get(sid, ())} if c in groups]
            if not inst2col.get(sid):
                bad = '有源记录所属丛书未建 Collection'; break
            if len(hit) != 1:
                bad = '源记录对应 Collection 不在本 Book 所挂之列或多于一个'; break
            groups[hit[0]].append(s)
        if bad:
            H(bad); continue
        if any(not v for v in groups.values()):
            H('有已挂 Collection 无源记录对应'); continue
        if any(byw[(b.get('work_id'), e)] - {bid} for c in ci for e in eq(c)):
            H('目标 Collection 已有同 Work 其他 Book（拆后要另判并）'); continue
        owner = {}
        for c, ss in groups.items():
            for s in ss:
                for h in rec[s]['holdings']:
                    owner.setdefault(item(h.get('item_uri')), set()).add(c)
        pv = collections.defaultdict(list); amb = False
        for p in b.get('provenance') or []:
            o = owner.get(item(p.get('source')))
            if not o or len(o) != 1:
                amb = True; break
            pv[next(iter(o))].append(p)
        if amb:
            H('provenance 分不干净'); continue
        srcmap = {s['id']: s for s in b.get('sources') or []}
        keepc = max(ci, key=lambda c: (len(pv[c]), -ci.index(c)))
        old_ed = b.get('edition') or ''
        dropped = {k: b[k] for k in DROP if k in b}
        uniform = len({clean(rec[s]['edition']['label']) for s in srcs if s not in virt}) == 1
        parts = []
        for c in ci:
            ss = groups[c]; nb = copy.deepcopy(b)
            for k in DROP:
                nb.pop(k, None)
            nb['edition'] = ''
            nb['sources'] = [srcmap[s] for s in ss]
            nb['provenance'] = pv[c]
            nb['contained_in'] = [{'id': c}]
            if not nb['provenance']:
                nb.pop('provenance')
            names = collections.Counter(rec[s]['title'].get('name') for s in ss if rec[s]['title'].get('name'))
            if virt and names:
                nb['title'] = names.most_common(1)[0][0]
            col = cols[c]
            for ib in nb.get('indexed_by') or []:
                if ib.get('summary') and ib['summary'].count('｜') >= 3:
                    f = ib['summary'].split('｜')
                    f[2] = col.get('edition') or ''
                    f[3] = '、'.join(dict.fromkeys(p.get('institution') for p in pv[c] if p.get('institution')))
                    ib['summary'] = '｜'.join(f)
            labels = list(dict.fromkeys(clean(rec[s]['edition']['label']) for s in ss if clean(rec[s]['edition']['label'])))
            others = [x for x in ci if x != c]
            note = (f'拆分（{TODAY}，去重方案拆回-二）：E／F／G 道聚簇把同一子目在不同叢書版次的總目記錄並成一條'
                    f'（原 {bid}，同挂 {len(ci)} 個 Collection），按源記錄所屬叢書實例（總目 series_id）拆開；本條只屬 {c}'
                    f'（{col.get("edition") or ""}），版本以該 Collection 為準。')
            if c == keepc:
                note += f'同時拆出的另見 Collection {"、".join(others)} 下同 Work 之 Book。'
                if virt:
                    note += f'總目「××本」子目著錄（無叢書、無館藏）{"、".join(virt)} 不屬任何實例，已自 sources 移出。'
            if old_ed or dropped:
                src = '各源記錄子目版本標注一致，但不能代表各叢書版次' if uniform else '取自聚簇代表記錄'
                note += f'原 edition「{old_ed}」' + (f'及 {",".join(dropped)}' if dropped else '') + f' {src}，已去，版本以所挂 Collection 為準。'
            if labels:
                note += f'總目子目版本標注：{"；".join(labels)}。'
            nb['ai_note'] = (b.get('ai_note') or '') + '\n' + note
            if c == keepc:
                rv = (b.get('revision') or '1.0.0').split('.')
                nb['revision'] = f'{int(rv[0]) + 1}.0.0'
            else:
                nb['revision'] = '1.0.0'
                nb.pop('merged_from', None)
            nb['revised_at'] = TODAY
            parts.append({'keep': c == keepc, 'collection': c, 'sources': ss, 'record': nb})
        # 核对：sources／provenance 不漏不重
        got = [s for p in parts for s in p['sources']]
        assert sorted(got + virt) == sorted(srcs), bid
        assert sum(len(p['record'].get('provenance') or []) for p in parts) == len(b.get('provenance') or []), bid
        plan.append({'book': bid, 'lane': lane, 'path': str(paths[bid].relative_to(ROOT)), 'sha256': sha(paths[bid]),
                     'virtual_removed': virt, 'parts': parts})
        stat['拆的原 Book'] += 1; stat['新建 Book'] += len(parts) - 1
        if a.limit and stat['拆的原 Book'] >= a.limit:
            break

    used = set(paths); ts = int(time.time()); seq = 0
    for it in plan:
        for p in it['parts']:
            if p['keep']:
                p['id'] = it['book']; p['path'] = it['path']; continue
            while True:
                if seq > 255:
                    ts += 1; seq = 0
                raw = ((ts & ((1 << 40) - 1)) << 19) | (MACHINE << 8) | seq
                seq += 1
                i = mintid.b36(raw)
                if mintid.dec(i) == raw and i not in used:
                    break
            used.add(i)
            r = p['record']; r['id'] = i
            p['record'] = {k: r[k] for k in ['schema_version', 'id'] + [k for k in r if k not in ('schema_version', 'id')]}
            p['id'] = i
            # 新档文件名只用题名，不带原档后缀里的旧版本名
            p['path'] = mintid.path_for(i, re.sub(r'[\s/\\［］\[\]（）()〔〕【】<>:"|?*、，。·]', '', p['record'].get('title') or '')
                                      or pathlib.Path(it['path']).name.split('-', 1)[1][:-5], 'Book')
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'plan.json').write_text(json.dumps({'stat': stat, 'hold': hold, 'plan': plan}, ensure_ascii=False, indent=1) + '\n',
                                   encoding='utf-8')
    (out / 'splits.json').write_text(json.dumps({'stat': stat, 'splits': [
        {'book': it['book'], 'virtual_removed': it['virtual_removed'],
         'parts': [{'id': p['id'], 'keep': p['keep'], 'collection': p['collection'], 'sources': p['sources'],
                    'path': p['path']} for p in it['parts']]} for it in plan]}, ensure_ascii=False, indent=1) + '\n',
        encoding='utf-8')
    with open(out / '存疑.tsv', 'w', encoding='utf-8') as f:
        f.write('book\tlane\twhy\ttitle\n')
        for h in hold:
            f.write(f"{h['book']}\t{h['lane']}\t{h['why']}\t{h['title']}\n")
    print(dict(stat))
    if not a.apply:
        return
    for it in plan:
        if sha(ROOT / it['path']) != it['sha256']:
            die('原档已变：' + it['path'])
        for p in it['parts']:
            fp = ROOT / p['path']
            if not p['keep']:
                if fp.exists():
                    die('新档已存在：' + p['path'])
                fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(jdump(p['record']), encoding='utf-8')
    sys.path.insert(0, str(ROOT / 'build'))
    import build_derived as BD
    shards = {}
    for it in plan:
        for p in it['parts']:
            rel = f"index/books/{BD.shard_of(p['id']):x}.json"
            if rel not in shards:
                shards[rel] = json.loads((ROOT / rel).read_text(encoding='utf-8'))
            shards[rel][p['id']] = BD.index_entry(p['record'], 'Book', p['path'])
    BD.write_index(str(ROOT), {k: dict(sorted(v.items())) for k, v in shards.items()})
    print('已写：原 Book', len(plan), '新 Book', sum(len(it['parts']) - 1 for it in plan))


if __name__ == '__main__':
    main()
