#!/usr/bin/env python3
"""去重第二轮细拆「新-异人登记-子」并条：复用 dedup-confirmed-163/apply_batch.py，另加两步前置：
1. 预检：组内任一条已非活条（墓碑、缺檔）者整组剔出，写 skipped.json；
2. batch 中 add_author 为真的组，先把被并者的责任者（keeper 尚无同 entity／同名者）补进 keeper.authors，
   name_basis 注明自哪条补入——原著者与注者／辑者／译者／刊刻者分题同书时，并后不丢次要责任者。
用法：apply_yrz.py <batch.json> [--apply]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
from apply_batch import V, path_of, ROOT  # noqa: E402
apply_batch.BY = 'A11-去重异人登记子'

def live(i):
    try:
        p = os.path.join(ROOT, path_of('work', i))
    except AssertionError:
        return None
    d = json.load(open(p, encoding='utf-8'))
    return None if d.get('merged_into') or d.get('type') == 'tombstone' else (p, d)

def main():
    bp = sys.argv[1]; apply = '--apply' in sys.argv
    b = json.load(open(bp, encoding='utf-8'))
    keep, skip = [], []
    for g in b['groups']:
        recs = {i: live(i) for i in [g['keeper']] + g['losers']}
        (keep if all(recs.values()) else skip).append(g)
        if not all(recs.values()):
            g['skip_reason'] = '非活条：' + '、'.join(i for i, r in recs.items() if not r)
            continue
        if not g.get('add_author'):
            continue
        kp, k = recs[g['keeper']]
        have_e = {a.get('entity_id') for a in k.get('authors') or [] if a.get('entity_id')}
        have_n = {a.get('name') for a in k.get('authors') or []}
        add = []
        for l in g['losers']:
            for a in recs[l][1].get('authors') or []:
                if not a.get('name') or a.get('entity_id') in have_e or a.get('name') in have_n:
                    continue
                na = {x: a[x] for x in ('name', 'role', 'dynasty', 'entity_id') if a.get(x)}
                na['name_basis'] = f'去重「新-異人登記-子」{g["case_id"]}：同書異署，自被並條 {l} 補入'
                add.append(na); have_n.add(a['name'])
                if a.get('entity_id'): have_e.add(a['entity_id'])
        g['added_authors'] = add
        print(g['case_id'], g['keeper'], '補責任者', '、'.join(f"{a['name']}({a.get('role','')})" for a in add) or '（無）')
        if apply and add:
            k['authors'] = (k.get('authors') or []) + add
            raw = open(kp, encoding='utf-8').read()
            with open(kp, 'w', encoding='utf-8') as f:
                f.write(V.dump(k, V.detect_format(raw, k)))
    d = os.path.dirname(os.path.abspath(bp))
    json.dump({'groups': skip}, open(os.path.join(d, 'skipped.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({'groups': keep}, open(os.path.join(d, 'batch.run.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'组 {len(b["groups"])}，剔出 {len(skip)}，执行 {len(keep)}', file=sys.stderr)
    sys.argv = [sys.argv[0], os.path.join(d, 'batch.run.json')] + (['--apply'] if apply else [])
    apply_batch.main()
    mp = os.path.join(d, 'merges.json')
    if apply and os.path.exists(mp):
        m = json.load(open(mp, encoding='utf-8'))
        add = {g['cluster_id']: g.get('added_authors') for g in keep if g.get('added_authors')}
        for x in m['merges']:
            if x['cluster_id'] in add:
                x['added_authors'] = add[x['cluster_id']]
                ids = {a.get('entity_id') for a in add[x['cluster_id']]}
                x['dropped_author_entities'] = [e for e in x.get('dropped_author_entities') or [] if e.get('entity_id') not in ids]
        json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
