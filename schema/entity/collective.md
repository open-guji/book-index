# collective（机构）与官署

总览与子类型索引见 [../entity.md](../entity.md)。

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

## 校验码

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
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

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
