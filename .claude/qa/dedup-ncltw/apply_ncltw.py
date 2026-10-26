#!/usr/bin/env python3
"""台湾国图挂接线索同题多 Work 核并批次实施：复用 dedup-confirmed-163/apply_batch.py，
只把署名改为台湾国图线索。用法同 apply_batch：apply_ncltw.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A4串-去重台湾国图线索'
if __name__ == '__main__':
    apply_batch.main()
