# 去重细拆单元子目-甲2：样本 20 簇

基线 main `aaa3e9aa05a38fdc01b4310eb8afc9dbc30546cf`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/细拆-并行单元-20261025.md`（子目-甲2 行）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**规则**（候选脚本 `../cand.py`）：叢書线（GUJI-526）按《總目》丛书版本记录各建一条子目 Work，同一丛书几个版次里的同一子目被建成多条。同题组（`scripts/dedup-census.py` 口径：去括注、异体归一）里，`ai_note`「所屬叢書記錄 X（丛书题名）」的丛书题名去卷数、种数后相同、而丛书记录不同的子目 Work 互并。另须：Book 所属 Collection 的首位撰者一致（不一致的丛书撰者写法不同簇另行逐条核，不在本批）；簇内首位责任者不矛盾（至多一种）、朝代不矛盾、卷数差≤1 或缺；同一丛书记录内同题两条的簇（疑异篇）、单字泛称题名（首／序／跋等，多为卷首卷末）不并，登记于 `../../dedup-judged/子目-甲2.tsv`；**跳过** 4a-α 清单（`../dedup-part4/候选/4a-alpha-*.json`）里的 Work，那些簇由 4a-α 并入同作者单行本。keeper：有责任者＞Book 多＞有非叢書部著录＞id 早。

工具：`apply_jia2.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

| 组 | 保留 | 丛书 | 并入条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|---:|
| jia2-d59fyx13m58i | 識小錄（無責任者） | 中復堂全集附 | 1 | 0 | 0 |
| jia2-d59fz4b7iy9u | 一隅草堂牡丹譜（無責任者） | 一隅草堂藳外集 | 1 | 0 | 0 |
| jia2-d59fyx13xds0 | 東溟文集（無責任者） | 中復堂全集附 | 1 | 0 | 0 |
| jia2-d59fyh3hhx4w | 種痘指掌（無責任者） | 借月山房彙鈔 | 1 | 0 | 0 |
| jia2-d59fytr716o2 | 元遺山先生集考證（無責任者） | 元遺山先生全集 | 1 | 0 | 0 |
| jia2-d59fybs011c0 | 沙中金集（無責任者） | 名家詩法 | 2 | 0 | 0 |
| jia2-d59fynz02801 | 李林甫外傳（無責任者） | 古今說海 | 3 | 0 | 0 |
| jia2-d59fz2582kn5 | 養性閑筆語錄次集（無責任者） | 厚庵鄧夫子遺書鄧厚庵先生遺書 | 1 | 0 | 0 |
| jia2-d59fywcf8vls | 唱經堂杜詩解（無責任者） | 唱經堂才子書彙稿 | 1 | 0 | 0 |
| jia2-d59fyrobycxs | 新編宣和遺事前集（無責任者） | 四部備要 | 1 | 0 | 0 |
| jia2-d59fynyzfqww | 裴伷先別傳（無責任者） | 古今說海 | 3 | 0 | 0 |
| jia2-d59fyroae680 | 包龍圖智賺合同文字雜劇（無責任者） | 四部備要 | 1 | 0 | 0 |
| jia2-d59fymc0u135 | 吳子（無責任者） | 四部叢刊 | 2 | 0 | 0 |
| jia2-d59fyx0de7ls | 鄉曲枝詞（無責任者） | 夢厂雜著 | 1 | 0 | 0 |
| jia2-d59fyro7l1c0 | 硃砂擔滴水浮漚記雜劇（無責任者） | 四部備要 | 1 | 0 | 0 |
| jia2-d59fy853uosi | 亢倉子（無責任者） | 墨海金壺 | 1 | 0 | 0 |
| jia2-d59fy8vf7tog | 哭弟（無責任者） | 寫心雜劇 | 1 | 0 | 0 |
| jia2-d59fyrod7b41 | 錦雲堂暗定連環計雜劇（無責任者） | 四部備要 | 1 | 0 | 0 |
| jia2-d59fyfkwuadd | 歙硯說（無責任者） | 學津討原 | 1 | 0 | 0 |
| jia2-d59fz4cc3sw0 | 政府應制稿（無責任者） | 廬陵周益國文忠公集周益國公全集周益公大全集 | 2 | 0 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
