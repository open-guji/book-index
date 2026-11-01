#!/usr/bin/env python3
"""混两部书的 Work 拆分（2026-11-01）：按 plan.json 把 Book 改挂正确 Work、整理合刻本 Work 的责任者。
用法（cwd 任意）：split_mixed.py [--plan plan.json] [--apply]；写后跑 dedup-confirmed-163/update_index.py 刷 index。
- moves：Book.work_id 改挂 to；revision 升 major，ai_note 记一行。来源／目标 Work 也升 major 并记一行。
- works.drop_authors：从 Work.authors 去掉这些人（合刻附刻书的撰人），ai_note 记原因。
- works.move_ib：把某条 indexed_by 从该 Work 移到另一 Work（目标已有同 source＋title_info 时不重复加）。
"""
import argparse, glob, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
TODAY = '2026-11-01'
NOTE = f'混两部书拆分（{TODAY}）：'
jdump = lambda o: json.dumps(o, ensure_ascii=False, indent=2) + '\n'
bump = lambda rv: f'{int((rv or "1.0.0").split(".")[0]) + 1}.0.0'


def find(kind, i):
    g = glob.glob(f'{ROOT}/{kind}/*/*/*/{i}-*.json') + glob.glob(f'{ROOT}/{kind}/*/*/*/{i}.json')
    assert len(g) == 1, (kind, i, g)
    return g[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', default=str(pathlib.Path(__file__).with_name('plan.json')))
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--out')
    a = ap.parse_args()
    P = json.load(open(a.plan, encoding='utf-8'))
    recs = {}

    def get(kind, i):
        if (kind, i) not in recs:
            p = find(kind, i); recs[(kind, i)] = [p, json.load(open(p, encoding='utf-8')), False]
        return recs[(kind, i)]

    def note(r, s):
        r['ai_note'] = (r.get('ai_note', '') + '\n' if r.get('ai_note') else '') + NOTE + s
    ledger = []
    for m in P['moves']:
        p, b, _ = get('Book', m['book'])
        src = b['work_id']
        assert src != m['to'], m
        _, S, _ = get('Work', src); _, T, _ = get('Work', m['to'])
        assert 'merged_into' not in T, m
        b['work_id'] = m['to']; note(b, f'原挂 {src}《{S["title"]}》，{m["why"]}，改挂 {m["to"]}《{T["title"]}》')
        recs[('Book', m['book'])][2] = True
        for k, w in ((src, S), (m['to'], T)):
            recs[('Work', k)][2] = True
        ledger.append({'book': m['book'], 'from': src, 'to': m['to'], 'why': m['why']})
    for wid, op in P['works'].items():
        _, W, _ = get('Work', wid)
        if op.get('drop_authors'):
            names = set(op['drop_authors'])
            gone = [x for x in W.get('authors', []) if x['name'] in names]
            assert len(gone) >= 1, (wid, W.get('authors'))
            W['authors'] = [x for x in W['authors'] if x['name'] not in names]
            assert W['authors'], wid
            note(W, f'去掉责任者 {"、".join(sorted(names))}：{op["why"]}')
        for mv in op.get('move_ib', []):
            hit = [x for x in W.get('indexed_by', []) if x.get('source') == mv['source'] and x.get('title_info') == mv['title_info']]
            assert len(hit) == 1, (wid, mv)
            _, T, _ = get('Work', mv['to']); recs[('Work', mv['to'])][2] = True
            if not any(x.get('source') == mv['source'] and x.get('title_info') == mv['title_info'] for x in T.get('indexed_by', [])):
                T.setdefault('indexed_by', []).append(hit[0])
            W['indexed_by'] = [x for x in W['indexed_by'] if x is not hit[0]]
            if not W['indexed_by']:
                W.pop('indexed_by')
            note(W, f'著录「{mv["title_info"]}」（{mv["source"]}）移到 {mv["to"]}：{op["why"]}')
            note(T, f'由 {wid} 移入著录「{mv["title_info"]}」（{mv["source"]}）')
        recs[('Work', wid)][2] = True
    for (kind, i), (p, r, touched) in recs.items():
        if touched:
            r['revision'] = bump(r.get('revision')); r['revised_at'] = TODAY
            if a.apply:
                open(p, 'w', encoding='utf-8').write(jdump(r))
    print('moves', len(ledger), '改动记录', sum(1 for v in recs.values() if v[2]))
    if a.out:
        pathlib.Path(a.out).write_text(jdump(ledger), encoding='utf-8')


if __name__ == '__main__':
    main()
