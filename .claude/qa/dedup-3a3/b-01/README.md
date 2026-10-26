# 去重方案 3a-3（一名／又名自证异题同书）：样本 20 组

基线 main `112dfbc5baf0435cde29e9a915516cabaa105b94`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/00-通用口径与门禁.md` Work 节 B 档（异题名同书须有原文自证：总目著录互见「一名／又名／原名／即」、或总目题名括注的其他题名与另一条题名、作者、卷数、内容都对上），`.claude/qa/正式库并条审查规则.md`。
候选由 `scan_alias.py` 全库扫描、`clean.py` 机械清洗（剔除首位责任者不同、原书对注疏本、「即」字句主语非本书、本库自动录入说明等），余者两道子 agent 独立逐条复核（第一道判对，第二道判簇），两道都判同、且无「著录混入他书／辑佚本／增订改编本」之嫌的才入批；`build_batch.py` 连簇出批。
工具：`../dedup-confirmed-163/apply_batch.py`（经 `apply_3a3.py` 调用；复用 mergework：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from 并 bump minor；升格表只改 production_id）、`postfix_common.py`、`update_index.py`、`fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`。被并者独有的作者 entity 在台账 `dropped_author_entities`（同名者已由 postfix_common 补到 keeper）。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 3a3-d59fajc7ttdt | 射覆經（東方朔） | 射覆經東方朔撰（東方朔） | 2 | 0 |
| 3a3-d59f28m65t6u | 唐朝名畫錄（朱景元） | 唐朝畫斷（—） | 0 | 0 |
| 3a3-d59f2hs1i32a | 安晚堂集（鄭清之） | 安晚堂詩集（鄭清之） | 2 | 0 |
| 3a3-d59f2huwiebm | 盧溪集（王庭珪） | 盧溪文集（王庭珪） | 0 | 1 |
| 3a3-d59f2j4ipw5d | 元秘史（—） | 元祕史（—） | 0 | 0 |
| 3a3-d59f2na2bsw2 | 孝經述注（丁晏） | 孝經述註（丁晏） | 0 | 0 |
| 3a3-d59f2njjiarm | 四書蒙引（蔡清） | 新刊舉業精義四書蒙引（蔡清） | 0 | 1 |
| 3a3-d59f2njmbfnk | 見素文集（林俊） | 見素集（林俊） | 2 | 0 |
| 3a3-d59f2njrmgw0 | 古音略例（楊慎） | 古音畧例（佚名） | 0 | 1 |
| 3a3-d59f2nky2qkg | 莊渠遺書（魏校） | 莊渠先生文集（魏校） | 0 | 1 |
| 3a3-d59fsg3wz211 | 于濆詩集（于濆） | 晚唐于濆詩（于濆） | 0 | 1 |
| 3a3-d59fxra5iw3k | 古文孝經直解（朱鴻） | 古文直解（朱鴻） | 0 | 0 |
| 3a3-d59fxru5yi2q | 宋文憲公集（宋濂） | 宋文憲先生集選（宋濂） | 0 | 1 |
| 3a3-d59fxzglqtj6 | 萬氏家傳傷寒摘錦（萬全） | 傷寒摘錦（萬全）、傷寒摘錦（—） | 1 | 2 |
| 3a3-d59fxzgmdam8 | 萬氏祕傳片玉痘疹（萬全） | 片玉痘疹（—） | 0 | 1 |
| 3a3-d59fxzhp2pz5 | 易簡方論（程履新） | 程氏易簡方論（程履新） | 1 | 0 |
| 3a3-d59f2nbzxs01 | 徐文長祕集（徐渭） | 刻徐文長先生祕集（徐渭） | 1 | 0 |
| 3a3-d59fydxjkgld | 郭子翼莊（郭象/高𤼷） | 新刻郭子翼莊（—）、翼莊（郭象） | 0 | 0 |
| 3a3-d59fytlnvwg2 | 海藏老人此事難知（王好古） | 此事難知（王好古） | 0 | 0 |
| 3a3-d59fyzq6pzi9 | 魯化遺詩鈔（徐於） | 徐魯化遺詩（徐於） | 0 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
