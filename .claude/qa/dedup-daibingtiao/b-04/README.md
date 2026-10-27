# 去重 新-待並條（待並條链接逐条定论）：b-04（30 组）

基线 main `430d36b9090ddde09a1d48ffc4021b9d1b1363ba`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/00-通用口径与门禁.md` Work 节 B 档（异题名同书须有原文自证：总目著录互见「一名／又名／原名／即」、或总目题名括注的其他题名与另一条题名、作者、卷数、内容都对上），`.claude/qa/正式库并条审查规则.md`。
候选由 `scan_alias.py` 全库扫描、`clean.py` 机械清洗（剔除首位责任者不同、原书对注疏本、「即」字句主语非本书、本库自动录入说明等），余者两道子 agent 独立逐条复核（第一道判对，第二道判簇），两道都判同、且无「著录混入他书／辑佚本／增订改编本」之嫌的才入批；`build_batch.py` 连簇出批。
工具：`../dedup-confirmed-163/apply_batch.py`（经 `apply_3a3.py` 调用；复用 mergework：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from 并 bump minor；升格表只改 production_id）、`postfix_common.py`、`update_index.py`、`fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`。被并者独有的作者 entity 在台账 `dropped_author_entities`（同名者已由 postfix_common 补到 keeper）。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| dbt-d59fyt6sjxfk | 太常奏議存（李日宣） | 太常奏議（李日宣） | 0 | 0 |
| dbt-d59fyt6yhfr5 | 滸東先生奏議（張鹵） | 滸東奏議（張鹵） | 1 | 0 |
| dbt-d59fyt71lt6q | 閉關三疏（張欽） | 閉開三疏（張欽） | 0 | 0 |
| dbt-d59fyt72jitd | 資治通鑑節要續編（張光啓） | 宋元通鑑節要續編（張光啓） | 2 | 1 |
| dbt-d59fyt72urcw | 資治通鑑後編校勘記（夏震武） | 續資治通鑑後編校勘記（夏震武） | 1 | 0 |
| dbt-d59fyt75cnpc | 通鑑綱目分注拾遺（芮長恤） | 綱目分注拾遺（芮長恤） | 1 | 0 |
| dbt-d59fyt76adc1 | 歷朝紀元錄（丘文學） | 紀元録（丘文學） | 0 | 1 |
| dbt-d59fyt77uk1t | 大明宣宗章皇帝實錄（楊士奇/張輔） | 明宣宗章皇帝實錄（楊士奇） | 1 | 0 |
| dbt-d59fyt7acge8 | 文苑傳（國史館） | 清史文苑傳（國史館） | 1 | 0 |
| dbt-d59fyt7c7vnl | 明史稿（王鴻緒） | 敕修明史稿（王鴻緒） | 2 | 0 |
| dbt-d59fyt7g9ypt | 職方存草（茅瑞徵） | 職方存稿（茅瑞徵） | 0 | 1 |
| dbt-d59fyt7gwfsw | 浙江海運全案初編（黃宗漢/椿壽） | 浙江海運全案（黃宗漢） | 1 | 0 |
| dbt-d59fyt7j33lt | 憲政編查館奏遵旨議覆國籍條例候頒行摺（奕劻） | 憲政編查館奏遵旨議覆國籍條例伏侯欽定頒行摺（奕劻） | 1 | 0 |
| dbt-d59fyt7jec5d | 憲政編查館奏覆核民政部修訂法律大臣奏禁煙條例摺（奕劻） | 憲政編查館奏覆核民政部修訂法律大臣會奏禁煙條例摺（奕劻） | 1 | 0 |
| dbt-d59fyt7jec5e | 憲政編查館會奏遵議憲法大綱暨選舉各法摺（奕劻） | 憲政編查館會奏遵議憲法大綱暨議院選舉各法並逐年籌備事宜摺（奕劻） | 1 | 0 |
| dbt-d59fyt7tp62o | 欽定工部則例（費淳/史貽直） | 工部則例（史貽直） | 1 | 0 |
| dbt-d59fyt7u0em8 | 欽定法院編制法（奕劻） | 欽定法院編制法十六章（奕劻） | 1 | 0 |
| dbt-d59fyt7w72f5 | 律條疏義（張楷） | 律條疏議（張楷） | 0 | 0 |
| dbt-d59fyt7ydq82 | 畿輔水道管見（吳邦慶） | 畿輔河道管見（吳邦慶） | 1 | 0 |
| dbt-d59fyt81tc75 | 防海備覽（薛傳源） | 海防備覽（薛傳源） | 1 | 0 |
| dbt-d59fyt84b8jm | 幣制說帖及簡明總要並度支部說帖（鹿傳霖） | 幣制說帖及簡明總要並度支部說帖各督撫議幣制摺奏電奏及節略（鹿傳霖） | 1 | 0 |
| dbt-d59fyt85vf9e | 中鑑錄（王畿） | 中官中鑒録（王畿） | 1 | 1 |
| dbt-d59fyt86hwcg | 鄭成功傳（鄭亦鄒/鬱永河） | 白麓藏書鄭成功傳（鄭亦鄒） | 0 | 0 |
| dbt-d59fyt8eatxd | 陝西右布政使備兵靖邊道畢公生祠記（張廷玉） | 畢公生祠記（張廷玉） | 1 | 0 |
| dbt-d59fyt8fjs3m | 七太子傳（陳懿典） | 正史七太子傳（陳懿典） | 0 | 1 |
| dbt-d59fyt8hf7cw | 陸清獻公日記（陸隴其） | 日記（陸隴其） | 2 | 0 |
| dbt-d59fytlyhywx | 陶學士先生事蹟（費宏） | 陶學士事蹟（費宏） | 0 | 0 |
| dbt-d59fyutnensx | 史目表（洪飴孫） | 歷代史目表（洪飴孫） | 1 | 0 |
| dbt-d59fyv4b1gch | 韓忠定公集（韓文） | 忠定集（韓文） | 1 | 1 |
| dbt-d59fz72gzpj4 | 新刻京板工師雕鏤正式魯班經匠家鏡（章嚴/午榮） | 魯班經（午榮/章嚴） | 0 | 1 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
