# publisher（出版社／刻书机构，GUJI-539）

总览与子类型索引见 [../entity.md](../entity.md)。

一个刻书／出版主体一条。**归属规则（写死）**：官署一律是 `collective`（`collective_kind=官署`，按[collective](collective.md)官署规则，具体条按朝代拆）；书院学校一律是 `collective`（`書院學校`）。`publisher` 只收非官署、非书院学校的主体。「官刻」「書院」只是传统刻书分类，不是 publisher 的取值。一个主体只一条 Entity，不得在 collective 与 publisher 各建一条；库里已有 collective 的，Book 的 `authors[].entity_id` 直接挂靠它。

**不建档**：①书坊集群（建陽書坊、麻沙、金陵書坊、徽州書坊等），只作地域线索，写进各书坊条的 `locations`；②外国出版社（日、韩、美等）暂不收；③不设「書房」类（自署書房／山房者按家刻或坊刻归类）；④不设 `predecessors`（沿革写 `description`）；⑤不设 `publisher_sub`；⑥不设 `legal_name`，全称写进 `alt_names`（`type: 全稱`）。

遵守[总说](../entity.md)：无 `cbdb_*`、无坐标、不存「刻过哪些书」。`external_ids` 只许 `wikidata_id`，现当代出版社另许 `isbn_publisher_code`。朝代由 `dynasty_ids` 表达，不写旧式 `dynasty`／`period` 字符串。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `publisher_kind` | string | **必填** | 原生 | 主类别 | `家刻`｜`坊刻`｜`寺觀`｜`藩府`｜`現代出版社`｜`未分`（K01） | 录入 | `"家刻"` |
| `kind_also` | array<string> | 可选 | 原生 | 兼营类别 | 取值同上，不含主类别（如汲古閣：主 `家刻`，兼 `坊刻`） | 录入 | `["坊刻"]` |
| `dynasty_ids` | array<id> | 条件：古代类**必填**；`現代出版社`**不得写** | 原生 | 活动所跨朝代 | dynasty id；跨朝单条仅限同一私人／书坊主体连续经营跨朝（如掃葉山房明清）（K02） | 录入 | `["hixi1ubjrxfw"]` |
| `start`、`end` | integer | 可选 | 原生 | 起止年 | 公历年，无 0 年，`start ≤ end`；有把握才填；仍存续者不写 `end`；現代出版社 `start` 可早于 1900（K03） | 录入 | `1912` |
| `dates_basis` | string | 条件：写了 `start`／`end` 时必填 | 原生 | 起止年依据 | 自由文本（K08，WARN） | 录入 | `"《書林清話》"` |
| `locations` | array<object> | 可选 | 原生 | 所在地（可多段） | 迁移（建陽→南京）用多段表达（K04） | 录入 | |
| `locations[].name` | string | **必填** | 原生 | 地名 | 非空；无地名条时只写这个 | 录入 | `"常熟"` |
| `locations[].place_id` | string | 可选 | 原生 | 地名条 id | 须指 `subtype=place`（K04） | 录入 | |
| `locations[].start`、`end` | integer | 可选 | 原生 | 该段起止年 | 同上 | 录入 | |
| `locations[].note` | string | 可选 | 原生 | 说明 | 自由文本 | 录入 | |
| `owners` | array<object> | 可选 | 原生 | 主持者／东家 | `{id, role, start?, end?, note?}`（K05） | 录入 | |
| `owners[].id` | string | **必填** | 原生 | 人或机构条 id | 指 people 或 collective | 录入 | |
| `owners[].role` | string | **必填** | 原生 | 角色 | 开放词表，常用：主人／創辦／主持／經營／督刻 | 录入 | `"主人"` |
| `owners[].start`、`end`、`note` | integer／string | 可选 | 原生 | 任期、说明 | 同上 | 录入 | |
| `parent_id` | string | 可选 | 原生 | 上级主体 | publisher 或 collective；只写下→上，下属由 build 派生；不自指、publisher 链无环（K05） | 录入 | |
| `status` | string | 可选 | 原生 | 存续状态 | `存續`｜`撤併`｜`停業`｜`未詳`；`end` 与 `status` 都缺按存续读 | 录入 | `"存續"` |
| `description` | object | **必填** | 原生 | 介绍与出处 | 同通则，`sources` 非空（K01） | 录入 | |
| `name_basis` | string | 可选 | 原生 | 名称取定依据 | 牌记、《書林清話》等 | 录入 | `"牌記作「汲古閣」"` |
| `external_ids.isbn_publisher_code` | string | 可选；現代出版社 | 原生 | 出版社 ISBN 前缀 | 字符串（K07）；其余仍只许 `wikidata_id` | 录入 | `"7-101"` |

**1900 前后边界**：以创办时的主营业务判。1911 年以前以雕版／木活字刻书为业者→古代类，`dynasty_ids` 写到清，入民国仍存续的在 `end`／`description` 写明，不拆两条；以铅印、石印、影印等现代出版机制、公司／出版社体制创办者→`現代出版社`（无论 1897 商務还是 1912 中華），不写 `dynasty_ids`；掃葉山房类木刻转石印的老字号，按创办时主业归坊刻，单条。

**与 Book／Work／Collection 的挂接**：唯一存储侧是 `authors[].entity_id`（见 [common.md〈authors〉](../common.md)），`entity_id` 可指 people、collective 或 publisher；`role` 用已有的刻印义项（`刻`／`刊`／`刻印`／`印行`／`出版`／`影印`／`整理出版`）。build 反查得 `_books`；Entity 档不存书目。`publication_info.publisher` 自由文本保留作原文。

禁字段（K06）：`predecessors`、`publisher_sub`、`legal_name`、`representative`、`books`、`subordinates`，以及人物／朝代／官职／地名／印章等其他子类型专属字段。校验码见[校验码](_checks.md)K01–K09。

## 校验码

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| K01 | publisher | `publisher_kind` 在 6 值内；`kind_also`／`status` 在枚举内；`primary_name` 非空；`description.sources` 非空 | ERROR |
| K02 | publisher | 古代类 `dynasty_ids` 非空且各指 dynasty；`現代出版社`不得写 `dynasty_ids` | ERROR |
| K03 | publisher | `start`／`end` 为非 0 整数且 `start ≤ end` | ERROR |
| K04 | publisher | `locations[]` 形状；`place_id` 须指 place（ERROR）、指墓碑（WARN） | ERROR／WARN |
| K05 | publisher | `owners[]={id, role}`，`id` 指 people／collective；`parent_id` 指 publisher／collective、不自指、publisher 链无环（ERROR）；指墓碑（WARN） | ERROR／WARN |
| K06 | publisher | 禁字段（见[publisher](publisher.md)） | ERROR |
| K07 | publisher | `external_ids` 只许 `wikidata_id`／`isbn_publisher_code` | ERROR |
| K08 | publisher | 写了 `start`／`end` 而缺 `dates_basis` | WARN |
| K09 | publisher | 同名＋同类别＋同朝代集重复，疑重复建档 | WARN |

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
