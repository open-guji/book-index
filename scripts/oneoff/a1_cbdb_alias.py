#!/usr/bin/env python3
"""A1（overview#508）：Entity 的 external_ids 旧键机械改名。

- `cbdb_aliases` 改名为 `cbdb_id_alt`（值不变，键序不变）；
- 删除 `cbdb_aliases_note`；
- 已经带 `cbdb_id_alt` 的文件不动（计入 conflict，要人看）。

读写走 build/v2common.py 的保格式函数（detect_format／dump），不改缩进和键序，
不改 revision／revised_at、不改文件名、不改 id。

用法（仓根目录）：
    python3 scripts/oneoff/a1_cbdb_alias.py --dry-run   # 只统计
    python3 scripts/oneoff/a1_cbdb_alias.py             # 真跑
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'build'))
import v2common as V  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.join(HERE, '..', '..'))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    files = renamed = dropped = conflict = bad_fmt = 0
    for p in sorted(V.iter_json(root, 'Entity')):
        if not V.is_record_path(root, p):
            continue
        raw = open(p, encoding='utf-8').read()
        d = json.loads(raw)
        ext = d.get('external_ids')
        if not isinstance(ext, dict) or 'cbdb_aliases' not in ext:
            continue
        rel = os.path.relpath(p, root)
        if 'cbdb_id_alt' in ext:
            conflict += 1
            print('CONFLICT（已有 cbdb_id_alt，未动）', rel)
            continue
        fmt = V.detect_format(raw, d)
        if fmt is None:
            bad_fmt += 1
            print('SKIP（无法保格式回写）', rel)
            continue
        new_ext = {}
        for k, v in ext.items():
            if k == 'cbdb_aliases':
                new_ext['cbdb_id_alt'] = v
                renamed += 1
            elif k == 'cbdb_aliases_note':
                dropped += 1
            else:
                new_ext[k] = v
        d['external_ids'] = new_ext
        files += 1
        if not a.dry_run:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(V.dump(d, fmt))

    mode = 'DRY-RUN' if a.dry_run else 'WRITE'
    print(f'[{mode}] 文件 {files}；改名 cbdb_aliases→cbdb_id_alt {renamed} 键；删 cbdb_aliases_note {dropped} 键；'
          f'冲突未动 {conflict}；保格式失败 {bad_fmt}')
    return 1 if (conflict or bad_fmt) else 0


if __name__ == '__main__':
    sys.exit(main())
