# 去重方案部分 4：卷数不同的单边对 d-01（6 组 6 条）

基线 main `07b1f5257b3c5988ff5a943089993153063e8bbe`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-α 修订节）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**本批规则**：4a-B 全集中同题、一侧有一侧无、卷数不同的单边对（排除族谱方志、敦煌、已判），按最新 main 复算余 262 对，分 8 份子 agent 逐对读原文判定。卷数不同时须有著录原文解释差异（原书与今本／残本／分卷不同），推断不算；同时须有同源、版本馆藏、自证等实质证据。首轮同书 11 对；本串逐条复看：原书史志条对玉函山房辑本 3 对改存疑（原书与辑本不并）；无责任者一侧挂有全文的 2 对暂不并（不能退为墓碑，反向又会丢作者）；`--strict` 复查无剔。落 6 组。分立／存疑 256 对登 `.claude/qa/dedup-judged/部分4-卷异.tsv`。


工具：`apply_4.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

| 组 | 保留 | 并入条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
| 4aB-d59fz72njoxt | 律（孫奭） | 1 | 2 | 1 |
| 4aB-d59f2hj2fgu9 | 桐陰舊話（韓元吉） | 1 | 2 | 1 |
| 4aB-d59f2mcfi9s0 | 談往（花村看行侍者） | 1 | 0 | 1 |
| 4aB-d59f9s1m0qo6 | 大方等陀羅尼經（釋法眾） | 1 | 1 | 0 |
| 4aB-d59f23nsclqd | 太平經（襄楷） | 1 | 0 | 1 |
| 4aB-d59f2n8s4ohs | 書傳補義（方宗誠） | 1 | 2 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。逐簇子 agent 核，另起独立子 agent 复核约 30%，抽检见 `抽检.md`。回滚：revert 本 PR。
