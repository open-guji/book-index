#!/usr/bin/env python3
"""去重方案细拆单元 3b-近题前后缀（同 Entity 近题·增删前缀／后缀）批次实施：复用 dedup-confirmed-163/apply_batch.py，
只把署名改为 3b-近题前后缀。用法同 apply_batch：apply_3bjt.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案3b-近題前後綴'
if __name__ == '__main__':
    apply_batch.main()
