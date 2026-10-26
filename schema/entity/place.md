# place（地名）

总览与子类型索引见 [../entity.md](../entity.md)。

## 真实示例

下列路径都是本仓真实文件（`tests/test_entity_examples.py` 逐条核实存在）；「index」列是派生分片索引，键即该条 id。分片编号会随重建变动，以测试核实为准。

| 示例 | 源档 | index | 演示什么 |
|---|---|---|---|
| 潼川府 `hixi4ugtgcn5` | [Entity/c/n/5/hixi4ugtgcn5-潼川府.json](../../Entity/c/n/5/hixi4ugtgcn5-潼川府.json) | [index/entities/3.json](../../index/entities/3.json) | 潼川府：一地一条＋14 段 `history` 沿革（梓州→梓潼郡→潼川府…）与 `modern` 今地对照 |
| 果州 `hixi5wawecy1` | [Entity/c/y/1/hixi5wawecy1-果州.json](../../Entity/c/y/1/hixi5wawecy1-果州.json) | [index/entities/0.json](../../index/entities/0.json) | 果州：多个 `alt_names`，同样 14 段沿革；演示换名与上级留空的写法 |

## 两层：跨朝条与朝代条

地名分两层，结构仿 office 的概念条／具体条（2026-10-25 定）：

- **朝代条**（`place_level: "concrete"`）：**某朝、某名、某级一条**，如「平陸縣（明）」「平陽府（明）」。顶层 `dynasty_ids` 必填；`history` 各段名与级都同 `primary_name`，只用来记朝内上级的变动（如由府属改直隶州属就拆段）；上级 `parent_id` 只指**同朝**的朝代条。朝内改名或升降（州升府、县降镇）另立一条朝代条，在后一条的 `predecessors` 写 `{"id": 前一条, "kind": "改置", "year": …}`。每段 `note` 录正史地理志等原典原文与卷次。人物籍贯（`native_place_entity_id`）知道朝代时宜指朝代条。
- **跨朝条**（`place_level: "concept"`，缺省即此）：不带顶层朝代，串起一地历代的名称与隶属变迁，就是下文「一地一条＋沿革」的写法；现有各条都是跨朝条。跨朝条沿革段的 `parent_id` 只指跨朝条。朝代条以 `concept_id` 挂到它所属的跨朝条，反查由 build 派生 `_concretes`（按起年排）。

先有朝代条、后补跨朝条也可以：朝代条的 `concept_id` 可选，跨朝条可以晚建。一朝之内的上下级查朝代条；问「某地历代叫什么、归哪里」查跨朝条。

| 字段（两层相关） | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `place_level` | string | 可选（缺省 `concept`）；新建朝代条**必写** | 层级 | `concept`｜`concrete`（P12） |
| `dynasty_ids` | array<string> | 条件：朝代条**必填**；跨朝条不得有 | 本条所属朝代 | dynasty id；唐含武周、元含蒙古时一并挂（P13） |
| `concept_id` | string | 可选；只许朝代条 | 所属跨朝条 | place 跨朝条 id（P14） |

例（朝代条，平陸縣（明），节录）：

```json
{
  "subtype": "place",
  "place_level": "concrete",
  "primary_name": "平陸縣",
  "dynasty_ids": ["hixi1ubjrxfw"],
  "concept_id": "<跨朝条 平陸縣>",
  "history": [
    {
      "start": 1368,
      "end": 1644,
      "dynasty_ids": ["hixi1ubjrxfw"],
      "name": "平陸縣",
      "level": "縣",
      "parent_id": "<朝代条 解州（明）>",
      "note": "《明史》卷四十一〈地理志二〉：平陸，州東南。…"
    }
  ]
}
```

## 跨朝条（一地一条＋沿革）

一地一条＋沿革；上级写在下级的沿革项里。**现状（10-08）**：草稿库已建 921 条（overview#464 地名二期 P5a／P5b 批），正式库 0 条。沿革据公版地志原典人工核对，依据写在各沿革项 `note`；不采用 CBDB／CHGIS 的内容或编号。

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
| `predecessors[].kind` | string | **必填** | 原生 | 承继方式 | 3 值：`析出`｜`並入`｜`改置`（同一地朝内改名或升降，朝代条用）（P07） | 录入 | |
| `predecessors[].year` | integer | 可选 | 原生 | 承继发生年 | 整数公历年 | 录入 | |
| `predecessors[].note` | string | 可选 | 原生 | 说明 | 自由文本 | 录入 | |
| `coords` | — | **不得有** | — | 坐标 | 第一期禁止出现（P08）；将来只许 Wikidata（CC0）或自测 | — | |

- 同名异地出 INFO 清单；同名且上级链相同的疑重复 WARN（P09）。朝代条只与同名同朝代的朝代条比，跨朝条与朝代条不互比。
- `_children`（沿革项 `parent_id` 反查）、`_span`（各段起讫的总跨度）、`_concretes`（朝代条 `concept_id` 反查，只在跨朝条上）由 build 派生。
- `place_keys.json` 候选里朝代条带 `place_level: "concrete"` 与 `dynasties`，按朝代挑；`default` 只在跨朝条间标，某键只有一条跨朝条、其余都是朝代条时标那条跨朝条。
- 草稿库 place 的 `history[].dynasty_ids` 已直接指正式库 dynasty id（`hixi1…`），校验时加 `--ref-root <book-index>`（见[校验码](_checks.md)）。

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

## 校验码

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| D3 | dynasty、reign、office、place | `dates` 键按 subtype 放行（office／place 有 `dates` 即错）；`start`／`end` 为整数、无 0 年、`start ≤ end`；dynasty 的 `period` 是现有 slug（ERROR）；有 `period` 而缺 `start`（WARN） | ERROR／WARN |
| P01 | place | `primary_name` 非空；`history` 为非空数组；各项为对象、`level` 在 12 值内、`name` 非空 | ERROR |
| P02 | place | 各项 `start`／`end` 为整数、`start ≤ end`、`end ≤ 1912`；各项时段不重叠 | ERROR |
| P03 | place | `history[].parent_id` 存在且为 place、不自引、上级链无环（ERROR）；`parent_id` 与 `parent_text` 并存（WARN） | ERROR／WARN |
| P04 | place | `history[].dynasty_ids` 存在且为 dynasty | ERROR |
| P06 | place | `modern` 为对象、`relation` 必填且在 5 值内、`adcode` 为六位数字 | ERROR |
| P07 | place | `predecessors[].id` 存在且为 place、`kind` ∈ `析出`／`並入`／`改置` | ERROR |
| P08 | place | 出现 `coords` | ERROR |
| P09 | place | 同名异地组（INFO）；同名且上级链相同，疑重复（WARN） | INFO／WARN |
| P10 | place | 某沿革段写了 `parent_id`，上级在该段年份内须有沿革段覆盖（端点相接算覆盖），否则应在空档处拆段、上级留空 | WARN |
| P11 | place | 某沿革段的年份须为其 `dynasty_ids` 各朝代起讫的并集覆盖（端点相接算覆盖；朝代缺起讫者不查） | WARN |
| P12 | place | `place_level` ∈ `concept`／`concrete`（缺省 concept） | ERROR |
| P13 | place | 朝代条：顶层 `dynasty_ids` 非空且都是 dynasty；各段 `name` 同 `primary_name`、`level` 一致；段的 `dynasty_ids` 不出顶层所挂。跨朝条不得有顶层 `dynasty_ids` | ERROR |
| P14 | place | 上级同层：朝代条段的 `parent_id` 须指朝代条且朝代相交，跨朝条段的 `parent_id` 须指跨朝条；`concept_id` 只许朝代条、须指跨朝条 | ERROR |

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
