#!/usr/bin/env python3
"""研-族谱 B 档（同一修族谱重复著录）批次实施：复用 dedup-confirmed-163/apply_batch.py，只改署名。
用法同 apply_batch：apply_zupu.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案研-族谱'
if __name__ == '__main__':
    apply_batch.main()
