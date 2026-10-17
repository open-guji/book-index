# people（人物）

总览与子类型索引见 [../entity.md](../entity.md)。

## 真实示例

下列路径都是本仓真实文件（`tests/test_entity_examples.py` 逐条核实存在）；「index」列是派生分片索引，键即该条 id。分片编号会随重建变动，以测试核实为准。

| 示例 | 源档 | index | 演示什么 |
|---|---|---|---|
| 蘇軾 `hixhd2h9bdqq` | [Entity/d/q/q/hixhd2h9bdqq-蘇軾.json](../../Entity/d/q/q/hixhd2h9bdqq-蘇軾.json) | [index/entities/2.json](../../index/entities/2.json) | 字、号等 `alt_names`、`external_ids`（CBDB／Wikidata 等）、籍贯、`dates` 的完整典型人物条 |
| 強仕 `hixi23un53pm` | [Entity/3/p/m/hixi23un53pm-強仕.json](../../Entity/3/p/m/hixi23un53pm-強仕.json) | [index/entities/7.json](../../index/entities/7.json) | 并条的**留存方**：`merged_in[]` 记录被并入的条（含并入时间、规则、理由） |
| 載湉 `hixi5ikz83tv` | [Entity/3/t/v/hixi5ikz83tv-載湉.json](../../Entity/3/t/v/hixi5ikz83tv-載湉.json) | [index/entities/2.json](../../index/entities/2.json) | 并条的**墓碑**：只留 `primary_name` 与 `merged_into`，指向留存条 `hixhd2h9brxy`（清德宗） |
| 張金瀾 `hixhd2h9bqib` | [Entity/q/i/b/hixhd2h9bqib-張金瀾.json](../../Entity/q/i/b/hixhd2h9bqib-張金瀾.json) | [index/entities/8.json](../../index/entities/8.json) | `native_place_entity_id` 指向 place 条（山陰縣 `hixi5xctqcxs`）的籍贯写法 |

通用字段全部可用（见[通用字段](_common.md)）。people 实际用到的字段一览（每行的完整取值、统计数见[通用字段](_common.md)对应行；`people` 没有专属于它的子类型字段，下面都是[通用字段](_common.md)里的通用字段）：

| 字段 | 类型 | 必填 | 含义 | 例 |
|---|---|---|---|---|
| `primary_name` | string | **必填** | 最通行的名字 | `"蘇軾"` |
| `alt_names[]` | array<AltName> | 可选 | 字、号、谥号、别名等，类型枚举见[alt_names 类型枚举](_alt-names.md#alt_namestype-枚举25-值) | `[{"name":"子瞻","type":"字"}]` |
| `dynasty`、`dynasty_basis` | string | 可选 | 所属朝代（规范名）及依据 | `"北宋"` |
| `period`、`period_basis` | string | 可选 | 时代轴 slug 及依据 | `"song"` |
| `dates` | object | 可选 | 生卒或活动年，键见[dates 按子类型放行](_dates-external-ids.md#dates-按子类型放行) | `{"birth":1036,"death":1101,"basis":"cbdb"}` |
| `native_place`、`native_place_basis` | string | 可选 | 籍贯（文本）及依据 | `"眉山"` |
| `native_place_entity_id` | string | 可选 | 籍贯对应的 place 条 id | `"hixi5xhv38jl"` |
| `title_or_office` | string | 可选 | 著录所见官职 | `"散騎常侍"` |
| `name_basis` | string | 可选 | 名字依据（正名经过） | |
| `external_ids` | object | 可选 | CBDB、Wikidata、VIAF，子键见[external_ids 子键](_dates-external-ids.md#external_ids-子键) | `{"cbdb_id":3767,"wikidata_id":"Q36020"}` |
| `description` | Description | 可选 | 介绍与出处（`sources`） | |
| `merged_in[]`／`merged_into`／`merge_history[]` | array／string／array | 可选 | 并条账与墓碑，见下 | |
| `retired`、`retired_reason` | boolean／string | 可选 | 退役 | |
| `suppressed_fields` | array<string> | 可选 | 人工确认 CBDB 值有误而清空的字段名 | `["cbdb_id"]` |
| `review`、`todo`、`ai_note` | object／array／string | 可选 | 审核状态、待办、备注 | |
| `revision`、`revised_at`、`updated_at` | string | 见[通用字段](_common.md) | 版本与改动时间 | `"1.1.0"` |

people 特有的规矩：

- 名下作品不写，build 生成 `_works`；朝代名由 build 解析为 `_dynasty_id`（规范名唯一命中且不歧义）或 `_dynasty_candidates`（歧义名的候选 id），见 [derived.md](../derived.md)。
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

## 校验码

people 无专名子类型码；`native_place_entity_id` 由 check_v2 的 N01–N03 查（见 [通用字段](_common.md)），`dates`／`external_ids` 形状由 verify 查（见 [dates 与 external_ids](_dates-external-ids.md)）。

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
