#!/usr/bin/env python3
"""混记录拆分后整 Work 并 Work：复用 dedup-confirmed-163/apply_batch.py，
署名 A11-去重混记录拆分。用法同 apply_batch：apply_mix.py <batch.json> [--apply]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重混记录拆分'
if __name__ == '__main__':
    apply_batch.main()
