# office（官职，两层）

总览与子类型索引见 [../entity.md](../entity.md)。

## 真实示例

下列路径都是本仓真实文件（`tests/test_entity_examples.py` 逐条核实存在）；「index」列是派生分片索引，键即该条 id。分片编号会随重建变动，以测试核实为准。

| 示例 | 源档 | index | 演示什么 |
|---|---|---|---|
| 尚書 `hixi4udstrm6` | [Entity/r/m/6/hixi4udstrm6-尚書.json](../../Entity/r/m/6/hixi4udstrm6-尚書.json) | [index/entities/9.json](../../index/entities/9.json) | 官职**概念条**（尚書，跨朝）：无朝代、无品秩，只写 `description` |
| 尚書 `hixi5v2mknbd` | [Entity/n/b/d/hixi5v2mknbd-尚書.json](../../Entity/n/b/d/hixi5v2mknbd-尚書.json) | [index/entities/3.json](../../index/entities/3.json) | 官职**具体条**（尚書，清）：`parent_id` 指概念条，带 `dynasty_ids`、`rank`（從一品）、`institution_ref`（指六部合称条） |
| 集賢殿修撰 `hixi5vx2u32n` | [Entity/3/2/n/hixi5vx2u32n-集賢殿修撰.json](../../Entity/3/2/n/hixi5vx2u32n-集賢殿修撰.json) | [index/entities/7.json](../../index/entities/7.json) | **固定复合条**（集賢殿修撰）：`base_office_id` 指基官（修撰），`qualifier` 记限定成分（`kind=institution`） |

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

## 校验码

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| D3 | dynasty、reign、office、place | `dates` 键按 subtype 放行（office／place 有 `dates` 即错）；`start`／`end` 为整数、无 0 年、`start ≤ end`；dynasty 的 `period` 是现有 slug（ERROR）；有 `period` 而缺 `start`（WARN） | ERROR／WARN |
| O01 | office | `office_level` ∈ `concept`／`concrete` | ERROR |
| O02 | office | 具体条 `dynasty_ids` 非空且指 dynasty、`function`／`basis` 非空；概念条禁字段 | ERROR |
| O03 | office | `office_class` 在 15 值内 | ERROR |
| O04 | office | `parent_id` 指 office 概念条；概念条不得有 `parent_id` | ERROR |
| O05 | office | `base_office_id` 存在、是 office、不自指、无环、与本条 `dynasty_ids` 相交；有 `base_office_id` 则必有 `qualifier`；`qualifier.kind` 在 4 值内、`name` 非空（以上 ERROR）；`base_office_id` 指概念条而 `ai_note` 未说明（WARN） | ERROR／WARN |
| O09 | office | `start`／`end` 为整数且 `start ≤ end` | ERROR |
| O10 | office | `簡稱` 长度 ≤2，须确认不与他概念重名 | WARN |
| O11 | office | 同一概念下同朝具体条重复 | WARN |
| O12 | 专名子类型、官署 | `alt_names[].type` 在 25 值枚举内 | ERROR |
| I12 | office | `institution_ref`：`COL:<名>` 占位（ERROR）；须指官署条（ERROR）；指具体条须与官职朝代相交（ERROR）；指概念条须 `ai_note` 标「待補」（WARN）；官名含部名而指合称（WARN）；id 不在本库（WARN） | ERROR／WARN |

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
