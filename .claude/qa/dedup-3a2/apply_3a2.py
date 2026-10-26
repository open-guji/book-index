#!/usr/bin/env python3
"""去重方案细拆单元 3a-2甲（近题·增删前缀／后缀，首位责任者相同）批次实施：复用 dedup-confirmed-163/apply_batch.py，
只把署名改为 3a-2甲。用法同 apply_batch：apply_3a2.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案3a-2甲'
if __name__ == '__main__':
    apply_batch.main()
