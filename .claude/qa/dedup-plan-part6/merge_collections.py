#!/usr/bin/env python3
"""去重方案部分 6：并重复 Collection（丛编），被并者留墓碑，成员侧 contained_in 改指 keeper。

    python3 .claude/qa/dedup-plan-part6/merge_collections.py <batch.json> [--apply]

batch.json：{"groups": [{"cluster_id", "keeper", "losers": [...], "evidence", "rule"}]}
不加 --apply 为乾跑（只印计划与冲突）。--apply 写文件，并在 batch.json 同目录写 merges.json（台账，
格式同 dedup-confirmed-163，type 为 collection），供 scripts/audit-merge-ledger.py 核。

做法（schema/collection.md〈merged_into〉、CHANGELOG 2026-10-25）：
- keeper：被并者题名与 keeper 不同的记入 additional_titles；被并者有而 keeper 没有的字段补入；indexed_by／sources／resources／additional_titles 取并集；
  两边都有且不同的标量保留 keeper 值（batch 里 prefer_loser 列的字段改取被并值），另一值记台账 retained_alternatives；batch 的 note 追加到 keeper 的 ai_note；merged_from 加被并 id；revision 升 minor。
- 被并者：只留 schema_version／id／type／subtype／title／merged_into／revision／revised_at。
- 成员（Book／Work／Collection 的 contained_in 指被并者）：改指 keeper；同一成员已挂 keeper 的，
  把被并项的 volume_index／sub_items／details 补到 keeper 项上（keeper 项已有不同值的记台账），删去被并项；
  成员 revision 升 patch。related_collections、Collection.contains 里的被并 id 同改。promotions 只改 production_id。
"""
import argparse, collections, datetime, glob, hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'build')]
import v2common as V  # noqa: E402

TODAY = datetime.date.today().isoformat()
UNION = ('indexed_by', 'sources', 'resources', 'additional_titles')
SKIP = {'id', 'type', 'schema_version', 'revision', 'revised_at', 'updated_at', 'merged_from', 'merged_into', 'ai_note'}
ATTRS = ('volume_index', 'sub_items', 'details')


def load(p):
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    return d, V.detect_format(raw, d)


def save(p, d, fmt):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(V.dump(d, fmt))


def col_path(i):
    hits = glob.glob(os.path.join(ROOT, 'Collection', *i[-3:], i + '-*.json'))
    assert len(hits) == 1, (i, hits)
    return hits[0]


def bump(rev, part):
    a, b, c = (int(x) for x in (rev or '1.0.0').split('.'))
    return '%d.%d.0' % (a, b + 1) if part == 'minor' else '%d.%d.%d' % (a, b, c + 1)


def base_sha(rel):
    b = subprocess.check_output(['git', '-c', 'core.quotePath=false', 'show', 'origin/main:' + rel], cwd=ROOT)
    return hashlib.sha256(b).hexdigest()


def referrers(ids):
    """工作树里文本含任一 id 的 Book／Work／Collection 档（rg 粗筛，再逐档精查）。"""
    out = subprocess.run(['rg', '-l', '-F', '-f', '/dev/stdin', '--glob', '*.json', 'Book', 'Work', 'Collection'],
                         input='\n'.join(ids) + '\n', cwd=ROOT, text=True, capture_output=True).stdout.split()
    return sorted(os.path.join(ROOT, p) for p in out)


def cid(x):
    return x.get('id') if isinstance(x, dict) else x


def merge_keeper(k, d, alts):
    for f, v in d.items():
        if f in SKIP or f.startswith('_'):
            continue
        if f in UNION and isinstance(v, list):
            cur = k.setdefault(f, [])
            for x in v:
                if x not in cur:
                    cur.append(x)
        elif f not in k or k[f] in (None, '', [], {}):
            k[f] = v
        elif k[f] != v:
            alts.append({'field': f, 'keeper_value': k[f], 'loser_value': v})


def fix_member(m, mapping, notes):
    """改一个成员档的 contained_in／related_collections／contains；回是否改动。"""
    changed = False
    ci = m.get('contained_in')
    if isinstance(ci, list) and any(cid(x) in mapping for x in ci):
        new = []
        for x in ci:
            i = cid(x)
            if i not in mapping:
                new.append(x)
                continue
            kid = mapping[i]
            hit = next((y for y in new + ci if cid(y) == kid), None)
            if hit is None:
                new.append({**x, 'id': kid} if isinstance(x, dict) else kid)
            elif isinstance(x, dict) and isinstance(hit, dict):
                for a in ATTRS:
                    if a in x and a not in hit:
                        hit[a] = x[a]
                    elif a in x and hit[a] != x[a]:
                        notes.append({'member': m['id'], 'attr': a, 'keeper_item': hit[a], 'loser_item': x[a], 'loser': i})
            changed = True
        # 去掉重复的 keeper 项（只留第一个）
        seen, out = set(), []
        for x in new:
            if cid(x) in seen:
                continue
            seen.add(cid(x)); out.append(x)
        m['contained_in'] = out
    v = m.get('related_collections')
    if isinstance(v, list) and any(x in mapping for x in v):
        r = []
        for x in v:
            x = mapping.get(x, x)
            if x != m['id'] and x not in r:
                r.append(x)
        m['related_collections'] = r
        changed = True
    for x in m.get('contains') or []:
        if isinstance(x, dict) and x.get('collection_id') in mapping:
            x['collection_id'] = mapping[x['collection_id']]; changed = True
    return changed


def fix_promotions(mapping, apply):
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'promotions', '*.json'))):
        t = open(f, encoding='utf-8').read(); o = t
        for l, k in mapping.items():
            t = t.replace('"production_id": "%s"' % l, '"production_id": "%s"' % k)
        if t != o:
            n += 1
            if apply:
                open(f, 'w', encoding='utf-8').write(t)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('batch'); ap.add_argument('--apply', action='store_true'); ap.add_argument('--by', default='A11-去重方案部分6')
    a = ap.parse_args()
    spec = json.load(open(a.batch, encoding='utf-8'))
    groups = spec['groups']
    mapping = {l: g['keeper'] for g in groups for l in g['losers']}
    assert not set(mapping) & {g['keeper'] for g in groups}, 'keeper 不得同时是被并者'
    print('载入组 %d，被并 %d' % (len(groups), len(mapping)))
    assert groups
    ledger = []
    for g in groups:
        kp = col_path(g['keeper']); k, kfmt = load(kp)
        assert not k.get('merged_into'), ('keeper 是墓碑', g['keeper'])
        pre = [{'id': g['keeper'], 'path': os.path.relpath(kp, ROOT), 'sha256': base_sha(os.path.relpath(kp, ROOT))}]
        alts = []
        for l in g['losers']:
            lp = col_path(l); d, lfmt = load(lp)
            assert not d.get('merged_into'), ('被并者已是墓碑', l)
            pre.append({'id': l, 'path': os.path.relpath(lp, ROOT), 'sha256': base_sha(os.path.relpath(lp, ROOT))})
            la = []
            if d.get('title') and d['title'] != k.get('title') and d['title'] not in (k.get('additional_titles') or []):
                k.setdefault('additional_titles', []).append(d['title'])   # 被并者题名留作异名
            for f in g.get('prefer_loser') or []:   # 被并者著录更准的字段：改取被并值，keeper 原值记台账
                if f in d and d[f] != k.get(f):
                    la.append({'field': f, 'keeper_value': k.get(f), 'loser_value': d[f], 'chosen': 'loser'})
                    k[f] = d[f]
            merge_keeper(k, d, la)
            if la:
                alts.append({'loser': l, 'fields': la})
            if d.get('ai_note') and d['ai_note'] != k.get('ai_note'):
                alts.append({'loser': l, 'fields': [{'field': 'ai_note', 'keeper_value': k.get('ai_note'), 'loser_value': d['ai_note']}]})
            if g.get('note'):
                k['ai_note'] = ((k.get('ai_note') or '').rstrip() + '\n' + g['note']).lstrip()
            k.setdefault('merged_from', [])
            if l not in k['merged_from']:
                k['merged_from'].append(l)
            tomb = {'schema_version': d.get('schema_version', 1), 'id': l, 'type': 'collection', 'subtype': d.get('subtype'),
                    'title': d.get('title'), 'merged_into': g['keeper'], 'revision': bump(d.get('revision'), 'minor'),
                    'revised_at': TODAY}
            if a.apply:
                save(lp, tomb, lfmt)
        k['revision'] = bump(k.get('revision'), 'minor'); k['revised_at'] = TODAY
        print('=====', g['cluster_id'], g['keeper'], '<-', g['losers'], '冲突字段', sum(len(x['fields']) for x in alts))
        for x in alts:
            for f in x['fields']:
                print('   改取被并值' if f.get('chosen') == 'loser' else '   保留 keeper 值', f['field'], '| 被并值', str(f['loser_value'])[:100].replace('\n', ' '))
        if a.apply:
            save(kp, k, kfmt)
        ledger.append({'cluster_id': g['cluster_id'], 'type': 'collection', 'keeper': g['keeper'], 'losers': g['losers'],
                       'evidence': g['evidence'], 'rule': g['rule'], 'by': a.by, 'at': TODAY, 'preconditions': pre,
                       'retained_alternatives': alts})
    notes, touched = [], collections.Counter()
    for p in referrers(list(mapping)):
        m, fmt = load(p)
        if m.get('id') in mapping:
            continue
        if fix_member(m, mapping, notes):
            touched[os.path.relpath(p, ROOT).split(os.sep)[0]] += 1
            m['revision'] = bump(m.get('revision'), 'patch'); m['revised_at'] = TODAY
            if a.apply:
                save(p, m, fmt)
    print('成员档改动', dict(touched), '；成员项属性冲突', len(notes))
    print('promotions 文件改动', fix_promotions(mapping, a.apply))
    if a.apply:
        base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
        for e in ledger:
            e['member_attr_conflicts'] = [n for n in notes if n['loser'] in e['losers']]
        json.dump({'base': base, 'merges': ledger}, open(os.path.join(os.path.dirname(os.path.abspath(a.batch)), 'merges.json'), 'w',
                  encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
