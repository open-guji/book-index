"""D：删源档 Work／Book 的 _has_text 与 _has_collated（改由 build --text-index 推）。
用法：d_drop_has.py [--apply]；默认干跑，只统计。
只删值为 true／false 的布尔旧键；其它形状（非布尔）不动并列出。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'build'))
import v2common as v

root = os.path.join(os.path.dirname(__file__), '..')
apply = '--apply' in sys.argv
recs, _, problems = v.load_repo(root, keep_raw=True)
assert not problems, problems[:3]
KEYS = ('_has_text', '_has_collated')
cnt = {}
files = set()
odd, nofmt = [], []
for typ in ('Work', 'Book', 'Collection', 'Entity'):
    for r in recs[typ].values():
        d = r.data
        ks = [k for k in KEYS if k in d]
        if not ks:
            continue
        if any(not isinstance(d[k], bool) for k in ks):
            odd.append((r.id, {k: d[k] for k in ks}))
            continue
        if r.fmt is None:
            nofmt.append(r.id)
            continue
        for k in ks:
            key = (typ, k, d[k])
            cnt[key] = cnt.get(key, 0) + 1
        files.add(r.path)
        if apply:
            for k in ks:
                del d[k]
            open(os.path.join(root, r.path), 'w', encoding='utf-8').write(v.dump(d, r.fmt))
for k in sorted(cnt):
    print(k, cnt[k])
print(f'文件 {len(files)}（{"已改" if apply else "待改"}）；非布尔 {len(odd)}；保格式失败 {len(nofmt)}')
for o in odd[:10]:
    print('非布尔', o)
