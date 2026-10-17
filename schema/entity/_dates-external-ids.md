# Entity：dates 与 external_ids

总览与子类型索引见 [../entity.md](../entity.md)。



## `dates` 按子类型放行
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
- `birth_year`／`death_year` 已由 book-index#139（B2）删除；展示与索引读 `dates.birth`／`dates.death`。
- 校验（`verify.py`）：`birth`／`death`／`floruit[0]`／`floruit[1]` 须为整数；`floruit` 为二元数组；`birth ≤ death`；`floruit[0] ≤ floruit[1]`。

## `external_ids` 子键
**专名四子类型、seal 与官署：只许 `wikidata_id`**（publisher 另许 `isbn_publisher_code`）（`^Q\d+$`，第一期不填）；出现任何其他子键即 ERROR（E1；官署报 I08）。下表其余子键只用于 `people`。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `external_ids.cbdb_id` | integer | 可选；people | 原生 | CBDB 人物 id | 正整数（正式库 14,328、草稿库 725） | 录入、bim | `3767` |
| `external_ids.cbdb_match` | string | 条件：有 `cbdb_id` 或核过 CBDB 时写 | 原生 | 匹配方式 | 开放词表。现值（正式库）：`auto` 5,825、`auto_2026-09-06` 3,246、`manual` 2,559、`auto_create` 1,831、`auto_create_p4` 720（草稿库 725）、`auto_placeholder_upgrade` 48、`auto_dy_ambig_year` 35、`none` 24、`manual_remap` 23、`auto_dy_unique` 22、`auto_altname_upgrade` 10、`manual (C5 batch17)` 5、`manual ; dynasty_fix: 南朝宋→宋 per CBDB dy=…` 4、`restored` 1。`none` 表示核过而 CBDB 无此人或只有误配，此时不写 `cbdb_id`，理由写在 `cbdb_source` | 录入、bim | `"manual"` |
| `external_ids.cbdb_source` | string | 条件：同 `cbdb_match` | 原生 | 匹配依据 | 自由文本 | 录入、bim | `"name_exact+dy_match+work_recall_0.56+unique"`；`"none: 僧肇[晉]→CBDB[明]，僧肇(384-414)是東晉僧，非明人"` |
| `external_ids.cbdb_id_alt` | array<integer> | 可选；people | 原生 | CBDB 为同一人另收的 id | 并条时被并方的 `cbdb_id`（正式库 45 条） | 录入 | `[66803]`（劉俊 `hixhd2h9bib6`） |
| `external_ids.cbdb_note` | string | 可选；people | 旧（暂留） | 匹配疑点备注 | 正式库 1 条（梁正 `hixhd2h9bi3z`：`"疑為同名異人誤配——見下 ai_note"`）；待并入 `ai_note` | 录入 | |
| `external_ids.wikidata_id` | string | 可选（全部） | 原生 | Wikidata Q 号 | `^Q\d+$`（正式库 people 11,516） | bim | `"Q36020"` |
| `external_ids.isbn_publisher_code` | string | 可选；仅 publisher（現代出版社） | 原生 | 出版社 ISBN 前缀 | 非空字符串（K07）；专名其他子类型不许 | 录入 | `"7-101"` |
| `external_ids.viaf_id` | string | 可选；people | 原生 | VIAF id | 纯数字字符串（正式库 2,054） | bim | `"96591338"` |

- `wikidata_id`／`viaf_id` 的取法（overview#159）：只给有 `cbdb_id` 的 people 补，经 Wikidata 属性 **P497**（CBDB ID）反查；用 Wikidata 官方 SPARQL 端点一次性批量取全部 `?item wdt:P497 ?cbdb`（及 `wdt:P214` VIAF），不逐条请求，脚本 `.claude/qa/s4/sync_wikidata_ids.py`。按 `cbdb_id` 精确对；一个 `cbdb_id` 对多个 Q 的不写（列入冲突清单，人工另核）；已有 `wikidata_id` 的不覆盖，与新取值不一致的列入冲突清单。两者缺省表示未取得或未对上。
- 校验（`verify.py`）：`wikidata_id` 须匹配 `^Q\d+$`；`viaf_id` 须为纯数字字符串。
- CBDB 相关信息（`cbdb_id`／`cbdb_match`／`cbdb_source`）只存在 Entity 的 `external_ids`，不存在 Work 的 `authors[]` 里。
- 空对象 `{}`：正式库 people 12,199 条、collective 41 条的 `external_ids` 是空对象（旧）。按总则 11 新写不写空对象，读者按缺省读。
