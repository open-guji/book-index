# Entity 通用字段

总览与子类型索引见 [../entity.md](../entity.md)。体例见 [../README.md〈八、字段表体例〉](../README.md#八字段表体例)。各子类型专有字段见同目录对应文件。

## 按类型找示例

每个子类型的字段表文件开头都有〈真实示例〉小节：2–3 个典型条目的仓内真实路径，并说明各演示什么。要看「实际写出来长什么样」，从下表进。

| 子类型 | 字段表与示例 | 首选示例（源档） |
|---|---|---|
| `people` | [people.md〈真实示例〉](people.md#真实示例) | [Entity/d/q/q/hixhd2h9bdqq-蘇軾.json](../../Entity/d/q/q/hixhd2h9bdqq-蘇軾.json)（蘇軾） |
| `collective` | [collective.md〈真实示例〉](collective.md#真实示例) | [Entity/o/p/e/hixhd2h9bope-仙鶴堂.json](../../Entity/o/p/e/hixhd2h9bope-仙鶴堂.json)（仙鶴堂） |
| `dynasty` | [dynasty.md〈真实示例〉](dynasty.md#真实示例) | [Entity/x/g/o/hixi1ubjrxgo-趙宋.json](../../Entity/x/g/o/hixi1ubjrxgo-趙宋.json)（趙宋） |
| `reign` | [reign.md〈真实示例〉](reign.md#真实示例) | [Entity/w/u/9/hixi1ubqbwu9-萬曆.json](../../Entity/w/u/9/hixi1ubqbwu9-萬曆.json)（萬曆） |
| `office` | [office.md〈真实示例〉](office.md#真实示例) | [Entity/r/m/6/hixi4udstrm6-尚書.json](../../Entity/r/m/6/hixi4udstrm6-尚書.json)（尚書） |
| `place` | [place.md〈真实示例〉](place.md#真实示例) | [Entity/c/n/5/hixi4ugtgcn5-潼川府.json](../../Entity/c/n/5/hixi4ugtgcn5-潼川府.json)（潼川府） |
| `seal` | [seal.md〈真实示例〉](seal.md#真实示例) | [Entity/4/e/a/hixi6zykf4ea-文淵閣寶.json](../../Entity/4/e/a/hixi6zykf4ea-文淵閣寶.json)（文淵閣寶） |
| `publisher` | [publisher.md〈真实示例〉](publisher.md#真实示例) | [Entity/f/y/8/hixi70yf5fy8-汲古閣.json](../../Entity/f/y/8/hixi70yf5fy8-汲古閣.json)（汲古閣） |

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
| `dates` | object | 条件：people、dynasty、reign 可写；office、place **不得有** | 原生 | 结构化起讫／生卒 | 按子类型放行的键见[dates 与 external_ids](_dates-external-ids.md) | 录入 | `{"birth":1036,"death":1101,"floruit":null,"basis":"現行字段"}` |
| `external_ids` | object | 可选（全部）；专名只许 `wikidata_id` | 原生 | 外部库 id | 子键见[external_ids 子键](_dates-external-ids.md#external_ids-子键) | 录入、bim | `{"cbdb_id":3767,"wikidata_id":"Q36020"}` |
| `description` | Description | 可选；官职概念条、官署概念条与合称条**必填** | 原生 | 介绍与出处 | 形状同 [common.md〈Description〉](../common.md)，但 Entity 的 `text` 可省（正式库 people 5,886 条 `description` 里只有 213 条有 `text`，其余只记出处），`sources` 必有；Entity 的出处一律记 `description.sources` | 录入 | `{"text":"都開封。","sources":[]}` |
| `suppressed_fields` | array<string> | 可选；people | 原生 | 人工确认 CBDB 值有误而清空的字段名 | 字段名（顶层键名，或 `external_ids` 的子键名）；正式库 6 条（2026-11-03 实测）：`["cbdb_id"]`、`["cbdb_id","wikidata_id"]`、`["dates"]`。见[people](people.md) | 录入 | `["cbdb_id"]` |
| `relations` | array<PersonRelation> | 可选；people | 原生 | 亲属／师承关系，双向对称写入 | 每项 `{type, entity_id, basis?, sources?[]}`；`type` 12 值：父／子／祖／孫／曾祖／曾孫／兄／弟／叔伯／姪／師／弟子；见[people](people.md) | 录入 | `[{"type":"父","entity_id":"hixhd2h9bf1f"}]` |
| `offices` | array<PersonOffice> | 可选；people | 原生 | 任官记录，按传文先后 | 每项 `{office_id, text, kind?, posthumous?, declined?, place_id?, institution_id?, start?, end?, date_text?, basis?, sources[]}`；`kind` 只记任命方式：兼／權／試／判／守／行／知／充；见[people](people.md) | 录入 | `[{"office_id":"hixi…","text":"知揚州","sources":[{"title":"《宋史》卷三百二十七·王安石傳"}]}]` |
| `ai_note` | string | 可选（全部） | 原生 | 录入备注 | 自由文本，见 [common.md〈ai_note〉](../common.md) | 录入 | |
| `todo` | array<object> | 可选（全部） | 原生 | 待办 | 每项 `{what, by?, date?}`，`what` 非空；正式库 people 37 条（2026-11-03 实测），其余类型无 | 录入 | |
| `revision` | string | **正式库必填**（全部） | 原生 | 记录内容版本 | `"主.次.补"`，新条 `"1.0.0"`；口径见 [common.md〈revision〉](../common.md#revision-口径)。Entity 也必填（overview#468），正式库已全补；草稿库 people 3 条缺（`1jb8icg27zjsx` 章淵、`1jb8icg2u5edf` 褚遂良、`1jb8icg2z572a` 沈瀛），升格时由 bim 补 | 录入、bim | `"1.1.0"` |
| `revised_at` | string | 可选（与 `revision` 同写） | 原生 | `revision` 最近一次改动日 | `YYYY-MM-DD` | 录入、bim | `"2026-10-07"` |

各子类型的专有字段见[dynasty](dynasty.md)[collective](collective.md)；不在本表与各子类型表里的键，源档不写（见[禁字段与派生](_forbidden-derived.md)）。
