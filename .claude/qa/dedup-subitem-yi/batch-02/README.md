# 去重方案子目-乙-并：batch-02（A／B 档 88 簇）

基线 main `f6c53dcc`。口径、工具同 `../batch-01/README.md`：判定表 `../judged-07fc66fc.tsv` 的 A／B 对按对连通成簇，剔除一侧已被并者（前批已并者成墓碑自动跳过）；本批按 id 排序取 **88 簇，并入 101 条**。

- 生成：`../mkbatch_yi.py ../judged-07fc66fc.tsv <本目录> --levels A B --keeper d59fy1cvlc00 d59fyh7uiaki d59fyh7zi39d --first 100`；实施：`../apply_yi.py batch.json --apply`，善后同第 1 批。
- 撰人善后（`postfix-authors.json`）：陳宏謀＝陳弘謀（避諱改字），補被并者所挂 entity_id；被并者著錄「（仲景診皮法、楊氏太素論診皮）廖宗濬纂輯」，補為次位責任者。被并者独有的撰人人物见 `merges.json` 的 dropped_author_entities。

验证：audit-merge-ledger（--draft）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0；草稿库无引用；index 定点刷新。
抽检：整批版本独立子 agent 抽 40 簇，同书 40/40、并后数据 40/40 正确（#1435 评论）。

回滚：revert 本 PR。
