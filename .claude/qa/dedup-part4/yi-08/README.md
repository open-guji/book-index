# 去重方案部分 4：4a-α乙 第 8 批：叢書子目并入同题单行本 Work（子集未分类）

基线 main `329cfc54c036a42eed41d8b3929aac905292c05e`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-α 修订节）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**4a-α 规则**（候选脚本 `../cand_alpha.py`）：同题组（`scripts/dedup-census.py` 口径：去括注、异体归一）里，无责任者一侧是叢書线（GUJI-526）新建的叢書子目 Work——《總目》叢書部獨撰類著录子目时不重复撰人，所以「無責任者」只是著录省略；其 Book 所属 Collection 的首位撰者（角色撰／撰輯／著等）与组内**唯一**一条有责任者 Work 的首位责任者同名、朝代相容；卷数相同、一侧缺或差≤1；单行本自身卷数不齐（差>1）的组跳过；同一叢書内有两条同题子目的组跳过（疑异篇）；有责任者多于 1 条的组留给 3a。子目 Work 并入单行本 Work，子目 Book 随之改挂。

工具：`apply_4.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

善后提示：并后 keeper 下可能同时有 F 道「某某叢書本」Book 与叢書线子目 Book（同丛书不同著录），属部分 5 同 Work 同版本 Book，留给部分 5。

| 组 | 保留（单行本） | 并入子目条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
| 4a-d59fymc30ow1 | 亭林餘集（顧炎武） | 2 | 0 | 0 |
| 4a-d59f2ntef08w | 樂府傳聲（徐大椿） | 3 | 0 | 0 |
| 4a-d59fy07f7thd | 武侯八陣兵法輯畧（汪宗沂） | 1 | 0 | 0 |
| 4a-d59f2nkvkuf6 | 涇皋藏稿（顧憲成） | 1 | 0 | 0 |
| 4a-d59fsgh2tam9 | 澤古齋文鈔（吳士模） | 1 | 0 | 0 |
| 4a-d59f2ngm02yr | 獪園（錢希言） | 1 | 0 | 0 |
| 4a-d59f2neumx34 | 竹懶畫媵（李日華） | 2 | 0 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
