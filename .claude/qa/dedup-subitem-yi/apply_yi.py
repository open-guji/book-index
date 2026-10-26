#!/usr/bin/env python3
"""子目-乙-并（跨丛书同题子目 Work 互并）批次实施：复用 dedup-confirmed-163/apply_batch.py，只把署名改为子目-乙。
用法同 apply_batch：apply_yi.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案子目乙'
if __name__ == '__main__':
    apply_batch.main()
