# Entity（人物与专名）总览

体例见 [README.md〈八、字段表体例〉](README.md#八字段表体例)。共用对象（Description、Source、`revision` 口径、朝代规范名、`period`、`ai_note`）见 [common.md](common.md)；派生字段的形状见 [derived.md](derived.md)；旧写法的兼容读法与删除计划见 [legacy.md](legacy.md)。

**本档是总览与索引**（2026-10-16 起）；各子类型的字段表、规则、示例、校验码分文件放在 [`entity/`](entity/) 目录。查字段：先看下面的〈子类型一览〉进对应文件；通用字段、别名、日期、外部 id 见〈通用部分〉。实测数字取自两库 10-08 普查（正式库 `book-index`、草稿库 `book-index-draft`）。

## 一、总说

Entity 是与书目（Work／Book／Collection）平级的抽象概念记录：人物，以及朝代、年号、官职、官署、地名等专名。id 的类型位为 4（见 [README.md〈四、ID〉](README.md#四id)），文件在 `Entity/{c1}/{c2}/{c3}/{id}-{名}.json`。

| subtype | 是什么 | 正式库 10-08 | 草稿库 10-08 | 例 |
|---|---|---|---|---|
| [`people`](entity/people.md) | 人物（作者、注家、编者等） | 31,483 | 728 | 蘇軾 `hixhd2h9bdqq` |
| [`collective`](entity/collective.md) | 机构、官署、局所、书院等非个人主体；`collective_kind=官署` 的是官署（见[collective](entity/collective.md)） | 51（其中官署 13） | 127（全为官署） | 郵傳部 `hixhd2h9bv4m`；禮部（概念）`hixi1ubqbwv2` |
| [`dynasty`](entity/dynasty.md) | 朝代／政权 | 139 | 139 | 趙宋 `hixi1ubjrxgo`、北宋 `hixi1ubk35zj` |
| [`reign`](entity/reign.md) | 年号 | 734 | 734 | 萬曆 `hixi1ubqbwu9` |
| [`office`](entity/office.md) | 官职（概念条＋每朝具体条两层） | 0 | 1,839 | 知縣（概念）`1jb8ajoi8crnk`、知縣（趙宋）`1jb8ajoiggxs0` |
| [`place`](entity/place.md) | 地名（一地一条＋沿革） | 0 | 921 | 河南府 `1jb8kgdh3pseq`、開封府 `1jb8lqn358dfk` |
| [`seal`](entity/seal.md) | 印章（官印、私印、鑒藏印、齋館印；见[seal](entity/seal.md)） | 见[seal](entity/seal.md)示例 | 0 | 文淵閣寶 |
| [`publisher`](entity/publisher.md) | 出版社／刻书机构（家刻、坊刻、寺觀、藩府、现代出版社；官署与书院**不在此**，仍是 collective；见[publisher](entity/publisher.md)） | 0（GUJI-539 试建中） | 0 | 汲古閣、中華書局 |

**Entity 档只存这个人（这个专名）自己的信息。**「他写了哪些书」不存在 Entity 里：Entity↔Work 关系的唯一存储侧是 `Work.authors[].entity_id`（见 [common.md〈authors〉](common.md)），build 反查后在产物里生成 `_works`（每项带 `work_id`、`role`，`role` 取自 Work 一侧，缺则补「撰」）。源档不写 `works`（V11）。

专名子类型（`dynasty`／`reign`／`office`／`place`／`seal`，及 `collective_kind=官署` 的 `collective`）另有三条硬约束（overview#464）：

1. **不与 CBDB 匹配，不存任何 `cbdb_*` 外部 id**；条目内容全部自写，仍按 CC BY-SA 4.0 发布；CBDB、CHGIS、DILA 只作人工校对参照。
2. `external_ids` 只许 `wikidata_id`，第一期不填（字段留位，CC0 来源，将来再填）。
3. 地名不带坐标（`coords` 第一期禁止出现）。

官职、官署是两层：跨朝的概念条＋每朝一条具体条。

### 按类型找示例

每个子类型的字段表文件开头都有〈真实示例〉小节：2–3 个典型条目的仓内真实路径，并说明各演示什么。要看「实际写出来长什么样」，从下表进。

| 子类型 | 字段表与示例 | 首选示例（源档） |
|---|---|---|
| `people` | [people.md〈真实示例〉](entity/people.md#真实示例) | [Entity/d/q/q/hixhd2h9bdqq-蘇軾.json](../Entity/d/q/q/hixhd2h9bdqq-蘇軾.json)（蘇軾） |
| `collective` | [collective.md〈真实示例〉](entity/collective.md#真实示例) | [Entity/o/p/e/hixhd2h9bope-仙鶴堂.json](../Entity/o/p/e/hixhd2h9bope-仙鶴堂.json)（仙鶴堂） |
| `dynasty` | [dynasty.md〈真实示例〉](entity/dynasty.md#真实示例) | [Entity/x/g/o/hixi1ubjrxgo-趙宋.json](../Entity/x/g/o/hixi1ubjrxgo-趙宋.json)（趙宋） |
| `reign` | [reign.md〈真实示例〉](entity/reign.md#真实示例) | [Entity/w/u/9/hixi1ubqbwu9-萬曆.json](../Entity/w/u/9/hixi1ubqbwu9-萬曆.json)（萬曆） |
| `office` | [office.md〈真实示例〉](entity/office.md#真实示例) | [Entity/r/m/6/hixi4udstrm6-尚書.json](../Entity/r/m/6/hixi4udstrm6-尚書.json)（尚書） |
| `place` | [place.md〈真实示例〉](entity/place.md#真实示例) | [Entity/c/n/5/hixi4ugtgcn5-潼川府.json](../Entity/c/n/5/hixi4ugtgcn5-潼川府.json)（潼川府） |
| `seal` | [seal.md〈真实示例〉](entity/seal.md#真实示例) | [Entity/4/e/a/hixi6zykf4ea-文淵閣寶.json](../Entity/4/e/a/hixi6zykf4ea-文淵閣寶.json)（文淵閣寶） |
| `publisher` | [publisher.md〈真实示例〉](entity/publisher.md#真实示例) | [Entity/f/y/8/hixi70yf5fy8-汲古閣.json](../Entity/f/y/8/hixi70yf5fy8-汲古閣.json)（汲古閣） |

## 二、文件地图

### 子类型（每个文件含：字段表八列、规则、示例、该类型校验码）

| 文件 | 内容 | 一句话 |
|---|---|---|
| [entity/people.md](entity/people.md) | people（人物） | 作者、注家、编者等；CBDB／Wikidata／VIAF、生卒、籍贯、并条与退役 |
| [entity/collective.md](entity/collective.md) | collective（机构）与官署 | 非个人主体；`collective_kind=官署` 另有概念／具体／合称三层规则 |
| [entity/dynasty.md](entity/dynasty.md) | dynasty（朝代／政权） | 规范朝代名、`parent_id` 上下级、起讫 |
| [entity/reign.md](entity/reign.md) | reign（年号） | 所属朝代、帝王、起讫 |
| [entity/office.md](entity/office.md) | office（官职） | 概念条＋每朝具体条两层；复合官职、官类、品秩 |
| [entity/place.md](entity/place.md) | place（地名） | 一地一条＋沿革；今地对照、前身 |
| [entity/seal.md](entity/seal.md) | seal（印章） | 印文、类别、印主、印影；与 `Book.provenance[].seal_marks`、book-index-asset 仓的关系 |
| [entity/publisher.md](entity/publisher.md) | publisher（出版社／刻书机构） | 家刻、坊刻、寺觀、藩府、现代出版社；归属规则与 1900 前后边界 |

### 通用部分（所有子类型共用）

| 文件 | 内容 |
|---|---|
| [entity/_common.md](entity/_common.md) | 通用字段表（`id`／`subtype`／`primary_name`／`alt_names`／`dynasty`／`dates`／`external_ids`／`description`／并条与退役／管理字段等） |
| [entity/_alt-names.md](entity/_alt-names.md) | `alt_names`：AltName 对象、`type` 25 值枚举、`ambiguous` 规则 |
| [entity/_dates-external-ids.md](entity/_dates-external-ids.md) | `dates` 按子类型放行的键；`external_ids` 各子键（CBDB、Wikidata、VIAF、ISBN 前缀） |
| [entity/_forbidden-derived.md](entity/_forbidden-derived.md) | 源档不许写的字段；build 派生字段（只在 `_build/entry/`） |
| [entity/_checks.md](entity/_checks.md) | 全部校验码总表（E／D／R／A／O／P／I／S／K／V）与 verify 的另查项 |

## 三、通用部分概要

- **必填**：`id`、`type`（恒 `"entity"`）、`subtype`、`schema_version`（`1`）、`primary_name`；正式库另必填 `revision`。
- **`alt_names`**：对象数组 `{name, type, ambiguous?, note?}`；`type` 25 值（字、号、諡號、簡稱、合稱、舊稱……）；单独不能定位到本条的名写 `ambiguous: true`。详见 [entity/_alt-names.md](entity/_alt-names.md)。
- **`dates`**：people 用 `birth`／`death`／`floruit`；dynasty、reign 用 `start`／`end`；office、place、seal、publisher、官署不用 `dates`（起讫在 `start`／`end` 或沿革项）。详见 [entity/_dates-external-ids.md](entity/_dates-external-ids.md)。
- **`external_ids`**：people 可有 `cbdb_id`／`wikidata_id`／`viaf_id` 等；专名子类型与 seal、官署只许 `wikidata_id`；publisher 另许 `isbn_publisher_code`。
- **并条与退役**：留存方写 `merged_in[]`，被并方只留墓碑并写 `merged_into`（不删档）；退役写 `retired: true` 与 `retired_reason`。
- **管理字段**：`ai_note`、`todo`、`review`、`revision`、`revised_at`、`updated_at`。
- **禁字段与派生**：源档不写 `_` 起首字段、`works`、反向列表等；见 [entity/_forbidden-derived.md](entity/_forbidden-derived.md)。

## 四、校验码索引

校验实现在 `.claude/qa/entity_subtypes.py`（`check_v2.py` 与 `verify.py` 共用）；Book 侧印章引用码 B-S01…B-S05 在 `check_v2.py` Book 段（见 [book.md〈四、provenance〉](book.md#四provenance馆藏)）。

| 码 | 适用 | 在哪个文件 |
|---|---|---|
| E1、A1、O12、V01、V11、V15、V16 | 通用（专名子类型／全部） | [entity/_checks.md](entity/_checks.md) |
| N01–N03 | people 的 `native_place_entity_id` | [entity/_common.md](entity/_common.md) |
| D1–D3 | dynasty（D3 另含 reign、office、place） | [entity/dynasty.md](entity/dynasty.md) |
| R1 | reign | [entity/reign.md](entity/reign.md) |
| O01–O12 | office（O12 为通用 `alt_names.type` 码） | [entity/office.md](entity/office.md) |
| P01–P11 | place | [entity/place.md](entity/place.md) |
| I01–I12 | 官署（I12 为 office 的 `institution_ref`） | [entity/collective.md](entity/collective.md)、[entity/office.md](entity/office.md) |
| S01–S06 | seal | [entity/seal.md](entity/seal.md) |
| K01–K09 | publisher | [entity/publisher.md](entity/publisher.md) |

## 五、旧章节号对照

旧版 entity.md 按〈一〉到〈八〉编号；他档、旧卡片里写的〈六·四〉之类按下表找：

| 旧章节号 | 现位置 |
|---|---|
| 〈一〉总说 | 本档〈一〉 |
| 〈二〉通用字段 | [entity/_common.md](entity/_common.md) |
| 〈三〉`alt_names`（〈三·一〉AltName、〈三·二〉type 枚举、〈三·三〉`ambiguous`） | [entity/_alt-names.md](entity/_alt-names.md) |
| 〈四〉`dates` 与 `external_ids`（〈四·一〉、〈四·二〉） | [entity/_dates-external-ids.md](entity/_dates-external-ids.md) |
| 〈五·一〉people | [entity/people.md](entity/people.md) |
| 〈五·二〉dynasty | [entity/dynasty.md](entity/dynasty.md) |
| 〈五·三〉reign | [entity/reign.md](entity/reign.md) |
| 〈六·一〉collective 与官署 | [entity/collective.md](entity/collective.md) |
| 〈六·二〉office | [entity/office.md](entity/office.md) |
| 〈六·三〉place | [entity/place.md](entity/place.md) |
| 〈六·四〉seal | [entity/seal.md](entity/seal.md) |
| 〈六·五〉publisher | [entity/publisher.md](entity/publisher.md) |
| 〈七〉禁字段与派生字段 | [entity/_forbidden-derived.md](entity/_forbidden-derived.md) |
| 〈八〉校验码 | [entity/_checks.md](entity/_checks.md)（各类型码另见各子类型文件末） |
