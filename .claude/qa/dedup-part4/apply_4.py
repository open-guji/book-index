#!/usr/bin/env python3
"""去重方案部分 4（Work 层·无责任者／弱证据）批次实施：复用 dedup-confirmed-163/apply_batch.py，
只把署名改为部分 4。用法同 apply_batch：apply_4.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案4'

# 提速：mergework.find 原用 Work/*/*/* 全目录 glob（每次约 1 秒），id 末三位即目录，先直查
import glob as _glob, mergework  # noqa: E402
_find = mergework.find
def _fast_find(typ, rid, root=None):
    r = root or mergework.ROOT
    if len(rid) >= 3:
        for pat in ('%s-*.json' % rid, '%s.json' % rid):
            for p in _glob.glob(os.path.join(r, typ, rid[-3], rid[-2], rid[-1], pat)):
                return p
    return _find(typ, rid, root)
mergework.find = _fast_find
if __name__ == '__main__':
    apply_batch.main()
