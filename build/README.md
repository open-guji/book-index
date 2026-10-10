# build/ — schema-v2 構建與遷移腳本（`schema-v2` 分支）

依據：overview `項目進展/古籍目錄/進度/F-數據結構/` F2-3（build 與派生欄）、F2-7（遷移方案 M0–M6，§六附 sidecar 方案 B）、F4-2（卡片欄位、樞紐）。任務卡 open-guji-core/overview#459。
**含 M0–M6 與 build（連 `index/` 生成）**。sidecar 留到 M6 才刪（目錄總管 10-07）。純 Python 標準庫，測試用 pytest。

| 檔 | 作用 |
|---|---|
| `v2common.py` | 共用：讀記錄（三層分片下的 `<id>-題名.json`；更深者是 sidecar）、保格式寫回、關係詞表（規範詞／反向詞／歸併詞／對稱／單向） |
| `names.py` | 專名派生欄（dynasty／reign／office／place／官署，people 與 Work 的 `_dynasty_id`）與 `dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`（F6-5b，overview#464／#458）；已升格草稿以正式條為準 |
| `build_derived.py` | 源記錄 → `_build/`（不進 git）。確定性、可重跑、只寫有變的檔、刪不再產出的檔 |
| `migrate_v2.py` | M0 盤點、M1 補齊（只增不刪）、M2 關係規範化、M3 刪派生與反向、M4 分類抽出（M4a 生成分類檔、M4b 剝離）、M5 build 全量自校驗、M6 重生 `index/`＋刪 sidecar。冪等；一步一提交；不改 `revision`／`revised_at` |

## build_derived.py

```
python3 build/build_derived.py                                   # 本倉 → _build/
python3 build/build_derived.py --root ../book-index-draft --ref-root .   # 草稿庫，指向正式記錄的 id 由正式庫解析
python3 build/build_derived.py --check-only --hub-check          # 只校驗；加跑「改樞紐名牽動幾檔」
```

產物：`entry/<id>.json`（源記錄＋`_` 派生欄；源裡的舊 `_` 欄丟掉重算）、`members/<cid>/<n>.json`、`catalog/<志書>/<n>.json`、`related/<wid>/<n>.json`（每頁 200）、`lineage/<wid>.json`、`_hubs.json`、`report.json`。

派生欄（F2-3 §二，卡片短鍵取 F4-2）：
- Work：`_books`（按 `dating` 年代、無年代按 id）、`_edition_count`、`_authors`（與 `authors[]` 同序）、`_related`（`{id, title, relation, direction, note?}`：`relation` 取本記錄視角的詞，`direction` 為 `out`（本記錄存儲）／`in`（對方存儲）；超 200 分頁）、`_catalogs`、`_collections`、`_member_catalog`（志書）、`_has_*`、`_lineage_graph_ref`、`_classifications`（有 `classification/` 才產出）、`promoted_to`（草稿記錄，由 `promotions.json`）。
- Book：`_work`、`_siblings`（≤40，超出 `_siblings_more`／`_siblings_total`）、`_collections`、`_lineage_refs`、`_derived_by`、`_has_*`。
- Collection：`_members`（前 20）＋`_member_pages`、`_member_count`、`_member_type`、`_children`。
- Entity：`_works`（`{work_id, role, title, …}`，全內嵌；role 取 `Work.authors[].role`，缺則「撰」並計數）。
- 專名（`names.py`，SCHEMA〈九〉末幾行）：dynasty `_children`／`_ancestors`／`_reigns`；reign `_dynasty`／`_ruler`／`_index_in_reign`／`_same_name`；office `_children`／`_compounds`；官署 `_children`／`_subordinates`／`_members`／`_offices`；place `_children`／`_span`；people 與 Work `_dynasty_id`／`_dynasty_candidates`。另出 `dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`（全量時才出；草稿庫帶 `--ref-root` 才齊）。`report.json` 的 `contract`＝2。
- 樞紐：入度 >200（`--hub`）者，他處卡片只寫 `{id, h:1}`，名稱進 `_hubs.json`。正式庫實測 58 個；改最大叢編／志書／人物之名分別牽動 2／4／2 檔（與 F4-4 同）。

過渡期（M3 前）：`Work.books`、`Entity.works`、`Collection.books`／`contained_works` 與成員側**取併集**，故遷移前後產物的關係集合相同；M3 刪掉舊欄後這一段自然空轉。

`index/`（原 `reindex.py`、bim `entry_extractor.py` 併入）：逐字照 `entry_extractor` 的欄位規則，另帶 `has_collated`；分片同 `shard_of`（h=h*31+ord(c) mod 16），鍵按 id 排序。預設寫 `<out>/index/`，`--write-index` 另寫回倉內 `index/`（沿用各分片的縮排與尾換行，只寫有變的檔）。報告 `index.drift_vs_repo_index` 列倉內舊索引與重生值之差（舊索引漂移；草稿庫因數據 PR 不帶 `index/`，差得多是預期）。

校驗（失敗退出碼 1）：條數守恒（源記錄數＝`entry/` 數）、派生值自洽（`_edition_count`＝`len(_books)`、分頁合計＝總數、`_members` 是第 1 頁前段）、卡片 id 皆可解析、`h:1` 皆在 `_hubs.json`、源檔含非舊有的 `_` 欄。報而不擋：懸空引用、舊 `_` 欄與重算值之差、源裡仍有的舊反向欄（`--strict` 時擋，M3 後用）。

## migrate_v2.py

```
python3 build/migrate_v2.py --root <倉> --steps M0               # 盤點；未識別形態非空則失敗
python3 build/migrate_v2.py --root <倉> --steps M0,M1,M2 [--git-commit] [--dry-run] [--report-dir D]
```

- **M0**：記錄數、各欄形態統計、sidecar 清單、**未識別形態清單**（含：重複鍵——寫回會丟數據；詞表外 relation；欄位形態不在已知集合）。印 `git tag pre-schema-v2 <HEAD>` 命令，`--tag` 才真打。
- **M1**（只增不刪）：⓪ sidecar 方案 B——`sub_items`→`Book.contained_in[].sub_items`、`wiki_title`→`Book.resources` 維基文庫項（`details` 注「頁名取自舊叢編對照表，未驗證」）、`parent_work_id`→該對 `related` 的 `note`、sidecar 成員記錄側缺者補 `contained_in`（帶冊號）；冊號、`zhsy_id`、百衲本冊數、武英殿頂層資訊**只對勘不改**，列入報告；① 叢編側獨有成員併入成員側（`group`、`note`→`details` 一併帶）；③ 按名補 `entity_id`（唯一同名且未繫者）；② `authors[].role` 由 Entity 回填；④⑤ 規範側（`related` 為小 id 側）拼接兩側 note。
- **M2**：`commentary_on`→`studies`、`related_to`→`related`；只有反向形者、`related` 只在大 id 側者，在規範側落筆（帶合併後的 note）；刪 `related_works[].title`、`contained_works[].title`、`Entity.works[].title`。**反向項留到 M3 刪**。斷言：只留規範形、展開後 ⊇ M2 輸入與 M0 時的全部邊（F2-6 T2「舊有而 build 無＝0」）。
- **M1 人工核處置**（目錄總管 10-07，#459 6029501374）：sidecar 列的舊 `book_id` 不在庫者，按 `zhsy_id`（唯一）或「題名＋同叢編成員」（唯一）改指現 id，`parent_work_id` 的子作品經該行 Book 的 `work_id` 改指，對不上的才算數據錯（sidecar 原樣不改）；冊號不一取並集、Book 缺 `volume_index` 自 sidecar 補；`zhsy_id` Book 側空者補；百衲本 sidecar 有鏈接而 Book 缺 resource 者生成；叢編側 `contained_works[].volume_index` 與成員側不一者，成員側為準、叢編側序號以「叢編原序 N」記入 `contained_in[].details`（build 據以排成員序）；Entity.works 有而 Work.authors 為空、且 Entity 是人物者，按 Entity 側補入作者（`note` 註明來源）；疑重複人物另存 `人物道-疑重複人物.md`。M2 轉 `related_collections` 對象時，`type`／`note` 等併入本叢編 `description.text`（一條一行，不增欄位）。
- **M1 ②b**：②之後仍缺 `role` 者機械補「撰」（目錄總管 10-07 定），按有無 `entity_id` 分開計數。
- **M2 對稱 id 列表**：`Collection.related_collections` 的對象轉 id 字串（`type`／`note` 等逐條列 `symmetric_object_info`；指向非叢編者原樣保留、列 `symmetric_unconvertible`）；`related_books`／`related_collections` 只在大 id 側者，在小 id 側補寫。
- **M3**：刪 `Work.books`、`_edition_count`、`_has_image`；`Book._has_image`；`Collection.books`／`contained_works`／`_member_count`／`_member_type`／`_has_image`；`Entity.works`；反向詞項與 `related` 在大 id 側者；對稱 id 列表的大 id 側；`promoted_to` 與 `promotions.json` 一致者。無底線舊鍵 `has_text`／`has_full_text`／`has_collated` 併入准留的 `_has_text`／`_has_collated` 後刪；`has_digitalization` 在 resources 推得出影像時刪。**刪前逐項對勘**：`Work.books` 每項的 Book 指回本作、叢編側每個成員在成員側都有 `contained_in`（否則失敗）；`Entity.works` 有而 Work 側無者照刪並逐條列（即 M1③ 人工核清單）。刪後斷言邊集守恆、對稱對守恆。
- **M4**（F3-2 §六；用戶 10-07 定：取消「未分類」占位、Collection 不分類、`basis` 不遷入）：
  - **M4a** 生成 `classification/schemes.json`、`zongmu/tree.json`、`zongmu/members/<節點>.json`（`{node, members:[[work_id, source]…]}`，按 work_id 排序、一行一條）。樹由 `classific.json` 首見順序建，不含「未分類」占位節點，id `zm0001` 起確定性分配；已有 `tree.json` 則沿用、永不重配。草稿庫無 `classific.json`，用 `--vocab <正式庫>/classification/zongmu/tree.json` 取同一棵樹。掛「未分類」者上移到父節點。**upsert**：Work 裡還有 `classification` 的（遷移後又進來的舊格式批）更新成員行，已抽走的靠成員檔保留，故可重跑。斷言：每部回填路徑與 `source` ＝原值；路徑不在樹上即失敗。`basis` 丟棄，非 S/A/B/C 的批次說明列報告 `basis_ledger`。
  - **M4b** 刪 `Work.classification`（不 bump）；刪前逐部核成員檔有等值行，否則不刪、失敗。
  - build：有 `classification/` 時產出 `_classifications`、卡片 `cls` 寫節點 id、`_build/classific.json`（由 tree 生成給舊讀者，F3-2 §六⑤）；自校驗含 `classify check`（節點存在且未 retired、互斥法一部一類、檔名＝node、成員是本倉或參照倉的 Work）；`--strict` 時 Work 裡殘留 `classification` 算失敗。
- **M5**（不改數據）：`build_derived.py --strict --hub-check` 跑全量、寫 `_build/`；`--baseline <遷移前 build 的 report.json>` 時懸空引用各類只許減。草稿庫加 `--ref-root <正式庫>`。
- **M6**：先重跑 M1，**必須零改動**（＝人工核處置都已落完、已提交），否則不動；再按各分片原格式重生 `index/`，刪 sidecar——但頂層資訊尚未定去處的 sidecar（武英殿 `8rlcsybg2hhf/catalog`）**保留**、列 `sidecars_kept`；並重生剩餘人工核清單。
- 正式上線順序（每步一提交）：`--steps M0,M1,M2,M3,M4,M5,M6 --git-commit [--baseline …]`；草稿庫另加 `--vocab <正式庫>/classification/zongmu/tree.json --ref-root <正式庫>`。
- 跑 M1–M3 任一步都會在報告目錄生成 `人工核清單.md`（M1 要人工核的、數據錯、M2 拿掉的 `related_collections` 資訊、M3 的人工項）。
- 每步寫回前斷言 `revision`／`revised_at` 未變；檔案保留原縮排（手排版、無法判讀者改寫為縮排 2，M0 報告列出）。

## 已定（目錄總管 10-07，#459）

- `Work.contained_in[]` 的 `group`／`details` 進 SCHEMA（F6-2 改）。反向詞項在 M3 刪（check_v2 的 V04 歸 M3）。
- `_has_text`／`_has_collated` 留作源欄，M3 不刪不改名，build 照「resources 推得 或 源值為真」。**工作包 C 起**：給 `--text-index <book-text>/index/texts`，改由 resources＋book-text 推，源值不再算（`textindex.py`）；不給則保持舊行為並警告。
- sidecar 到 M6 才刪；武英殿 sidecar 頂層資訊先留著。

## 未決

1. `Collection 8rlcsybg2hi4.related_collections` 有一項指向 Work（`work_id`），轉不成叢編 id，原樣保留（check_v2 V06 剩這 1 處）。
