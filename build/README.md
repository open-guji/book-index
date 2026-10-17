# build/ — schema-v2 構建與遷移腳本（`schema-v2` 分支）

依據：overview `項目進展/古籍目錄/進度/F-數據結構/` F2-3（build 與派生欄）、F2-7（遷移方案 M0–M6，§六附 sidecar 方案 B）、F4-2（卡片欄位、樞紐）。任務卡 open-guji-core/overview#459。
**含 M0–M6 與 build（連 `index/` 生成）**。sidecar 留到 M6 才刪（目錄總管 10-07）。純 Python 標準庫，測試用 pytest。

| 檔 | 作用 |
|---|---|
| `v2common.py` | 共用：讀記錄（三層分片下的 `<id>-題名.json`；更深者是 sidecar）、保格式寫回、關係詞表（規範詞／反向詞／歸併詞／對稱／單向） |
| `names.py` | 專名派生欄（dynasty／reign／office／place／官署，people 與 Work 的 `_dynasty_id`）與 `dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`（F6-5b，overview#464／#458）；已升格草稿以正式條為準 |
| `build_derived.py` | 源記錄 → `_build/`（不進 git）。確定性、可重跑、只寫有變的檔、刪不再產出的檔 |

## build_derived.py

```
python3 build/build_derived.py --text-index "$BOOK_TEXT_DIR/index/texts"                                   # 本倉 → _build/
python3 build/build_derived.py --root ../book-index-draft --ref-root . --text-index "$BOOK_TEXT_DIR/index/texts"   # 草稿庫，指向正式記錄的 id 由正式庫解析
python3 build/build_derived.py --check-only --hub-check --text-index "$BOOK_TEXT_DIR/index/texts"          # 只校驗；加跑「改樞紐名牽動幾檔」
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

校驗（失敗退出碼 1）：條數守恒（源記錄數＝`entry/` 數）、派生值自洽（`_edition_count`＝`len(_books)`、分頁合計＝總數、`_members` 是第 1 頁前段）、卡片 id 皆可解析、`h:1` 皆在 `_hubs.json`、源檔含非舊有的 `_` 欄。報而不擋：懸空引用。（舊 `_` 欄與舊反向欄的容忍已於 2026-10-11 刪除：源檔任何 `_` 欄即擋；`--strict` 現為空操作。）

`index/seals.json`＋`index/seals/<seal_id>/<n>.json`（GUJI-542 P2，`sealindex.py`）：印章反查表，由 `Book.provenance[].seal_marks` 派生，計數＋分頁（每頁 ≤500 Book id）；規則見 schema/derived.md〈8.3〉。`report.json` 的 `index.seals` 帶計數、漂移與 `appears_in` 對賬；`verify.py` 重算比對。

## 已定（目錄總管 10-07，#459）

- `Work.contained_in[]` 的 `group`／`details` 進 SCHEMA（F6-2 改）。反向詞項在 M3 刪（check_v2 的 V04 歸 M3）。
- `_has_text`／`_has_collated` 留作源欄，M3 不刪不改名，build 照「resources 推得 或 源值為真」。**工作包 C 起**：給 `--text-index <book-text>/index/texts`，改由 resources＋book-text 推，源值不再算（`textindex.py`）；#144 起必給，不給直接報錯。
- sidecar 到 M6 才刪；武英殿 sidecar 頂層資訊先留著。

## 未決

1. `Collection 8rlcsybg2hi4.related_collections` 有一項指向 Work（`work_id`），轉不成叢編 id，原樣保留（check_v2 V06 剩這 1 處）。
