# 新-子目异名-集未 第 3 批（94 簇，并入 113 条；本单元末批）

基线 main `8fcd32d842`。判定表 `../judged-da710227.tsv` A／B 对连通成簇，剔除前两批已并与他线已并（墓碑自动跳过）后的全部余簇。

- 生成：`../mkbatch_zj.py ../judged-da710227.tsv batch-03 --levels A B`；实施：`../apply_zj.py batch.json --apply`；善后：`../../dedup-subitem/post.sh`（草稿库引用改指 5 处，见 book-index-draft 分支 dedup-zimu-ji-b3）。

验证：check_v2（378 档）0；check-classification 0；audit-merge-ledger T/L/P/R 0，D 5 为草稿库引用，已在草稿库 PR 改指；check_promo_dup 0；check-duplicate-audit PASS；build_derived 无 fatal。抽检见 `../README.md`。回滚：revert 本 PR（及草稿库 PR）。
