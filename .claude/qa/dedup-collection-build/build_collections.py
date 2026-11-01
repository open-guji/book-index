#!/usr/bin/env python3
"""U1-c 丛书 Collection 补建：给总目里有 series_id 却还没有 Collection 的丛书头各建一个 book_collection，
并把落库的成员 Book 挂上去（contained_in）。

口径（用户 2026-11-01 定：总目提过的丛书一律录入，不设成员数门槛；经史子集部的丛书头也算）：
- 一个 Collection ＝ 总目一个丛书头记录（series_id），sources[].id 即 series_id，与叢書线（GUJI-526）一致。
- 成员关系只写在成员 Book 的 contained_in（Collection 档不列成员）。
- Book 的各源记录若属多个丛书头：头的（丛书名＋版本项）相同则都挂（同版本不同分册）；不同则不动，进存疑.tsv。
- 已有 contained_in 的 Book 只追加，不改原项。
乾跑默认；--apply 才写正式库与 index。
用法：build_collections.py --parsed <parsed 目录> --out <批目录> [--limit-heads N | --pilot N --seed S] [--apply]
"""
import argparse, collections, glob, json, os, pathlib, random, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.claude/qa'))
sys.path.insert(0, str(ROOT / 'build'))
import mintid  # noqa: E402

MACHINE = 2083
TODAY = time.strftime('%Y-%m-%d')
SRC_NAME = '中國古籍總目（上圖聯合目錄）'
SOURCE_BID = 'd59frnrt4lxc'
URL = 'https://gj.library.sh.cn/unionCatalogue/work/list#uri=http://data.library.sh.cn/gj/resource/instance/%s&from=evidence'


def die(m):
    sys.exit('错误：' + m)


def jdump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def load(parsed):
    rec = {}
    for f in sorted(glob.glob(os.path.join(parsed, '*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            rec[r['source_record_id']] = r
    return rec


def year_text(e):
    b, en = e.get('beginAd'), e.get('endAd')
    if not b:
        return None
    return str(b) if (not en or en == b) else f'{b}-{en}'


def make_collection(h, nmem):
    t, e = h['title'], h['edition']
    holders = list(dict.fromkeys(x.get('name') for x in h.get('holdings') or [] if x.get('name')))
    au = []
    for a in (h.get('authors') or {}).get('责任者') or []:
        if a.get('name'):
            x = {'name': a['name'], 'role': a.get('role') or '撰'}
            if a.get('dynasty'):
                x['dynasty'] = a['dynasty']
            au.append(x)
    d = {'schema_version': 1, 'id': None, 'type': 'collection', 'subtype': 'book_collection',
         'title': t.get('name') or t.get('raw')}
    if au:
        d['authors'] = au
    if e.get('label'):
        d['edition'] = e['label']
    y, pub = year_text(e), e.get('publisher')
    if y or pub:
        pi = {}
        if y:
            pi['year'] = y
        if pub:
            pi['details'] = f'刊刻者：{pub}'
        d['publication_info'] = pi
    dcl = (h.get('authors') or {}).get('dclabel') or ''
    d['indexed_by'] = [{'source': '中國古籍總目', 'source_bid': SOURCE_BID, 'title_info': t.get('raw') or t.get('name'),
                        'summary': '｜'.join([t.get('raw') or '', dcl, e.get('label') or '', '、'.join(x.get('abbr') or x.get('name') for x in h.get('holdings') or [])])}]
    sid = h['source_record_id']
    d['sources'] = [{'id': sid, 'name': SRC_NAME, 'type': 'url', 'details': URL % sid}]
    top = ((h.get('classification') or {}).get('path') or [''])[0]
    d['ai_note'] = (f'【叢書线·Collection】叢書线（GUJI-526 口徑）補建（{TODAY}，U1-c）：據《中國古籍總目》（上圖聯合目錄）丛書頭記錄錄入；源記錄：{sid}\n'
                    f'此丛書頭著錄於總目{top}，非叢書部；叢書自成 Collection，子目登 Book 挂其下、不判 Work。總目該丛書下有成員記錄 {nmem} 條。'
                    + (f'\n館藏：{"、".join(holders)}' if holders else ''))
    d['revision'] = '1.0.0'
    d['revised_at'] = TODAY
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parsed', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit-heads', type=int)
    ap.add_argument('--max-book-edits', type=int, default=4000)
    ap.add_argument('--pilot', type=int)
    ap.add_argument('--seed', type=int, default=11)
    ap.add_argument('--only')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()

    # 正式库现状
    exist = {}  # series_id -> collection id
    for f in glob.glob(str(ROOT / 'Collection/**/*.json'), recursive=True):
        d = json.load(open(f, encoding='utf-8'))
        for s in d.get('sources') or []:
            if isinstance(s, dict) and s.get('id'):
                exist[s['id']] = d['id']
    books, paths = {}, {}
    for r, _d, fs in os.walk(ROOT / 'Book'):
        for fn in fs:
            if fn.endswith('.json'):
                p = pathlib.Path(r) / fn
                d = json.loads(p.read_text(encoding='utf-8'))
                paths[d['id']] = p
                if 'merged_into' not in d:
                    books[d['id']] = d
    rec = load(a.parsed)
    mem = collections.defaultdict(list)
    for r in rec.values():
        s = (r.get('series') or {}).get('series_id')
        if s:
            mem[s].append(r['source_record_id'])
    missing = [h for h in mem if h not in exist and h in rec]
    print(f'正式 Collection 源 id {len(exist)}；总目丛书头 {len(mem)}；缺 {len(missing)}（头记录缺 {sum(1 for h in mem if h not in rec)}）')

    def key(h):
        r = rec[h]
        return ((r['title'].get('name') or r['title'].get('raw')), r['edition'].get('label') or '')

    # 成员 Book → 丛书头
    attach, hold = collections.defaultdict(list), []
    miss_set = set(missing)
    book_heads = {}
    for bid, b in books.items():
        hs = []
        for s in b.get('sources') or []:
            r = rec.get(s.get('id'))
            sid = ((r or {}).get('series') or {}).get('series_id')
            if sid and sid not in hs:
                hs.append(sid)
        if any(x in miss_set for x in hs):
            book_heads[bid] = hs
    for bid, hs in book_heads.items():
        b = books[bid]
        if len({key(x) for x in hs if x in rec}) > 1 or any(x not in rec for x in hs):
            hold.append((bid, '源记录分属多个版本不同的丛书头', b.get('title'))); continue
        cur = {x['id'] if isinstance(x, dict) else x for x in b.get('contained_in') or []}
        built = {exist[x] for x in hs if x in exist}
        if cur and not cur <= built:
            hold.append((bid, '已挂的 Collection 与总目丛书头不符', b.get('title'))); continue
        for x in hs:
            if x in miss_set:
                attach[x].append(bid)

    heads = sorted(missing, key=lambda h: (-len(attach.get(h, [])), h))
    if a.only:
        o = set(open(a.only).read().split()); heads = [h for h in heads if h in o]
    if a.pilot:
        random.Random(a.seed).shuffle(heads); heads = heads[:a.pilot]
    if a.limit_heads:
        heads = heads[:a.limit_heads]
    edits, sel = 0, []
    for h in heads:
        n = len(attach.get(h, []))
        if sel and edits + n > a.max_book_edits:
            continue
        sel.append(h); edits += n
    heads = sel
    stat = collections.Counter({'新建 Collection': len(heads), '挂接 Book 项': edits, '存疑 Book': len(hold),
                                '无成员 Book 的丛书头': sum(1 for h in heads if not attach.get(h))})

    ts, seq, used = int(time.time()), 0, set(paths) | set(exist.values())
    plan = []
    for h in heads:
        d = make_collection(rec[h], len(mem[h]))
        while True:
            if seq > 255:
                ts += 1; seq = 0
            raw = (2 << 59) | ((ts & ((1 << 40) - 1)) << 19) | (MACHINE << 8) | seq
            seq += 1
            i = mintid.b36(raw)
            if mintid.dec(i) == raw and i not in used:
                break
        used.add(i)
        d['id'] = i
        d = {k: d[k] for k in ['schema_version', 'id'] + [k for k in d if k not in ('schema_version', 'id')]}
        nm = re.sub(r'[\s/\\［］\[\]（）()〔〕【】<>:"|?*、，。·]', '', d['title'] + d.get('edition', ''))[:60]
        plan.append({'head': h, 'id': i, 'path': mintid.path_for(i, nm, 'Collection'), 'record': d, 'books': attach.get(h, [])})
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'plan.json').write_text(json.dumps({'stat': stat, 'plan': [{k: v for k, v in p.items() if k != 'record'} | {'title': p['record']['title'], 'edition': p['record'].get('edition')} for p in plan]}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    with open(out / '存疑.tsv', 'w', encoding='utf-8') as f:
        f.write('book\twhy\ttitle\n')
        for x in hold:
            f.write('\t'.join(map(str, x)) + '\n')
    print(dict(stat))
    if not a.apply:
        return
    cid_of = {p['head']: p['id'] for p in plan}
    add = collections.defaultdict(list)
    for p in plan:
        for bid in p['books']:
            add[bid].append(p['id'])
    import build_derived as BD
    idx = {}
    for p in plan:
        fp = ROOT / p['path']
        if fp.exists():
            die('新档已存在：' + p['path'])
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(jdump(p['record']), encoding='utf-8')
    coll_idx = json.loads((ROOT / 'index/collections.json').read_text(encoding='utf-8'))
    for p in plan:
        coll_idx[p['id']] = BD.index_entry(p['record'], 'Collection', p['path'])
    idx['index/collections.json'] = dict(sorted(coll_idx.items()))
    for bid, cids in add.items():
        b = json.loads(paths[bid].read_text(encoding='utf-8'))
        ci = b.get('contained_in') or []
        have = {x['id'] if isinstance(x, dict) else x for x in ci}
        ci += [{'id': c} for c in cids if c not in have]
        b['contained_in'] = ci
        rv = (b.get('revision') or '1.0.0').split('.')
        b['revision'] = f'{int(rv[0]) + 1}.0.0'
        b['revised_at'] = TODAY
        paths[bid].write_text(jdump(b), encoding='utf-8')
        rel = f"index/books/{BD.shard_of(bid):x}.json"
        if rel not in idx:
            idx[rel] = json.loads((ROOT / rel).read_text(encoding='utf-8'))
        idx[rel][bid] = BD.index_entry(b, 'Book', str(paths[bid].relative_to(ROOT)))
    BD.write_index(str(ROOT), {k: dict(sorted(v.items())) for k, v in idx.items()})
    print('已写：Collection', len(plan), '改 Book', len(add))


if __name__ == '__main__':
    main()
