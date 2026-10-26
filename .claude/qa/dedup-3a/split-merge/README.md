# 去重方案部分 3a：拆混记录后复核并 3 组

基线 main `7faafda5ac54f90dfcb594988015e51a774edf16`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/00-通用口径与门禁.md` Work 节 A 档（题名归一后相同——简繁、异体、去括注、去「新刊／新刻／重刊／欽定」等坊刻套语；首位责任者同名、朝代兼容、卷数差≤1 或一侧缺、著作领域不冲突），`.claude/qa/正式库并条审查规则.md`。
候选由全库扫描生成：同题同首位责任者组，剔除已互链（已判分立）、朝代相差≥2、首位责任者 entity 不同、卷数悬殊、增订／重订本、次要责任者或角色不同、题名尾有附刻他书、描述撰人不符等，余者逐组人工过目后入批。
工具：`../dedup-confirmed-163/apply_batch.py`（经 `apply_3a.py` 调用；复用 mergework：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from 并 bump minor；升格表只改 production_id）、`postfix_common.py`、`update_index.py`、`fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`。被并者独有的作者 entity 在台账 `dropped_author_entities`（同名者已由 postfix_common 补到 keeper）。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 3a-G0518 | 易章句（吕大臨） | 易章句（呂大臨） | 1 | 0 |
| 3a-G0534 | 今水經一卷表一卷（黃宗羲） | 今水經（黃宗羲） | 1 | 1 |
| 3a-G0715 | 蓮鬚閣集（黎遂球） | 蓮鬚閣集（黎遂球） | 0 | 1 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
