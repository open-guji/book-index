# 规范化目录库（v2）

> GUJI-755。设计：Claude Doc《规范化目录数据库设计 v2》（2026-11-04，用户 11-05 定「按推荐走」）。
> 本目录的 `schema.sql`、`constraints.sql`、`checks.sql` 是 **book-index-manager 生成的**，不要手改；
> 拆表映射（唯一真源）在 bim `book_index_manager/db/mapping.py`，说明见 bim `book_index_manager/db/README.md`。

## 定位
git 里的 JSON 是唯一真源。库由 bim 从 JSON 生成，随时可重建；派生文件（`_build/`）与检索以后从库出。草稿库不进库，只把旧 id 的去向装进 `id_map`。在线库（Neon）延后到有在线查询功能再开。

## 文件

| 文件 | 来源 | 内容 |
|---|---|---|
| [schema.sql](schema.sql) | `python -m book_index_manager.db ddl` | 47 张表：目录 34 张＋book-text 13 张（`bt_*`、`fragment*`），枚举、索引（需 `pg_trgm`） |
| [constraints.sql](constraints.sql) | `… ddl --constraints` | 外键，全部 `NOT VALID` |
| [checks.sql](checks.sql) | `… ddl --checks` | 悬空、owner_type、id 跨类重复检查，应全为 0 行（book-text 指向目录的几条除外，见下） |
| [book_text.sql](book_text.sql) | 手写草案 | book-text 尚未进库的部分（sections、专名、伴生层、CHANGES、pages.tsv）＋物化视图 `bt_mention` |
| [checks_book_text.sql](checks_book_text.sql) | 手写 | book-text 悬空检查（只报不拦） |

顺序：`schema.sql` → 灌库 → `constraints.sql` → `checks.sql` 全 0 行 → 逐条 `VALIDATE CONSTRAINT`。

```bash
# 在 bim 仓里：建表＋灌四类＋逐条还原比对（0 不一致才提交）
python -m book_index_manager.db roundtrip --root ../book-index --dsn "host=… dbname=gj" --create --keep
python -m book_index_manager.db coverage --schema ../book-index/schema/json   # schema 有、映射没有 → ERROR
```

## 表（34 张）
- **主表 4**：`work`、`book`、`collection`、`entity`。
- **Entity 子类与明细 12**：`person`、`place`、`office`、`collective`、`reign`、`publisher`、`seal`（主键即 entity.id；朝代没有自己的列，不设子类表）；`entity_dates`、`entity_external_id`、`entity_relation`（朝代、上级、前身、印主、合称、亲属师承等，`rel`＋`src_key` 区分）、`place_history`、`place_history_dynasty`。
- **Book／Collection 明细 5**：`book_provenance`、`book_seal_mark`、`book_base_edition`、`book_location_history`、`collection_content`。
- **四类共用 8**（带 `owner_type` W/B/C/E）：`alt_name`（四类异名，`kind`：null＝异名、`附刻`、实体别名类型）、`authorship`、`index_entry`（`kind` I／E）、`resource`、`resource_group`、`measure`、`source_ref`、`description_source`。
- **关系 4**：`member_of`、`work_relation`、`related_record`（Book→Book、Collection→Collection）、`id_map`（旧 id → 现行 id；`kind` merged／promoted，`src` tombstone／台账名）。
- **建库记录 1**：`build_meta`。

规矩：
1. 只给要展示、要查、要连的字段建列。依据（`*_basis`）、判断备注（`*_note`）、`ai_note`、`original_name` 等审计字段进每行 `notes jsonb`，键名照源文件，拆平对象里的记成 `对象.子键`（如 `dating.basis`）。查法：`notes->>'period_basis'`。
2. 不到一千行、也没人按它查的长尾放 jsonb 列（Entity `images`、`locations`、`todo`、`appears_in`，Work `additional_works`）或 `extra`。
3. 值装不进列（类型不对、不在枚举、不合法日期）原样进 `extra`，还原无损。
4. 数据为 0 的字段不建列，并从 JSON schema 删（11-05 删了 16 个，见 [CHANGELOG](../CHANGELOG.md)）。

## 实测（2026-11-05，本地 PostgreSQL 16，book-index main 含 #2240）

| 类型 | 条数 | 灌库＋还原＋比对 | 还原不一致 |
|---|---|---|---|
| Collection | 3,707 | 1 秒 | 0 |
| Entity | 151,188 | 26 秒 | 0 |
| Work | 249,774 | 68 秒 | 0 |
| Book | 403,118 | 113 秒 | 0 |

库 1.32 GB（含 trigram 索引）。`checks.sql` 27 条全 0 行，29 个外键全部 VALIDATE 通过。

## 建库

```bash
python -m book_index_manager.db build --root ../book-index --dsn "host=… dbname=gj" [--full] [--verify]
```

`build_meta` 记上次建到的提交与表结构指纹；指纹没变就只把 `git diff` 里改动的记录删了重灌（外键 `DEFERRABLE`，一个事务）。`id_map` 四个来源：记录里的墓碑、`.claude/qa/purge-tombstones/ledger/*.tsv`（清墓碑、并条历史、草稿墓碑改指）、`promotions/*.json`（草稿 id → 正式 id），`live_id` 沿链解到现行记录。细节见 bim `book_index_manager/db/README.md`。

实测（2026-11-05）：#2239 时全量 201 秒；增量到 #2241（Entity 12.1 万、Work 49 个 id 改动）71 秒，`--verify` 四类 807,787 条还原 0 不一致；`id_map` 610,211 行全部解到现行记录，`checks.sql` 28 条全 0 行。

## 从库产出 `_build/`

```bash
python -m book_index_manager.db build --root . --dsn "$DSN"
python3 build/build_derived.py --from-db "$DSN" --text-index ../book-text/index/texts
```

`--from-db` 时四类记录从库还原（主表 `file_name` 记源文件名，供 index 里的路径），分类、升格表、book-text 仍从文件读。实测（2026-11-05，#2242）：从库与从文件产出的 `_build/` 813,486 个文件 sha1 全同（含 `report.json`）；从库 5 分钟、从文件 4 分 16 秒。

## 下一步
1. 上线流程（derive-slim、网站 render）改走 `--from-db`，稳定后退役按文件读的那一路。
2. book-text 第二批进库：`book_text.sql` 里剩下的 sections、专名、伴生层、CHANGES、pages.tsv。

## book-text（第一批，2026-11-05）

`build --text-root ../book-text` 把 manifest.json、各版本 index.json、辑佚 fragments/*.json 一起灌进库（每次整批重灌），`--verify` 还原比对：8,689＋11,288＋1,248 份 0 不一致。正文和 char／cord 逐格数据不进库。

book-text 指向目录的引用只出悬空检查、不加外键。当时有 26 处悬空：11 处是已并条的旧号（id_map 能解到现行记录），4 处 `work_id` 填的是 Book id，11 处目录里查不到。清单见项目文件 `catalog-db/book-text-dangling-20261105.tsv`。每夜任务暂不带 book-text，清完再加。

## 沿革
D1 草案（11-02）到 v2 之间各轮评审与修订（A12、A33、S1–S6、可做可不做第 3–13 组）的逐条记录见本文件 git 历史（2026-11-04 及以前的版本）与 [CHANGELOG](../CHANGELOG.md)。v2 相对 D1：去掉 `repo` 列与 `dynasty`、`record_todo`、`entity_image`、`entity_location`、`entity_appears_in`、`work_additional` 表；四张异名表并成 `alt_name`；`related_book`／`related_collection` 并成 `related_record`；`merged_into` 改名 `id_map`；审计字段收进 `notes`；原型 `proto/roundtrip.py` 由 bim 取代。
