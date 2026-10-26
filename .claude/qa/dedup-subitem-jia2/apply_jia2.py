#!/usr/bin/env python3
"""去重细拆单元子目-甲2（同名丛书异版次子目 Work 互并·子集未分类）批次实施：复用 dedup-confirmed-163/apply_batch.py，
只把署名改为子目-甲2。用法同 apply_batch：apply_jia2.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重子目甲2'
if __name__ == '__main__':
    apply_batch.main()
