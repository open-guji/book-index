# 旧字段与旧写法

本档列出 schema-v2 以前的字段与写法：哪些已经删净，哪些暂时留着，哪些现存数据里还有、要列入修正方案；网站和 bim 现在怎样兼容读这些写法；什么时候删、由谁删。

- 格式本身（新写法）见各类记录的字段表：[common.md](common.md)、[work.md](work.md)、[book.md](book.md)、[collection.md](collection.md)、[entity.md](entity.md)；派生字段见 [derived.md](derived.md)。
- 总则 9「读者先切后拆」：网站与 bim 读数据时「新字段有就用新的，没有再回退旧字段」，数据切换完成后再删回退分支。build 不产出旧字段的别名。
- 来历：schema-v2 迁移（M0–M6）见 overview#451、#459；`_build/` 契约见 overview#458；专名子类型见 overview#464。

---

## 一、怎么读本档

**实测口径**：2026-10-08 两库全量（正式库 `aad88a5ff3`，草稿库 `d2d0b6429`；bim `b405824`）。记录文件＝恰好在 `<类型>/{c1}/{c2}/{c3}/` 下、带 `id` 与 `type` 的 `.json`。
记录数：正式库 Work 119,527、Book 54,477、Collection 85、Entity 32,407；草稿库 Work 36,721、Book 68,144、Entity 4,488（无 Collection）。

数字写作「n 处／m 条」时，「处」是出现次数（数组元素级），「条」是涉及的记录数；只写一个数时是条数。复现：`python3 schema/check_schema.py --json 报告.json`（正式库）与 `python3 schema/check_schema.py --root ../book-index-draft --draft --json 报告.json`（草稿库），各旧字段、旧写法的处数即报告里 `level: WARN` 的各项；少数不属形状问题的计数（如 dynasty 非规范值、`_has_text` 仅凭源值者）见 overview `项目进展/古籍目录/进度/F-数据结构/格式终版-吻合度报告.md`。

**列义**

| 列 | 写什么 |
|---|---|
| 旧字段或写法 | 键名或写法；嵌套写 `a[].b` |
| 在哪类记录 | Work／Book／Collection／Entity |
| 现状 | 正式库 n／草稿库 n（10-08 实测） |
| 新写法 | 现行格式怎么写；已删者写去向 |
| 读者兼容读法 | 网站（经 bim 的 `book-index-ui` 包）与 bim 现在怎么读，引 bim 仓 `文件:行`；build 与校验的读法也列在这里 |
| 何时删 | 有日期写日期；没有就写「未定日期，条件是……」 |
| 由谁删 | 目录侧数据修正交 **S**；读者回退分支归**网站经理**；build／校验归 **S**；bim 写入代码见 [§五](#五仍会产出旧写法的代码交-bim-侧) |

文中 bim 路径相对于 `book-index-manager` 仓根；build／校验路径相对于本仓根。kaiyuanguji-web 自身的打包脚本不在本次核对范围，网站的条目页、检索页读法都在 `book-index-ui`（即 bim `ui/`）里。

---

## 二、已删（现存为 0）

迁移 M2／M3／M4／M6 已删净，两库实测都是 0。这些写法若再出现，`check_v2.py` 报对应代码（审数据 PR 必跑），按错处理，不再兼容。

| 旧字段或写法 | 在哪类记录 | 现状 | 新写法 | 读者兼容读法 | 何时删 | 由谁删 |
|---|---|---|---|---|---|---|
| `books`（版本 id 列表） | Work | 0／0（V03） | 源：`Book.work_id`；产物 `_books`、`_edition_count` | bim `ui/src/core/derived-compat.ts:63-65`（`_books` 补回旧形 `books`）；`ui/src/components/detail/WorkPage.tsx:66`、`ui/src/components/detail/EntityPage.tsx:179` 仍读 `books`；build 过渡期并集 `build/build_derived.py:225-233` | 数据：M3 已删。读者回退与 build 并集：未定日期，条件是数据切换完成（F4-5 批次 3.7） | 读者：网站经理；build：S |
| `books`、`contained_works`（含 `title`、`volume_index`、`group`） | Collection | 0／—（V10） | 源：成员侧 `Book.contained_in[]`、`Work.contained_in[]`；产物 `_members`、`_member_count` 等 | `derived-compat.ts:113-131`（`_members` 补回 `books`／`contained_works`）；build `build_derived.py:245-265` 并集 | 同上 | 同上 |
| `works` | Entity | 0／0（V11） | 源：`Work.authors[].entity_id`（含 `role`）；产物 `_works` | `derived-compat.ts:134-141`；build `build_derived.py:235-244` 并集 | 同上 | 同上 |
| `related_works[].title`；`contained_works[].title`；`Entity.works[].title` | Work 等 | 0／0（V06） | 删；产物 `_related[].title` 取对方现行题名 | `derived-compat.ts:76-86`：有 `_related` 时整体覆盖 `related_works`（带 `title`） | M2 已删；读者同上 | 同上 |
| 反向词 `has_part`、`studied_by`、`text_carried_by`、`followed_by`、`has_pseudepigraph`、`has_adaptation` 作源值 | Work | 0／0（V04） | 对方源档写规范词 `part_of`、`studies`、`contains_text_of`、`preceded_by`、`pseudepigraph_of`、`adapted_from`；本侧只在 `_related`（`direction:"in"`） | 页面按 `_related` 里的反向词分组：`ui/src/core/detail-model.ts:984-985`、`WorkPage.tsx:137`（这是产物的正当读法，不是回退） | M3 已删 | — |
| `commentary_on`、`related_to`（`related_works[].relation`） | Work | 0／0（V05） | `studies`、`related` | 页面不再识别这两个词；注意 `Book.lineage.related_to` 是另一个现行字段，与此无关 | M2 已删 | — |
| `related` 写在 id 较大一侧；两侧都写 | Work | 0／0（V07） | 只存 id 较小一侧（字符串比较），两侧 note 拼接；另一侧在 `_related` | 读 `_related` | M1⑤＋M3 已删 | — |
| `related_books`、`related_collections` 写在 id 较大一侧或两侧都写 | Book、Collection | 0／0（V07） | 只存 id 较小一侧；产物 `_related` 给并集（契约 3） | 读 `_related` | M3 已删 | — |
| `related_collections[]` 用对象形（`{work_id, type, note}` 等） | Collection | 0／—（V14） | id 字符串 | — | M2 已改；最后 1 处（`8rlcsybg2hi4` 指向 Work）已由 `aa7a3d8a7b` 补立叢編 `8rldhjfpv8cg`、改为该 id，原 `type`／`note` 移入 `ai_note`。`build/README.md`〈未决〉1 已过时 | — |
| `classification {l1, l2, l3, l4, basis, source}` | Work（Collection 不分类） | 0／0（V09） | `classification/<分类法>/members/<节点>.json` 的 `[work_id, source]`；产物 `_classifications` | `derived-compat.ts:66-74`（取 `zongmu` 一项补回旧形，供 `WorkPage.tsx:212` 读） | M4 已删；读者回退：未定日期，条件同上 | 网站经理 |
| 源档 `_edition_count`、`_has_image`、`_member_count`、`_member_type`、`_promoted_to`、`_promoted_at` | Work、Book、Collection、Entity | 0／0（V01） | 产物同名字段（`_promoted_to` 改为产物与 `index/` 里的 `promoted_to`，权威是 `promotions/`） | build 遇源值丢掉重算，`build/v2common.py:32-37` `LEGACY_DERIVED` 只报不挡；`.claude/qa/verify.py` 的 `_edition_count`／`_member_*` 校验在新格式下恒 0 | M3 已删；`LEGACY_DERIVED` 与 `legacy_diffs`（`build_derived.py:935-955`）：未定日期，条件同上 | S |
| `has_text`、`has_image`、`has_collated`、`has_full_text`、`has_digitalization`（无下划线） | Work、Book、Collection | 0／0（V02） | 产物 `_has_*`；`index/` 里的 `has_text` 等（`index/` 整个是产物，键不加下划线，是现行写法） | build `build_derived.py:314` 与 `:738`、bim `book_index_manager/entry_extractor.py:267` 仍兼读 `has_collated`；`book_index_manager/revision_fields.py:18` 列为不 bump | M3 已删；兼读分支：未定日期，条件同上 | build：S；bim：网站经理 |
| 记录内 `promoted_to`、`promoted_at` | 草稿记录 | 0／0（V02） | 正式库 `promotions/<草稿 id 末 2 位>.json`（见 [promotions.md](promotions.md)）；产物与 `index/` 回填 `promoted_to` | bim `book_index_manager/_utils.py:32-49` `read_promoted_to` 兼读 `_promoted_to`／`promoted_to`；`book_index_manager/storage.py:533-540` 档上旧印记优先于 `promotions`；`entry_extractor.py:191`、`:289` | M3 已删；兼读分支：未定日期，条件同上 | 网站经理 |
| sidecar 对照表（`volume_book_mapping.json` 等 6 份） | Collection 目录下 | 0／0（V12） | 独有信息已在 M1⓪ 并入记录：`sub_items`→`Book.contained_in[].sub_items`，`wiki_title`→`Book.resources[]` 的 `wikisource` 项，`parent_work_id`→对应 `related` 的 `note` | 不读 | M6 已删 | — |
| `collections`（Collection id 数组） | Work | 0／0 | `contained_in[]`（对象形） | `WorkPage.tsx:66`、`EntityPage.tsx:179` 仍读 `collections` | 数据已无；读者：未定日期，条件同上 | 网站经理 |
| `aliases` | Entity | 0／0 | `alt_names` | 不读 | 数据已无 | — |
| `ai_note_fix`、`ai_note2`、`ai_note_periodfix` | Work | 0／0 | 并入 `ai_note` | 不读 | 数据已无 | — |
| `book_contained_in`、`parent_works`（Work）；`history`、`volume_count`（Collection） | Work、Collection | 0／0 | `parent_works`→`related_works` 的 `part_of`；其余库中原本为零 | 不读（但 bim 仍可写 `history`，见 §五） | 2026-08 已删 | — |
| `parent_work {id, title}` | Book、Work | 0／0 | `Book.work_id`；作品层级用 `related_works` 的 `part_of` | `ui/src/storage/local-storage.ts:134-136` 仍读 | 读者：未定日期，条件同上 | 网站经理 |
| `related_works[]` 以 `work_id` 代 `id` | Work | 0／0 | `id` | `check_v2.py` `rel_target` 兼认 | — | — |
| `relation` 不在词表（V13）；缺 `schema_version` 或值非 `1`（V15） | 全部 | 0／0 | 见 [work.md〈关联词表〉](work.md#五关联词表)、[README〈五〉](README.md#五三种版本号) | — | — | — |

**`check_v2.py` 不删**：V01–V16 是防回潮的门禁，数据删净以后照样要拦新进的旧格式批，长期保留。

---

## 三、暂留

| 旧字段或写法 | 在哪类记录 | 现状 | 新写法 | 读者兼容读法 | 何时删（迁） | 由谁删 |
|---|---|---|---|---|---|---|
| `_has_text` | Work、Book | 正式库 Work 10,723（`true` 10,677、`false` 46）、Book 13（皆 `true`）／草稿库 0 | 目标：产物 `_has_text`，由 build 从稳定来源推得 | 源档允许，`check_v2.py` V01 豁免（`UNDERSCORE_EXEMPT`）。build `build_derived.py:310-318` `put_has`：resources 推得 **或** 源值为真即出 `_has_text:true`；其中 Work 292、Book 3 条（共 295）resources 推不出、只凭源值（`legacy_hastext.py` 实测）。`index/` 的 `has_text` 只看 resources、不看源值（`build_derived.py:655-668` `_res_flags`），与 `_build/entry` 口径不一，**待 build 统一** | 未定日期，条件是文本总管给出稳定来源（book-text 全文／整理本清单）、build 改从该来源推 | 数据：S；build：S |
| `_has_collated` | Work | 正式库 66（`true` 65、`false` 1）／草稿库 0 | 同上，产物 `_has_collated` | build 不推 collated，只看源值（`build_derived.py:312-314`）；`index/` 的 `has_collated` 取源值（`build_derived.py:738`；bim `entry_extractor.py:267` 同） | 同上 | 同上 |
| `_has_text:false`、`_has_collated:false` | Work | 正式库 46＋1／0 | 不写（总则 11：只标异常，缺省即无） | 读者按「缺即假」，`false` 与缺省同义 | 可随时删，不必等文本来源 | S |
| `classific.json`（旧分类词表） | 正式库根；产物 `_build/classific.json` | 正式库有／草稿库无 | `classification/zongmu/tree.json`；`classific.json` 由 build 从 tree 生成，给尚未改读树的旧读者 | bim `ui/src/components/catalog/model.ts:9-58`（同级顺序按 `classific.json`）；`book_index_manager/__main__.py:607`、`book_index_manager/schema_fields.py:21`（词表四元组） | 未定日期，条件是上述读者改读 `tree.json` | 读者：网站经理；生成与仓根文件：S |

**为何暂留**：`_has_text`／`_has_collated` 的依据有一部分在 book-text（整理本、全文），本仓的 resources 推不出；目录经理 10-07 定 M3 不删、不改名（#459）。它们是源档里**唯一**允许的 `_` 起首字段，专名子类型不享此例外。

---

## 四、现存旧写法（列入修正方案）

这些写法现存数据里还有，新数据不写。数据修正交 S；读者回退分支在数据改完后删。

| 旧字段或写法 | 在哪类记录 | 现状 | 新写法 | 读者兼容读法 | 何时删 | 由谁删 |
|---|---|---|---|---|---|---|
| `authors[].role` 写英文 `"author"` | Book、Collection | 正式库 Book 8 处／6 条、Collection 8 处／8 条，共 16／草稿库 0 | 志书原文责任方式（开放词表）；判不出时写 `撰`（build 缺省同）。不得写英文 | bim `ui/src/core/detail-model.ts:1412` `normalizeRole` 把 `author` 归「撰」；`detail-model.ts:1431` `displayAuthorRole` 不显示无汉字的 role | 数据：未定日期，条件是 S 逐条按原文改定；读者：条件是数据改完 | 数据：S；读者：网站经理 |
| `authors[].cbdb_match`、`cbdb_source`、`cbdb_id` | Work | 正式库 18、18、3／0 | 移到所指 Entity 的外部对齐字段（见 [entity.md](entity.md)）；`authors[]` 里不写 | 不读 | 未定日期，条件是 S 并入 Entity | S |
| `authors[]` 其余杂键：`title_or_office` 97 处／96 条、`courtesy_name` 84 处／82 条（另 Book 2）、`alt_names` 42、`entity_basis` 19、`sources` 16、`birthplace` 4、`ai_note` 3、`alias` 2、`additional_names` 1、`official` 1、`name_note` 1 | Work（`courtesy_name` 另有 Book） | 正式库如左／草稿库 0 | 人物信息（字、别名、籍贯、官职）归 Entity；判断依据并入 `note`／`ai_note`。`authors[]` 的正式键只有 `name`、`role`、`dynasty`、`entity_id`、`source`、`name_basis`、`dynasty_basis`、`note`、`role_basis`、`original_name`（见 [common.md〈Author〉](common.md#一authorauthors-的元素)） | 不读 | 未定日期，条件是 S 并入 note／ai_note 或 Entity | S |
| `resources[].type`（单值） | Work、Book | 正式库 Work 12,604 处（`image` 11,413、`text` 1,191），Book 1,511 处（`image` 1,361、`physical` 150）／草稿库 0。与 `types` 并存 0；`types` 闭集外的值 0 | `types`（数组，闭集 `image`／`text`／`physical`／`catalog`／`annotated`） | bim `ui/src/types.ts:14-20` `getResourceTypes`：`types` 有就用，否则 `[type]`（`text+image` 拆两项）；`ui/src/components/detail/BookPage.tsx:293`、`ui/src/core/storage.ts:262-280`、`book_index_manager/entry_extractor.py:118-145` 同法。build `build_derived.py:66-76` `types_of` 取 `types` 与 `type` 并集（`text+image` 不拆，现存 0 处），`:655-668` 同 bim | 数据：未定日期，条件是 S 机械改 `type`→`types:[type]`（不 bump）；读者：条件是数据改完且 §五 的写入点已改 | 数据与 build：S；读者：网站经理 |
| `resources[].group_label` | Work、Book | 0／0 | `resource_groups[<group>].label` | **bim 已不读**：`detail-model.ts:1078` 组名取 `resource_groups[key].label`，缺时显示组键 | 现存为 0、读者不读，可从格式中删去（旧 SCHEMA「仍读、优先级低」一句已过时） | — |
| `contained_in[]` 字符串形 | Collection | 0／0（2026-10-09 S 已把正式库 19 处／17 条改为对象形；草稿库无 Collection）。Book、Work 的 `contained_in[]` 全是对象形 | 对象形 `{id, …}`，与 Book／Work 一致 | build 两形都认（`build_derived.py:110-121`、`:219-224` 经 `V.ref_id`）；bim `book_index_manager/scripts/update_catalog_stats.py:43` 两形都认。**bim 页面只认字符串形**：`ui/src/components/detail/CollectionPage.tsx:148` 取 `contained_in[0]` 当 id，`ui/src/types.ts:541` 声明 `string[]`——现有 3 条对象形的上级丛编显示不出 | 先切后拆：① bim `CollectionPage` 先改为两形都认（条件：无）；② S 把 19 处改为对象形（**2026-10-09 已完成**）；③ 删字符串分支（条件已满足） | ①③：网站经理；②：S |
| `related_collections: []`（空数组占位） | Collection | 正式库 1 条（`8rlcsybg2hi6`）／— | 不写（缺省即无） | 读者按空处理 | 可随时删 | S |
| `indexed_by[]` 的 `merged_from` 596 处／404 条、`text`／`self_note`／`commentaries` 各 592 处／578 条、`comment` 405 处／402 条（另 Book 1）、`category` 321 处／319 条、`additional_comment` 71、`link_basis` 71 处／69 条、`ai_note` 1 | Work（`comment` 另有 Book） | 正式库如左／草稿库 0 | **保留不删**：这些是志书原文与并条证据（如 `text`／`self_note`／`commentaries` 是考证类志书的原文分层，`merged_from` 记并条来源），删了就丢证据。性质记为「旧（暂留）」：新录入的同类信息写进 [common.md〈IndexEntry〉](common.md#二indexentryindexed_byemendated_by-的元素) 的正式键（`summary`、`note` 等） | 页面不专门读，原样随记录展示 | 不删 | — |
| `birth_year`、`death_year` 与 `dates` 并存 | Entity（people） | 正式库 7,142 条有其一：与 `dates` 并存 7,138、无 `dates` 4（如 `hixhd2h9bib6`）、`birth_year:null` 3；两者不一致 0／草稿库 253（皆与 `dates` 并存） | `dates`（`{birth, death, floruit…}`，见 [entity.md](entity.md)） | bim 页面 **`birth_year` 优先**、缺时回退 `dates`：`ui/src/components/detail/EntityPage.tsx:215-217`；只读 `birth_year`：`ui/src/components/EntityDetail.tsx:38-46`、`ui/src/components/IndexBrowser.tsx:1045-1047`、`ui/src/components/search/SearchResultsTable.tsx:67`、`ui/src/components/meta-home/model.ts:113-118`；`book_index_manager/entry_extractor.py:158-176` 写进 `index/`；`book_index_manager/schema_fields.py:205-209` 校两者一致 | **只增不删**：现阶段新数据两处都写、保持一致。删的条件：网站改为读 `dates` 展示、`index/` 改出 `dates` 摘要之后；未定日期 | 读者：网站经理；数据：S |
| `birth_year: null` | Entity | 正式库 3（`hixhd2h9bmql`、`hixhd2h9bgf0`、`hixhd2h9bgl5`）／0 | 不写（缺省即未考） | — | 可随时删 | S |
| 缺 `revision` | Work、Book、Entity | 正式库 0／草稿库 Work 36,721（全部）、Book 68,144（全部）、Entity 3（people `1jb8icg27zjsx`、`1jb8icg2u5edf`、`1jb8icg2z572a`） | 正式库必填；草稿库可省，升格时 bim 补 `"1.0.0"`（见 [common.md〈revision 口径〉](common.md#revision-口径)） | 草稿缺省是正当写法，不算错 | 不删（草稿库的正当状态）。旧 SCHEMA〈十〉「正式库缺 1,113 部」已补齐为 0 | — |
| `current_location`、`page_count`（值为空：`{"name": ""}`、`{"number": 0, "description": ""}`） | Work | 0／0（2026-10-09 S 已删） | 不写占位值；Work 层不录这两项（属 Book） | — | 可随时删；来源是 bim 中文键迁移（§五） | S |
| `dynasty`（顶层与 `authors[]`）非规范值、空串、`null` | Work、Book、Collection、Entity | 正式库：`Work.dynasty` 非规范 1,850、`null` 4；`Work.authors[].dynasty` 非规范 3,099、空串 4,138、`null` 4；`Book.authors[].dynasty` 非规范 320、空串 508；`Collection.authors[].dynasty` 非规范 15；`Entity.dynasty` 非规范 1,941、`null` 28。草稿库：`Work.dynasty` 非规范 1,365；`Work.authors[].dynasty` 非规范 1,438、空串 4,448；`Book.authors[].dynasty` 非规范 1,270、空串 1,099；`Entity.dynasty` 非规范 41。非规范值以 `宋`（正式库 5,312、草稿库 3,175）、`民國`、`漢`、`宋末元初`、`元末明初`、`遼金元`、`魏` 居多 | 规范朝代名（＝正式库 `subtype:"dynasty"` 条目的 `primary_name`，139 个）；判不出留空、不写空串 | build 按名查 `dynasty_reign_keys`：唯一给 `_dynasty_id`，否则给 `_dynasty_candidates`（`build/names.py`） | 未定日期，按 [common.md〈dynasty〉](common.md#dynasty-与-dynasty_basis) 的歧义拆分表逐条判 | S |
| `dynasty` 跨朝代值：`宋末元初`、`元末明初`、`遼金元`、`明末清初`、`隋唐`、`秦漢`、`齊梁`、`金元`、`宋、齊`、`隋末唐初`、`清末民初` | Work、Book、Entity | 正式库 10-09 共 862 处（宋末元初 316、元末明初 254、遼金元 243，余各 ≤12） | **准许的存量写法**，日后逐条细化为单一规范朝代（common.md〈跨朝代值〉）。这些值带有真实信息（作者跨两朝），不强改为某一朝；`period` 按〈跨朝代值〉表取或留空 | check_schema 不校 `dynasty` 值，故不报 WARN；check_v2 亦不计。build 给 `_dynasty_candidates` | 无截止日；随人物细化逐条改（overview#496 C1・R5，2026-10-09 目录经理定） | S |

「非规范」按正式库 139 个 dynasty 条目的 `primary_name` 逐字比对；别名（如 `民國`→`中華民國`）也算非规范，因为源档应写规范名。

---

## 五、仍会产出旧写法的代码（交 bim 侧）

数据删净以后，下列代码点仍会把旧写法写回源档。按「谁写」分，bim（含 `ui/`）归网站块，由网站经理排期；修好之前，审数据 PR 靠 `check_v2.py` 兜底。

| 代码点 | 会写出什么 | 建议 |
|---|---|---|
| `book_index_manager/manager.py:57` `save_item` → `book_index_manager/storage.py:180` `save_item`（落盘 `:329` 只做 `strip_nulls`） | 不拦 `_` 起首字段，也不拦 `books`、`works`、`contained_works`、`classification`、`has_text`、`promoted_to` 等已删字段：调用方传进来什么就写什么 | 落盘前按 `check_v2.py` V01／V02／V03／V09／V10／V11 拒写或剥除（`_has_text`、`_has_collated` 除外） |
| `book_index_manager/manager.py:98-130` `update_field` | `"其他版本"`→`related_books` 整栏覆盖写，不分 id 大小、不管对方一侧；`"收藏历史"`→`history`（2026-08 已删字段） | `related_books` 改走对称关系写法（只写 id 较小一侧，见 [README 总则 3](README.md#二总则)）；删 `history` 映射 |
| `book_index_manager/storage.py:346-376` `_migrate_keys`（中文键迁移，`LEGACY_KEY_MAP` 在 `:101-112`） | `作者` 字符串 → `[{"name": …, "role": "author"}]`（`:355`，英文 role，即现存 16 处的来路）；`收录于` 字符串 → `contained_in: [<字符串>]`（`:373-376`，字符串形）；`页数`／`册数` → `{"number": 0, …}`（占位 0）；`现藏于` → `current_location {"name"}`；`出版年份` → `publication_info {"year", "details": ""}`（空串占位） | role 改写 `撰`；`contained_in` 写对象形 `{id}`；不写占位值。若已无中文键数据，整段删 |
| `book_index_manager/__main__.py:192`（`add-resource`，`--type` 选项在 `:876`）；`book_index_manager/migration.py:14-29`；`ui/src/components/ResourceEditor.tsx:40`、`:80` | 新 resource 写单值 `type`（`add-resource` 还接受 `text+image`） | 改写 `types` 数组 |
| `ui/src/storage/local-storage.ts:150-189` `linkEntity`（及 `:192-215` `unlinkEntity`） | `parent_work {id, title}`（`:173-176`，已删字段且带题名副本）；`books`（`:179-184`，Work／Collection 的反向列表） | 删这两个分支；作品归属只写 `Book.work_id`，丛编成员只写成员侧 `contained_in` |
| `ui/src/storage/github-storage.ts:89-97` `fetchPromotions` | 不写数据，但仍从**草稿仓**读 `promotions.json`；草稿仓那份现为空表 `{"version": 1, "promotions": {}}`，升格对照已在正式库 `promotions/` 分片（overview#432），故 GitHub 模式下草稿→正式重定向全部落空 | 改读正式库 `promotions/<末 2 位>.json`（`ui/src/storage/bundle-storage.ts` 已按分片读，可照搬）；之后草稿仓的空 `promotions.json` 可删（S） |
| `book_index_manager/_utils.py:54` `mark_promoted` | 写记录内 `_promoted_to`／`_promoted_at`；现无调用方（死代码） | 删 |
| bim CLI（`book_index_manager/__main__.py:773-935`） | 不写旧字段，但现在没有 `link`、`build`、`classify` 子命令；README 总则 3 说对称关系「由 `bim link` 落笔」，实际上没有工具保证写在 id 较小一侧，目前只靠 `check_v2.py` V07 拦 | 补 `link` 子命令，或在格式文档里改写为「由 `check_v2.py` V07 把关」 |

---

## 六、读者回退分支：先切后拆

网站与 bim 的回退分支（「新字段有就用新的，没有再读旧的」）**一律未定删除日期，条件是数据切换完成**：F4-5 批次 3.7 完成、正式站与 bim 都只读 `_build/entry/<id>.json`。删除归**网站经理**；删之前上面 §二、§四 对应行的现存数应为 0。

| 回退分支 | 位置（bim） | 前提 |
|---|---|---|
| `adaptEntry`：把 `_books`、`_classifications`、`_related`、`_catalogs`、`_collections`、`_members`、`_works` 补回旧形 `books`、`classification`、`related_works`、`indexed_by`、`contained_in`、`books`／`contained_works`、`works` | `ui/src/core/derived-compat.ts:57-145`；入口 `ui/src/storage/derived-compat-transport.ts:17`、`ui/src/components/BookDetailLayout.tsx:251`、`:406` | 页面改为直接读 `_` 字段 |
| 读 `books`、`collections`（Work） | `ui/src/components/detail/WorkPage.tsx:66`、`ui/src/components/detail/EntityPage.tsx:179` | 同上 |
| 读 `parent_work`、`books` | `ui/src/storage/local-storage.ts:126-142` | §五 写入点删除 |
| `read_promoted_to`、`promoted_to_of` 档上旧印记优先 | `book_index_manager/_utils.py:32-49`、`book_index_manager/storage.py:533-540`、`book_index_manager/entry_extractor.py:191`、`:289` | 两库记录内 `promoted_to` 为 0（已满足），只差切换完成 |
| 兼读无下划线 `has_collated` | `book_index_manager/entry_extractor.py:267`；build `build_derived.py:314`、`:738` | 同上（build 一侧归 S） |
| `resources[].type` 回退 | `ui/src/types.ts:14-20`、`ui/src/components/detail/BookPage.tsx:293`、`ui/src/core/storage.ts:262-280`、`book_index_manager/entry_extractor.py:118-145`；build `build_derived.py:66-76`、`:655-668` | §四 `type` 改完、§五 写入点改完 |
| `role: "author"` 归「撰」 | `ui/src/core/detail-model.ts:1412` | §四 16 处改完、§五 `_migrate_keys` 改完。`displayAuthorRole`（`:1431`）隐藏无汉字 role 是防御，可留 |
| `Collection.contained_in` 字符串形 | `ui/src/components/detail/CollectionPage.tsx:148`、`ui/src/types.ts:541`（先补对象形，见 §四） | §四 19 处改完（2026-10-09 已满足） |
| `birth_year`／`death_year` 优先 | 见 §四 该行所列各处 | 网站改读 `dates` |
| 读 `classific.json` | `ui/src/components/catalog/model.ts`、`book_index_manager/__main__.py:607`、`book_index_manager/schema_fields.py:21` | 改读 `classification/zongmu/tree.json` |
| `revision_fields.py` 不 bump 名单里的旧键（`books`、`contained_works`、`has_*`、`promoted_to` 等） | `book_index_manager/revision_fields.py:16-19` | 无害，可长期留 |

**build／校验一侧（归 S）**：`build/v2common.py:32-45` 的 `LEGACY_DERIVED`、`LEGACY_REVERSE`，`build/build_derived.py:225-265` 的过渡期并集、`:860-880` 的 `source_checks` 旧字段计数、`:935-955` 的 `legacy_diffs`，以及 `.claude/qa/verify.py` 里新格式下恒 0 的旧格式检查（文件头 schema-v2 一段所列），在两库现存为 0 后已空转。删除条件同上（切换完成）；删时把 build 的 `--strict` 改为默认。`check_v2.py` 不删（见 §二末）。
