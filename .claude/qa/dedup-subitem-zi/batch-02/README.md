# 新-子目异名-子 第 2 批（161 组，并入 228 条）＋分立／存疑登记

基线 main `324af287e8`。`../mkbatch_zi.py ../clusters.json ../pairs_zi.tsv batch-02 --part 2/2`（后一半无冲突簇，已被他线并掉的自动跳过；首版与 main 撞 15 个文件，从新 main 整批重跑），`../apply_zi.py batch.json --apply`，善后与门禁 `../post_zi.sh batch-02`；草稿库 14 处引用另开 PR 同步。
登记：`../../dedup-judged/新-子目异名-子.tsv` 1,318 对（C 343、D 975），每组只登连通并后各簇所需最少对（`../mkjudged.py`）；冲突簇 27 簇的 A／B 边记 D。

验证：check_v2（822 档）0；check-classification 0；audit-merge-ledger（--draft）T/L/P/R/D 全 0；check_promo_dup 0；check-duplicate-audit PASS；build_derived --check-only OK。
回滚：revert 本 PR。
