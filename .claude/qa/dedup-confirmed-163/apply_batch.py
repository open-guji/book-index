#!/usr/bin/env python3
"""去重确认案小批实施：按 batch 规格（JSON）并 Work／人物／Book，被并者留墓碑，生成并条台账。

    python3 apply_batch.py <batch.json> [--apply]

不加 --apply 为乾跑（只印 mergework 的逐欄 diff 与计划）。--apply 后写 merges.json（与 batch.json 同目录）。
Work 复用 .claude/qa/mergework.py（但其原本删被并者之檔，这里改为写墓碑）；
人物复用 .claude/qa/entity_merge.py（原本即留墓碑）；Book 自带最小实现。
"""
import argparse, contextlib, datetime, glob, hashlib, io, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(QA, '..', '..'))
sys.path[:0] = [QA, os.path.join(ROOT, 'build')]
import mergework, entity_merge, jio, backrefs  # noqa: E402
import v2common as V  # noqa: E402

_scan = backrefs.scan
_cache = {}
def cached_scan(root, *a, **k):
    # 全库反查一次约 30 秒；各组 ID 互不相交，缓存对其余组的被并者仍有效
    if root not in _cache:
        _cache[root] = _scan(root, *a, **k)
    return _cache[root]
backrefs.scan = cached_scan

TODAY = datetime.date.today().isoformat()
BY = 'A11-去重确认案'


def path_of(typ, i):
    d = {'work': 'Work', 'people': 'Entity', 'book': 'Book'}[typ]
    hits = glob.glob(os.path.join(ROOT, d, *i[-3:], i + '-*.json'))
    assert len(hits) == 1, (i, hits)
    return os.path.relpath(hits[0], ROOT)


def base_sha(rel):
    b = subprocess.check_output(['git', '-c', 'core.quotePath=false', 'show', 'origin/main:' + rel], cwd=ROOT)
    return hashlib.sha256(b).hexdigest(), json.loads(b)


def bump_minor(rev):
    a, b, c = (rev or '1.0.0').split('.')
    return '%s.%d.0' % (a, int(b) + 1)


def work_tomb(d, keeper):
    return {'schema_version': d.get('schema_version', 1), 'id': d['id'], 'type': 'work',
            'title': d.get('title'), 'revision': d.get('revision') or '1.0.0',
            'merged_into': keeper, 'revised_at': TODAY}


def merge_work(g, apply):
    keeper, losers = g['keeper'], g['losers']
    lpaths = {l: os.path.join(ROOT, path_of('work', l)) for l in losers}
    argv = ['--keeper', keeper, '--drop', ','.join(losers), '--rule', g['rule'], '--why', g['why'], '--by', BY]
    if apply:
        argv.append('--apply')
    recs = {l: json.load(open(p, encoding='utf-8')) for l, p in lpaths.items()}
    kp0 = os.path.join(ROOT, path_of('work', keeper))
    k0 = json.load(open(kp0, encoding='utf-8'))
    dps = [(l, lpaths[l], recs[l], None) for l in losers]
    _moved, conflicts, _nv = mergework.plan_scalar_merge(k0, dps)
    g['retained_alternatives'] = [{'loser': l, 'fields': [{'field': f, 'keeper_value': kv, 'loser_value': v}
                                  for d, f, kv, v in conflicts if d == l]} for l in losers if any(d == l for d, *_ in conflicts)]
    _w, g['classification_decisions'] = mergework.plan_classification(ROOT, keeper, set(losers))
    g['classification_decisions'] = list(g['classification_decisions'])
    g['dropped_author_entities'] = [{'loser': l, 'name': a.get('name'), 'entity_id': a.get('entity_id')}
                                    for l in losers for a in recs[l].get('authors') or []
                                    if a.get('entity_id') and a['entity_id'] not in {x.get('entity_id') for x in k0.get('authors') or []}]
    real_remove = os.remove
    def fake_remove(p):
        for l, lp in lpaths.items():
            if os.path.abspath(p) == lp:
                with open(lp, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(work_tomb(recs[l], keeper), ensure_ascii=False, indent=2) + '\n')
                return
        real_remove(p)
    buf = io.StringIO()
    os.remove = fake_remove
    try:
        with contextlib.redirect_stdout(buf):
            mergework.main(argv)
    finally:
        os.remove = real_remove
    out = buf.getvalue()
    if apply:
        kp = os.path.join(ROOT, path_of('work', keeper))
        k = json.load(open(kp, encoding='utf-8'))
        k['revision'] = bump_minor(k.get('revision')); k['revised_at'] = TODAY
        k.setdefault('merged_from', [])
        for l in losers:
            if l not in k['merged_from']:
                k['merged_from'].append(l)
            for m in k.get('merged_in') or []:
                if isinstance(m, dict) and m.get('id') == l:
                    au = '、'.join(str(a.get('name')) for a in recs[l].get('authors') or [])
                    if au: m['author'] = au
                    ti = '；'.join([x['title_info'] for x in recs[l].get('indexed_by') or [] if x.get('title_info')][:6])
                    if ti: m['title_info'] = ti   # schema：string（多條以「；」連）
        with open(kp, 'w', encoding='utf-8') as f:
            f.write(V.dump(k, V.detect_format(open(kp, encoding='utf-8').read(), k)))
    return out


def merge_people(g, apply):
    out = []
    for l in g['losers']:
        if not apply:
            out.append('people dry %s <- %s' % (g['keeper'], l)); continue
        s = entity_merge.merge(l, g['keeper'], reason=g['why'], rule=g['rule'], date=TODAY, by=BY)
        rel = path_of('people', g['keeper']); k, fmt = jio.load(rel)
        lname = s['loser_name']
        if lname and lname != k.get('primary_name') and lname not in {x.get('name') for x in k.get('alt_names') or []}:
            k.setdefault('alt_names', []).append({'name': lname, 'type': '別稱', 'note': '并入重出人物条（%s）；见 %s' % (l, g['cluster_id'])})
            jio.save(rel, k, fmt)
        out.append(json.dumps(s, ensure_ascii=False)[:600])
    return '\n'.join(out)


def merge_book(g, apply):
    keeper = g['keeper']
    kp = os.path.join(ROOT, path_of('book', keeper))
    k = json.load(open(kp, encoding='utf-8'))
    for l in g['losers']:
        lp = os.path.join(ROOT, path_of('book', l))
        d = json.load(open(lp, encoding='utf-8'))
        for f in ('contained_in', 'resources'):
            for x in d.get(f) or []:
                if x not in (k.get(f) or []):
                    k.setdefault(f, []).append(x)
        k.setdefault('merged_from', [])
        if l not in k['merged_from']:
            k['merged_from'].append(l)
        if apply:
            t = {'schema_version': d.get('schema_version', 1), 'id': l, 'type': 'book', 'title': d.get('title'),
                 'work_id': d.get('work_id'), 'revision': d.get('revision') or '1.0.0',
                 'merged_into': keeper, 'revised_at': TODAY}
            open(lp, 'w', encoding='utf-8').write(json.dumps(t, ensure_ascii=False, indent=2) + '\n')
    if apply:
        k['revision'] = '%d.0.0' % (int((k.get('revision') or '1.0.0').split('.')[0]) + 1); k['revised_at'] = TODAY
        open(kp, 'w', encoding='utf-8').write(json.dumps(k, ensure_ascii=False, indent=2) + '\n')
    return 'book %s <- %s' % (keeper, g['losers'])


def fix_promotions(mapping):
    # 升格表：只允许 production_id 由被并者改为 keeper，其余字段不动
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'promotions', '*.json'))):
        t = open(f, encoding='utf-8').read(); o = t
        for l, k in mapping.items():
            t = t.replace('"production_id": "%s"' % l, '"production_id": "%s"' % k)
        if t != o:
            open(f, 'w', encoding='utf-8').write(t); n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('batch'); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    spec = json.load(open(a.batch, encoding='utf-8'))
    ledger = []
    for g in spec['groups']:
        pre = []
        for i in [g['keeper']] + g['losers']:
            rel = path_of(g['type'], i); sha, _ = base_sha(rel)
            pre.append({'id': i, 'path': rel, 'sha256': sha})
        out = {'work': merge_work, 'people': merge_people, 'book': merge_book}[g['type']](g, a.apply)
        print('=====', g['cluster_id'], g['type'], g['keeper'], '<-', g['losers']); print(out)
        ledger.append({'cluster_id': g['cluster_id'], 'type': g['type'], 'keeper': g['keeper'], 'losers': g['losers'],
                       'evidence': g['evidence'], 'rule': g['rule'], 'preconditions': pre, 'retained_alternatives': g.get('retained_alternatives', []),
                       'classification_decisions': g.get('classification_decisions', []), 'dropped_author_entities': g.get('dropped_author_entities', []),
                       'loser_original_notes': g.get('loser_original_notes', {})})
    if a.apply:
        mp = {l: g['keeper'] for g in spec['groups'] for l in g['losers']}
        print('promotions 文件改动：', fix_promotions(mp))
    if a.apply:
        base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
        json.dump({'base': base, 'merges': ledger}, open(os.path.join(os.path.dirname(os.path.abspath(a.batch)), 'merges.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
