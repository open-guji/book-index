#!/usr/bin/env python3
"""新-子目异名-子 批次实施：复用 dedup-confirmed-163/apply_batch.py，只把署名改为本单元。用法：apply_zi.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案子目异名子'
if __name__ == '__main__':
    apply_batch.main()
