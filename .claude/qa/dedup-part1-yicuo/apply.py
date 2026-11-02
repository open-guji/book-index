#!/usr/bin/env python3
"""部分1 存疑核定：复用 apply_batch，署名 A11-去重方案部分1存疑核定。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重方案部分1存疑核定'
if __name__ == '__main__':
    apply_batch.main()
