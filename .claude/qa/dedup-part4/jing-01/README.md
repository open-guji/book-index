# 去重方案部分 4：4a-α 經部第 1 批（样本 20 组）

基线 main `3c74b458683fdde4028b6b8d4e8b4d990b9c35a1`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-α 修订节）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**4a-α 规则**（候选脚本 `../cand_alpha.py`）：同题组（`scripts/dedup-census.py` 口径：去括注、异体归一）里，无责任者一侧是叢書线（GUJI-526）新建的叢書子目 Work——《總目》叢書部獨撰類著录子目时不重复撰人，所以「無責任者」只是著录省略；其 Book 所属 Collection 的首位撰者（角色撰／撰輯／著等）与组内**唯一**一条有责任者 Work 的首位责任者同名、朝代相容；卷数相同、一侧缺或差≤1；单行本自身卷数不齐（差>1）的组跳过；同一叢書内有两条同题子目的组跳过（疑异篇）；有责任者多于 1 条的组留给 3a。子目 Work 并入单行本 Work，子目 Book 随之改挂。

工具：`apply_4.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

善后提示：并后 keeper 下可能同时有 F 道「某某叢書本」Book 与叢書线子目 Book（同丛书不同著录），属部分 5 同 Work 同版本 Book，留给部分 5。

| 组 | 保留（单行本） | 并入子目条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
| 4a-d59fxs6m7dvl | 七月漫錄（郭柏蒼） | 1 | 0 | 0 |
| 4a-d59fxvkq6fwi | 七緯拾遺（顧觀光） | 1 | 0 | 0 |
| 4a-d59fxx7s7rpd | 三綱制服尊尊述義（夏炘） | 3 | 0 | 0 |
| 4a-d59fxs6ngc1s | 三頌備說（張承華） | 1 | 0 | 0 |
| 4a-d59fxvk4n2f4 | 中候儀明（喬松年） | 1 | 0 | 0 |
| 4a-d59fxvk4btvm | 中候苗興（喬松年） | 1 | 0 | 0 |
| 4a-d59fxvk4n2f5 | 中候運衡（喬松年） | 1 | 0 | 0 |
| 4a-d59fxu0egv7m | 中庸俟（陳世鎔） | 1 | 0 | 0 |
| 4a-d59f2nd8w0lc | 中庸凡（崔銑） | 2 | 0 | 0 |
| 4a-d59fxu0ca7eo | 中庸古本述註（姜國伊） | 1 | 0 | 0 |
| 4a-d59f2nicfk00 | 中庸外傳（顧起元） | 1 | 0 | 0 |
| 4a-d59fxw2a9zwh | 中庸旨說（程智） | 1 | 0 | 0 |
| 4a-d59fxw29yrcy | 中庸正說（趙南星） | 2 | 0 | 0 |
| 4a-d59fxu0gnj0i | 中庸直解（許衡） | 3 | 0 | 0 |
| 4a-d59fxu0es3r4 | 中庸私解（徐潤第） | 2 | 0 | 0 |
| 4a-d59f2molg7wh | 中庸章段（李光地） | 2 | 0 | 0 |
| 4a-d59fxu0dj5kw | 中庸節訓（呂調陽） | 2 | 0 | 0 |
| 4a-d59fxu0hl8n4 | 中庸總說（王又樸） | 1 | 0 | 0 |
| 4a-d59fxu0e5mo1 | 中庸述義續（單爲鏓） | 1 | 0 | 0 |
| 4a-d59fxu0due4h | 中庸釋（郭階） | 1 | 0 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
