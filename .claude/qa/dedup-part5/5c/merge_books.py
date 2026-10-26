#!/usr/bin/env python3
"""去重方案部分 5c（2026-10-25）：按 batch.json 把国图重配新建的 Book 并入同版本的总目 Book。

    python3 merge_books.py <batch.json> [--apply]

在 dedup-confirmed-163/apply_batch.py 的 merge_book 之上补：resource_groups 一并迁入（国图资源按 group 挂
「國圖藏本：」标签）；被并者独有字段（edition／dating／juan_count／ai_note 等）原样记入台账
loser_original_notes，不盲覆盖 keeper。keeper 写 merged_from，被并者留最小墓碑。
引用：Book 只被 Collection.contains、Book.related_books／base_edition／lineage、book-text 指；
脚本用 backrefs 全扫被并 ID，有活引用即停（国图新建 Book 实测无入边）。promotions 照 apply_batch 改写（实测无）。
乾跑只印计划；--apply 后写 merges.json（与 batch.json 同目录，格式同 dedup-confirmed-163）。"""
import argparse, datetime, glob, hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
sys.path[:0] = [os.path.join(ROOT, '.claude/qa')]
import backrefs  # noqa: E402
TODAY = datetime.date.today().isoformat()
SKIP = {'schema_version', 'id', 'type', 'title', 'work_id', 'revision', 'revised_at', 'updated_at', 'ai_note', 'edition',
        'contained_in', 'resources', 'sources', 'indexed_by', 'provenance', 'resource_groups', 'merged_from', 'merged_into'}


def path_of(i):
    hits = glob.glob(os.path.join(ROOT, 'Book', i[-3], i[-2], i[-1], i + '-*.json'))
    assert len(hits) == 1, (i, hits)
    return os.path.relpath(hits[0], ROOT)


def base_sha(rel):
    b = subprocess.check_output(['git', '-c', 'core.quotePath=false', 'show', 'origin/main:' + rel], cwd=ROOT)
    return hashlib.sha256(b).hexdigest()


def save(rel, j):
    open(os.path.join(ROOT, rel), 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('batch'); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    spec = json.load(open(a.batch, encoding='utf-8'))
    groups = spec['groups']
    print(f'載入 {len(groups)} 組', file=sys.stderr); assert groups
    losers = [l for g in groups for l in g['losers']]
    assert len(losers) == len(set(losers)) and not set(losers) & {g['keeper'] for g in groups}
    back = backrefs.scan(ROOT)
    live = {i: back[i] for i in losers if back.get(i)}
    assert not live, ('被并 Book 有入边，先处理', live)
    ledger = []
    for g in groups:
        kr = path_of(g['keeper']); k = json.load(open(os.path.join(ROOT, kr), encoding='utf-8'))
        assert not k.get('merged_into') and k.get('type') == 'book'
        pre = [{'id': g['keeper'], 'path': kr, 'sha256': base_sha(kr)}]
        notes = {}
        for l in g['losers']:
            lr = path_of(l); d = json.load(open(os.path.join(ROOT, lr), encoding='utf-8'))
            assert not d.get('merged_into') and d['work_id'] == k['work_id'], (l, d.get('work_id'), k['work_id'])
            pre.append({'id': l, 'path': lr, 'sha256': base_sha(lr)})
            for f in ('contained_in', 'resources', 'sources', 'indexed_by', 'provenance'):
                for x in d.get(f) or []:
                    if x in (k.get(f) or []): continue
                    if f == 'contained_in' and x.get('id') in {c.get('id') for c in k.get(f) or []}: continue  # 同一 Collection 不重复挂
                    k.setdefault(f, []).append(x)
            for gk, gv in (d.get('resource_groups') or {}).items():
                k.setdefault('resource_groups', {}).setdefault(gk, gv)
            notes[l] = {f: d[f] for f in ('title', 'edition', 'dating', 'juan_count', 'ai_note') if f in d}
            if g.get('copy_missing'):  # 部分 5b 平圖：keeper 缺的单值欄从被并者补入，两边都有而不同的记台账
                for f, v in d.items():
                    if f in SKIP: continue
                    if f not in k: k[f] = v
                    elif k[f] != v: notes[l].setdefault('conflicts', {})[f] = v
            if g.get('tag_provenance') and d.get('edition') and d.get('edition') != k.get('edition'):
                for x in k.get('provenance') or []:
                    if x in (d.get('provenance') or []) and g['tag_provenance'] not in (x.get('notes') or ''):
                        x['notes'] = ((x.get('notes') or '') + ('；' if x.get('notes') else '') + g['tag_provenance'] + d['edition'])
            k.setdefault('merged_from', [])
            if l not in k['merged_from']: k['merged_from'].append(l)
            t = {'schema_version': d.get('schema_version', 1), 'id': l, 'type': 'book', 'title': d.get('title'),
                 'work_id': d.get('work_id'), 'revision': d.get('revision') or '1.0.0', 'merged_into': g['keeper'], 'revised_at': TODAY}
            if a.apply: save(lr, t)
        rev = '%d.0.0' % (int((k.get('revision') or '1.0.0').split('.')[0]) + 1)
        k.pop('revision', None); k.pop('revised_at', None); k['revision'] = rev; k['revised_at'] = TODAY  # 管理欄留在末尾
        if a.apply: save(kr, k)
        print(('並 ' if a.apply else '乾跑 ') + f"{g['cluster_id']} {g['keeper']} <- {g['losers']}")
        ledger.append({'cluster_id': g['cluster_id'], 'type': 'book', 'keeper': g['keeper'], 'losers': g['losers'],
                       'evidence': g['evidence'], 'rule': g['rule'], 'preconditions': pre, 'retained_alternatives': [],
                       'classification_decisions': [], 'dropped_author_entities': [], 'loser_original_notes': notes})
    if a.apply:
        n = 0
        for f in sorted(glob.glob(os.path.join(ROOT, 'promotions', '*.json'))):
            t = open(f, encoding='utf-8').read(); o = t
            for l, kp in {l: g['keeper'] for g in groups for l in g['losers']}.items():
                t = t.replace('"production_id": "%s"' % l, '"production_id": "%s"' % kp)
            if t != o: open(f, 'w', encoding='utf-8').write(t); n += 1
        print('promotions 文件改动：', n)
        base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
        json.dump({'base': base, 'merges': ledger}, open(os.path.join(os.path.dirname(os.path.abspath(a.batch)), 'merges.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
