# 旧字段与旧写法

本档只回答三件事：①哪些旧写法已删净（现存 0，门禁防回潮）；②哪些**有意保留**；③哪些**还没清**（读者回退、写入代码、存量数据）。新写法见各类字段表：[common.md](common.md)、[work.md](work.md)、[book.md](book.md)、[collection.md](collection.md)、[entity.md](entity.md)、[derived.md](derived.md)。

- 总则 9「读者先切后拆」：读者新字段有就用、没有回退旧字段；数据切换完成后再删回退。build 不产出旧字段别名。
- 来历：schema-v2 迁移见 overview#451、#459、#458、#464；本档 2026-10-12 按 #568 B1a 重写，数字来自 `check_schema --json` 与 `check_v2 --summary`（正式库 HEAD 25042ef9c1），复现命令见文末。

## 一、已删（现存 0；`check_v2.py` V01–V16 长期门禁，再出现按错处理）

| 旧写法 | 新写法 / 去向 |
|---|---|
| Work `books`、`collections`；Collection `books`、`contained_works`；Entity `works` | 源：`Book.work_id`、成员侧 `contained_in[]`、`Work.authors[].entity_id`；产物 `_books`、`_members`、`_works` |
| `related_works[].title`、`contained_works[].title`、`Entity.works[].title` | 删；产物 `_related[].title` |
| 反向词 `has_part`、`studied_by`、`text_carried_by`、`followed_by`、`has_pseudepigraph`、`has_adaptation`；`commentary_on`、`related_to` | 规范词 `part_of`、`studies`、`contains_text_of`、`preceded_by`、`pseudepigraph_of`、`adapted_from`；`studies`、`related`；反向只在 `_related` |
| `related*` 写在 id 较大一侧或两侧都写；`related_works[]` 用 `work_id` 代 `id`；`related_collections[]` 对象形 | 只存 id 较小一侧；`id`；id 字符串 |
| Work `classification {l1…}` | `classification/<分类法>/members/<节点>.json`；产物 `_classifications` |
| 源档 `_` 起首派生字段（`_edition_count` 等）；无下划线 `has_text`／`has_image` 等；记录内 `promoted_to`／`promoted_at` | 产物同名带下划线；权威是 `promotions/`（见 [promotions.md](promotions.md)） |
| sidecar 对照表 6 份；`aliases`；`ai_note_fix`／`ai_note2`／`ai_note_periodfix`；`book_contained_in`、`parent_works`、`history`、`volume_count`；`parent_work {id,title}` | 并入记录／`alt_names`／`ai_note`／`related_works`／`Book.work_id` |
| 源档 `_has_text`、`_has_collated`（含 `false`） | 产物 `_has_*`，由 build 经 `--text-index` 从 book-text 推（book-index#141、overview#507） |
| Entity `birth_year`、`death_year`（含 `null`） | `dates`（book-index#139） |
| `authors[].role` 写英文 `author`；`authors[]` 里的 `cbdb_*`、`title_or_office`、`courtesy_name`、`alt_names`、`entity_basis`、`sources`、`birthplace`、`alias`、`additional_names`、`official`、`name_note` | 志书原文 role（缺省 `撰`）；人物信息归 Entity，依据入 `note`／`ai_note` |
| `resources[].type`（单值）、`resources[].group_label` | `types[]`（闭集 `image`／`text`／`physical`／`catalog`／`annotated`）；`resource_groups[].label` |
| Collection `contained_in[]` 字符串形；`related_collections: []` 空占位 | 对象形 `{id,…}`；不写 |
| Work 层 `current_location`、`page_count` 空值占位 | 不写（Book／Collection 层是正当字段，非旧写法） |

以上「已删」项的计数 2026-10-12 重扫均为 0（扫描脚本见 B1a PR 说明）；仍写旧值的是 §三 列的代码，不是数据。

## 二、有意保留（不删，不是欠账）

| 写法 | 现状（正式库） | 理由与口径 |
|---|---|---|
| `indexed_by[]` 的 `merged_from` 596、`text`／`self_note`／`commentaries` 各 592、`comment` 405（另 Book 1）、`category` 321、`additional_comment` 71、`link_basis` 71 | check_schema INFO `legacy-keep` 共 3,241，WARN 0 | 志书原文与并条证据，删了丢证据。Schema 里标 `x-legacy:"keep"`（overview#496）；新录入同类信息写 [common.md〈IndexEntry〉](common.md#二indexentryindexed_byemendated_by-的元素) 正式键 |
| 草稿库缺 `revision` | 草稿库 Work／Book 全部 | 草稿库正当状态，升格时 bim 补 `"1.0.0"`（[common.md〈revision 口径〉](common.md#revision-口径)） |
| `dynasty` 跨朝代值（宋末元初、元末明初、遼金元等） | 10-09 共 862 处（未重测） | 带真实信息，准许存量；随人物细化逐条改，无截止日（overview#496 C1・R5） |
| `classific.json`（仓根旧分类词表） | 正式库有、草稿库无 | 2026-10-12 裁决：**保留**，由 build 从 `classification/zongmu/tree.json` 生成；读者 web 3 个脚本、bim 4 处仍读，改读 tree 前不删。读者全改完另立条再删 |
| `check_v2.py` WARN 9（D2 2／D3 2／R1 5） | 7 条列入 `.claude/qa/check_v2_allow.txt`（降为 INFO）；承平 `hixi1ubml2ch`、鳳凰 `hixi1ubm9ts3` 2 条未核实，仍算 WARN | 清单只收逐条核过的例外；清单外新增 WARN 才算新问题；那 2 条待 Mirren 核后再加 |

## 三、还没清

**数据（待 S 修，规则在对应字段表）**：`dynasty` 非规范值、空串、`null`（10-08 数：Work 1,850、`authors[].dynasty` 非规范 3,099／空串 4,138，其余见 [common.md〈dynasty〉](common.md#dynasty-与-dynasty_basis)；check_schema 不校，**未重测**）。

**读者回退分支（网站经理，数据切换完成后删）**：bim `ui/src/core/derived-compat.ts`（补回 `books`／`works`／`classification`／`_members`）；`WorkPage.tsx`、`EntityPage.tsx` 读 `books`／`collections`；`ui/src/storage/local-storage.ts` 读 `parent_work`；`ui/src/types.ts:getResourceTypes` 兜 `type`；`CollectionPage.tsx` 的 `contained_in[0]` 只认字符串形（对象形上级丛编显示不出）；`has_collated` 兼读在 `entry_extractor.py`、`_utils.py:read_promoted_to` 兼读 `_promoted_to`。行号随提交漂移，以 `grep` 为准。

**仍会写回旧写法的代码（bim 侧，网站经理排期；修好前靠 `check_v2.py` 兜底）**：`manager.py`／`storage.py` 的 `save_item` 不拦已删字段；`update_field` 的「其他版本」整栏覆盖 `related_books`、「收藏历史」写 `history`；`storage.py:_migrate_keys` 的中文键迁移（`role:"author"`、字符串 `contained_in`、占位 0）；`add-resource` 与 `ResourceEditor.tsx` 写单值 `type`；`local-storage.ts:linkEntity` 写 `parent_work`／`books`；`github-storage.ts:fetchPromotions` 读草稿仓空 `promotions.json`；`_utils.py:mark_promoted` 死代码；bim CLI 无 `link` 子命令（对称关系仅靠 V07 把关）。

**build／校验侧（S）**：`build_derived.py` 对 `books`／`works`／`contained_works` 与 `type` 的并集过渡分支；`.claude/qa/verify.py` 的 `_edition_count`／`_member_*` 校验在新格式下恒 0，待删。

**复现**：`python3 schema/check_schema.py --json 报告.json --quiet-warn`；`python3 .claude/qa/check_v2.py --summary`；草稿库加 `--root ../book-index-draft --draft`。
