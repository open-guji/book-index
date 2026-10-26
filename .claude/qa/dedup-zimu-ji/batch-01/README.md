# 新-子目异名-集未 第 1 批（190 簇，并入 240 条）

基线 main `425cff5d8d`。判定表 `../judged-da710227.tsv` A／B 对按对连通成簇，按 id 排序取前 190 簇。

- 生成：`../mkbatch_zj.py ../judged-da710227.tsv batch-01 --levels A B --first 190`；实施：`../apply_zj.py batch.json --apply`（被并者留墓碑，著录并入、Book 改挂、引用改指，冲突字段留 keeper 值、被并值记 retained_alternatives，原 ai_note／description 记 loser_original_notes）。
- 善后：`../../dedup-subitem/post.sh`（postfix_common 39 处、index 定点刷新＋强制重算 34、草稿库引用改指 12 处，见 book-index-draft 分支 dedup-zimu-ji-b1）。

验证：check_v2（868 档）0；check-classification 0；audit-merge-ledger T/L/P/R 0，D 12 为草稿库引用，已在草稿库 PR 改指；check_promo_dup 0；check-duplicate-audit PASS；build_derived --check-only 无 fatal。
抽检见 `../README.md`。回滚：revert 本 PR（及草稿库 PR）。
