# 去重方案 3a-2丁：子集未分类·题名差一字·存疑复核批 d01（7 组，B 档）

基线 main `012a36a412fef6d84b3ff8a5868899f99c790477`。单元说明见 `../README.md`。
3a-2丁／3a-2乙 登记存疑对中，库内书目原文有括注互见（一名）或同实物重复著录、经判定员与独立复核员两道核查为同一部书同一层次者转并；判定登记同步改写（转并者删去，改 C 者改判，需先拆者加注）。
`gen_batch.py --rule B` 剔除已并、簇内有分立／存疑对（`../../dedup-judged/3a-2丁.tsv`）、已互链、合刻著录、多出他人责任者的簇。
工具：`../gen_batch.py`、`../apply.py`、`../../dedup-confirmed-163/postfix_common.py`、`update_index.py`、`fix_draft.py`（草稿库引用另开草稿库 PR）。

冲突字段一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类登记在 `分类互斥登记.tsv`。题名取 keeper 原题，不改题；被并题名进 keeper additional_titles。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 3a-2丁-d01-001 | 陶淵明集（陶潛） | 陶淵明文集（陶潛） | 1 | 0 |
| 3a-2丁-d01-002 | 秦隱君集（秦系） | 秦隱君詩（秦係） | 0 | 0 |
| 3a-2丁-d01-003 | 西湖竹枝集（楊維楨） | 西湖竹枝詞（楊維楨） | 2 | 0 |
| 3a-2丁-d01-004 | 山谷（黃庭堅） | 山谷集（黃庭堅） | 3 | 0 |
| 3a-2丁-d01-005 | 數書九章（秦九韶） | 數學九章（秦九韶） | 2 | 0 |
| 3a-2丁-d01-006 | 墨井畫跋（吳歷） | 墨井題跋（吳歷） | 0 | 0 |
| 3a-2丁-d01-007 | 春風堂隨筆（陸深） | 春雨堂隨筆（陸深） | 0 | 1 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
