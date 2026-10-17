# reign（年号）

总览与子类型索引见 [../entity.md](../entity.md)。

## 真实示例

下列路径都是本仓真实文件（`tests/test_entity_examples.py` 逐条核实存在）；「index」列是派生分片索引，键即该条 id。分片编号会随重建变动，以测试核实为准。

| 示例 | 源档 | index | 演示什么 |
|---|---|---|---|
| 萬曆 `hixi1ubqbwu9` | [Entity/w/u/9/hixi1ubqbwu9-萬曆.json](../../Entity/w/u/9/hixi1ubqbwu9-萬曆.json) | [index/entities/e.json](../../index/entities/e.json) | 萬曆：`ruler`、`dates`（起讫）与 `alt_names`（異體「萬歷」） |
| 康熙 `hixi1ubqbwun` | [Entity/w/u/n/hixi1ubqbwun-康熙.json](../../Entity/w/u/n/hixi1ubqbwun-康熙.json) | [index/entities/3.json](../../index/entities/3.json) | 康熙：只有 `ruler` 与 `dates` 的最小写法 |
| 承平 `hixi1ubml2ch` | [Entity/2/c/h/hixi1ubml2ch-承平.json](../../Entity/2/c/h/hixi1ubml2ch-承平.json) | [index/entities/c.json](../../index/entities/c.json) | 承平（443–460）：同名年号并存，另有 `hixi1ubml2cj`（承平，452）；演示重名年号靠起讫区分 |

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `primary_name` | string | **必填** | 原生 | 年号 | 自由文本 | 录入 | `"萬曆"` |
| `dynasty_id` | string | **必填**（所属政权无条目时可缺，须在 `ai_note` 说明，报 WARN） | 原生 | 颁行当时的政权 | dynasty id（天命、天聰取「後金」） | 录入 | `"hixi1ubjrxfw"`（明） |
| `ruler` | object | **必填** | 原生 | 颁行者 | `{name, entity_id?}` | 录入 | `{"name":"朱翊鈞"}` |
| `ruler.name` | string | **必填** | 原生 | 帝王名 | 非空 | 录入 | `"朱翊鈞"` |
| `ruler.entity_id` | string | 可选 | 原生 | 帝王的人物条 | 须指向 `people`；库中无该帝王条时只写名（两库现无此键） | 录入 | |
| `dates` | object | **必填**（`start` 必填） | 原生 | 起讫 | `{start, end?, basis, chinese?}`，见[dates 按子类型放行](_dates-external-ids.md#dates-按子类型放行)；须落在所属朝代 `dates` 内（容差 5 年，越界 WARN） | 录入 | `{"start":1573,"end":1620,"basis":"通行紀年；與CBDB、DILA相符"}` |

- `(primary_name, dynasty_id, dates.start)` 全库唯一；同朝同名年号区间不重叠（R1）。
- `index_in_reign`、干支不写（build 派生 `_index_in_reign`）。
- 10-08：两库各 734 条（草稿库的已全部升格）。

## 校验码

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| D3 | dynasty、reign、office、place | `dates` 键按 subtype 放行（office／place 有 `dates` 即错）；`start`／`end` 为整数、无 0 年、`start ≤ end`；dynasty 的 `period` 是现有 slug（ERROR）；有 `period` 而缺 `start`（WARN） | ERROR／WARN |
| R1 | reign | `dynasty_id` 必填且指 dynasty（缺而 `ai_note` 有说明为 WARN）；`ruler.name` 非空；`ruler.entity_id` 指 people；`dates.start` 必填整数；`(primary_name, dynasty_id, start)` 唯一；同朝同名年号区间不重叠（以上 ERROR）；`dates` 越出所属朝代，容差 5 年（WARN） | ERROR／WARN |

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
