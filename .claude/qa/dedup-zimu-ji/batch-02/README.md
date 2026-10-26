# 新-子目异名-集未 第 2 批（100 簇，并入 114 条）

基线 main `098d183a9e`。判定表 `../judged-da710227.tsv`（子目-乙-并已收口，原先让出的 31 对放回；一侧已被他线并成墓碑者自动跳过）A／B 对连通成簇，按 id 排序取前 100 簇（含第 1 批撤出的 7 簇）。

- 生成：`../mkbatch_zj.py ../judged-da710227.tsv batch-02 --levels A B --first 100`；实施：`../apply_zj.py batch.json --apply`；善后：`../../dedup-subitem/post.sh`（草稿库引用改指 1 处，见 book-index-draft 分支 dedup-zimu-ji-b2）。

验证：check_v2（368 档）0；check-classification 0；audit-merge-ledger T/L/P/R 0，D 1 为草稿库引用，已在草稿库 PR 改指；check_promo_dup 0；check-duplicate-audit PASS；build_derived 无 fatal。抽检见 `../README.md`。回滚：revert 本 PR（及草稿库 PR）。
