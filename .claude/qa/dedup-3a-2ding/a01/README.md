# 去重方案 3a-2丁：子集未分类·题名差一字·A7 国图异体线索批 a01（4 组，B 档）

基线 main `fd8f899d048a0edf61cfa3ff6a75fc1df5edfa20`。单元说明见 `../README.md`。
A7 资源挂接线（国图记录）转来的异体字同题线索（略／畧、稿／槁）：首位责任者为同一 entity、卷数相合或差异可解释者并；合刻、多出他人责任者、已互链、卷数悬殊的不并。
`gen_batch.py --rule B` 剔除已并、簇内有分立／存疑对（`../../dedup-judged/3a-2丁.tsv`）、已互链、合刻著录、多出他人责任者的簇。
工具：`../gen_batch.py`、`../apply.py`、`../../dedup-confirmed-163/postfix_common.py`、`update_index.py`、`fix_draft.py`（草稿库引用另开草稿库 PR）。

冲突字段一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类登记在 `分类互斥登记.tsv`。题名取 keeper 原题，不改题；被并题名进 keeper additional_titles。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 3a-2丁-a01-001 | 平臺紀略（藍鼎元） | 平臺紀畧（藍鼎元）、平臺紀畧（藍鼎元）、平臺紀畧（藍鼎元）、平臺紀畧（藍鼎元） | 0 | 0 |
| 3a-2丁-a01-002 | 粵東金石略（翁方綱） | 粵東金石畧（翁方綱） | 0 | 0 |
| 3a-2丁-a01-003 | 高要金石略（彭泰來） | 高要金石畧（彭泰來） | 0 | 0 |
| 3a-2丁-a01-004 | 耕祿稿（胡錡） | 耕祿槁（胡錡） | 2 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
