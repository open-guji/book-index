#!/usr/bin/env python3
"""方志-并批次实施：复用 dedup-confirmed-163/apply_batch.py，只把署名改为方志-并。用法同 apply_batch：apply_fz.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案方志-并'
if __name__ == '__main__':
    apply_batch.main()
