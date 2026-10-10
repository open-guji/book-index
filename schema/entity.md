# Entity（人物与专名）

体例见 [README.md〈八、字段表体例〉](README.md#八字段表体例)。共用对象（Description、Source、`revision` 口径、朝代规范名、`period`、`ai_note`）见 [common.md](common.md)；派生字段的形状见 [derived.md](derived.md)；旧写法的兼容读法与删除计划见 [legacy.md](legacy.md)。

实测数字取自两库 10-08 普查（正式库 `book-index`、草稿库 `book-index-draft`）。

---

## 一、总说

Entity 是与书目（Work／Book／Collection）平级的抽象概念记录：人物，以及朝代、年号、官职、官署、地名等专名。id 的类型位为 4（见 [README.md〈四、ID〉](README.md#四id)），文件在 `Entity/{c1}/{c2}/{c3}/{id}-{名}.json`。

| subtype | 是什么 | 正式库 10-08 | 草稿库 10-08 | 例 |
|---|---|---|---|---|
| `people` | 人物（作者、注家、编者等） | 31,483 | 728 | 蘇軾 `hixhd2h9bdqq` |
| `collective` | 机构、官署、局所、书院等非个人主体；`collective_kind=官署` 的是官署（见〈六〉） | 51（其中官署 13） | 127（全为官署） | 郵傳部 `hixhd2h9bv4m`；禮部（概念）`hixi1ubqbwv2` |
| `dynasty` | 朝代／政权 | 139 | 139 | 趙宋 `hixi1ubjrxgo`、北宋 `hixi1ubk35zj` |
| `reign` | 年号 | 734 | 734 | 萬曆 `hixi1ubqbwu9` |
| `office` | 官职（概念条＋每朝具体条两层） | 0 | 1,839 | 知縣（概念）`1jb8ajoi8crnk`、知縣（趙宋）`1jb8ajoiggxs0` |
| `place` | 地名（一地一条＋沿革） | 0 | 921 | 河南府 `1jb8kgdh3pseq`、開封府 `1jb8lqn358dfk` |

**Entity 档只存这个人（这个专名）自己的信息。**「他写了哪些书」不存在 Entity 里：Entity↔Work 关系的唯一存储侧是 `Work.authors[].entity_id`（见 [common.md〈authors〉](common.md)），build 反查后在产物里生成 `_works`（每项带 `work_id`、`role`，`role` 取自 Work 一侧，缺则补「撰」）。源档不写 `works`（V11）。

专名子类型（`dynasty`／`reign`／`office`／`place`，及 `collective_kind=官署` 的 `collective`）另有三条硬约束（overview#464）：

1. **不与 CBDB 匹配，不存任何 `cbdb_*` 外部 id**；条目内容全部自写，仍按 CC0 发布；CBDB、CHGIS、DILA 只作人工校对参照。
2. `external_ids` 只许 `wikidata_id`，第一期不填（字段留位，CC0 来源，将来再填）。
3. 地名不带坐标（`coords` 第一期禁止出现）。

官职、官署是两层：跨朝的概念条＋每朝一条具体条。

---

## 二、通用字段

「适用」写在「必填」列里。「专名」指 `dynasty`／`reign`／`office`／`place` 四子类型及官署。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | **必填**（全部） | 原生 | 记录 id | base36 snowflake，正式库 12 字符、草稿库 13 字符，类型位 4 | bim | `"hixhd2h9bdqq"` |
| `type` | string | **必填**（全部） | 原生 | 记录类型 | 恒为 `"entity"` | bim | `"entity"` |
| `subtype` | string | **必填**（全部） | 原生 | 子类型 | `people`｜`collective`｜`dynasty`｜`reign`｜`office`｜`place`；读者遇缺省按 `people` 读（现存无缺） | 录入 | `"people"` |
| `schema_version` | integer | **必填**（全部） | 原生 | 记录格式大版本 | `1`（V15） | bim | `1` |
| `primary_name` | string | **必填**（全部） | 原生 | 最通行的名字 | 自由文本，繁体；dynasty 须是规范朝代名（见〈五〉） | 录入 | `"蘇軾"` |
| `alt_names` | array<AltName> | 可选（全部） | 原生 | 别名 | 见〈三〉 | 录入 | `[{"name":"子瞻","type":"字"}]` |
| `dynasty` | string | 可选；people、未分类 collective | 原生 | 所属朝代（规范名） | 见 [common.md〈朝代规范名〉](common.md)；专名子类型与新建官署条**不写**（朝代由 `dynasty_ids` 等表达）。正式库 people 23,946 条有值（其中 28 条为 `null`，旧） | 录入 | `"北宋"` |
| `dynasty_basis` | string | 可选；同 `dynasty` | 原生 | 朝代的依据 | 自由文本 | 录入 | `"cbdb:birth/death_name=北宋"` |
| `period` | string | 可选；people、未分类 collective、dynasty | 原生 | 时代轴 slug | 12 个 slug 之一，见 [common.md〈period〉](common.md)；在 dynasty 条里含义见〈五·二〉 | 录入 | `"song"` |
| `period_basis` | string | 可选；people、未分类 collective | 原生 | `period` 的依据 | 自由文本 | 录入 | `"据 dynasty「北宋」自动归并"` |
| `native_place` | string | 可选；people | 原生 | 籍贯 | 自由文本（正式库 3 条为 `null`，旧） | 录入 | `"山陰"`、`"眉山"` |
| `native_place_basis` | string | 可选；people | 原生 | 籍贯的依据 | 自由文本 | 录入 | `"CBDB 3767 index_addr（2026-09-06 CBDB enrich）"` |
| `title_or_office` | string | 可选；people | 原生 | 著录所见官职 | 自由文本（正式库 1 条） | 录入 | `"散騎常侍"`（顾长康 `hixhi7qcyxa8`） |
| `name_basis` | string | 可选；people | 原生 | 名字的依据（正名经过） | 自由文本（正式库 164 条） | 录入 | `"catalog：著錄之撰人名（2026-09-06 撰人書名切分訂正）"` |
| `birth_year` | integer | 可选；people | 原生 | 生年 | 公历年，公元前负数；与 `dates.birth` 并存（见〈四〉）。正式库 3 条为 `null`（旧） | 录入 | `1036` |
| `death_year` | integer | 可选；people | 原生 | 卒年 | 同上 | 录入 | `1101` |
| `dates` | object | 条件：people、dynasty、reign 可写；office、place **不得有** | 原生 | 结构化起讫／生卒 | 按子类型放行的键见〈四〉 | 录入 | `{"birth":1036,"death":1101,"floruit":null,"basis":"現行字段"}` |
| `external_ids` | object | 可选（全部）；专名只许 `wikidata_id` | 原生 | 外部库 id | 子键见〈四·二〉 | 录入、bim | `{"cbdb_id":3767,"wikidata_id":"Q36020"}` |
| `description` | Description | 可选；官职概念条、官署概念条与合称条**必填** | 原生 | 介绍与出处 | 形状同 [common.md〈Description〉](common.md)，但 Entity 的 `text` 可省（正式库 people 5,886 条 `description` 里只有 213 条有 `text`，其余只记出处），`sources` 必有；Entity 的出处一律记 `description.sources` | 录入 | `{"text":"都開封。","sources":[]}` |
| `merge_history` | array<object> | 可选；people | 原生 | 早期并条账（2026-09-09 一次写入） | 每项 `{primary_name, date, reason}`（正式库 4,409 条） | 迁移 | `[{"primary_name":"曾仲質","date":"2026-09-09","reason":"draft/production 同人同书重出（CBDB auto_create 批次遗留，纯冗余无增量），2026-09-09 併條"}]` |
| `merged_in` | array<object> | 可选；留存方（keeper） | 原生 | 并入本条的他条 | 每项 `{id, primary_name, at, by, rule, why}`（正式库 people 313 条／324 项，collective 1 条） | 录入 | 见〈六·一〉馬令例 |
| `merged_into` | string | 可选；被并方 | 原生 | 本条已并入的条目 id | entity id；被并条只留 `schema_version`、`id`、`type`、`subtype`、`primary_name`、`merged_into`、`revision`、`revised_at`（正式库 2 条）。**并条一律写墓碑、不删档**（2026-10-09 起） | 录入 | `"hixhd2h9biza"`（成無巳 `hixhd2h9blyf`） |
| `retired` | boolean | 可选 | 原生 | 本条已退役 | 只写 `true`（正式库 5 条） | 录入 | `true` |
| `retired_reason` | string | 条件：`retired` 时必填 | 原生 | 退役原因 | 自由文本 | 录入 | `"N3 壞名 entity 歸正（2026-08-24 南北朝斷代與壞名專項）：…"`（廋信 `hixhd2h9bq93`） |
| `suppressed_fields` | array<string> | 可选；people | 原生 | 人工确认 CBDB 值有误而清空的字段名 | 字段名（顶层键名，或 `external_ids` 的子键名）；正式库 2 条，值均为 `"cbdb_id"`。见〈六·一〉 | 录入 | `["cbdb_id"]` |
| `ai_note` | string | 可选（全部） | 原生 | 录入备注 | 自由文本，见 [common.md〈ai_note〉](common.md) | 录入 | |
| `todo` | array<object> | 可选（全部） | 原生 | 待办 | 每项 `{what, by?, date?}`，`what` 非空；两库 Entity 现无此键 | 录入 | |
| `review` | object | 可选（全部） | 原生 | 审核状态 | `{status, by?, date?}`，`status` ∈ `unreviewed`｜`reviewed`｜`disputed` | 录入 | `{"status":"unreviewed"}` |
| `revision` | string | **正式库必填**（全部） | 原生 | 记录内容版本 | `"主.次.补"`，新条 `"1.0.0"`；口径见 [common.md〈revision〉](common.md#revision-口径)。Entity 也必填（overview#468），正式库已全补；草稿库 people 3 条缺（`1jb8icg27zjsx` 章淵、`1jb8icg2u5edf` 褚遂良、`1jb8icg2z572a` 沈瀛），升格时由 bim 补 | 录入、bim | `"1.1.0"` |
| `revised_at` | string | 可选（与 `revision` 同写） | 原生 | `revision` 最近一次改动日 | `YYYY-MM-DD` | 录入、bim | `"2026-10-07"` |
| `updated_at` | string | 可选（全部） | 原生 | 记录最近改动时刻 | ISO 8601 时间（现存也有只写日期的：dynasty 23 条、reign 233 条，如 `"2026-10-07"`）；草稿库 people 全无此键 | bim | `"2026-08-24T00:00:00+00:00"` |

各子类型的专有字段见〈五〉〈六〉；不在本表与各子类型表里的键，源档不写（见〈七〉）。

---

## 三、`alt_names`

### 三·一　AltName 对象

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `alt_names[]` | AltName | — | 原生 | 一个别名 | 对象。正式库 people 有 47 项是裸字符串（旧，如僧肇 `hixhd2h9bixi` 的 `["僧", "蕭維禎"]`），读者按 `{name: 该串}` 读 | 录入 | |
| `alt_names[].name` | string | **必填** | 原生 | 别名本字 | 非空（A1） | 录入 | `"子瞻"` |
| `alt_names[].type` | string | **必填**（新写） | 原生 | 别名类别 | 〈三·二〉23 值；专名子类型与官署里不在表内即 ERROR（O12）。正式库 people 有 2,613 项缺 `type`（旧） | 录入 | `"字"` |
| `alt_names[].ambiguous` | boolean | 可选 | 原生 | 此名单独不能定位到本条 | 只写 `true`，缺省即 false；规则见〈三·三〉 | 录入 | `true` |
| `alt_names[].note` | string | 可选；people | 原生 | 此别名的来历说明 | 自由文本（正式库 22 项，多为「著錄形」之说明） | 录入 | `"《補晉書藝文志》諸本著錄之形，官銜「豫章太守」在名前。存之以覆按著錄原文。"`（`hixhjtdlfbb6`） |

### 三·二　`alt_names[].type` 枚举（23 值）

以 `.claude/qa/entity_subtypes.py` 的 `ALT_TYPES` 为准。这是活字典：新增合法值就补进本表与 `ALT_TYPES`。

| type | 含义 | 对应 CBDB ALTNAME_CODES | 例 |
|---|---|---|---|
| `字` | 表字 | 4 | 子瞻（蘇軾） |
| `號` | 号、室名别号 | 5 | 東坡居士（蘇軾） |
| `諡號` | 谥号 | 6 | 文忠（蘇軾） |
| `賜號` | 赐号 | 11 | |
| `別名` | 其他别名 | 3 | |
| `常用名` | 常用称谓 | — | 陽明先生 |
| `簡體` | 简体写法 | — | |
| `行第` | 排行称谓 | — | 李十二 |
| `廟號` | 庙号 | — | |
| `訛名` | 著录讹误而流传的名 | — | |
| `異體` | 异体字写法 | — | 萬歷（萬曆） |
| `封爵` | 封爵称谓 | — | |
| `俗姓` | 出家前本姓（僧道人物常见） | — | |
| `簡稱` | 简称；长度 ≤2 者常需配 `ambiguous` | — | 宋（北宋）、御史（監察御史） |
| `合稱` | 合称 | — | 兩宋、南北宋（趙宋） |
| `避諱` | 避讳改字写法 | — | |
| `別稱` | 别称 | — | 蜀漢、劉宋 |
| `雅稱` | 雅称 | — | 春官（禮部） |
| `全稱` | 全称（**不参与匹配**） | — | 黑龍江駐防將軍 |
| `異寫` | 异写（用字不同而音义同） | — | 太平天国 |
| `舊稱` | 旧称（专名用） | — | 洛州（河南府） |
| `異稱` | 异称（专名用） | — | 洛陽（河南府） |
| `今名` | 今名（地名用） | — | |

各库实际用到的（10-08）：正式库 people 用 `字` 9,603、`號` 6,933、`別名` 5,852、`行第` 1,406、`諡號` 1,294、`異體` 169、`訛名` 113、`封爵` 65、`廟號` 63、`賜號` 27、`俗姓` 18、`異寫` 11、`常用名` 2；dynasty（两库同）用 `簡稱` 89、`別稱` 49、`合稱` 7、`全稱` 4、`異寫`／`訛名`／`舊稱` 各 1；reign 用 `異體` 22、`避諱` 2、`別名` 2；草稿库 office 用 `簡稱` 149、`別稱` 73、`全稱` 53、`異稱` 3、`雅稱` 3；place 用 `舊稱` 879、`簡稱` 438、`異稱` 56、`今名` 17、`全稱` 16、`別稱` 7、`異寫` 6、`雅稱` 5；官署用 `別稱`、`雅稱`、`舊稱`。

**表外值（旧，暂留，WARN）**：只出现在正式库 people。check_v2 不查 people 的 `alt_names.type`，由人物质检判 WARN，人工按需并入表内或改写，不强求一次穷举。10-08 实测：

| 值 | 出现 | 值 | 出现 | 值 | 出现 |
|---|---|---|---|---|---|
| `著錄形` | 121 | `小字` | 40 | `著錄原形` | 31 |
| `小名` | 26 | `法號` | 20 | `本名` | 18 |
| `舊著錄形` | 15 | `殘名` | 13 | `著錄異形` | 8 |
| `稱謂` | 5 | `本姓` | 5 | `年號` | 4 |
| `其他譯名` | 3 | `剝字之訛` | 3 | `洗名` | 3 |
| `著錄異寫` | 2 | `异体` | 2 | `稱號` | 2 |
| `位號` | 2 | `尊號` | 2 | `俗名` | 2 |
| `異書/或訛` | 2 | `異體字` | 1 | `著錄原形（誤切）` | 1 |
| `名` | 1 | `簡稱/或訛` | 1 | `訛寫` | 1 |
| `道號` | 1 | `形訛` | 1 | `著錄殘文` | 1 |
| `廟額` | 1 | `廟號諡號` | 1 | `志書異文` | 1 |

共 33 种、340 项。其中 `异体`、`異體字` 是 `異體` 的异写，可机械归并。

### 三·三　`ambiguous` 规则

- `ambiguous: true` 表示这个名字**单独不能定位**到本条（如「宋」「漢」「魏」「太守」「御史」）。匹配时一律出 `ambiguous`、候选全带出，永不 `matched`。
- 写在**每一个**声称该名的条目上。例：「宋」在 趙宋、北宋（及南宋、劉宋等）上都标 `ambiguous`。
- 校验（A1）：带 `ambiguous` 的名字全库须有 ≥2 个条目声称（以它作 `primary_name` 的 dynasty 也算一条，如「後漢」既是五代后汉的规范名、又是东汉的别称），否则 WARN（标记多余）。
- 不带 `ambiguous` 的 dynasty 别名，在全部 dynasty 条里必须唯一，也不得与他条重名，否则 ERROR（A1）。
- 官职 `簡稱` 长度 ≤2 的，须确认不与他概念重名（O10，WARN）。
- 跨概念同名的别名（如都察院（明）之「御史臺」）照官职规则标 `ambiguous`。
- 正式库 people 现无 `ambiguous`；10-08 dynasty 90 项、草稿库 office 102 项、place 49 项、官署 8 项。

---

## 四、`dates` 与 `external_ids`

### 四·一　`dates` 按子类型放行

| subtype | 放行的键 | 必填 | 说明 |
|---|---|---|---|
| `people` | `birth`、`death`、`floruit`、`basis`、`chinese` | 可选 | 见下表 |
| `dynasty` | `start`、`end`、`basis`、`chinese` | 中国朝代必填 `start`（有 `period` 而缺 `start` 为 D3 WARN）；域外可缺 | 公元年，公元前负数，无 0 年，闭区间；仍存续者不写 `end`（正式库「中華民國」「中華人民共和國」省略；草稿库此 2 条写 `null`，读者两种都认） |
| `reign` | `start`、`end`、`basis`、`chinese` | `start` 必填 | 改元当年记为起年 |
| `office` | — | **不得有 `dates`**（D3） | 起讫在 `start`／`end` |
| `place` | — | **不得有 `dates`**（D3） | 起讫在 `history[]` 各项 |
| `collective` | — | 不用（官署起讫在 `start`／`end`） | |

`dates` 各键：

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `dates.birth` | integer（`null` 为旧） | 可选；people | 原生 | 生年 | 公历年，公元前负数 | 录入、迁移 | `1036` |
| `dates.death` | integer（`null` 为旧） | 可选；people | 原生 | 卒年 | 同上 | 录入、迁移 | `1101` |
| `dates.floruit` | array<integer>（`null` 为旧） | 可选；people | 原生 | 活动年区间 `[起, 止]` | 二元整数组，起 ≤ 止；只在生卒双缺、且 CBDB 侧另有旁证（`index_year`，即 `BIOG_MAIN` 的活动年代参考值）时补，`basis` 记 `"cbdb:index_year"`；取不到旁证的不补、留 `dates` 缺省 | 迁移 | `[1019, 1019]`（馬玗 `hixhd2h9biiy`） |
| `dates.start` | integer | 条件：dynasty（中国朝代）、reign 必填 | 原生 | 起年 | 公历年，无 0 年 | 录入 | `960` |
| `dates.end` | integer | 可选；dynasty、reign | 原生 | 止年 | 同上，`start ≤ end` | 录入 | `1127` |
| `dates.basis` | string | 条件：有年值时写 | 原生 | 年值的来源 | 自由文本，非枚举。people 现值 `"現行字段"`（机械迁移自 `birth_year`／`death_year`，正式库 6,889）、`"cbdb:index_year"`（336）、`"cbdb"`（正式库 249、草稿库 253） | 录入、迁移 | `"趙匡胤 960 稱帝，止於靖康"` |
| `dates.chinese` | string | 可选 | 原生 | 原文纪年 | 如「嘉靖二年—萬曆元年」；无原文材料时省略（两库现无） | 录入 | |

people 的 `dates` 规则：

- `birth`／`death` 与 `floruit` 不共存于同一条：生卒已知就不必补活动年。现存数据里 `floruit: null`（正式库 6,889、草稿库 253）、`birth: null`（正式库 1,048、草稿库 17）、`death: null`（正式库 1,493、草稿库 28）是迁移时写下的空槽（旧，check_schema 报 WARN），读者按缺省读；新写不写 `null`。
- `dates` 逐步取代 `birth_year`／`death_year` 的展示用途；现阶段**只增不删**，两者并存，待网站改完展示后另开卡再删。
- 校验（`verify.py`）：`birth`／`death`／`floruit[0]`／`floruit[1]` 须为整数；`floruit` 为二元数组；`birth ≤ death`；`floruit[0] ≤ floruit[1]`；`dates.birth`／`dates.death` 与 `birth_year`／`death_year` 两者皆有时须一致。

### 四·二　`external_ids` 子键

**专名四子类型与官署：只许 `wikidata_id`**（`^Q\d+$`，第一期不填）；出现任何其他子键即 ERROR（E1；官署报 I08）。下表其余子键只用于 `people`。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `external_ids.cbdb_id` | integer | 可选；people | 原生 | CBDB 人物 id | 正整数（正式库 14,328、草稿库 725） | 录入、bim | `3767` |
| `external_ids.cbdb_match` | string | 条件：有 `cbdb_id` 或核过 CBDB 时写 | 原生 | 匹配方式 | 开放词表。现值（正式库）：`auto` 5,825、`auto_2026-09-06` 3,246、`manual` 2,559、`auto_create` 1,831、`auto_create_p4` 720（草稿库 725）、`auto_placeholder_upgrade` 48、`auto_dy_ambig_year` 35、`none` 24、`manual_remap` 23、`auto_dy_unique` 22、`auto_altname_upgrade` 10、`manual (C5 batch17)` 5、`manual ; dynasty_fix: 南朝宋→宋 per CBDB dy=…` 4、`restored` 1。`none` 表示核过而 CBDB 无此人或只有误配，此时不写 `cbdb_id`，理由写在 `cbdb_source` | 录入、bim | `"manual"` |
| `external_ids.cbdb_source` | string | 条件：同 `cbdb_match` | 原生 | 匹配依据 | 自由文本 | 录入、bim | `"name_exact+dy_match+work_recall_0.56+unique"`；`"none: 僧肇[晉]→CBDB[明]，僧肇(384-414)是東晉僧，非明人"` |
| `external_ids.cbdb_id_alt` | array<integer> | 可选；people | 原生 | CBDB 为同一人另收的 id | 并条时被并方的 `cbdb_id`（正式库 45 条） | 录入 | `[66803]`（劉俊 `hixhd2h9bib6`） |
| `external_ids.cbdb_aliases` | array<integer> | 可选；people | 旧（暂留） | 同 `cbdb_id_alt` | 正式库 12 条，均带 `cbdb_aliases_note`；待并入 `cbdb_id_alt` | 录入 | `[106639]`（張理 `hixhd2h9bie2`） |
| `external_ids.cbdb_aliases_note` | string | 可选；people | 旧（暂留） | `cbdb_aliases` 的说明 | 现值只有 `"人工判定同一人，CBDB 收为多条"`（12）；待删 | 录入 | |
| `external_ids.cbdb_note` | string | 可选；people | 旧（暂留） | 匹配疑点备注 | 正式库 1 条（梁正 `hixhd2h9bi3z`：`"疑為同名異人誤配——見下 ai_note"`）；待并入 `ai_note` | 录入 | |
| `external_ids.wikidata_id` | string | 可选（全部） | 原生 | Wikidata Q 号 | `^Q\d+$`（正式库 people 11,516） | bim | `"Q36020"` |
| `external_ids.viaf_id` | string | 可选；people | 原生 | VIAF id | 纯数字字符串（正式库 2,054） | bim | `"96591338"` |

- `wikidata_id`／`viaf_id` 的取法（overview#159）：只给有 `cbdb_id` 的 people 补，经 Wikidata 属性 **P497**（CBDB ID）反查；用 Wikidata 官方 SPARQL 端点一次性批量取全部 `?item wdt:P497 ?cbdb`（及 `wdt:P214` VIAF），不逐条请求，脚本 `.claude/qa/s4/sync_wikidata_ids.py`。按 `cbdb_id` 精确对；一个 `cbdb_id` 对多个 Q 的不写（列入冲突清单，人工另核）；已有 `wikidata_id` 的不覆盖，与新取值不一致的列入冲突清单。两者缺省表示未取得或未对上。
- 校验（`verify.py`）：`wikidata_id` 须匹配 `^Q\d+$`；`viaf_id` 须为纯数字字符串。
- CBDB 相关信息（`cbdb_id`／`cbdb_match`／`cbdb_source`）只存在 Entity 的 `external_ids`，不存在 Work 的 `authors[]` 里。
- 空对象 `{}`：正式库 people 12,199 条、collective 41 条的 `external_ids` 是空对象（旧）。按总则 11 新写不写空对象，读者按缺省读。

---

## 五、各子类型：人物与朝代纪年

### 五·一　`people`

通用字段全部可用（见〈二〉）。people 特有的规矩：

- 名下作品不写，build 生成 `_works`；朝代名由 build 解析为 `_dynasty_id`（规范名唯一命中且不歧义）或 `_dynasty_candidates`（歧义名的候选 id），见 [derived.md](derived.md)。
- **`suppressed_fields`**（2026-09-26 用户裁，甲案）：人工核过、确认 CBDB 该字段之值有误而清空的，把字段名列进 `suppressed_fields`；补空槽的 enrich 脚本（`cbdb-sync/apply_enrich.py`）逢清单里的字段即绕开，不再拿 CBDB 之值回填。原行为只认「字段现在是否空」，人清空一次、下一轮 enrich 就自动填回去，俞安期、謝顯两例皆如此每跑一次就再犯一次。**只影响列名的字段**，其余空槽仍照常补。
- 并条：留存方写 `merged_in[]`，被并方只留 stub（墓碑）并写 `merged_into`，**不删档**（2026-10-09 目录经理定，overview#409；`.claude/qa/entity_merge.py` 已改为写墓碑）。网站按被并方记录的 `merged_into` 308 跳到留存方；build 现仍把墓碑列入 `index/`。早期（2026-09-09）的并条账在 `merge_history[]`；此前 entity_merge.py 删档的并条只在留存方 `merged_in` 里有账。
- 退役：写 `retired: true` 与 `retired_reason`，记录保留。

例（正式库，馬令 `hixhd2h9bv8d`，节录）：

```json
{
  "schema_version": 1,
  "id": "hixhd2h9bv8d",
  "type": "entity",
  "subtype": "people",
  "primary_name": "馬令",
  "external_ids": {},
  "period": "song",
  "revision": "1.1.0",
  "revised_at": "2026-10-07",
  "merged_in": [
    {
      "id": "hixhd2h9bmfu",
      "primary_name": "馬令",
      "at": "2026-10-08",
      "by": "D4-Entity清账",
      "rule": "M1 裁定（10-07）：keeper 取 B，朝代定宋",
      "why": "P4b（批3c，M1 裁）：总目宋馬令名下著作与两条皆合；A 误标朝代且所繫 cbdb 为他人，不带入"
    }
  ],
  "dynasty": "宋",
  "dynasty_basis": "中國古籍總目（上圖聯合目錄）責任者著錄「宋」；P4b 批3c 目錄經理裁定（2026-10-07）",
  "suppressed_fields": [
    "cbdb_id"
  ]
}
```

正式库蘇軾 `hixhd2h9bdqq` 是带 CBDB／Wikidata／VIAF 与 `dates` 的完整例：`external_ids` 为 `{"cbdb_id": 3767, "cbdb_match": "manual", "cbdb_source": "name_exact+dy_match+work_recall_0.56+unique", "wikidata_id": "Q36020", "viaf_id": "96591338"}`，`dates` 为 `{"birth": 1036, "death": 1101, "floruit": null, "basis": "現行字段"}`，`description.sources` 为 `[{"name": "中國古籍總目", "type": "url", "details": "http://data.library.sh.cn/entity/person/fia6wo2nwkdcrjll"}]`。

### 五·二　`dynasty`（朝代／政权）

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `primary_name` | string | **必填** | 原生 | 规范朝代名 | 必须**逐字**在 [common.md〈朝代规范名〉](common.md) 的规范名表（含域外朝代表）里，全库唯一（D1）；条目化后枚举改由 build 从条目生成，不得再手写第二份 | 录入 | `"北宋"` |
| `parent_id` | string | 可选 | 原生 | 上级朝代 | dynasty id；单父，上溯深度 ≤3（如 春秋吳→春秋→東周→先秦），无环；子朝代 `dates` 落在上级之内（容差 1 年，越界 WARN）（D2）。子列表由 build 派生 `_children` | 录入 | `"hixi1ubjrxgo"`（北宋→趙宋） |
| `dates` | object | 条件：中国朝代必填 `start` | 原生 | 起讫 | `{start, end?, basis, chinese?}`，见〈四·一〉 | 录入 | `{"start":960,"end":1127,"basis":"趙匡胤 960 稱帝，止於靖康"}` |
| `period` | string | 可选（中国朝代宜填） | 原生 | 默认时代轴 | 现有 period slug（D3）；只作默认值，**不反写** `Work.period` | 录入 | `"song"` |

另可写通用字段 `alt_names`、`description`、`ai_note`、`review`、`revision`、`revised_at`、`updated_at`。10-08：两库各 139 条（草稿库的 139 条已全部升格，正式库 id `hixi1…`），有 `dates` 136、`parent_id` 68、`period` 124；无 `dates` 的 3 条是「上古」「上古傳說」「日本」。

例（正式库，北宋 `hixi1ubk35zj`）：

```json
{
  "schema_version": 1,
  "id": "hixi1ubk35zj",
  "type": "entity",
  "subtype": "dynasty",
  "primary_name": "北宋",
  "alt_names": [
    {
      "name": "宋",
      "type": "簡稱",
      "ambiguous": true
    }
  ],
  "parent_id": "hixi1ubjrxgo",
  "dates": {
    "start": 960,
    "end": 1127,
    "basis": "趙匡胤 960 稱帝，止於靖康"
  },
  "period": "song",
  "description": {
    "text": "都開封。",
    "sources": []
  },
  "review": {
    "status": "unreviewed"
  },
  "revision": "1.0.1",
  "revised_at": "2026-10-07",
  "updated_at": "2026-10-07T00:00:00+00:00"
}
```

### 五·三　`reign`（年号）

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `primary_name` | string | **必填** | 原生 | 年号 | 自由文本 | 录入 | `"萬曆"` |
| `dynasty_id` | string | **必填**（所属政权无条目时可缺，须在 `ai_note` 说明，报 WARN） | 原生 | 颁行当时的政权 | dynasty id（天命、天聰取「後金」） | 录入 | `"hixi1ubjrxfw"`（明） |
| `ruler` | object | **必填** | 原生 | 颁行者 | `{name, entity_id?}` | 录入 | `{"name":"朱翊鈞"}` |
| `ruler.name` | string | **必填** | 原生 | 帝王名 | 非空 | 录入 | `"朱翊鈞"` |
| `ruler.entity_id` | string | 可选 | 原生 | 帝王的人物条 | 须指向 `people`；库中无该帝王条时只写名（两库现无此键） | 录入 | |
| `dates` | object | **必填**（`start` 必填） | 原生 | 起讫 | `{start, end?, basis, chinese?}`，见〈四·一〉；须落在所属朝代 `dates` 内（容差 5 年，越界 WARN） | 录入 | `{"start":1573,"end":1620,"basis":"通行紀年；與CBDB、DILA相符"}` |

- `(primary_name, dynasty_id, dates.start)` 全库唯一；同朝同名年号区间不重叠（R1）。
- `index_in_reign`、干支不写（build 派生 `_index_in_reign`）。
- 10-08：两库各 734 条（草稿库的已全部升格）。

---

## 六、各子类型：机构、官职、地名

### 六·一　`collective` 与官署

`collective` 是非个人主体。官署不另立 subtype，仍是 `collective`，以 `collective_kind` 区分；**只有 `collective_kind=官署` 受本节官署规则约束**，其余取值与缺 `collective_kind` 的旧条（缺省即 `未分`，正式库 38 条，如宗人府 `hixhd2h9bq2d`、郵傳部 `hixhd2h9bv4m`）照通用字段写，可带 `dynasty`／`dynasty_basis`／`period`／`period_basis`。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `collective_kind` | string | 条件：官署**必填**；其余可选 | 原生 | 机构类别 | `官署`｜`書院學校`｜`館局`｜`民間`｜`未分`；缺省即 `未分`（I01） | 录入 | `"官署"` |
| `institution_level` | string | 条件：官署**必填** | 原生 | 层级 | `concept`（概念）｜`concrete`（每朝具体）｜`group`（合称，如六部、东宫）（I01） | 录入 | `"concrete"` |
| `parent_id` | string | 条件：具体条有概念时填；概念、合称**不得有** | 原生 | 所属概念条 | 官署概念条 id（与 office 同义：具体→概念；概念只一级）（I03） | 录入 | `"hixi1ubqbwv2"` |
| `dynasty_ids` | array<string> | 条件：具体条**必填**；概念、合称不得有 | 原生 | 所属朝代 | dynasty id 数组；默认一朝一条，**各字段完全一致**才许多值合并（`ai_note` 标【合併條】） | 录入 | `["hixi1ubjrxgo"]` |
| `function` | string | 条件：具体条**必填**；概念、合称不得有 | 原生 | 本朝职掌 | 自写，一句即可 | 录入 | `"掌禮樂、祭祀、朝會、貢舉等政令；…"` |
| `basis` | string | 条件：具体条**必填**；概念、合称不得有 | 原生 | 依据 | 自由文本，不得含「待核」（I02） | 录入 | `"《宋史·職官志》"` |
| `start`、`end` | integer | 可选；具体条（概念、合称不得有） | 原生 | 起讫 | 整数公历年，无 0 年，`start ≤ end`；有把握才填；越出所属朝代 5 年 WARN（I06） | 录入 | `1082` |
| `superiors` | array<object> | 可选；具体条（概念、合称不得有） | 原生 | 上级官署 | 每项 `{id, start?, end?, note?}`，`id` 指同朝**具体**官署条，不自指、无环；只写下级→上级（下属由 build 派生 `_subordinates`）；隶属有变用 `start`／`end` 分段（I04） | 录入 | `[{"id":"hixi1ubqbwv7","start":1082}]` |
| `group_ids` | array<string> | 可选；概念或具体条（合称不得有，合称不嵌套） | 原生 | 所属合称 | 合称条 id；成员→合称单向。跨朝不变挂概念条，随朝而变挂具体条；具体条与其概念条重复挂同一合称 WARN（I05） | 录入 | `["hixi1ubqbwuz"]`（六部） |
| `description` | Description | 条件：概念、合称**必填** | 原生 | 介绍 | 同通用 | 录入 | |
| `succeeds` | array<string> | 不填 | 原生 | 承继 | 第一期只留字段位；承继写 `description`；出现即 WARN（I09） | — | |
| `location_id` | — | **不得有** | — | 所在地 | 第一期禁出现（I09） | — | |

- 官署条不得有官职专有字段（`office_level`、`office_class`、`rank`、`salary`、`base_office_id`、`qualifier`、`institution_ref`）（I08）；不设 `rank`、`institution_class`；`external_ids` 只许 `wikidata_id`（I08）。
- 新建官署条不写旧式 `dynasty`／`period` 字符串（朝代名由 build 自 `dynasty_ids` 派生）。
- `_children`、`_subordinates`、`_members`、`_offices` 由 build 派生，不入源档（I11）。
- 正式库已有的官署 collective（兵部、禮部、樞密院…）原地升格以正式库补丁为之，**正式库条不得指草稿 id**。
- 10-08：正式库官署 13 条（concrete 6、concept 5、group 2）；草稿库 127 条（concrete 94、concept 28、group 5）。

例（正式库，禮部（趙宋）`hixi1ubqbwv8`）：

```json
{
  "schema_version": 1,
  "id": "hixi1ubqbwv8",
  "type": "entity",
  "subtype": "collective",
  "collective_kind": "官署",
  "institution_level": "concrete",
  "primary_name": "禮部",
  "parent_id": "hixi1ubqbwv2",
  "dynasty_ids": [
    "hixi1ubjrxgo"
  ],
  "function": "掌禮樂、祭祀、朝會、貢舉等政令；元豐改制（1082）前貢舉由臨時差遣的知貢舉主持，禮儀由太常禮院分掌，改制後併歸禮部，始專其政。",
  "superiors": [
    {
      "id": "hixi1ubqbwv7",
      "start": 1082
    }
  ],
  "basis": "《宋史·職官志》",
  "review": {
    "status": "unreviewed"
  },
  "revision": "1.0.1",
  "revised_at": "2026-10-07",
  "updated_at": "2026-10-07T00:00:00+00:00"
}
```

合称条例（草稿库，三省 `1jb8bq09l0mww`）只有 `primary_name`、`description`、`ai_note` 等通用字段，其 `ai_note` 原文为：「合稱條（group）：不寫朝代、職掌、隸屬、起訖；成員在各概念條的 `group_ids` 裡單向指向本條。」

### 六·二　`office`（官职，两层）

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `office_level` | string | **必填** | 原生 | 层级 | `concept`｜`concrete`（O01） | 录入 | `"concrete"` |
| `parent_id` | string | 条件：具体条有概念时填；**概念条不得有**（概念只一级） | 原生 | 所属概念条 | office 概念条 id（O04） | 录入 | `"1jb8ajoi8crnk"` |
| `dynasty_ids` | array<string> | 条件：具体条**必填**；概念不得有 | 原生 | 所属朝代 | dynasty id 数组（宋默认「趙宋」，北南宋有变才拆）（O02） | 录入 | `["1jb89swq2uvb4"]` |
| `function` | string | 条件：具体条**必填** | 原生 | 本朝职掌 | 自写（O02） | 录入 | `"一縣之長官，掌一縣之賦役、刑獄、教化與勸農。"` |
| `basis` | string | 条件：具体条**必填** | 原生 | 本条依据 | 自由文本（O02） | 录入 | `"《明史·職官志》"` |
| `office_class` | string | 可选；具体条（概念不得有） | 原生 | 官类 | 15 值：`職事官`｜`差遣`｜`散官`｜`階官`｜`加官`｜`貼職`｜`寄祿官`｜`祠祿官`｜`勳`｜`爵`｜`本官`｜`試秩`｜`憲官`｜`兼職差遣`｜`未詳`（O03）。草稿库 10-08 用到：`職事官` 1,064、`差遣` 98、`貼職` 51、`寄祿官` 40、`散官` 10、`加官` 6 | 录入 | `"差遣"` |
| `rank` | object | 可选；具体条（概念不得有） | 原生 | 品秩 | `{text, basis}`，自写 | 录入 | `{"text":"正七品","basis":"《明史·職官志》"}` |
| `salary` | object | 可选；具体条（概念不得有） | 原生 | 俸禄 | `{text, basis}`，自写（现无数据） | 录入 | |
| `start`、`end` | integer | 可选；具体条 | 原生 | 起讫 | 整数公历年，`start ≤ end`（O09） | 录入 | |
| `institution_ref` | string | 可选；具体条 | 原生 | 所属官署 | 官署条 id（`collective_kind=官署`）。指具体条须与本条 `dynasty_ids` 相交；指概念条须 `ai_note` 标「待補」（否则 WARN）；官名含部名而指合称 WARN；id 不在本库 WARN。不得写 `COL:<名>` 占位（ERROR，新官署先建条）（I12） | 录入 | `"1jb8bl20kqn7k"` |
| `base_office_id` | string | 条件：固定复合条**必填** | 原生 | 复合条的基官 | 指同朝**具体** office 条，不自指、无环；与本条 `dynasty_ids` 须相交；指向概念条而 `ai_note` 未说明为 WARN（O05）。反查由 build 派生 `_compounds` | 录入 | `"1jb8awb7yk5q8"` |
| `qualifier` | object | 条件：有 `base_office_id` 时**必填** | 原生 | 复合的限定成分 | `{kind, name, target?, note?}`（O05） | 录入 | |
| `qualifier.kind` | string | **必填** | 原生 | 限定类别 | `institution`｜`place`｜`mode`｜`mode+institution`。草稿库 10-08：`institution` 197、`mode` 26、`place` 7 | 录入 | `"institution"` |
| `qualifier.name` | string | **必填** | 原生 | 限定成分本字 | 非空 | 录入 | `"稽勳清吏司"` |
| `qualifier.target` | string | 可选 | 原生 | 限定成分对应的条目 id | 草稿库 230 项全写 `null`（未指条目），读者按缺省读 | 录入 | `null` |
| `qualifier.note` | string | 可选 | 原生 | 说明 | 自由文本。现值：`官署條待立` 115、`殿閣，官署條待立` 36、`官署條不立` 26、`職事名目` 24、`幕府，官署條不立` 14、`地名條待立` 7、`行政層級，官署條不立` 4、`官署條見 institution_ref` 2、`加官前綴` 2 | 录入 | `"官署條待立"` |
| `succeeds` | string | 不填 | 原生 | 前代概念或具体条 id | 只留字段位，第一期不填 | — | |

- 概念条不得有 `dynasty_ids`、`rank`、`salary`、`office_class`、`base_office_id`、`parent_id`（O02／O04）；概念条宜写 `description`。
- 同一概念下同朝具体条（`dynasty_ids` 完全相同）多于一条 WARN（O11）。
- `_children`（概念→具体）、`_compounds`（`base_office_id` 反查）由 build 派生。
- 10-08：只在草稿库，1,839 条（concrete 1,511、concept 328；复合条 230、有 `institution_ref` 368）。草稿库 office 的 `dynasty_ids` 指草稿 dynasty id（`1jb89…`），build 经 `promotions/` 换成正式 id。

例（草稿库，知縣（明）`1jb8ajoigs6bk`；复合例 稽勳郎中（明）`1jb8db78fa3uo`）：

```json
{
  "schema_version": 1,
  "id": "1jb8ajoigs6bk",
  "type": "entity",
  "subtype": "office",
  "office_level": "concrete",
  "primary_name": "知縣",
  "parent_id": "1jb8ajoi8crnk",
  "dynasty_ids": [
    "1jb89swq01qf4"
  ],
  "function": "一縣之長官，掌一縣之賦役、刑獄、教化與勸農。",
  "office_class": "職事官",
  "rank": {
    "text": "正七品",
    "basis": "《明史·職官志》"
  },
  "basis": "《明史·職官志》",
  "review": {
    "status": "unreviewed"
  },
  "revision": "1.0.0",
  "revised_at": "2026-10-07",
  "updated_at": "2026-10-07T00:00:00+00:00"
}
```

```json
  "institution_ref": "1jb8bl20kqn7k",
  "base_office_id": "1jb8awb7yk5q8",
  "qualifier": {
    "kind": "institution",
    "name": "稽勳清吏司",
    "target": null,
    "note": "官署條待立"
  },
```

### 六·三　`place`（地名）

一地一条＋沿革（不拆每朝一条）；上级写在下级的沿革项里。**现状（10-08）**：草稿库已建 921 条（overview#464 地名二期 P5a／P5b 批），正式库 0 条。沿革据公版地志原典人工核对，依据写在各沿革项 `note`；不采用 CBDB／CHGIS 的内容或编号。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `primary_name` | string | **必填** | 原生 | 地名 | 非空（P01） | 录入 | `"開封府"` |
| `history` | array<object> | **必填**（非空） | 原生 | 沿革 | 各项时段不重叠（可有空档）（P01、P02） | 录入 | |
| `history[].start` | integer | 可选 | 原生 | 本段起年 | 整数公历年，`start ≤ end`（P02） | 录入 | `960` |
| `history[].end` | integer | 可选 | 原生 | 本段止年 | 整数，≤ 1912（其后用 `modern` 表达）（P02） | 录入 | `1053` |
| `history[].dynasty_ids` | array<string> | 可选 | 原生 | 本段所属朝代 | dynasty id，须存在（P04）；本段年份须为所挂各朝代起讫的并集覆盖（端点相接算覆盖；朝代缺起讫者不查），否则 WARN——元明、明清之际等交替年份要补挂前朝或拆段（P11） | 录入 | `["hixi1ubk35zj"]` |
| `history[].name` | string | **必填** | 原生 | 本段当时之名 | 非空（P01） | 录入 | `"汴州"` |
| `history[].level` | string | **必填** | 原生 | 政区层级 | 12 值：`國`｜`郡`｜`州`｜`府`｜`軍`｜`監`｜`路`｜`道`｜`省`｜`縣`｜`廳`｜`都`（P01）。草稿库 10-08 用到：`縣` 2,776、`州` 1,726、`府` 472、`路` 318、`軍` 112、`郡` 85、`省` 68、`道` 16、`監` 8、`都` 7、`廳` 2 | 录入 | `"府"` |
| `history[].parent_id` | string | 可选 | 原生 | 本段上级 | place id，须存在、不自引、无环（P03）；上级在本段年份内须有沿革段覆盖（端点相接算覆盖），否则 WARN，应在空档处拆段、该段上级留空（P10） | 录入 | `"1jb8kox0psbuo"` |
| `history[].parent_text` | string | 可选 | 原生 | 上级未建条时的上级名 | 与 `parent_id` 并存 WARN，入库前清掉 `parent_text`（P03）；草稿库现无 | 录入 | |
| `history[].note` | string | 可选 | 原生 | 本段依据 | 自由文本（草稿库 5,590 项全有） | 录入 | `"《宋史》卷八十五〈地理志一〉：…"` |
| `modern` | object | 可选 | 原生 | 今地对照 | `{text, adcode?, relation, note?}`（P06） | 录入 | `{"text":"河南省開封市（府治在今老城區）","adcode":"410200","relation":"治所今在"}` |
| `modern.text` | string | 条件：有 `modern` 时必填 | 原生 | 今地 | 自由文本 | 录入 | `"河南省洛陽市"` |
| `modern.adcode` | string | 可选 | 原生 | 行政区划代码 | GB/T 2260 六位数字（P06）；草稿库 808／921 | 录入 | `"410300"` |
| `modern.relation` | string | 条件：有 `modern` 时**必填** | 原生 | 古今关系 | 5 值：`同名同地`｜`治所今在`｜`轄域約當`｜`沿用其名而異地`｜`無對應`（P06）。草稿库 10-08：`治所今在` 468、`同名同地` 322、`轄域約當` 127、`沿用其名而異地` 3、`無對應` 1 | 录入 | `"治所今在"` |
| `modern.note` | string | 可选 | 原生 | 说明 | 自由文本 | 录入 | |
| `predecessors` | array<object> | 可选 | 原生 | 前身 | 每项 `{id, kind, year?, note?}`，`id` 须为 place（P07）；写在后继一侧；草稿库现无 | 录入 | |
| `predecessors[].kind` | string | **必填** | 原生 | 承继方式 | 2 值：`析出`｜`並入`（P07） | 录入 | |
| `coords` | — | **不得有** | — | 坐标 | 第一期禁止出现（P08）；将来只许 Wikidata（CC0）或自测 | — | |

- 同名异地出 INFO 清单；同名且上级链相同的疑重复 WARN（P09）。
- `_children`（沿革项 `parent_id` 反查）、`_span`（各段起讫的总跨度）由 build 派生。
- 草稿库 place 的 `history[].dynasty_ids` 已直接指正式库 dynasty id（`hixi1…`），校验时加 `--ref-root <book-index>`（见〈八〉）。

例（草稿库，開封府 `1jb8lqn358dfk`，节录两段沿革）：

```json
{
  "schema_version": 1,
  "id": "1jb8lqn358dfk",
  "type": "entity",
  "subtype": "place",
  "primary_name": "開封府",
  "alt_names": [
    {
      "name": "汴州",
      "type": "舊稱"
    },
    {
      "name": "開封",
      "type": "簡稱",
      "ambiguous": true
    }
  ],
  "history": [
    {
      "start": 1053,
      "end": 1055,
      "dynasty_ids": [
        "hixi1ubk35zj"
      ],
      "name": "開封府",
      "level": "府",
      "parent_id": "1jb8kox0psbuo",
      "note": "《宋史》卷八十五〈地理志一〉：開封府，領縣十六（浚儀改祥符等）；皇祐五年（1053）曾置京畿路，至和二年（1055）罷，崇寧四年（1105）改開封府界為京畿路。五代（907–960）沿革志文未載，不寫。"
    },
    {
      "start": 1055,
      "end": 1105,
      "dynasty_ids": [
        "hixi1ubk35zj"
      ],
      "name": "開封府",
      "level": "府",
      "note": "…（本段年份上級條目無沿革段，上級留空。）"
    }
  ],
  "modern": {
    "text": "河南省開封市（府治在今老城區）",
    "adcode": "410200",
    "relation": "治所今在"
  }
}
```

---

## 七、禁字段与派生字段

### 七·一　源档不写

| 字段 | 适用 | 为什么 | 码 |
|---|---|---|---|
| 任何 `_` 起首字段 | 全部 | 派生字段只在产物里；`_has_text`／`_has_collated` 的暂留豁免已全面收回（包 E），任何类型源档都不该有 | V01 |
| `works` | 全部 | 名下作品由 `Work.authors[].entity_id` 反查，build 生成 `_works`（两库现无） | V11 |
| `children`、`reigns`、`index_in_reign`、`successors`、`people`、`holders`、`compounds`、`ancestors`、`span`、`same_name` | 专名四子类型 | 反向列表／派生值 | V01 |
| `subordinates`、`members`、`offices`（及 `_children`、`_subordinates`、`_members`、`_offices`） | 官署 | 反向列表 | I11 |
| `cbdb_*`、`dila_*`、`chgis*` 起首的任何顶层键；`translation`、`c_office_trans`、`cbdb_alt_names` | 专名四子类型、官署 | 授权硬约束，防日后顺手搬进来 | E1（官署报 I08） |
| `external_ids` 中 `wikidata_id` 以外的子键 | 专名四子类型、官署 | 同上 | E1（官署报 I08） |
| `coords` | dynasty、reign、office；place | 只 place 预留，且第一期禁出现 | E1；place 报 P08 |
| `dates` | office、place | 起讫在 `start`／`end` 或沿革项里 | D3 |
| `office_level`、`office_class`、`rank`、`salary`、`base_office_id`、`qualifier`、`institution_ref` | 官署 | 官职专有字段 | I08 |
| `location_id` | 官署 | 第一期禁出现 | I09 |
| `sources`（顶层） | 全部 | 出处一律记 `description.sources`（两库现无） | — |
| `aliases` | 全部 | 旧写法，形状同 `alt_names`，已并入 `alt_names`（两库 10-08 已清零） | — |

### 七·二　build 派生（只在 `_build/entry/<id>.json`）

| 适用 | 派生字段 | 来源 |
|---|---|---|
| 全部 Entity | `_works` | `Work.authors[].entity_id` 反查；每项 `{work_id, role, title, …}`，`role` 缺则补「撰」 |
| people | `_dynasty_id`／`_dynasty_candidates` | `dynasty` 名在朝代键表里唯一且不歧义命中 → `_dynasty_id`；否则有候选 → `_dynasty_candidates` |
| dynasty | `_children`、`_ancestors`、`_reigns` | `parent_id` 反查；上溯至多 3 级；reign 的 `dynasty_id` 反查 |
| reign | `_dynasty`、`_ruler`、`_index_in_reign`、`_same_name` | `dynasty_id`；`ruler.entity_id`；同朝同帝王年号按起年排序的序号；同名年号 |
| office | `_children`、`_compounds` | 具体条 `parent_id` 反查；`base_office_id` 反查 |
| place | `_children`、`_span` | 沿革项 `parent_id` 反查；各段起讫 |
| 官署 | `_children`、`_subordinates`、`_members`、`_offices` | `parent_id`、`superiors`、`group_ids`、office 的 `institution_ref` 反查 |

已升格的草稿条以正式条为准：不进反查、不进键表，一切 id 引用先经 `promotions/` 换成正式 id。卡片形状与键表（`dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`）见 [derived.md](derived.md)。

---

## 八、校验码

专名子类型校验（E、D、R、A、O、P、I 系列，及 V01 对新子类型的加严）实现在 `.claude/qa/entity_subtypes.py`，`check_v2.py` 与 `verify.py` 共用同一份。只对专名四子类型与带 `collective_kind` 的 collective 生效；people、无 `collective_kind` 的旧 collective 不受这些码约束。ERROR 计残留；WARN 只报不计；INFO 只出清单。

草稿库查专名时加 `--ref-root <book-index>`：草稿条目的 `dynasty_ids`、`parent_id` 等可以直接指正式库 id（专名升格后的规范写法），引用解析会认正式库的 Entity；跨条目检查（D1 唯一、P09 同名、I10 疑重复等）仍只在本仓内比，两仓同名条不算重复。

```bash
find Entity -name '*.json' | python3 .claude/qa/check_v2.py --paths - --summary
# 草稿库：
find Entity -name '*.json' | python3 <book-index>/.claude/qa/check_v2.py --root . --ref-root <book-index> --paths - --summary
```

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| E1 | 专名四子类型 | 出现 `cbdb_*`、`chgis*`、`dila_*`、`translation`、`c_office_trans`、`cbdb_alt_names`；`external_ids` 含 `wikidata_id` 以外的键，或 `wikidata_id` 不合 `^Q\d+$`；非 place 出现 `coords` | ERROR |
| D1 | dynasty | `primary_name` 非空、在规范朝代名枚举内、全库唯一（读不到规范名表时跳过枚举比对） | ERROR |
| D2 | dynasty | `parent_id` 存在、是 dynasty、无环、上溯深度 ≤3（ERROR）；子朝代 `dates` 落在上级之内，容差 1 年（WARN） | ERROR／WARN |
| D3 | dynasty、reign、office、place | `dates` 键按 subtype 放行（office／place 有 `dates` 即错）；`start`／`end` 为整数、无 0 年、`start ≤ end`；dynasty 的 `period` 是现有 slug（ERROR）；有 `period` 而缺 `start`（WARN） | ERROR／WARN |
| R1 | reign | `dynasty_id` 必填且指 dynasty（缺而 `ai_note` 有说明为 WARN）；`ruler.name` 非空；`ruler.entity_id` 指 people；`dates.start` 必填整数；`(primary_name, dynasty_id, start)` 唯一；同朝同名年号区间不重叠（以上 ERROR）；`dates` 越出所属朝代，容差 5 年（WARN） | ERROR／WARN |
| A1 | 专名四子类型、官署 | `alt_names` 为数组、每项 `name` 非空、`ambiguous` 为 bool；无 `ambiguous` 的 dynasty 别名在 dynasty 内全局唯一（以上 ERROR）；`ambiguous` 之名全库 ≥2 条声称（WARN） | ERROR／WARN |
| O01 | office | `office_level` ∈ `concept`／`concrete` | ERROR |
| O02 | office | 具体条 `dynasty_ids` 非空且指 dynasty、`function`／`basis` 非空；概念条禁字段 | ERROR |
| O03 | office | `office_class` 在 15 值内 | ERROR |
| O04 | office | `parent_id` 指 office 概念条；概念条不得有 `parent_id` | ERROR |
| O05 | office | `base_office_id` 存在、是 office、不自指、无环、与本条 `dynasty_ids` 相交；有 `base_office_id` 则必有 `qualifier`；`qualifier.kind` 在 4 值内、`name` 非空（以上 ERROR）；`base_office_id` 指概念条而 `ai_note` 未说明（WARN） | ERROR／WARN |
| O09 | office | `start`／`end` 为整数且 `start ≤ end` | ERROR |
| O10 | office | `簡稱` 长度 ≤2，须确认不与他概念重名 | WARN |
| O11 | office | 同一概念下同朝具体条重复 | WARN |
| O12 | 专名四子类型、官署 | `alt_names[].type` 在 23 值枚举内 | ERROR |
| P01 | place | `primary_name` 非空；`history` 为非空数组；各项为对象、`level` 在 12 值内、`name` 非空 | ERROR |
| P02 | place | 各项 `start`／`end` 为整数、`start ≤ end`、`end ≤ 1912`；各项时段不重叠 | ERROR |
| P03 | place | `history[].parent_id` 存在且为 place、不自引、上级链无环（ERROR）；`parent_id` 与 `parent_text` 并存（WARN） | ERROR／WARN |
| P04 | place | `history[].dynasty_ids` 存在且为 dynasty | ERROR |
| P06 | place | `modern` 为对象、`relation` 必填且在 5 值内、`adcode` 为六位数字 | ERROR |
| P07 | place | `predecessors[].id` 存在且为 place、`kind` ∈ `析出`／`並入` | ERROR |
| P08 | place | 出现 `coords` | ERROR |
| P09 | place | 同名异地组（INFO）；同名且上级链相同，疑重复（WARN） | INFO／WARN |
| P10 | place | 某沿革段写了 `parent_id`，上级在该段年份内须有沿革段覆盖（端点相接算覆盖），否则应在空档处拆段、上级留空 | WARN |
| P11 | place | 某沿革段的年份须为其 `dynasty_ids` 各朝代起讫的并集覆盖（端点相接算覆盖；朝代缺起讫者不查） | WARN |
| I01 | collective | `collective_kind` 在 5 值内；官署的 `institution_level` 在 3 值内 | ERROR |
| I02 | 官署 | 具体条 `dynasty_ids`（非空、指 dynasty）／`function`／`basis` 必填、`basis` 不含「待核」；概念条与合称条禁 `dynasty_ids`、`function`、`superiors`、`start`、`end`、`basis`；合称条不得有 `group_ids`；概念条与合称条 `description` 必填 | ERROR |
| I03 | 官署 | 具体条 `parent_id` 指官署概念条；概念条、合称条不得有 `parent_id` | ERROR |
| I04 | 官署 | `superiors` 为数组，各项指同朝官署具体条、不自指、无环、`start`／`end` 为整数且 `start ≤ end`（ERROR）；上级与本条朝代不相交（WARN） | ERROR／WARN |
| I05 | 官署 | `group_ids` 指合称条（ERROR）；具体条与其概念条重复挂同一合称（WARN） | ERROR／WARN |
| I06 | 官署 | 具体条 `start`／`end` 为整数、无 0 年、`start ≤ end`（ERROR）；越出所属朝代 5 年（WARN） | ERROR／WARN |
| I07 | 官署 | 同一概念下同朝（合并条按展开的朝代算）只一条具体条 | WARN |
| I08 | 官署 | 外部 id 与禁字段（同 E1）；官职专有字段 | ERROR |
| I09 | 官署 | `location_id` 出现（ERROR）；`succeeds` 出现（WARN） | ERROR／WARN |
| I10 | 官署 | 同名且朝代重叠的具体条，疑重复 | WARN |
| I11 | 官署 | 派生字段入源档 | ERROR |
| I12 | office | `institution_ref`：`COL:<名>` 占位（ERROR）；须指官署条（ERROR）；指具体条须与官职朝代相交（ERROR）；指概念条须 `ai_note` 标「待補」（WARN）；官名含部名而指合称（WARN）；id 不在本库（WARN） | ERROR／WARN |
| V01 | 全部 | 源档出现 `_` 起首字段；专名四子类型另查无下划线的派生名（见〈七·一〉）；`_has_text`／`_has_collated` 豁免已收回 | ERROR |
| V11 | 全部 | 源档有 `works` | ERROR |
| V15 | 全部 | 缺 `schema_version` 或其值不是整数 `1` | ERROR |
| V16 | 全部 | `description.sources` 不是数组，或元素既非字符串亦非对象 | ERROR |

- 已废的码：O06（CBDB 码防重）已删；O07 并入 V01；O08 并入 E1；P05 并入 V01。
- 口径：上下级区间不合（如战国止年晚于东周、北朝起年早于南北朝）、年号越出所属朝代区间，一律 WARN，不是 ERROR。
- 10-08 实测基线：正式库 ERROR 0，WARN 9（D2 2、D3 2、R1 5）；草稿库（带 `--ref-root`）ERROR 0，WARN 113（A1 16、D2 2、D3 2、O10 88、R1 5），INFO 38（P09）。

`verify.py` 另查以下各项（无码，出计数；「是否计成败」一列说明）：

| 查什么 | 说明 | 是否计成败 |
|---|---|---|
| `dates` 合法性 | 见〈四·一〉末 | 一律计 |
| `external_ids` 合法性 | `wikidata_id`、`viaf_id` 形状，见〈四·二〉 | 一律计 |
| `todo`、`review` 形状 | 见〈二〉 | 一律计 |
| entities 索引漂移 | `index/` 里的 `primary_name`、`dynasty`、`birth_year`、`death_year`、`period` 与源档不一致 | 一律计 |
| `Work.authors[].entity_id` 悬空 | 指向不存在的 Entity | `--strict` 时计 |
| 专名校验码与 V 系列 | 同上表，与 check_v2 共用实现（verify 不带 `--ref-root`） | 专名码的 ERROR 一律计；V 系列 ERROR `--strict` 时计；WARN／INFO 只报数 |
| 朝代与生卒世纪明显不合 | people 的 `dynasty` 与 `birth_year`／`death_year`／`dates.birth`／`dates.death` 在宽容 ±40 年外不合；史学惯例常以主要活动或卒年所属朝代标注 | 只报数，不计 |
