# 去重方案 3a-2乙（集部别集名异写）：样本 20 组

基线 main `66fcf76197fa47b7199c949027833adc464ad43b`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/00-通用口径与门禁.md` Work 节 B 档，及 `ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/3a-2乙-别集名异写口径.md`（体裁相容＋非选本＋主卷数相合＋至少一项同书佐证），`.claude/qa/正式库并条审查规则.md`。
候选由 `细拆脚本/near_title_alias.py` 生成（同首位责任者、题名去集名后缀后相同的集部对 1,967 对）；机械初分后 1,153 对由 16 个子 agent 逐条读两侧著录判定，判并的 363 对再由独立子 agent 盲判抽检 110 对（见 `../抽检.md`），抽检不同意者改存疑。全部判定见 `../判定.tsv`；簇内任两条有分立／存疑边的整簇不并。
工具：`mkbatch.py`（成簇、选 keeper）→ `../dedup-confirmed-163/apply_batch.py`（经 `apply_3a2yi.py` 调用；复用 mergework：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from 并 bump minor；升格表只改 production_id）、`../dedup-confirmed-163/postfix_common.py`、`update_index.py`、`fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`。被并者独有的作者 entity 在台账 `dropped_author_entities`（同名者已由 postfix_common 补到 keeper）。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 3a2yi-d59f6erf6vpe | 甌安館詩集（黄景昉） | 甌安館集（黃景昉） | 0 | 0 |
| 3a2yi-d59f28je9vd1 | 張承吉集（張祜） | 張承吉文集（張祜） | 0 | 0 |
| 3a2yi-d59f2mie9ji8 | 榕村集（李光地） | 榕村全集（李光地） | 1 | 1 |
| 3a2yi-d59fxwvgyole | 大旭山房文集（鄧渼） | 大旭山房集（鄧渼） | 0 | 1 |
| 3a2yi-d59fsfeob8qr | 雪浪山房集（顏懋僑） | 雪浪山房稿（顏懋僑） | 0 | 1 |
| 3a2yi-d59fxvate39d | 思益堂詞鈔（周壽昌） | 思益堂詞（周壽昌） | 1 | 0 |
| 3a2yi-d59f28kduxaf | 祖詠集（祖詠） | 祖詠詩集（祖詠） | 0 | 1 |
| 3a2yi-d59f2mxdcdmq | 滕王閣全集（蔡士英） | 滕王閣集（蔡士英） | 1 | 1 |
| 3a2yi-d59f28jw2ebm | 劉隨州集（劉長卿） | 劉隨州文集（劉長卿） | 1 | 0 |
| 3a2yi-d59fy1ik1o8w | 舫齋文集（陳祖綬） | 舫齋集（陳祖綬） | 0 | 1 |
| 3a2yi-d59f2nk0ocn5 | 蘇平仲文集（蘇伯衡） | 蘇平仲集（蘇伯衡） | 2 | 1 |
| 3a2yi-d59f2gizl0jk | 草窗詞（周密） | 草窗詞集（周密） | 1 | 0 |
| 3a2yi-d59fs7ese13b | 焚餘集（宗元豫） | 焚餘稿（宗元豫） | 0 | 1 |
| 3a2yi-d59f2j58xts1 | 陵川文集（郝經） | 陵川集（郝經） | 0 | 0 |
| 3a2yi-d59fxvapn8qo | 向懷葛先生文集（向洪邁） | 向懷葛先生集（向洪邁） | 0 | 1 |
| 3a2yi-d59f2hrmiozl | 北遊集（汪夢斗） | 北遊詩集（汪夢斗） | 1 | 1 |
| 3a2yi-d59f2ptb2fb5 | 孟襄陽集（孟浩然） | 孟襄陽詩集（孟浩然） | 0 | 1 |
| 3a2yi-d59fseca4fet | 敬齋遺鈔（朱光耀） | 敬齋遺集（朱光耀） | 0 | 0 |
| 3a2yi-d59f2net2pz6 | 緱山集（王衡） | 緱山文集（王衡） | 1 | 0 |
| 3a2yi-d59f2hsuue4h | 蘇魏公集（蘇頌） | 蘇魏公文集（蘇頌） | 1 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `../抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
