# 去重确认案实施：第 6 批：163 案收尾 7 组（含 book-text 迁移后的 4 组）

基线 main `1c18582af97647fb2098fe74b1cafec068f639b6`。依据：`/mnt/project-files/总目/去重研究/expanded-duplicate-audit-2026-10-22/` 确认案及各案证据；口径 `.claude/qa/正式库并条审查规则.md`（同题同责任者同朝代；异体字／别题经原题或志书互证）。
工具：`../apply_batch.py`（复用 mergework：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from 并 bump minor；升格表只改 production_id）、`../update_index.py`、`../fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`（同步到项目文件 总目/分类互斥/）。被并者独有的作者 entity 在台账 `dropped_author_entities`。

| 案 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| JC-001 | 周易繫辭謝萬注（謝萬） | 周易系辭（謝萬）、周易繫辭注（謝萬）、繫辭注（謝萬） | 3 | 0 |
| JC-007 | 周易王肅注（王肅） | 周易注（王肅）、周易王氏注（王肅）、王肅周易注（王肅）、周易注（王肅）、易注（王肅）、周易王子雍氏（王肅） | 16 | 4 |
| COL-R001 | 鳧藻集（高啟） | 鳬藻集（高啟）、高太史鳧藻集（高啟） | 0 | 1 |
| COL-R008 | 來鶴亭詩（呂誠） | 來鶴亭集（呂誠） | 1 | 1 |
| COL-R013 | 篔窗集（陳耆卿） | 篔窻集（陳耆卿） | 0 | 1 |
| H-H001 | 國語補音（宋庠） | 國語補音（—） | 0 | 0 |
| MR-H2000-005 | 三教平心論（劉謐） | 靜齋學士三教平心論（劉謐）、静齋學士三教平心論（劉謐） | 3 | 1 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup 全 0。回滚：revert 本 PR（及草稿库对应 PR）。

## 本批附带修正
- **前置**：book-text#241 已把 COL-R001／R008／R013、MR-H2000-005 被并条的转录本迁为 keeper 的第二版本，JC-007 辑佚档迁到 keeper，13 处整理本 work_id 改指 keeper。
- **MR-H2000-005 闭包**：研究提示的第三条 d59f6ekv7h1c（千頃堂「劉謐静齋學士三教平心論」二卷，同 entity hixhd2h9bh1y）一并并入；keeper 补 entity_id、改写含「靜同劉字十」污染的 description（原文在 `postfix-原值.json`）。
- **H-H001 污染修复**（`postfix.py`）：宋史藝文志「《國語補音》三卷林概」「《辨國語》三卷崔表」两条加 note 说明跨条断行（引文照录）；《辨國語》d59f2q0i5ds1 补撰人林概（暂无 entity，交去重方案部分 2）；Book 993fzgxdkw 的版本串接只加 ai_note 交部分 5。
- **JC-007**：keeper loss_status 由 lost 改 partially_extant（并入条载马国翰等辑本）。
- **163 案遗留**（`leftovers.py`）：PNA-2000-005、PRV-T008、PRV-H2000-002、PRV-H2000-004 四位 keeper 补回被并者的 description.sources（上图人物 URI，带 note 注来历）；MR-022～024 三个 Book 的 contained_in 草稿 Collection ID 按 promotions 换正式 ID 后去重；PRV-H2000-006 遗留：Work d59fxwb68a9t 撰人「釋實叉難陀」补挂 entity hixhd2h9bnrk。
- **工具**：`scripts/check-duplicate-audit.py` 原在 main 上报错（10-21 台账的 keeper d59fxunlrzeo 后在第 3 批被并），改为沿 merged_into 链走到活条再核。
