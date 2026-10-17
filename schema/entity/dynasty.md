# dynasty（朝代／政权）

总览与子类型索引见 [../entity.md](../entity.md)。

## 真实示例

下列路径都是本仓真实文件（`tests/test_entity_examples.py` 逐条核实存在）；「index」列是派生分片索引，键即该条 id。分片编号会随重建变动，以测试核实为准。

| 示例 | 源档 | index | 演示什么 |
|---|---|---|---|
| 趙宋 `hixi1ubjrxgo` | [Entity/x/g/o/hixi1ubjrxgo-趙宋.json](../../Entity/x/g/o/hixi1ubjrxgo-趙宋.json) | [index/entities/c.json](../../index/entities/c.json) | 总称朝代（趙宋），无 `parent_id`，`alt_names` 含別稱 |
| 北宋 `hixi1ubk35zj` | [Entity/5/z/j/hixi1ubk35zj-北宋.json](../../Entity/5/z/j/hixi1ubk35zj-北宋.json) | [index/entities/1.json](../../index/entities/1.json) | 子政权（北宋）：`parent_id` 指向趙宋，演示上下级写法 |
| 清 `hixi1ubjrxga` | [Entity/x/g/a/hixi1ubjrxga-清.json](../../Entity/x/g/a/hixi1ubjrxga-清.json) | [index/entities/e.json](../../index/entities/e.json) | 清：顶层朝代，起讫与 `basis` 的写法 |

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `primary_name` | string | **必填** | 原生 | 规范朝代名 | 必须**逐字**在 [common.md〈朝代规范名〉](../common.md) 的规范名表（含域外朝代表）里，全库唯一（D1）；条目化后枚举改由 build 从条目生成，不得再手写第二份 | 录入 | `"北宋"` |
| `parent_id` | string | 可选 | 原生 | 上级朝代 | dynasty id；单父，上溯深度 ≤3（如 春秋吳→春秋→東周→先秦），无环；子朝代 `dates` 落在上级之内（容差 1 年，越界 WARN）（D2）。子列表由 build 派生 `_children` | 录入 | `"hixi1ubjrxgo"`（北宋→趙宋） |
| `dates` | object | 条件：中国朝代必填 `start` | 原生 | 起讫 | `{start, end?, basis, chinese?}`，见[dates 按子类型放行](_dates-external-ids.md#dates-按子类型放行) | 录入 | `{"start":960,"end":1127,"basis":"趙匡胤 960 稱帝，止於靖康"}` |
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

## 校验码

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| D1 | dynasty | `primary_name` 非空、在规范朝代名枚举内、全库唯一（读不到规范名表时跳过枚举比对） | ERROR |
| D2 | dynasty | `parent_id` 存在、是 dynasty、无环、上溯深度 ≤3（ERROR）；子朝代 `dates` 落在上级之内，容差 1 年（WARN） | ERROR／WARN |
| D3 | dynasty、reign、office、place | `dates` 键按 subtype 放行（office／place 有 `dates` 即错）；`start`／`end` 为整数、无 0 年、`start ≤ end`；dynasty 的 `period` 是现有 slug（ERROR）；有 `period` 而缺 `start`（WARN） | ERROR／WARN |

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
