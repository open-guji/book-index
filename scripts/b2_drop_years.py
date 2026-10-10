"""B2：从 Entity 删 birth_year／death_year（读者已改读 dates，B1）。
用法：b2_drop_years.py [--apply]；默认干跑，只统计。
删前逐条核对：有其一的记录，其值须与 dates.birth／dates.death 全一致，否则不动并列出。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'build'))
import v2common as v

root = os.path.join(os.path.dirname(__file__), '..')
apply = '--apply' in sys.argv
recs, _, problems = v.load_repo(root, keep_raw=True)
assert not problems, problems[:3]
KEYS = (('birth_year', 'birth'), ('death_year', 'death'))
n_has = n_ok = n_bad = n_nofmt = 0
per_key = {'birth_year': 0, 'death_year': 0}
bad = []
for r in recs['Entity'].values():
    d = r.data
    ks = [k for k, _ in KEYS if k in d]
    if not ks:
        continue
    n_has += 1
    dates = d.get('dates') or {}
    if any(d[k] != dates.get(dk) for k, dk in KEYS if k in d):
        n_bad += 1
        bad.append((r.id, {k: d[k] for k in ks}, dates))
        continue
    if r.fmt is None:
        n_nofmt += 1
        continue
    n_ok += 1
    for k in ks:
        per_key[k] += 1
    if apply:
        for k in ks:
            del d[k]
        open(os.path.join(root, r.path), 'w', encoding='utf-8').write(v.dump(d, r.fmt))
print(f'有其一 {n_has}；与 dates 一致（{"已改" if apply else "待改"}）{n_ok}；不一致 {n_bad}；保格式失败 {n_nofmt}')
print('删键数', per_key)
for b in bad:
    print('不一致', b)
