# 去重细拆「上图-并」第 1 批（样本 12 组）

基线 main `026eda1dccf6ec2187d5a2469742c037af1c7bb9`。线索来源：book_index_json `library_data/_匹配/上海圖書館藏書/A6-研究-20261025/去重候选-同一上图work对多Work.tsv`（2,422 组：上图藏书 `work_uri` 与《中國古籍總目》`instanceOf` 同一 work，经总目 instance → Book.sources／Work 源記錄 落到正式库 2 个以上在世 Work）。在 main e79f0d6346 重算：2,422 组对应 8,749 个在世 Work、37,714 对（脚本 `../1_*.py`～`../classify.py`，`../pool.py`）。

剔除（不碰）：dedup-judged/ 已判 445 对、已互链 1,620 对、方志 1,362 对（归方志-并）、族谱 40 对（待用户定口径）、任一侧为叢書子目者约 2.1 万对（归子目-甲／子目-乙／4a-α）、4a-α／4b-α 候选里的 Work、开着的去重 PR 动过的 Work。

本批口径：总目同一 work（ID 证据）＋题名归一后同或仅异体／冠称之别＋首位责任者同一（同 entity 或同名异写、字号互证）＋卷数差≤1 或一侧缺＋朝代相容。逐组人工过目，证据写在 batch.json 每组 evidence。原挑 19 组：盲审撤 1 组；重跑时另有 4 组已由别的单元（3a-2丁）在 main 上并完、1 组少 1 个被并者，`../mkbatch.py` 自动剔除。

工具：`../apply_shlib.py`（复用 `../../dedup-confirmed-163/apply_batch.py`，署名 A11-去重上图-并）→ `postfix_common.py` → `update_index.py` → `fix_draft.py`（草稿库另开 PR）。冲突字段保留 keeper 原值、被并值记台账 `retained_alternatives`；被并者原 description／ai_note 存 `loser_original_notes`；互斥分类留 keeper 节点、被并者节点登记 `classification_decisions`。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
| 上图-并-gh7s36vns0skvigc | 抱朴子內篇（葛洪） | 抱朴子内篇（葛洪） | 3 | 0 |
| 上图-并-5jfn3j5ttfkqkzet | 疎寮集（高似孫） | 踈寮小集（高似孫）；疏竂小集（高似孫）；疏寮小集（高似孫） | 7 | 0 |
| 上图-并-dv58803qhoszt51j | 雞肋編（莊綽） | 雞肋編（莊季裕） | 1 | 0 |
| 上图-并-k2640r31pwv824s5 | 新唐書糾謬（吳縝） | 新唐書糾繆（吳縝） | 1 | 0 |
| 上图-并-agr6aenlwgwhiud6 | 谷音（杜本） | 穀音（杜本） | 2 | 0 |
| 上图-并-32zyb5nib6tasyto | 姓觿（陳士元） | 姓觽（陳士元） | 0 | 1 |
| 上图-并-nr44mfrqnm36qsgp | 山公啟事（山濤） | 山公啓事（山濤） | 1 | 0 |
| 上图-并-n0y4meqbntnkxooc | 大方廣佛華嚴經（實叉難陀） | 大方廣佛花嚴經（釋實叉難陀） | 0 | 0 |
| 上图-并-mv6ju7q1ijrp3k8s | 嬾真子（馬永卿） | 懶真子（馬永卿） | 3 | 0 |
| 上图-并-uypfcrfw5uzjzbo6 | 和靖詩集（林逋） | 宋林和靖先生詩集（林逋） | 1 | 0 |
| 上图-并-b6gbioaon4lzrqx5 | 三家世典（郭勳） | 三家世典（郭勛） | 0 | 0 |
| 上图-并-np5nh3n1zfkj6n7c | 遯世編（錢一本） | 遁世編（錢一本） | 0 | 1 |

抽检：另起子 agent 盲审原 19 组（只给路径，不给判断），SAME 18／UNSURE 1／DIFF 0，见 `抽检.md`。UNSURE 的太子沐魄／慕魄／墓珀经一组已撤出，登记 `dedup-judged/上图-并.tsv`。

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2（123 檔）、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 自检全 0。回滚：revert 本 PR 及草稿库对应 PR。
