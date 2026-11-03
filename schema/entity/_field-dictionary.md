# Entity 字段词典（异义同名、同义异名对照）

2026-11-03 起，由 A12 维护。来源：A11 的 Entity 字段审查（ai-team `domain/专名/schema审查/S4-Entity.md`）与 A12 的意见（同目录 `S4-Entity-A12意见.md`）。

**定位**：Entity 字段里有些同名不同义、同义不同名的地方。这里**不改名**（改名要同步 A33 的匹配、A42 的检索、A11 的数据库装载和网站，成本远大于收益），只写清各字段在哪些类型里用、含什么、谁读。新增字段先查本表，避免再造同义词。

## 一、同义异名（同一概念各类型叫法不同）

| 概念 | 叫法与适用类型 | 说明 |
|---|---|---|
| 所属朝代 | people（及旧 collective）：`dynasty`（规范名字符串）＋`dynasty_basis`＋`period`＋`period_basis`；office／官署／place／publisher／seal：`dynasty_ids`（dynasty 条 id 数组）；reign：`dynasty_id`（单个 id）；place 沿革：`history[].dynasty_ids` | `dynasty` 是**软引用**：people 里「宋」「元末明初」等总称、过渡称对不上单个 dynasty 条（用户 2026-10-30 定允许记「宋」）；`dynasty_ids` 是**硬引用** |
| 起讫年 | people：`dates.birth／death／floruit`；dynasty／reign：`dates.start／end`；官署、seal、publisher：`dates.start／end／basis`（2026-11-03 起，原顶层 `start`／`end`／`dates_basis`；顶层已不合法，ERROR）；place：`history[].start／end` | 已统一，见 S4 PR |
| 依据说明 | `dynasty_basis`、`period_basis`、`native_place_basis`、`name_basis`、`dates.basis`、`dates.basis`（已含原 publisher 顶层 `dates_basis`）、`rank.basis`、`function_basis`（office／官署的职掌依据） | 都是「这个值凭什么」，各管各的字段 |
| 上级／所属 | dynasty：`parent_id`＝上位政权；office／官署：`parent_id`＝概念条；place 朝代条：`concept_id`＝跨朝条；place 沿革 `history[].parent_id`＝行政上级；官署隶属：`superiors[]`；成员→合称：`group_ids`；office→官署：`institution_ref`；seal→机构：`institution_ids` | 几种「上」不同，不能互相替代 |
| 概念／具体层 | office：`office_level`；官署：`institution_level`（另有 `group`）；place：`place_level`（`concept`／`concrete`／`region`） | `region` 是区域条，不是层级 |

## 二、异义同名

| 名 | 含义 |
|---|---|
| `basis` | 顶层已无此键（office／官署的职掌依据 2026-11-03 起叫 `function_basis`）；`dates.basis`＝年值依据；`rank.basis`＝品秩依据 |
| `level` | `history[].level`＝行政级别（縣、府、州、山、水等）；`*_level`＝概念／具体层 |
| `type` | `alt_names[].type`＝别名类别；`relations[].type`＝本条是对方的什么（如父、師）；顶层 `type` 恒为 `entity`；`sources[].type` |
| `kind` | `predecessors[].kind`＝承继方式（析出／並入／改置，数据现只有改置）；`qualifier.kind`＝institution／place／mode |
| `status` | publisher 顶层 `status`＝存续状态；`review.status`＝审核（Entity 已停写，见第四节） |
| `name` | `alt_names[].name`、`history[].name`、`ruler.name`、`qualifier.name`、`locations[].name` 各自含义不同 |
| `title_or_office` | people，**文本**：著录所见官职或头衔；不是 office 实体引用 |

## 三、几个容易误读的字段

- `ai_note`：实际是**来源登记**（批次、依据、变更说明），不是随手备注，约 14 万条。新写入时格式：日期＋批次号或 Jira 卡号＋一句依据；存量不动，不改名、不拆结构。
- `external_ids.cbdb_match`／`cbdb_source`：匹配过程的内部元数据，不是外部 id；按红线专名类不存 cbdb_* id，people 里这两个键仅用于内部互验。A/B/C 档与 `none` 值保持合法。
- 并条账只在墓碑上（`merged_into`＋`merged_basis`），清墓碑后在台账 `.claude/qa/purge-tombstones/ledger/`。留存方的 `merged_in`／`merge_history` 已于 2026-11-03 删除，旧账导出在 `ledger/history-20261103.tsv`。
- `native_place`（文本，著录所见）与 `native_place_entity_id`（校正后的 place id）并存。

## 四、停写与待定

- `review`：Entity 里 121,416 条恒为 `{"status":"unreviewed"}`，用户 2026-11-02 定**只停新写、存量不动**。可信度靠 `description.sources`、A/B/C 档、`ai_note` 表达。
- 已删 0 条预留字段：`salary`、`succeeds`、`kind_also`、`seal_script`、`material`、`size`、`dates.chinese`、`birth_year`、`death_year`。真要用时再加。
