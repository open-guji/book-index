#!/usr/bin/env python3
"""去重细拆单元 新-同姓异名余批次实施：复用 dedup-confirmed-163/apply_batch.py，只把署名改为 3b-0。
用法同 apply_batch：apply_3b0.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重同姓异名余'
if __name__ == '__main__':
    apply_batch.main()
