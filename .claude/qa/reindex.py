#!/usr/bin/env python3
"""以記錄檔為真，回寫索引之漂移欄（協調者與各道合流撞衝突時用）。
  python3 .claude/qa/reindex.py            # 乾跑，只列
  python3 .claude/qa/reindex.py --run
索引 works 分片之欄與記錄之對應：
  period/loss_status/title/subtype ← 同名頂層欄
  author ← authors[0].name   role ← authors[0].role
  dynasty ← 頂層 dynasty，無則 authors[0].dynasty（空字串視同無）
索引 entities 分片：primary_name/dynasty/birth_year/death_year/period ← 同名頂層欄
"""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import jio
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
def nz(v): return None if v in ('', None) else v
def expect_work(d):
    au = d.get('authors') or []; a0 = au[0] if au else {}
    return {'period': nz(d.get('period')), 'loss_status': nz(d.get('loss_status')), 'title': d.get('title'),
            'subtype': nz(d.get('subtype')), 'author': nz(a0.get('name')), 'role': nz(a0.get('role')),
            'dynasty': nz(d.get('dynasty')) if nz(d.get('dynasty')) is not None else nz(a0.get('dynasty'))}
def expect_ent(d):
    return {k: nz(d.get(k)) for k in ('primary_name', 'dynasty', 'birth_year', 'death_year', 'period')}
def main():
    run = '--run' in sys.argv; n = 0
    for fam, exp in (('works', expect_work), ('entities', expect_ent)):
        for f in sorted(glob.glob(os.path.join(ROOT, 'index', fam, '*.json'))):
            rel = os.path.relpath(f, ROOT); idx, fmt = jio.load(rel); ch = False
            for k, ie in idx.items():
                p = os.path.join(ROOT, ie['path'])
                if not os.path.exists(p): continue
                want = exp(json.load(open(p)))
                for fld, v in want.items():
                    if nz(ie.get(fld)) != v:
                        n += 1; print(f'[{fam}] {k} {fld}: {ie.get(fld)!r} -> {v!r}')
                        if v is None: ie.pop(fld, None)
                        else: ie[fld] = v
                        ch = True
            if ch and run: jio.save(rel, idx, fmt)
    print(('回寫' if run else '待回寫'), n)
if __name__ == '__main__': main()
