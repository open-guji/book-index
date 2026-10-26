#!/usr/bin/env python3
"""去重方案子目-甲（同名叢書不同版次子目 Work 互并）批次实施：复用 dedup-confirmed-163/apply_batch.py，
只把署名改为子目-甲。用法同 apply_batch：apply_sub.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案子目甲'
if __name__ == '__main__':
    apply_batch.main()
