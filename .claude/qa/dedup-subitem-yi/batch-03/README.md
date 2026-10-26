# 去重方案子目-乙-并：batch-03（B? 复核可并 35 簇）

基线 main `5e60d9a1`。口径、工具同 `../batch-01/README.md`：B? 档 56 对经子 agent 逐条复核（`../judged-Bq-复核.tsv`：可并 48、存疑 7〔含证据偏弱 3〕、异书 1）后取「B?可」对按对连通成簇，剔除一侧已被并者（前批已并者成墓碑自动跳过）；本批按 id 排序取 **35 簇，并入 35 条**。

- 生成：`../mkbatch_yi.py ../judged-Bq-复核.tsv <本目录> --levels B?可`；复核存疑 7 对、异书 1 对补登 `../../dedup-judged/子目-乙.tsv`（D／C）；实施：`../apply_yi.py batch.json --apply`，善后同第 1 批。
- 撰人善后（`postfix-authors.json`）：无。被并者独有的撰人人物见 `merges.json` 的 dropped_author_entities。

验证：audit-merge-ledger（--draft）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0；草稿库无引用；index 定点刷新。
抽检：整批版本独立子 agent 抽 40 簇，同书 40/40、并后数据 40/40 正确（#1435 评论）。

回滚：revert 本 PR。
