#!/usr/bin/env python3
"""去重方案细拆单元 3a-2丙（差一字·經史）批次实施：复用 dedup-confirmed-163/apply_batch.py，只改署名。
用法同 apply_batch：apply_3a2c.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案3a-2丙'
if __name__ == '__main__':
    apply_batch.main()
