# 规范化目录库（v2）

> GUJI-755。设计：Claude Doc《规范化目录数据库设计 v2》（2026-11-04，用户 11-05 定「按推荐走」）。
> 本目录的 `schema.sql`、`constraints.sql`、`checks.sql` 是 **book-index-manager 生成的**，不要手改；
> 拆表映射（唯一真源）在 bim `book_index_manager/db/mapping.py`，说明见 bim `book_index_manager/db/README.md`。

## 定位
git 里的 JSON 是唯一真源。库由 bim 从 JSON 生成，随时可重建；派生文件（`_build/`）与检索以后从库出。草稿库不进库，只把旧 id 的去向装进 `id_map`。在线库（Neon）延后到有在线查询功能再开。

## 文件

| 文件 | 来源 | 内容 |
|---|---|---|
| [schema.sql](schema.sql) | `python -m book_index_manager.db ddl` | 34 张表、枚举、索引（需 `pg_trgm`） |
| [constraints.sql](constraints.sql) | `… ddl --constraints` | 外键，全部 `NOT VALID` |
| [checks.sql](checks.sql) | `… ddl --checks` | 悬空、owner_type、id 跨类重复检查，应全为 0 行 |
| [book_text.sql](book_text.sql) | 手写（第 4 步并进映射） | book-text 20 张表＋物化视图 `bt_mention` |
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

## 下一步
1. 库产出与 `build/build_derived.py` 逐字节一致的 `_build/`，并跑一致后请网站串切换、退役 `build_derived.py`。
2. book-text 进库（`book_text.sql` 并进映射，导入还原实测）。

## 沿革
D1 草案（11-02）到 v2 之间各轮评审与修订（A12、A33、S1–S6、可做可不做第 3–13 组）的逐条记录见本文件 git 历史（2026-11-04 及以前的版本）与 [CHANGELOG](../CHANGELOG.md)。v2 相对 D1：去掉 `repo` 列与 `dynasty`、`record_todo`、`entity_image`、`entity_location`、`entity_appears_in`、`work_additional` 表；四张异名表并成 `alt_name`；`related_book`／`related_collection` 并成 `related_record`；`merged_into` 改名 `id_map`；审计字段收进 `notes`；原型 `proto/roundtrip.py` 由 bim 取代。
