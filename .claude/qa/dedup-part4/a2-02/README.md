# 去重方案部分 4：4a-α2 同 Entity 同题同名含叢書子目组 a2-02（9 组 10 条）

基线 main `c3cda02f183b7335766f6dd16d1cfeb94ca5581d`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-α 修订节）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**4a-α2 规则**（候选脚本 `../cand_alpha2.py`，输入为 3a／3b 交来的同 Entity 同题同名含子目组清单）：组内首位责任者同名同 Entity；每条子目所属叢書的首位撰者即本人、角色为撰；同一叢書下无两条同题子目；组内非子目 Work 至多 1 条（有则作 keeper，否则取 Book 最多、id 最早的子目）；全组已知卷数（含题下 title_info）须全同；两字以内泛名须全组卷数齐全且相同；朝代相容。不并的组登 `.claude/qa/dedup-judged/部分4-4aα2.tsv`（存疑）。

工具：`apply_4.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

善后提示：并后 keeper 下可能同时有 F 道「某某叢書本」Book 与叢書线子目 Book（同丛书不同著录），属部分 5 同 Work 同版本 Book，留给部分 5。

| 组 | 保留 | 并入条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
| 4a-d59fyh7dnh8h | 三史拾遺（錢大昕） | 1 | 0 | 0 |
| 4a-d59fyzb2z1mo | 參兩算經（汪萊） | 1 | 0 | 0 |
| 4a-d59fyzb1q3gh | 校正九章算術及戴氏訂訛（汪萊） | 1 | 0 | 0 |
| 4a-d59fryqj0qh5 | 桃花源（尤侗） | 1 | 0 | 0 |
| 4a-d59f2nuoaw3k | 蘇詩補注（翁方綱） | 1 | 0 | 0 |
| 4a-d59fyzb2z1mp | 覆載通幾附四邊形算法（汪萊） | 1 | 0 | 0 |
| 4a-d59f2mof7h1f | 詞話（毛奇齡） | 1 | 0 | 0 |
| 4a-d59f2nu74u80 | 讀書雜記（周鎬） | 1 | 0 | 0 |
| 4a-d59fsdx9sn45 | 黃陵詩鈔（杜俞） | 2 | 0 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
