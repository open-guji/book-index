# 分类（`classification/`）

分类归属**不写在 Work 里**，写在分类法目录下：一个分类法一个目录。Collection 不分类。两库同构（`book-index/classification/`、`book-index-draft/classification/`）。

```
classification/
  schemes.json              全部分类法登记
  zongmu/                   《中國古籍總目》（主分类法）
    tree.json               分类树
    members/zm0810.json     某一类的成员（一类一档）
  <其他分类法>/ …           结构同上
```

**写入口**：规划中是 `bim classify`（`assign`／`move`／`rename`／`check`），**尚未实现**。在它落地之前，成员档由迁移脚本与录入脚本写，手改须守本档格式（一行一条、按 work_id 排序、文件名＝节点 id），提交前跑 `build/build_derived.py --check-only` 与 `verify.py`。并发由排班管写域；两道在同一类档末尾追加撞车时，两边都留、按 id 重排。

实测（正式库 10-08）：一个分类法 `zongmu`，732 个节点（一级 5：經部、史部、子部、集部、叢書部；二级 57；三级 296；四级 374），101 个类档有成员，成员行 79,056。

---

## 一、`schemes.json`

数组，每项登记一个分类法。

| 字段 | 类型 | 必填 | 含义 | 取值 | 例 |
|---|---|---|---|---|---|
| `id` | string | 必填 | 分类法 id，也是目录名 | ASCII 小写 | `"zongmu"` |
| `name` | string | 必填 | 分类法名称 | | `"中國古籍總目"` |
| `primary` | boolean | 必填 | 是否主分类法 | 全库恰一个为 `true`；主分类法的归属是产物 `_classifications[0]` | `true` |
| `exclusive` | boolean | 必填 | 是否互斥：一部书只能归一类 | | `true` |
| `tree` | string | 必填 | 分类树文件的相对路径 | `<id>/tree.json` | `"zongmu/tree.json"` |

```json
[{"id": "zongmu", "name": "中國古籍總目", "primary": true, "exclusive": true, "tree": "zongmu/tree.json"}]
```

## 二、`<分类法>/tree.json`

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `scheme` | string | 必填 | 分类法 id | 同 `schemes.json` |
| `name` | string | 必填 | 分类法名称 | |
| `nodes` | array<object> | 必填 | 节点；**数组顺序＝显示顺序** | 见下 |
| `nodes[].id` | string | 必填 | 节点 id | 主分类法为 `zm` ＋ 4 位数字（`zm0001`）；**永不变、永不复用** |
| `nodes[].label` | string | 必填 | 类名 | 繁体；改类名只改 `label` |
| `nodes[].parent` | string｜null | 必填 | 上级节点 id | 一级节点为 `null` |
| `nodes[].level` | integer | 必填 | 层级 | 1–4 |
| `nodes[].retired` | boolean | 可选 | 已退役 | 只写 `true`；删类＝标 `retired:true` 并移走成员，不删行 |

```json
{"scheme": "zongmu", "name": "中國古籍總目", "nodes": [
  {"id": "zm0001", "label": "經部", "parent": null, "level": 1},
  {"id": "zm0002", "label": "總類", "parent": "zm0001", "level": 2},
  {"id": "zm0003", "label": "石經之屬", "parent": "zm0002", "level": 3}
]}
```

## 三、`<分类法>/members/<节点 id>.json`

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `node` | string | 必填 | 本档对应的节点 id | 须等于文件名 |
| `members` | array<array> | 必填 | 成员行，一行一条，**按 work_id 排序** | 每行 `[work_id, source]`，见下 |

成员行：

| 位置 | 类型 | 含义 |
|---|---|---|
| `[0]` | string | Work id（草稿库可指正式库 Work） |
| `[1]` | string | 来源目录书或原文类目（如 `"中國古籍總目"`、`"經義考/易"`），供回查 |
| `[2]` | string | 预留：`status`（`adopted`｜`candidate`｜`revoked`），本轮不用、不写 |

不存 `basis`（旧分类字段的 S／A／B／C 依据码已删）。

```json
{"node": "zm0693", "members": [["d59f2mw4pfy9", "中國古籍總目"], ["d59f2mw69mo0", "中國古籍總目"]]}
```

---

## 四、规则

- **任何节点都是合法归属点**：挂在有子类的节点上＝已分到这一层、下面未细分。不再有「未分類」占位节点。
- 互斥分类法下，一部 Work 只出现在一个成员档里，且只出现一次。
- 分类变化**不 bump** Work 的 `revision`（分类是编排，不是对作品的陈述）。
- 草稿 Work 升格时，bim `promote` 把它的成员行改成正式 id、搬进正式库类档。
- 归属规则（小说入子部、诗文评入集部……）由 `tree.json` 的节点体现。
- **不进成员档的东西**：`indexed_by[].section`（目录书原文类目，是引文证据）、`Book.section`（丛编内位置）。

**校验**（`verify.py` 与 build 自校验）：① 节点存在且未退役；② 文件名＝`node`；③ 成员是本仓 Work（草稿库可指正式库）；④ 成员行按 work_id 排序；⑤ 互斥分类法下一部 Work 只出现一次。

**产物**：build 给每部有归属的 Work 加 `_classifications: [{scheme, node, path, l1, l2, l3, l4, source}]`，主分类法在前；卡片的 `cls` 只写节点 id。另生成旧格式 `classific.json` 给尚未改读树的旧读者（过渡件）。见 [derived.md](derived.md)。旧 `Work.classification` 字段已删，见 [legacy.md](legacy.md)。
