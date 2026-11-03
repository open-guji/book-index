#!/usr/bin/env python3
"""从 build_derived.py 的产物目录抽出 works 索引要用的两个派生字段（overview#557）。
索引重建只读 `_classifications`、`_edition_count`；整份产物 1.2G／25 万文件，不搬，只搬这张小表。
（与 overview 的 scripts/web/derived-slim-extract.py 同一份；derive-slim.yml 在 GitHub 托管 runner 上用它。）
用法：derived_slim_extract.py <derived 目录> <输出 .json.gz>
输出 {id: [_classifications 或 null, _edition_count 或 null]}（两个字段都没有的条目不收）。"""
import gzip, json, os, sys

src, out = sys.argv[1], sys.argv[2]
d = os.path.join(src, 'entry')
m = {}
for name in os.listdir(d):
    if not name.endswith('.json'):
        continue
    with open(os.path.join(d, name), encoding='utf-8') as f:
        e = json.load(f)
    c, n = e.get('_classifications'), e.get('_edition_count')
    if c is None and n is None:
        continue
    m[name[:-5]] = [c, n]
with gzip.open(out, 'wt', encoding='utf-8') as f:
    json.dump(m, f, ensure_ascii=False, separators=(',', ':'))
print(f'抽出 {len(m)} 条 → {out}（{os.path.getsize(out)/1e6:.2f} MB）')
