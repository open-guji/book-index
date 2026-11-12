#!/usr/bin/env python3
"""L2（11-12）：丛书总名条与互链。
1) 成员多的大丛书（同归一化题名、≥3 个版本 Collection、平均每版本成员 ≥40；兩宋名賢小集编者不同除外）：新建 work_collection 总名条，
   各版本 Collection 的 contained_in 指向它。5 组已有手建伞状条（武英殿聚珍版叢書、四部叢刊、平津館叢書、湖海樓叢書、四庫全書珍本初集）：版本条挂到手建条下，不新建。
2) 其余同题异版本的 Collection（组内 2–6 个，且题名相同或编者相交／缺）：补 related_collections 互链（只存 id 较小一侧）。
不改 Book／Work。乾跑默认，--apply 才写。
用法：build_umbrella.py [--apply] --out <批目录>
"""
import argparse, collections, datetime, glob, itertools, json, os, pathlib, re, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / '.claude/qa'), str(ROOT / 'build')]
import mintid, v2common as V  # noqa: E401
TODAY = datetime.date.today().isoformat()
MACHINE = 2083
NORM = re.compile(r'（[^）]*）|[一二三四五六七八九十百千零〇]+[種集編帙函卷].*$|[一二三四五六七八九十百千零〇]+種.*$')
HAND = {'武英殿聚珍版書': '8rlcsybg2hhf', '四部叢刊': '8rld46zzcyrp', '平津館叢書': '8rld46zzcyrl', '湖海樓叢書': '8rld46zzcyrm', '四庫全書珍本初集': '8rlb6yy86eww'}
EXCL = {'兩宋名賢小集'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
    cols, paths = {}, {}
    for f in glob.glob(str(ROOT / 'Collection/*/*/*/*.json')):
        raw = open(f, encoding='utf-8').read(); c = json.loads(raw)
        if 'merged_into' in c: continue
        cols[c['id']] = c; paths[c['id']] = f
    mem = collections.Counter()
    for f in glob.glob(str(ROOT / 'Book/*/*/*/*.json')):
        b = json.load(open(f, encoding='utf-8'))
        if 'merged_into' in b: continue
        for x in b.get('contained_in') or []: mem[x['id']] += 1
    g = collections.defaultdict(list)
    for i, c in cols.items():
        if c.get('sources') and c['subtype'] == 'book_collection': g[NORM.sub('', c['title'])].append(i)
    auth = lambda c: {x.get('name') for x in c.get('authors', []) if x.get('name')}
    parent = {}   # child -> umbrella id (existing or 'NEW:<title>')
    for t, v in g.items():
        if t in HAND or any(t.startswith(h) for h in HAND):
            continue
    for h, uid in HAND.items():
        for i, c in cols.items():
            if c.get('sources') and c['title'].startswith(h) and i != uid:
                parent[i] = uid
    newu = []
    for t, v in g.items():
        if t in EXCL or any(i in parent for i in v) or len(v) < 3: continue
        if sum(mem[i] for i in v) / len(v) < 40 or sum(mem[i] for i in v) < 300: continue
        parent.update({i: 'NEW:' + t for i in v}); newu.append((t, v))
    ts, seq, used = int(time.time()), 0, set(paths)
    ids = {}
    for t, v in newu:
        while True:
            if seq > 255: ts += 1; seq = 0
            raw = (2 << 59) | ((ts & ((1 << 40) - 1)) << 19) | (MACHINE << 8) | seq; seq += 1
            i = mintid.b36(raw)
            if mintid.dec(i) == raw and i not in used: break
        used.add(i); ids[t] = i
    rel = []
    for t, v in g.items():
        vv = [i for i in v if i not in parent]
        if 2 <= len(vv) <= 6:
            for x, y in itertools.combinations(sorted(vv), 2):
                cx, cy = cols[x], cols[y]
                if cx['title'] == cy['title'] or (auth(cx) & auth(cy)) or not auth(cx) or not auth(cy): rel.append((x, y))
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    plan = {'umbrella_new': [{'title': t, 'id': ids[t], 'children': v} for t, v in newu],
            'umbrella_hand': {h: [i for i, u in parent.items() if u == uid] for h, uid in HAND.items()},
            'related': rel}
    (out / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('新建总名条', len(newu), '手建条下挂', sum(len(x) for x in plan['umbrella_hand'].values()), '互链', len(rel))
    if not a.apply: return
    def save(i, c, raw=None):
        p = paths[i]; r0 = open(p, encoding='utf-8').read(); fmt = V.detect_format(r0, json.loads(r0))
        open(p, 'w', encoding='utf-8', newline='\n').write(V.dump(c, fmt))
    def bump(c):
        x, y, z = (int(n) for n in (c.get('revision') or '1.0.0').split('.')); c['revision'] = f'{x}.{y}.{z + 1}'; c['revised_at'] = TODAY
    touched = {}
    for i, u in parent.items():
        uid = ids[u[4:]] if u.startswith('NEW:') else u
        c = touched.setdefault(i, json.loads(open(paths[i], encoding='utf-8').read()))
        ci = c.setdefault('contained_in', [])
        if uid not in [x['id'] for x in ci]: ci.append({'id': uid})
    for x, y in rel:
        lo, hi = sorted((x, y)); c = touched.setdefault(lo, json.loads(open(paths[lo], encoding='utf-8').read()))
        r = c.setdefault('related_collections', [])
        if hi not in r: r.append(hi)
    for i, c in touched.items():
        bump(c); save(i, c)
    for t, v in newu:
        i = ids[t]
        d = {'schema_version': 1, 'id': i, 'type': 'collection', 'subtype': 'work_collection', 'title': t,
             'ai_note': f'【丛书总名条】L2（{TODAY}）：《{t}》在總目有 {len(v)} 個版本條（版本 Collection，各自一條），本條為其跨版本的總名條，各版本條的 contained_in 指向本條；不另挂成員，成員仍登在各版本條下。',
             'revision': '1.0.0', 'revised_at': TODAY}
        p = pathlib.Path(mintid.path_for(i, re.sub(r'[\s/\\［］\[\]（）()〔〕【】<>:"|?*、，。·]', '', t)[:60], 'Collection'))
        fp = ROOT / p; fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('已写：改 Collection', len(touched), '新建', len(newu))


if __name__ == '__main__':
    main()
