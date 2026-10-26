#!/usr/bin/env python3
"""去重细拆「上图-并」（上图／总目同一 work 对多条正式库 Work）批次实施：复用 dedup-confirmed-163/apply_batch.py，
只把署名改为上图-并。用法同 apply_batch：apply_shlib.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重上图-并'
if __name__ == '__main__':
    apply_batch.main()
