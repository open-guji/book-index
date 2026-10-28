#!/usr/bin/env python3
"""去重方案部分 5（2026-10-28 用户定口径）：故宫／国图同版本分册并为一个 Book。

    python3 merge_volumes.py <batch.json> [--apply]

口径：Book＝版本，不是册。同 Work 同版本的多个索书号／多册／多复本并成一个 Book，各号作为藏本信息保留：
- provenance 取并集（各号索书号保留；被并者的「存缺」写进对应 provenance 条的 notes）；
- resources 取并集，每条资源加 note 标明所属藏本（「故宮藏本：<索书号>」「國圖藏本：fid <号>」），资源 metadata 原样；
- resource_groups／contained_in／sources／indexed_by 取并集；
- 被并者的 physical_description／metadata／edition 等原样记入台账 loser_original_notes；
- 被并者留最小墓碑（merged_into），keeper 写 merged_from；
- 指向被并者的 Book.related_books 与墓碑 merged_into 改指 keeper；promotions 改指。
乾跑只印计划；--apply 后写 merges.json（与 batch.json 同目录，格式同 dedup-confirmed-163）。"""
import argparse, datetime, glob, hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
sys.path[:0] = [os.path.join(ROOT, '.claude/qa')]
import backrefs  # noqa: E402
TODAY = datetime.date.today().isoformat()


def path_of(i):
    hits = glob.glob(os.path.join(ROOT, 'Book', i[-3], i[-2], i[-1], i + '-*.json'))
    assert len(hits) == 1, (i, hits)
    return os.path.relpath(hits[0], ROOT)


def base_sha(rel):
    b = subprocess.check_output(['git', '-c', 'core.quotePath=false', 'show', 'origin/main:' + rel], cwd=ROOT)
    return hashlib.sha256(b).hexdigest()


def load(rel): return json.load(open(os.path.join(ROOT, rel), encoding='utf-8'))


def save(rel, j): open(os.path.join(ROOT, rel), 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')


def label(d):
    cns = [p.get('call_number') for p in d.get('provenance') or [] if p.get('call_number')]
    if cns: return '故宮藏本：' + '、'.join(cns)
    for r in d.get('resources') or []:
        fid = (r.get('metadata') or {}).get('nlc_fid')
        if fid: return '國圖藏本：fid ' + str(fid)
    return None


def tag(d):
    """给一条 Book 的 resources 逐条加 note（已有则不动），provenance 条加存缺。返回（resources, provenance）副本。"""
    lab = label(d)
    res = []
    for r in d.get('resources') or []:
        r = dict(r)
        if lab and not r.get('note'): r['note'] = lab
        res.append(r)
    cond = ((d.get('physical_description') or {}).get('condition') or '').strip()
    prov = []
    for p in d.get('provenance') or []:
        p = dict(p)
        if cond and cond not in (p.get('notes') or ''):
            p['notes'] = ((p.get('notes') or '') + ('；' if p.get('notes') else '') + '存缺：' + cond)
        prov.append(p)
    return res, prov


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('batch'); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    groups = json.load(open(a.batch, encoding='utf-8'))['groups']
    print(f'載入 {len(groups)} 組', file=sys.stderr); assert groups
    losers = [l for g in groups for l in g['losers']]
    assert len(losers) == len(set(losers)) and not set(losers) & {g['keeper'] for g in groups}
    back = backrefs.scan(ROOT)
    kmap = {l: g['keeper'] for g in groups for l in g['losers']}
    ledger = []
    for l in losers:  # 入边：只处理 Book.related_books 与 Book 墓碑 merged_into
        for e in back.get(l) or []:
            assert e[0] in ('Book.related_books', 'Book.merged_in'), ('未处理的入边', l, e)
    for g in groups:
        kr = path_of(g['keeper']); k = load(kr)
        assert not k.get('merged_into') and k.get('type') == 'book'
        pre = [{'id': g['keeper'], 'path': kr, 'sha256': base_sha(kr)}]
        kres, kprov = tag(k)
        k['resources'] = kres if kres else k.get('resources')
        if kprov: k['provenance'] = kprov
        notes = {}
        for l in g['losers']:
            lr = path_of(l); d = load(lr)
            assert not d.get('merged_into') and d['work_id'] == k['work_id'], (l, d.get('work_id'), k['work_id'])
            pre.append({'id': l, 'path': lr, 'sha256': base_sha(lr)})
            dres, dprov = tag(d)
            for f, xs in (('resources', dres), ('provenance', dprov), ('contained_in', d.get('contained_in') or []),
                          ('sources', d.get('sources') or []), ('indexed_by', d.get('indexed_by') or [])):
                for x in xs:
                    if x in (k.get(f) or []): continue
                    if f == 'contained_in' and x.get('id') in {c.get('id') for c in k.get(f) or []}: continue
                    k.setdefault(f, []).append(x)
            for gk, gv in (d.get('resource_groups') or {}).items():
                k.setdefault('resource_groups', {}).setdefault(gk, gv)
            notes[l] = {f: d[f] for f in ('title', 'edition', 'dating', 'juan_count', 'ai_note', 'physical_description', 'metadata', 'measure_info') if f in d}
            k.setdefault('merged_from', [])
            if l not in k['merged_from']: k['merged_from'].append(l)
            t = {'schema_version': d.get('schema_version', 1), 'id': l, 'type': 'book', 'title': d.get('title'),
                 'work_id': d.get('work_id'), 'revision': d.get('revision') or '1.0.0', 'merged_into': g['keeper'], 'revised_at': TODAY}
            if a.apply: save(lr, t)
            # 入边改指
            for e in back.get(l) or []:
                hr = path_of(e[1]); h = load(hr)
                if e[0] == 'Book.related_books':
                    new = []
                    for x in h.get('related_books') or []:
                        x = kmap.get(x, x)
                        if x != h['id'] and x not in new: new.append(x)
                    h['related_books'] = new
                else:
                    h['merged_into'] = g['keeper']
                if a.apply: save(hr, h)
        rev = '%d.0.0' % (int((k.get('revision') or '1.0.0').split('.')[0]) + 1)
        k.pop('revision', None); k.pop('revised_at', None); k['revision'] = rev; k['revised_at'] = TODAY
        if a.apply: save(kr, k)
        print(('並 ' if a.apply else '乾跑 ') + f"{g['cluster_id']} {g['keeper']} <- {g['losers']}")
        ledger.append({'cluster_id': g['cluster_id'], 'type': 'book', 'keeper': g['keeper'], 'losers': g['losers'],
                       'evidence': g['evidence'], 'rule': g['rule'], 'preconditions': pre, 'retained_alternatives': [],
                       'classification_decisions': [], 'dropped_author_entities': [], 'loser_original_notes': notes})
    if a.apply:
        n = 0
        for f in sorted(glob.glob(os.path.join(ROOT, 'promotions', '*.json'))):
            t = open(f, encoding='utf-8').read(); o = t
            for l, kp in kmap.items():
                t = t.replace('"production_id": "%s"' % l, '"production_id": "%s"' % kp)
            if t != o: open(f, 'w', encoding='utf-8').write(t); n += 1
        print('promotions 文件改动：', n)
        base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
        json.dump({'base': base, 'merges': ledger}, open(os.path.join(os.path.dirname(os.path.abspath(a.batch)), 'merges.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
