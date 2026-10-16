# Entity 通用字段

总览与子类型索引见 [../entity.md](../entity.md)。体例见 [../README.md〈八、字段表体例〉](../README.md#八字段表体例)。各子类型专有字段见同目录对应文件。

「适用」写在「必填」列里。「专名」指 `dynasty`／`reign`／`office`／`place` 四子类型及官署。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | **必填**（全部） | 原生 | 记录 id | base36 snowflake，正式库 12 字符、草稿库 13 字符，类型位 4 | bim | `"hixhd2h9bdqq"` |
| `type` | string | **必填**（全部） | 原生 | 记录类型 | 恒为 `"entity"` | bim | `"entity"` |
| `subtype` | string | **必填**（全部） | 原生 | 子类型 | `people`｜`collective`｜`dynasty`｜`reign`｜`office`｜`place`｜`seal`｜`publisher`；读者遇缺省按 `people` 读（现存无缺） | 录入 | `"people"` |
| `schema_version` | integer | **必填**（全部） | 原生 | 记录格式大版本 | `1`（V15） | bim | `1` |
| `primary_name` | string | **必填**（全部） | 原生 | 最通行的名字 | 自由文本，繁体；dynasty 须是规范朝代名（见[dynasty](dynasty.md)） | 录入 | `"蘇軾"` |
| `alt_names` | array<AltName> | 可选（全部） | 原生 | 别名 | 见[alt_names](_alt-names.md) | 录入 | `[{"name":"子瞻","type":"字"}]` |
| `dynasty` | string | 可选；people、未分类 collective | 原生 | 所属朝代（规范名） | 见 [common.md〈朝代规范名〉](../common.md)；专名子类型与新建官署条**不写**（朝代由 `dynasty_ids` 等表达）。正式库 people 23,946 条有值（其中 28 条为 `null`，旧） | 录入 | `"北宋"` |
| `dynasty_basis` | string | 可选；同 `dynasty` | 原生 | 朝代的依据 | 自由文本 | 录入 | `"cbdb:birth/death_name=北宋"` |
| `period` | string | 可选；people、未分类 collective、dynasty | 原生 | 时代轴 slug | 12 个 slug 之一，见 [common.md〈period〉](../common.md)；在 dynasty 条里含义见[dynasty](dynasty.md) | 录入 | `"song"` |
| `period_basis` | string | 可选；people、未分类 collective | 原生 | `period` 的依据 | 自由文本 | 录入 | `"据 dynasty「北宋」自动归并"` |
| `native_place` | string | 可选；people | 原生 | 籍贯 | 自由文本（正式库 3 条为 `null`，旧） | 录入 | `"山陰"`、`"眉山"` |
| `native_place_basis` | string | 可选；people | 原生 | 籍贯的依据 | 自由文本 | 录入 | `"CBDB 3767 index_addr（2026-09-06 CBDB enrich）"` |
| `native_place_entity_id` | string | 可选；people | 原生 | 籍贯对应的地名 Entity id | 非空字符串，须指向 `subtype=place` 的 Entity（格式同 Entity id）。旧 `native_place`／`native_place_basis` 保留、语义不变；缺此字段的旧数据仍合法，不要求补。`check_v2`：N01 非 people 或非字符串＝ERROR；N02 不存在／非 place＝ERROR；N03 指向墓碑＝WARN，提示改指 `merged_into`。同名异地靠 id 区分，不靠 `primary_name`（overview ai-team#2，2026-10-15） | 录入 | `"hixi5xhv38jl"` |
| `title_or_office` | string | 可选；people | 原生 | 著录所见官职 | 自由文本（正式库 1 条） | 录入 | `"散騎常侍"`（顾长康 `hixhi7qcyxa8`） |
| `name_basis` | string | 可选；people | 原生 | 名字的依据（正名经过） | 自由文本（正式库 164 条） | 录入 | `"catalog：著錄之撰人名（2026-09-06 撰人書名切分訂正）"` |
| `birth_year` | integer | 可选；people | 原生 | 生年（已删） | 已删（book-index#139 B2，正式库 0 个文件）；读 `dates.birth` | — | — |
| `death_year` | integer | 可选；people | 原生 | 卒年（已删） | 已删（book-index#139 B2）；读 `dates.death` | — | — |
| `dates` | object | 条件：people、dynasty、reign 可写；office、place **不得有** | 原生 | 结构化起讫／生卒 | 按子类型放行的键见[dates 与 external_ids](_dates-external-ids.md) | 录入 | `{"birth":1036,"death":1101,"floruit":null,"basis":"現行字段"}` |
| `external_ids` | object | 可选（全部）；专名只许 `wikidata_id` | 原生 | 外部库 id | 子键见[external_ids 子键](_dates-external-ids.md#external_ids-子键) | 录入、bim | `{"cbdb_id":3767,"wikidata_id":"Q36020"}` |
| `description` | Description | 可选；官职概念条、官署概念条与合称条**必填** | 原生 | 介绍与出处 | 形状同 [common.md〈Description〉](../common.md)，但 Entity 的 `text` 可省（正式库 people 5,886 条 `description` 里只有 213 条有 `text`，其余只记出处），`sources` 必有；Entity 的出处一律记 `description.sources` | 录入 | `{"text":"都開封。","sources":[]}` |
| `merge_history` | array<object> | 可选；people | 原生 | 早期并条账（2026-09-09 一次写入） | 每项 `{primary_name, date, reason}`（正式库 4,409 条） | 迁移 | `[{"primary_name":"曾仲質","date":"2026-09-09","reason":"draft/production 同人同书重出（CBDB auto_create 批次遗留，纯冗余无增量），2026-09-09 併條"}]` |
| `merged_in` | array<object> | 可选；留存方（keeper） | 原生 | 并入本条的他条 | 每项 `{id, primary_name, at, by, rule, why}`（正式库 people 313 条／324 项，collective 1 条） | 录入 | 见[people](people.md)馬令例 |
| `merge_history[].primary_name` | string | **必填** | 原生 | 并入前的名 | 自由文本 | 迁移 | `"曾仲質"` |
| `merge_history[].date` | string | **必填** | 原生 | 并条日 | `YYYY-MM-DD` | 迁移 | `"2026-09-09"` |
| `merge_history[].reason` | string | **必填** | 原生 | 并条原因 | 自由文本 | 迁移 | |
| `merged_in[].id` | string | **必填** | 原生 | 被并方 id | entity id | 录入 | `"hixhd2h9bmfu"` |
| `merged_in[].primary_name` | string | 可选 | 原生 | 被并方名 | 自由文本 | 录入 | `"馬令"` |
| `merged_in[].at`、`by`、`rule`、`why` | string | 可选 | 原生 | 并入日、经手人、裁定依据、理由 | 自由文本（`at` 为 `YYYY-MM-DD`） | 录入 | 见[people](people.md)馬令例 |
| `merged_into` | string | 可选；被并方 | 原生 | 本条已并入的条目 id | entity id；被并条只留 `schema_version`、`id`、`type`、`subtype`、`primary_name`、`merged_into`、`revision`、`revised_at`（正式库 2 条）。**并条一律写墓碑、不删档**（2026-10-09 起） | 录入 | `"hixhd2h9biza"`（成無巳 `hixhd2h9blyf`） |
| `retired` | boolean | 可选 | 原生 | 本条已退役 | 只写 `true`（正式库 5 条） | 录入 | `true` |
| `retired_reason` | string | 条件：`retired` 时必填 | 原生 | 退役原因 | 自由文本 | 录入 | `"N3 壞名 entity 歸正（2026-08-24 南北朝斷代與壞名專項）：…"`（廋信 `hixhd2h9bq93`） |
| `suppressed_fields` | array<string> | 可选；people | 原生 | 人工确认 CBDB 值有误而清空的字段名 | 字段名（顶层键名，或 `external_ids` 的子键名）；正式库 2 条，值均为 `"cbdb_id"`。见[collective](collective.md) | 录入 | `["cbdb_id"]` |
| `ai_note` | string | 可选（全部） | 原生 | 录入备注 | 自由文本，见 [common.md〈ai_note〉](../common.md) | 录入 | |
| `todo` | array<object> | 可选（全部） | 原生 | 待办 | 每项 `{what, by?, date?}`，`what` 非空；两库 Entity 现无此键 | 录入 | |
| `review` | object | 可选（全部） | 原生 | 审核状态 | `{status, by?, date?}`，`status` ∈ `unreviewed`｜`reviewed`｜`disputed` | 录入 | `{"status":"unreviewed"}` |
| `revision` | string | **正式库必填**（全部） | 原生 | 记录内容版本 | `"主.次.补"`，新条 `"1.0.0"`；口径见 [common.md〈revision〉](../common.md#revision-口径)。Entity 也必填（overview#468），正式库已全补；草稿库 people 3 条缺（`1jb8icg27zjsx` 章淵、`1jb8icg2u5edf` 褚遂良、`1jb8icg2z572a` 沈瀛），升格时由 bim 补 | 录入、bim | `"1.1.0"` |
| `revised_at` | string | 可选（与 `revision` 同写） | 原生 | `revision` 最近一次改动日 | `YYYY-MM-DD` | 录入、bim | `"2026-10-07"` |
| `updated_at` | string | 可选（全部） | 原生 | 记录最近改动时刻 | ISO 8601 时间（现存也有只写日期的：dynasty 23 条、reign 233 条，如 `"2026-10-07"`）；草稿库 people 全无此键 | bim | `"2026-08-24T00:00:00+00:00"` |

各子类型的专有字段见[dynasty](dynasty.md)[collective](collective.md)；不在本表与各子类型表里的键，源档不写（见[禁字段与派生](_forbidden-derived.md)）。
