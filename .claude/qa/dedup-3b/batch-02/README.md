# 去重细拆单元 3b：重扫（2.2续-丙、2.3 收口后新挂 Entity 的作者位，2 组）

基线 main `22cd9ed32eb0690529426bd252936724c7b77aef`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/00-通用口径与门禁.md` Work 节 B 档、`部分3-Work层有责任者.md` 3b（以作者 Entity 为键的署名异写），`.claude/qa/正式库并条审查规则.md`。
候选由 `scan.py` 生成：首位撰人已繫同一 Entity、题名归一后相同而署名写法不同（避讳改字、异体、名／字號、帝号、法名）的 Work 组；剔除已互链、已登 dedup-judged 者，及叢書子目（归 3a 第二轮／4a-α）。同一 Entity 只作线索，每组另核原文题名、卷数、版本，逐对判定见 `判定.tsv`（S 并、D 存疑、X 分立），再由独立子 agent 只读原文逐条核验。规范名、keeper 由 `mkbatch.py`。
工具：`apply_3b.py`（包 `../dedup-confirmed-163/apply_batch.py`：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`../dedup-confirmed-163/postfix_common.py`、`postfix_3b.py`（keeper 撰人补繫 entity；被并条的署名异写形补进该 Entity 的 alt_names，type 取 訛名／異體／避諱／別稱，泛称、误切、省称不补；原值存 `postfix_3b-原值.json`）、`update_index.py`、`fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`。判为分立／存疑的对登记在 `../dedup-judged/3b.tsv`。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 3b-064 | 佛說希有校量功德經（闍那崛多） | 佛說希有挍量功德經（釋闍那崛多） | 0 | 1 |
| 3b-065 | 金丹秘㫖（張三丰） | 金丹祕旨（張三豐） | 2 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
