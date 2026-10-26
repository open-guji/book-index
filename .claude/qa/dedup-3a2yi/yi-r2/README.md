# 去重方案 3a-2乙（集部别集名异写）：第二轮细查

基线 main `ae30795f88940f0134de976e14c6aacf2bdec632`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/00-通用口径与门禁.md` Work 节 B 档，及 `ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/3a-2乙-别集名异写口径.md`（体裁相容＋非选本＋主卷数相合＋至少一项同书佐证），`.claude/qa/正式库并条审查规则.md`。
候选由 `细拆脚本/near_title_alias.py` 生成（同首位责任者、题名去集名后缀后相同的集部对 1,967 对）；机械初分后 1,153 对由 16 个子 agent 逐条读两侧著录判定，判并的 363 对再由独立子 agent 盲判抽检 110 对（见 `../抽检.md`），抽检不同意者改存疑。全部判定见 `../判定.tsv`；簇内任两条有分立／存疑边的整簇不并。
工具：`mkbatch.py`（成簇、选 keeper）→ `../dedup-confirmed-163/apply_batch.py`（经 `apply_3a2yi.py` 调用；复用 mergework：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from 并 bump minor；升格表只改 production_id）、`../dedup-confirmed-163/postfix_common.py`、`update_index.py`、`fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`。被并者独有的作者 entity 在台账 `dropped_author_entities`（同名者已由 postfix_common 补到 keeper）。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 3a2yi-d59f28jo9gqt | 資吟集（鍾安禮） | 資吟（鍾安禮） | 1 | 0 |
| 3a2yi-d59f28ljdhja | 李頎集（李頎） | 李頎詩集（李頎） | 0 | 0 |
| 3a2yi-d59f28lfmn0g | 常建詩集（常建） | 常建集（常建） | 1 | 0 |
| 3a2yi-d59f28kff401 | 顏魯公文集（顏真卿） | 顏魯公集（顏真卿） | 0 | 1 |
| 3a2yi-d59fxv95giyo | 黎嶽詩集（李頻） | 黎嶽集（李頻） | 0 | 0 |
| 3a2yi-d59fxw3sl6o0 | 滄州集（羅公升） | 滄洲詩集（羅公升） | 3 | 0 |
| 3a2yi-d59f2gkgylfm | 訥齋文集（王毅） | 訥齋集（王毅） | 1 | 0 |
| 3a2yi-d59f2go7hvk0 | 知非堂稿（何中） | 知非堂集（何中） | 0 | 0 |
| 3a2yi-d59fymbw5gxu | 東維子文集（楊維楨） | 東維子集（楊維楨） | 0 | 0 |
| 3a2yi-d59f2higw3cz | 北澗文集（釋居簡） | 北磵集（釋居簡） | 0 | 1 |
| 3a2yi-d59f2hro2vpc | 鐔津文集（釋契嵩） | 鐔津集（釋契嵩） | 1 | 1 |
| 3a2yi-d59f2hrs4yrl | 蛟峯文集（方逢辰） | 蛟峯集（方逢辰/方逢振） | 3 | 0 |
| 3a2yi-d59f2nkxg9oh | 松隱文集（曹勛） | 松隱集（曹勛） | 2 | 1 |
| 3a2yi-d59fy1ifzl6o | 薝蔔花館詞集（徐鴻謨） | 薝蔔花館詞（徐鴻謨） | 1 | 0 |
| 3a2yi-d59f2ndu45j6 | 劉古直集（劉珝） | 劉古直文集（劉珝） | 1 | 0 |
| 3a2yi-d59f2ngb2s5c | 龍皋稿（陸簡） | 龍皋文集（陸簡） | 0 | 0 |
| 3a2yi-d59f2nejedj4 | 龍溪文集（王畿） | 龍溪集（王畿） | 1 | 0 |
| 3a2yi-d59f6eq5azuq | 邕歈稿（董傳策） | 邕歈集（董傳策） | 2 | 0 |
| 3a2yi-d59f2nlavgu8 | 鄭端簡公文集（鄭曉） | 鄭端簡公集（鄭曉） | 2 | 0 |
| 3a2yi-d59fxw3ccuf5 | 雲起軒詞（文廷式） | 雲起軒詞鈔（文廷式） | 1 | 1 |
| 3a2yi-d59f2og6qznl | 張喬詩集（張喬） | 張喬集（張喬） | 5 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `../抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
