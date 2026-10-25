# 格式变更记录

自 schema-v2（2026-10-07）起记。每条写：日期（洛杉矶）、改了什么、依据（issue／PR）。更早的沿革见 git 历史中的 `SCHEMA.md`。

---

## 2026-10-25　Collection 加 `merged_into`／`merged_from`（墓碑；去重方案部分 6，用户 10-25 放行）

- `collection.schema.json` 加 `merged_into`（Id）与 `merged_from`（MergedFrom）；`collection.md` 字段表加两行，`common.md〈并条账〉`、`derived.md〈八〉` 同步。形状照 Book 墓碑（2026-10-13）：墓碑只留 `schema_version／id／type／subtype／title／merged_into／revision／revised_at`，keeper 的 `merged_from` 记被并 id。
- 成员关系只在成员侧，所以并 Collection 时被并者成员的 `contained_in` 改指 keeper（同项已有则合并，保留 `volume_index`／`sub_items`／`details`）；网站 `item-redirect` 读 entry 的 `merged_into`，对 Collection 同样 308（kaiyuanguji-web `item-redirect.ts` 不分类型）。
- `scripts/audit-merge-ledger.py` 支持 `type: collection`（T/L/R 同查）。
- 背景：正式库并条审查规则第 6 条「另立 Collection 墓碑 schema 后再并」；首批是叢書线把同一总目源记录录成两个 Collection 的 7 组。

## 2026-10-19　Work 加 `merged_basis`（草稿库墓碑的并条留痕；schema 补登，不改数据）

- `schema/json/work.schema.json` 加 `merged_basis`（object：`rule`、`at`、`by` 为字符串，`author_as_written`、`indexed_by` 不限类型，不许其他键）；`common.md〈并条账〉` 与 `work.md` 字段表各补一行。
- 背景：并条脚本在保留方位于正式库时不改正式库文件，把被并方的 `indexed_by`、作者异写写进草稿库墓碑的 `merged_basis`。草稿库已有 2696 个这样的墓碑（跨部查重 2287、子部一近重复复核 210、叢書去重 199），此前 check_schema 对它们报 `unknown-field`。
- 正式库没有带 `merged_basis` 的档。

## 2026-10-19　`measure_info` 卷数一律用汉字数字（用户报《永樂大典》显示「22877（阿拉伯數字）卷」）

- 数据：正式库 165 条 `measure_info` 由阿拉伯数字改为汉字数字（158 条形如「1卷」「20卷」，《永樂大典》「22877（阿拉伯數字）卷」→「二萬二千八百七十七卷」，5 条夹全角「０」如「一百０八冊」→「一百零八冊」）；同步改 `index/` 分片里的同一字段。
- 简介：上面 165 条里简介照抄了旧写法的一并改；另 185 条 J11／南北朝批次简介的「某撰，30卷。」「》作6卷，卷數異文」模板句改为汉字数字。《永樂大典》简介「別作二千九百卷、二千二百十一卷、二千八百七十七卷」丢了「萬」且把本数当异数，改为「別作二萬二千九百卷、二萬二千二百十一卷」；《破萬總錄》《大一統志》删去与本数相同的假异数「別作1000卷」。各条 `revision` 记 patch。
- 引文（`indexed_by[].title_info` 等）照原样不动；现代体例的叙述文（如出版册数）不动。
- `schema/json/{work,book,collection}.schema.json` 的 `measure_info` 加 `not` 闸：整串是「阿拉伯数字＋量词」或汉字数字中夹「0／０」即报 ERROR。

## 2026-10-17　entity 各子类型文档加〈真实示例〉，总览加「按类型找示例」入口（用户要求；纯文档＋一条测试）

- `schema/entity/{people,collective,dynasty,reign,office,place,seal,publisher}.md` 开头各加〈真实示例〉小节：2–5 个典型条目，列仓内源档路径与 `index/entities/N.json` 分片路径，并说明各演示什么。
- `schema/entity.md`、`schema/README.md`、`schema/entity/_common.md` 加「按类型找示例」入口表。
- `tests/test_entity_examples.py`（新）：核实示例源档存在、subtype 与所在文档一致、id 在所指 index 分片里，入口表链接都能解析。不改任何字段规则或数据。

## 2026-10-16　新增派生 `index/seals.json`＋`index/seals/<seal_id>/<n>.json`（印章反查表；GUJI-542 P2，Sylvie 核）

- `build/sealindex.py`（新）：由 `Book.provenance[].seal_marks` 派生每枚现行印章的 Book 计数与分页（每页 ≤500）；`build_derived.py` 产出并自校验，`--write-index` 写回仓内；`report.json` 加 `index.seals`（含与手写 `appears_in` 的对账，只报不拦）。
- `verify.py` 加「印章反查表漂移」（计入 FAIL）；`check_schema --build` 跳过这两处（形状不同于 `{id: 条目}`）。
- 说明见 derived.md〈8.3〉。不改任何源记录；现 `seal_marks` 尚无数据，故现有 5 枚印章 `count` 均为 0（回填在 P4）。

---

## 2026-10-16　拆分 `schema/entity.md`：总览＋`schema/entity/` 分档（纯文档；用户要求，Sylvie 核）

- `entity.md` 改为总览（子类型一览、专名硬约束、通用部分概要、校验码索引、旧〈章节号〉对照表）。
- 新增 `schema/entity/`：`people`／`collective`（含官署）／`dynasty`／`reign`／`office`／`place`／`seal`／`publisher`（各含八列字段表、规则、示例、该类型校验码）；`_common`（通用字段）、`_alt-names`、`_dates-external-ids`、`_forbidden-derived`、`_checks`（校验码总表）。
- 旧〈六·四〉〈六·五〉等章节号按 `entity.md`〈五、旧章节号对照〉找；下方旧条目里的 `entity.md〈…〉` 为历史写法，不改。
- 不动 JSON schema 结构与数据；仅 `entity.schema.json`、QA 注释里的路径说明同步。

---

## 2026-10-16　Entity 新增 `publisher`（出版社／刻书机构；GUJI-539 v3，用户当日拍板；Sylvie 核）

- `entity.md` 增〈六·五〉与 K01–K09；`entity.schema.json` 增 `publisher` 子类型及字段（`publisher_kind`／`kind_also`／`dates_basis`／`locations`／`owners`／`status`），其他子类型的「不许带」清单同步加；`entity_subtypes.py` 增 `_check_publisher`（K01–K08）与 K09。
- `alt_names[].type` 增 `堂號`、`牌記名`（23→25 值）。
- `authors[].entity_id`（Work／Book／Collection）说明由 people／collective 放开到 people／collective／publisher（common.md）；现有校验只查悬空，不限类型，无代码改动。
- 取舍（用户定）：不设 `publisher_sub`、`predecessors`、`legal_name`、「書房」类；书坊集群不建；官署、书院一律 collective，不建 publisher；外国出版社暂不收；全称入 `alt_names`（`全稱`）。

---

## 2026-10-15　people 加 `native_place_entity_id`（籍贯回挂地名 Entity；GUJI-237，ai-team#2 Marcus 6182137410）

- `entity.schema.json` 加 `native_place_entity_id`（非空字符串），非 people 子类型的「不许带」清单同步加；`entity.md` 字段表加一行。旧 `native_place`／`native_place_basis` 保留不改语义；缺此字段的旧数据仍合法。
- `check_v2` 增 N01（非 people 或非字符串，ERROR）、N02（不存在或非 place，ERROR）、N03（指向墓碑，WARN，提示跟 `merged_into`），实现在 `.claude/qa/entity_subtypes.py` 的 `check_native_place`，草稿库用 `--ref-root` 指正式库即可解析正式 id。
- 不进 `index/entities`（同 `native_place` 不入索引）；网站展示（EntityPage 读该 id 链到地名页）另案，不在本次。

## 2026-10-13　Book 加 `merged_into`（墓碑，用户定「Schema 口径放行，Book 墓碑用 A」；GUJI-89 薈要重复 Book 合并）

- `book.schema.json` 加 `merged_into`（Id）；`book.md` 字段表加一行。墓碑只留 `schema_version／id／type／title／work_id／merged_into／revision／revised_at`，与 Work 墓碑同形；keeper 的 `merged_from` 记被并 id。网站 `item-redirect` 读 `merged_into`，对 Book 同样 308。

## 2026-10-12　删一次性脚本（overview#568 B1b，book-index#162）

- 删 `scripts/`（`oneoff` 6 个、`a2`／`a3`／`b2`／`d` 4 个）、`.claude/qa/s5/`、`s3_collection_count.py`、`audit_biejii_dup.py`；来历一句话见 `.claude/qa/known-issues/oneoff-删除记录-20261012.md`。
- 登记不删：`.claude/qa/s2/`、`s4/`（测试依赖），`s1/`、`b5/`、`rh/`（可复用工具）。

## 2026-10-12　`legacy.md` 重写；`check_v2` 增已知例外清单（overview#568 B1a，book-index#160）

- `schema/legacy.md` 重写为三节（已删／有意保留／还没清），不再列文件行号。
- 新增 `.claude/qa/check_v2_allow.txt`，`check_v2.py` 读它把已核实的例外 WARN 降为 INFO；承平、鳳凰两条未核实，仍报 WARN（核对卡 overview#578）。

## 2026-10-11　`entity.schema.json` 删 `birth_year`／`death_year` 占位（overview#506 B 第一批 3/3）

- 源档 Entity 的 `birth_year`／`death_year` 已 0 个文件（B2），schema 里的 `null` 占位（`x-legacy`）及各子类型「不许带」清单里的两项一并删；schema 本就 `additionalProperties: false`，此后源档再带这两键即 ERROR。`index/` 里的同名键（网站读，由 `dates.birth`／`dates.death` 推出）不受影响。
- `derived.md`、`entity.md` 里对应说明改为「读 `dates.*`」；`entity_merge.py`／`mergework.py` 里指向已删 `migrate_v2.py` 的提示语改掉。

## 2026-10-11　build 删旧容忍（overview#506 B 第一批）

- `build/build_derived.py`：删过渡期旧反向欄并集（`Work.books`、`Entity.works`、`Collection.books`／`contained_works`）、`legacy_flag`、记录内 `_promoted_to`／`promoted_to` 兜底（`promoted_to` 只取 `promotions/`）、`classification` 旧形回退（无 `classification/` 目录时卡片不带分类）、`has_text_lost_work`／`has_text_gained_work`（源 `_has_text` 已无）。`source_checks` 只剩一条：源档任何 `_` 起首字段即报错（`source_fields` 只剩 `unknown_underscore_fields`／`unknown_underscore_where`）。`--strict` 现恒为真，命令行参数保留为空操作。
- `build/v2common.py`：删 `LEGACY_DERIVED`、`LEGACY_REVERSE`。
- 契约（〈二〉到〈九〉的产物）不变；`report.json` 不属契约。数据 0 改动。

## 2026-10-10　删 `birth_year`／`death_year`（book-index#139 B2）

- 依据 book-index#139（B2）：Entity 的 `birth_year`／`death_year` 已删净（10-11 核：Work／Book／Collection／Entity 各类 0 个文件）。展示与索引读 `dates.birth`／`dates.death`。
- `entity.md`、`legacy.md` 中两键由「并存」改为「已删」；`schema/json/entity.schema.json` 的 `null` 占位保留，读时按缺省。

## 2026-10-10　`cbdb_aliases` 改名为 `cbdb_id_alt`（book-index#133 A1）

- `external_ids.cbdb_aliases` 改名为 `external_ids.cbdb_id_alt`，值不变；删 `cbdb_aliases_note`。`entity.md`、`schema/json/entity.schema.json` 同步去掉旧键（旧键 0 个文件）。

## 2026-10-10　收回 `_has_text`／`_has_collated` 源档豁免（overview#507 工作包 E）

- 源档已无这两键（book-index#141 删净）。`.claude/qa/check_v2.py` 去掉 `UNDERSCORE_EXEMPT`、`build/v2common.py` 去掉 `SOURCE_UNDERSCORE`、`build/build_derived.py` 源检不再放行：源档任何 `_` 起首字段（含这两个）一律报错（check_v2 V01；`build_derived --strict` 的 unknown_underscore_fields）。
- `build_derived.py` 的 `--text-index` 仍可不给（旧行为＋警告），本包未动；是否改为必给待经理定。**已定（Mason 10-10）：必给**，见 book-index#144。
- `build/migrate_v2.py` 的 M3 仍把旧 `has_text`／`has_full_text`／`has_collated` 折进 `_has_text`／`_has_collated`（历史迁移，已跑完）；重跑会产出被新规则拦下的记录，测试样本已在 M3 后手工移掉。

## 2026-10-10　`_has_text`／`_has_collated` 改从 book-text 推（overview#506 工作包 C）

- `build/build_derived.py` 新参数 `--text-index <book-text>/index/texts`；给了，entry 的 `_has_text`／`_has_collated`、卡片 `txt`、`index/` 的 `has_text`／`has_collated` **统一口径**：resources 含 `text`（Work 并其 Book）或 book-text 有该 id 且版本 `quality` 不是 `none`／`placeholder`；`_has_collated` 看 `kind ∈ {collated, self_collated}`；id 沿 `merged_into` 解析，悬空 id 写入 `report.json` 的 `dangling_text_ids`。源档旧值不再算。不给＝保持旧行为并警告。
- `report.json` 新增 `text_index`（接入统计、丢掉的 Work 清单 `has_text_lost_work`）。
- 文档同步：`derived.md`、`text-files.md`、`legacy.md`、`build/README.md`。
- 待办：`index/texts` 条目现不带 `quality`（在 `manifest.json`），需文本总管让 `build_texts_index.py` 写入，否则 `placeholder`／`none` 版本过滤不生效。

---

## 2026-10-09　Entity 并条一律写墓碑（overview#409）

- `.claude/qa/entity_merge.py`：被并方不再删档，改写为墓碑（只留 `schema_version`、`id`、`type`、`subtype`、`primary_name`、`merged_into`、`revision`、`revised_at`）；新增 `--by`（`merged_in.by`）；拒绝把墓碑当 loser 或 keeper。回归测试同步改。依据：目录经理 10-09（徐光啓并入徐光啟时发现原脚本删档）。
- `schema/entity.md`〈merged_into〉与〈并条〉两处记明「并条一律写墓碑、不删档」。
- 核对结论：网站 `/item/<id>` 按记录上的 `merged_into` 308 跳到留存方（kaiyuanguji-web `item-redirect.ts`），Entity 同样适用；check_schema、check_v2 对墓碑不报；build 仍把墓碑（Work 395、Entity 2）列入 `index/`；目录经理定不排除，`derived.md`〈八〉记「index 含墓碑条，检索端自行过滤」。
- `.claude/qa/verify.py`：works 索引的 dynasty 口径改为「第一个有朝代的作者，无则顶层」，与 build（book-index#75）一致；此前按 `authors[0]` 算，报 14 条假漂移。

## 2026-10-08　格式定义终版（overview#496）

文档：
- 新建 `schema/` 目录作为格式的唯一权威：README、common、work、book、collection、entity、classification、promotions、text-files、derived、legacy、cataloging-rules、本档，以及 `json/` 下的 JSON Schema 2020-12 与校验脚本 `schema/check_schema.py`。
- `SCHEMA.md` 缩成指向 `schema/` 的目录页；`book-index-draft/SCHEMA.md` 照旧只是指针。
- 文档改为简体中文；字段值、枚举值、引文、例子照数据原文。
- 派生字段的精确形状收回本仓（[derived.md](derived.md)），以 build 现行产出为准，不再引用 overview 的设计文档。

裁定（目录经理 10-08，overview#496）：
- `authors[].role` 是开放词表（录志书原文的责任方式），必填、非空、汉字；有专门含义的值为 `撰`、`舊題撰`、`託名`。英文 `author` 列入修正方案。
- `authors[]` 正式可选键：`source`、`name_basis`、`dynasty_basis`、`role_basis`、`original_name`、`note`；`cbdb_*` 与其余少量键为旧（暂留）。
- `indexed_by[]` 补入正式可选键 `author_info`、`edition`、`volume`、`page`、`juan`、`note`、`section_basis`、`catalog_no`；`merged_from`、`text`、`self_note`、`commentaries`、`comment`、`category`、`additional_comment`、`link_basis`、`ai_note` 为旧（暂留），保留不删。
- `resources[].types` 定为闭集 `image`｜`text`｜`physical`｜`catalog`｜`annotated`；单值 `resources[].type` 为旧（暂留）。补记 `short_name`、`volumes`、`expected_volumes`、`root_type`、`color_mode`、`metadata` 等既有键。
- `revision` 正式库必填，草稿库可省（升格时 bim 补 `"1.0.0"`）。
- `Collection.contained_in` 正式形状定为对象形 `{id}`，与 Book、Work 一致；现存字符串形列为旧写法，读者在数据改完前两种都认。
- 派生字段以 build 现行产出（契约 3）为准；早期设计里的 `_members_total`、`rel`／`dir`、150／300 分页、`_incoming`、`_works` 分页、`_catalogs` 的 `source_bid` 键作废。
- 规范里写的写入口 `bim link`、`bim classify`、`bim build` 尚未实现（bim 无这三个子命令），文档改为如实写「规划中」，现由 `check_v2.py` 与 build 自校验把关。
- 录入判准移入 [cataloging-rules.md](cataloging-rules.md)；整理本、辑佚档的格式见 [text-files.md](text-files.md)（两类文件已不在本仓）。

按现行代码与数据订正的旧文档说法（不改数据、不改代码）：
- promotions 一律指分片 `promotions/`，不再写整档 `promotions.json`。
- `related_works` 成对词是 6 对（`part_of`、`studies`、`contains_text_of`、`preceded_by`、`adapted_from`、`pseudepigraph_of`），不是 4 对；`adapted_from`、`pseudepigraph_of` 不是单向词。
- `_lineage_graph_ref` 的值是路径字符串 `"lineage/<work_id>.json"`；`lineage/<work_id>.json` 是 build 汇出的 `{work_id, nodes, edges}`，不是「原样取自源」。
- 草稿库 `_build` 的 `catalog/` 页元素、`_hubs.json` 的 `t` 等照实记录，见 derived.md。
- index 中 Entity 条目的 `type` 是小写 `entity`，Work／Book／Collection 首字母大写。
- 正式库 id 长度：Book 10 字符，Work、Collection、Entity 12 字符（不补前导零）；草稿库 13 字符。
- 路径分片 `{c1}/{c2}/{c3}` 是 id 末三字符按原序。
- `dynasty_basis`、`period_basis` 实为自由文本（宜以代码起首），不是闭集。
- `Work.juan_count.unit` 尚未回填（0 条）；Book 已有。
- 旧附三待定项已结：`Work.collections`（0 条，并入 `contained_in`）、`Entity.aliases`（0 条，并入 `alt_names`）、`ai_note_fix` 等三键（0 条，并入 `ai_note`）、武英殿 sidecar 顶层信息（sidecar 已于 M6 全部删除）、志书成员页（overview#468：暂不做，`catalog/` 照常产出）。

## 2026-10-08　build 契约 3（book-index#41）

- Book、Collection 的产物加 `_related`：对称关系两侧的并集，每项带 `t`、`relation:"related"`、`direction`。纯增量，overview#458 已通知网站经理。

## 2026-10-08　promotions 分片（book-index#43）

- 根目录整档 `promotions.json` 切成 `promotions/<草稿 id 末 2 位>.json`，每片形状同原整档；整档删除，不双写。读写一律经 bim `PromotionsStore`／`load_all` 或 build `read_promotions_raw`。

## 2026-10-07　专名子类型（overview#464）

- Entity 新增 `reign`、`office` 子类型，`dynasty`、`place` 转正；`collective` 加 `collective_kind`，官署（`collective_kind=官署`）立两层＋合称结构。
- `alt_names[].type` 增 10 项（`簡稱`、`合稱`、`避諱`、`別稱`、`雅稱`、`全稱`、`異寫`、`舊稱`、`異稱`、`今名`），增 `alt_names[].ambiguous`。
- 专名四类的 `external_ids` 只许 `wikidata_id`；不存任何 `cbdb_*`、`chgis_id`、`dila_*`；地名不带坐标。
- 规范朝代名表与 dynasty 条目逐字一致（139 条）；高麗自朝鮮拆出。
- `check_v2.py` 加 E1、D1–D3、R1、A1、O、P、I 系列校验码。
- build 契约 2：专名派生字段（`_children`、`_ancestors`、`_reigns`、`_dynasty`、`_ruler`、`_index_in_reign`、`_same_name`、`_compounds`、`_subordinates`、`_members`、`_offices`、`_span`、`_dynasty_id`、`_dynasty_candidates`）与 `dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`。

## 2026-10-07　`authors[].role` 必填扩至 Book、Collection；Entity 套 revision（overview#468）

- `check_v2.py` V08 扩至 Book、Collection。
- Entity 也套 `revision`，缺者统一补 `"1.0.0"`。
- 志书成员页（`_member_catalog`）暂不在网站用，`catalog/` 照常产出。
- `Collection.related_collections` 只能写丛编 id 字符串。

## 2026-10-07　`schema_version` 必填；`description.sources` 两种形状（overview#473）

- Work／Book／Collection／Entity 的 `schema_version` 必填，值为整数 `1`（V15）。
- `description.sources[]` 的元素可为字符串或对象，长期并存（V16）。

## 2026-10-07　schema-v2（overview#451、#459）

- 一个事实只写一次：源档只存关系的一侧，反向、计数、对方题名由 build 生成。
- 成对关系只写规范方向；对称关系存 id 较小一侧。
- 源档不写 `_` 起首字段（`_has_text`、`_has_collated` 暂留）；派生字段只在 `_build/entry/` 里。
- 删除 `Work.books`、`Collection.books`、`Collection.contained_works`、`Entity.works`、`related_works[].title`、反向关系词、`commentary_on`、`related_to`。
- 分类移出 Work，改为 `classification/<分类法>/` 目录；Collection 不分类；取消「未分類」占位节点；成员行不存 `basis`。
- `Work.contained_in[]` 加 `group`、`details`；`Book.contained_in[]` 加 `sub_items`；sidecar 对照表并入记录后删除。
- `Work.preferred_book` 取代 `Work.books` 的手排顺序。
- 迁移 M0–M6 在两库跑完；迁移不改 `revision`／`revised_at`。
- `index/` 改由 `build/build_derived.py` 生成；build 产物契约 v1（overview#458）。
