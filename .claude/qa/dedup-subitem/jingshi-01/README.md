# 去重方案子目-甲：經史第 1 批（样本 20 组）

基线 main `aaa3e9aa05a38fdc01b4310eb8afc9dbc30546cf`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/细拆-并行单元-20261025.md` 子目-甲行与 `00-通用口径与门禁.md` Work 节 A 档，`.claude/qa/正式库并条审查规则.md`。
叢書线（GUJI-526）按《中國古籍總目》每条丛书版本记录各建子目 Work，于是同一子目在同一丛书的不同版次（各自一个 Collection）里被建成多条同题 Work。本批把它们并成一条。
候选（`cand_sub.py`）：同题组里，所属丛书题名去卷种数后相同的叢書子目 Work 成簇；簇内各条所挂 Collection 互不相同（同一 Collection 内同题两条疑为异篇，不并，登记 D）；Collection 实际题名归一后一致；子目自身首位责任者至多一个、朝代相容；卷数（Work／Book juan_count、title_info 首个卷数）全等或缺。跳过部分 4 的 4a-α 清单里的 Work id（那些由 4a-α 并入同作者单行本）。keeper 取 Book 多者、有责任者者、id 早者。存疑对见 `../dedup-judged/子目-甲1.tsv`。
工具：`apply_sub.py`（包装 `../dedup-confirmed-163/apply_batch.py`：著录并入、Book 改挂、引用与分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from；升格表只改 production_id）、`../dedup-confirmed-163/postfix_common.py`、`update_index.py`、`fix_draft.py`。

冲突字段一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note（含所屬叢書記錄、源記錄）存台账 `loser_original_notes`；分类互斥登记在 `分类互斥登记.tsv`。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| sub-d59fyz9qwhz4 | 一齋陳先生考終錄（—） | 一齋陳先生考終錄（—） | 0 | 0 |
| sub-d59fy84r1yiq | 三國志辨誤（—） | 三國志辨誤（—）、三國志辨誤（—） | 0 | 0 |
| sub-d59fy855q41s | 三國志辨誤（—） | 三國志辨誤（—） | 0 | 0 |
| sub-d59fyn4a4fep | 三國志辨誤（—） | 三國志辨誤（—）、三國志辨誤（—）、三國志辨誤（—） | 0 | 0 |
| sub-d59fysibzgg1 | 三國志辨誤（—） | 三國志辨誤（—）、三國志辨誤（—）、三國志辨誤（—）、三國志辨誤（—） | 0 | 0 |
| sub-d59fz13n7lz4 | 三墳（—） | 三墳（—）、三墳（—） | 0 | 0 |
| sub-d59fz147i1a8 | 三墳（—） | 三墳（—） | 0 | 0 |
| sub-d59fyfcdornk | 三墳書（—） | 三墳書（—） | 0 | 0 |
| sub-d59fyjrw9lhd | 三字石經尚書（—） | 三字石經尚書（—）、三字石經尚書（—）、三字石經尚書（—）、三字石經尚書（—） | 0 | 0 |
| sub-d59fxpm7yl8h | 三家詩拾遺（—） | 三家詩拾遺（—）、三家詩拾遺（—） | 0 | 0 |
| sub-d59fy5optj41 | 三朝野史（—） | 三朝野史（—） | 0 | 0 |
| sub-d59fynz1mept | 三朝野史（—） | 三朝野史（—）、三朝野史（—）、三朝野史（—） | 0 | 0 |
| sub-d59fyoocgvsw | 三洲遊記（—） | 三洲遊記（—） | 0 | 0 |
| sub-d59fyx12zo5c | 三禮義證（—） | 三禮義證（—） | 0 | 0 |
| sub-d59fyfcmqnep | 三秦記（—） | 三秦記（—） | 0 | 0 |
| sub-d59fyjs5mps0 | 三蒼（—） | 三蒼（—）、三蒼（—）、三蒼（—）、三蒼（—） | 0 | 0 |
| sub-d59fy03b99fk | 三輔黃圖（—） | 三輔黃圖（—） | 0 | 0 |
| sub-d59fyfbsgmpt | 三輔黃圖（—） | 三輔黃圖（—）、三輔黃圖（—） | 0 | 0 |
| sub-d59fyfe3t05d | 三輔黃圖（—） | 三輔黃圖（—）、三輔黃圖（—） | 0 | 0 |
| sub-d59fylju1j42 | 三輔黃圖（—） | 三輔黃圖（—） | 0 | 0 |

验证：audit-merge-ledger（--draft）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
