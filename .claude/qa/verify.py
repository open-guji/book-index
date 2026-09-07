#!/usr/bin/env python3
"""每批之後必跑之驗（qa-sweep 硬門禁）。

  python3 .claude/qa/verify.py            # 全庫：索引漂移必須為 0；懸空計數與基線比
  python3 .claude/qa/verify.py --strict   # 懸空亦須為 0（收工前）

輸出五個數：works 索引漂移（period/loss_status/title/subtype/author/dynasty/role；dynasty 取頂層，無則 authors[0]）、
entities 索引漂移、work 側懸空引用、entity.works 懸空、單向邊（人指書而書不指人）。
漂移不為 0 即失敗（exit 1）——改了記錄而未回寫索引，或改了索引而未改記錄。
"""
import argparse, collections, glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def idx(fam):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')): out.update(json.load(open(f)))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--why', action='store_true', help='「索引缺記錄檔」時印出各 id 之最後刪除提交（坑 41）')
    ap.add_argument('--strict', action='store_true'); a = ap.parse_args()
    IW, IB, IE = idx('works'), idx('books'), idx('entities')
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json')))
    ALL = set(IW) | set(IB) | set(IE) | set(IC)
    drift_w, dangle_w, missing, back = [], [], [], {}
    for wid, ie in IW.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): missing.append(wid); continue
        d = json.load(open(p))
        for f in ('period', 'loss_status', 'title', 'subtype'):
            x, y = ie.get(f), d.get(f)
            if x is None and y is None: continue
            if x != y: drift_w.append((wid, f, x, y))
        au = d.get('authors') or []; a0 = au[0] if au else {}
        nz = lambda v: None if v in ('', None) else v
        want = {'author': nz(a0.get('name')), 'role': nz(a0.get('role')),
                'dynasty': nz(d.get('dynasty')) if nz(d.get('dynasty')) is not None else nz(a0.get('dynasty'))}
        for f, y in want.items():
            if nz(ie.get(f)) != y: drift_w.append((wid, f, ie.get(f), y))
        for r in (d.get('related_works') or []):
            if r.get('id') and r['id'] not in ALL: dangle_w.append((wid, 'related_works', r['id']))
        for b in (d.get('books') or []):
            if b not in ALL: dangle_w.append((wid, 'books', b))
        back[wid] = {x.get('entity_id') for x in au if x.get('entity_id')}
        for x in au:
            if x.get('entity_id') and x['entity_id'] not in IE: dangle_w.append((wid, 'authors.entity_id', x['entity_id']))
    drift_e, dangle_e, fwd = [], [], {}
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
            elif w.get('work_id'): fwd.setdefault(eid, set()).add(w['work_id'])
    oneway = [(e, w) for e, ws in fwd.items() for w in ws if e not in back.get(w, set())]
    print(f'索引檔缺記錄檔        {len(missing)}')
    print(f'works 索引漂移        {len(drift_w)}')
    print(f'entities 索引漂移     {len(drift_e)}')
    print(f'work 側懸空引用       {len(dangle_w)}')
    print(f'entity.works 懸空     {len(dangle_e)}')
    print(f'單向邊 人指書書不指人 {len(oneway)}')
    for r in (drift_w[:10] + drift_e[:10]): print('  漂移', r)
    if missing and a.why:
        # 「索引缺記錄檔」多半是併條刪檔而未清索引（坑 41）。逕查該 id 之最後刪除提交，
        # 各道遂能自判「是我的批次沒清乾淨」抑或「別人的病，該報協調者」。
        import subprocess
        print('  ── 缺檔之由（--why）──')
        for wid in missing[:20]:
            c = subprocess.run(['git', '-c', 'core.quotePath=false', 'log', '--all',
                                '--diff-filter=D', '--format=%h %an %s', '-1',
                                '--', f'Work/*/*/*/{wid}-*.json'],
                               capture_output=True, text=True).stdout.strip()
            print(f'  {wid}  {c or "（未見刪除提交——檔名或曾改，先查索引 path 是否過時）"}')
        if len(missing) > 20: print(f'  …另有 {len(missing)-20} 條')
    if a.strict:
        for r in dangle_w[:10] + dangle_e[:10]: print('  懸空', r)
        for r in oneway[:10]: print('  單向', r)
    bad = missing or drift_w or drift_e or (a.strict and (dangle_w or dangle_e or oneway))
    print('FAIL' if bad else 'OK')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
