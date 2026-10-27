# 新-子目异名-子 第 1 批（158 组，并入 213 条）

基线 main `b7b84b137c`。`../mkbatch_zi.py ../clusters.json ../pairs_zi.tsv batch-01 --part 1/2`（前一半无冲突簇 168 簇，其中 10 簇已被他线并掉自动跳过），`../apply_zi.py batch.json --apply`，善后与门禁 `../post_zi.sh batch-01`；草稿库 3 处引用另开 PR 同步。
keeper：单行本优先，再取有撰人、indexed_by 多、资源多、id 早者。冲突字段保留 keeper 值，被并值记 `retained_alternatives`；被并者原 ai_note／description 记 `loser_original_notes`。
善后：被并者原有 `merged_in` 137 项补进 keeper；指向本批被并者的旧墓碑 139 个改指 keeper。

验证：check_v2（893 档）0；check-classification 0；audit-merge-ledger（--draft）T/L/P/R/D 全 0；check_promo_dup 0；check-duplicate-audit PASS；build_derived --check-only OK。
抽检：见 `../抽检/`，92 簇异质 1（青史子正编／續编混连，已修规则，本批该簇只并正编一条）。
回滚：revert 本 PR。
