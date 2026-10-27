#!/usr/bin/env python3
"""新-子目异名（含叢書子目、丛书异名或对单行本的同题组）批次实施：复用 dedup-confirmed-163/apply_batch.py，只把署名改为子目异名。
用法同 apply_batch：apply_yiming.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案子目异名'
if __name__ == '__main__':
    apply_batch.main()
