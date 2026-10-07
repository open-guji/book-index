# build/ — schema-v2 構建與遷移腳本（`schema-v2` 分支）

依據：overview `項目進展/古籍目錄/進度/F-數據結構/` F2-3（build 與派生欄）、F2-7（遷移方案 M0–M6，§六附 sidecar 方案 B）、F4-2（卡片欄位、樞紐）。任務卡 open-guji-core/overview#459。
**只含 M0–M2 與 build**；M3（刪派生與反向、刪 sidecar）、M4（分類抽出）及以後不在此。純 Python 標準庫，測試用 pytest。

| 檔 | 作用 |
|---|---|
| `v2common.py` | 共用：讀記錄（三層分片下的 `<id>-題名.json`；更深者是 sidecar）、保格式寫回、關係詞表（規範詞／反向詞／歸併詞／對稱／單向） |
| `build_derived.py` | 源記錄 → `_build/`（不進 git）。確定性、可重跑、只寫有變的檔、刪不再產出的檔 |
| `migrate_v2.py` | M0 盤點、M1 補齊（只增不刪）、M2 關係規範化。冪等；不改 `revision`／`revised_at` |

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
- 樞紐：入度 >200（`--hub`）者，他處卡片只寫 `{id, h:1}`，名稱進 `_hubs.json`。正式庫實測 58 個；改最大叢編／志書／人物之名分別牽動 2／4／2 檔（與 F4-4 同）。

過渡期（M3 前）：`Work.books`、`Entity.works`、`Collection.books`／`contained_works` 與成員側**取併集**，故遷移前後產物的關係集合相同；M3 刪掉舊欄後這一段自然空轉。

校驗（失敗退出碼 1）：條數守恒（源記錄數＝`entry/` 數）、派生值自洽（`_edition_count`＝`len(_books)`、分頁合計＝總數、`_members` 是第 1 頁前段）、卡片 id 皆可解析、`h:1` 皆在 `_hubs.json`、源檔含非舊有的 `_` 欄。報而不擋：懸空引用、舊 `_` 欄與重算值之差、源裡仍有的舊反向欄（`--strict` 時擋，M3 後用）。

## migrate_v2.py

```
python3 build/migrate_v2.py --root <倉> --steps M0               # 盤點；未識別形態非空則失敗
python3 build/migrate_v2.py --root <倉> --steps M0,M1,M2 [--git-commit] [--dry-run] [--report-dir D]
```

- **M0**：記錄數、各欄形態統計、sidecar 清單、**未識別形態清單**（含：重複鍵——寫回會丟數據；詞表外 relation；欄位形態不在已知集合）。印 `git tag pre-schema-v2 <HEAD>` 命令，`--tag` 才真打。
- **M1**（只增不刪）：⓪ sidecar 方案 B——`sub_items`→`Book.contained_in[].sub_items`、`wiki_title`→`Book.resources` 維基文庫項（`details` 注「頁名取自舊叢編對照表，未驗證」）、`parent_work_id`→該對 `related` 的 `note`、sidecar 成員記錄側缺者補 `contained_in`（帶冊號）；冊號、`zhsy_id`、百衲本冊數、武英殿頂層資訊**只對勘不改**，列入報告；① 叢編側獨有成員併入成員側（`group`、`note`→`details` 一併帶）；③ 按名補 `entity_id`（唯一同名且未繫者）；② `authors[].role` 由 Entity 回填；④⑤ 規範側（`related` 為小 id 側）拼接兩側 note。
- **M2**：`commentary_on`→`studies`、`related_to`→`related`；只有反向形者、`related` 只在大 id 側者，在規範側落筆（帶合併後的 note）；刪 `related_works[].title`、`contained_works[].title`、`Entity.works[].title`。**反向項留到 M3 刪**。斷言：只留規範形、展開後 ⊇ M2 輸入與 M0 時的全部邊（F2-6 T2「舊有而 build 無＝0」）。
- 每步寫回前斷言 `revision`／`revised_at` 未變；檔案保留原縮排（手排版、無法判讀者改寫為縮排 2，M0 報告列出）。

## 未決（交目錄總管）

1. `_has_text`／`_has_collated` 有一部分依據不在本倉（book-text 整理本、全文），resources 推不出；M3 刪源裡舊值之前要給 build 接上來源（或保留這兩欄為源欄）。
2. 列表卡片 `cls`：分類檔（M4）出來前寫 `[l1, l2]` 標籤；有 `classification/` 後自動改寫節點 id。
3. `index/` 生成（現 `reindex.py`）尚未併入 build（F2-3 §一），本批不做。
4. 反向詞項（`has_part` 等，check_v2 的 V04）何時刪：F2-7 寫「M2 翻成規範方向、M3 刪派生與反向」，本腳本 M2 只在規範側補寫、**反向項留到 M3**（M2 純增改、不刪邊）；check_v2 把 V04 標為 M2。要在 M2 就刪，是一處改動。
5. `Work.contained_in[]` 的 `group`（自 `contained_works`，200 項）與 `details`（自 `contained_works[].note`，6 項）：M1 為免 M3 刪 `contained_works` 時丟失而併入成員側；SCHEMA〈Work〉目前只寫 `{id, volume_index?}`，需補這兩個可選鍵或另定去處。
6. `Collection.related_collections[]` 是帶 `title`／`note`／`type` 的對象（3 項），SCHEMA 寫作 ID 字串數組；F2-7 M2 未列，本腳本未動。
7. `authors[].role` 迄 M1 後仍缺 937 項（Entity 側也無 730、無 entity_id 者 207）；SCHEMA 定為必填，build 以「撰」兜底並計數，是否機械補「撰」待定。
