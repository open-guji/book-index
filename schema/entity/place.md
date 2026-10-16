# place（地名）

总览与子类型索引见 [../entity.md](../entity.md)。

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
| `predecessors[].year` | integer | 可选 | 原生 | 承继发生年 | 整数公历年 | 录入 | |
| `predecessors[].note` | string | 可选 | 原生 | 说明 | 自由文本 | 录入 | |
| `coords` | — | **不得有** | — | 坐标 | 第一期禁止出现（P08）；将来只许 Wikidata（CC0）或自测 | — | |

- 同名异地出 INFO 清单；同名且上级链相同的疑重复 WARN（P09）。
- `_children`（沿革项 `parent_id` 反查）、`_span`（各段起讫的总跨度）由 build 派生。
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
| P07 | place | `predecessors[].id` 存在且为 place、`kind` ∈ `析出`／`並入` | ERROR |
| P08 | place | 出现 `coords` | ERROR |
| P09 | place | 同名异地组（INFO）；同名且上级链相同，疑重复（WARN） | INFO／WARN |
| P10 | place | 某沿革段写了 `parent_id`，上级在该段年份内须有沿革段覆盖（端点相接算覆盖），否则应在空档处拆段、上级留空 | WARN |
| P11 | place | 某沿革段的年份须为其 `dynasty_ids` 各朝代起讫的并集覆盖（端点相接算覆盖；朝代缺起讫者不查） | WARN |

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
