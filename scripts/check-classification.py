#!/usr/bin/env python3
"""分類檔校驗（與上線時 build_derived 同一套 load_classification，不另寫邏輯）。

查：節點存在且未 retired、成員檔名＝node、互斥分類法一部只出現一次（同一 Work 不得掛兩個互斥節點）。
data.yml 建包與 reindex-search 都在這一步之後才失敗過，所以提前到 PR。

    python3 scripts/check-classification.py [倉根]            # 有問題退出碼 1
    python3 scripts/check-classification.py [倉根] --warn-only  # 只報警（草稿庫用），恆退出 0
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build'))
import build_derived as B  # noqa: E402


def main(argv):
    warn = '--warn-only' in argv
    args = [a for a in argv if not a.startswith('--')]
    root = args[0] if args else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cls, problems, _ = B.load_classification(root)
    if cls is None:
        print(f'{root}: 無 classification/，跳過')
        return 0
    print(f'{root}: {len(cls)} 個 Work 有分類，問題 {len(problems)} 項')
    for p in problems:
        print(('::warning::' if warn else '::error::') + p)
    return 0 if warn or not problems else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
