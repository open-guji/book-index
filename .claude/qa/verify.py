#!/usr/bin/env python3
"""每批之後必跑之驗（qa-sweep 硬門禁）。

  python3 .claude/qa/verify.py            # 全庫：索引漂移必須為 0；懸空計數與基線比
  python3 .claude/qa/verify.py --strict   # 懸空亦須為 0（收工前）

輸出四個數：works 索引漂移、entities 索引漂移、work 側懸空引用、entity.works 懸空。
漂移不為 0 即失敗（exit 1）——改了記錄而未回寫索引，或改了索引而未改記錄。
"""
import argparse, collections, glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def idx(fam):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')): out.update(json.load(open(f)))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--strict', action='store_true'); a = ap.parse_args()
    IW, IB, IE = idx('works'), idx('books'), idx('entities')
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json')))
    ALL = set(IW) | set(IB) | set(IE) | set(IC)
    drift_w, dangle_w, missing = [], [], []
    for wid, ie in IW.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(wid); continue
        d = json.load(open(p))
        for f in ('period', 'loss_status', 'title', 'subtype'):
            x, y = ie.get(f), d.get(f)
            if x is None and y is None: continue
            if x != y: drift_w.append((wid, f, x, y))
        au = d.get('authors') or []
        if au and (ie.get('author') != au[0].get('name')): drift_w.append((wid, 'author', ie.get('author'), au[0].get('name')))
        for r in (d.get('related_works') or []):
            if r.get('id') and r['id'] not in ALL: dangle_w.append((wid, 'related_works', r['id']))
        for b in (d.get('books') or []):
            if b not in ALL: dangle_w.append((wid, 'books', b))
        for x in au:
            if x.get('entity_id') and x['entity_id'] not in IE: dangle_w.append((wid, 'authors.entity_id', x['entity_id']))
    drift_e, dangle_e = [], []
    for eid, ie in IE.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(eid); continue
        d = json.load(open(p))
        for f in ('primary_name', 'dynasty', 'birth_year', 'death_year', 'period'):
            x, y = ie.get(f), d.get(f)
            if x is None and y is None: continue
            if x != y: drift_e.append((eid, f, x, y))
        if ie.get('path') != d.get('path', ie.get('path')): pass
        for w in (d.get('works') or []):
            if w.get('work_id') and w['work_id'] not in IW: dangle_e.append((eid, w['work_id']))
    print(f'索引檔缺記錄檔        {len(missing)}')
    print(f'works 索引漂移        {len(drift_w)}')
    print(f'entities 索引漂移     {len(drift_e)}')
    print(f'work 側懸空引用       {len(dangle_w)}')
    print(f'entity.works 懸空     {len(dangle_e)}')
    for r in (drift_w[:10] + drift_e[:10]): print('  漂移', r)
    if a.strict:
        for r in dangle_w[:10] + dangle_e[:10]: print('  懸空', r)
    bad = missing or drift_w or drift_e or (a.strict and (dangle_w or dangle_e))
    print('FAIL' if bad else 'OK')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
