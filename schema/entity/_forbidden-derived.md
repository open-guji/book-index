# Entity：禁字段与 build 派生

总览与子类型索引见 [../entity.md](../entity.md)。



## 源档不写
| 字段 | 适用 | 为什么 | 码 |
|---|---|---|---|
| 任何 `_` 起首字段 | 全部 | 派生字段只在产物里；`_has_text`／`_has_collated` 的暂留豁免已全面收回（包 E），任何类型源档都不该有 | V01 |
| `works` | 全部 | 名下作品由 `Work.authors[].entity_id` 反查，build 生成 `_works`（两库现无） | V11 |
| `children`、`reigns`、`index_in_reign`、`successors`、`people`、`holders`、`compounds`、`ancestors`、`span`、`same_name` | 专名四子类型 | 反向列表／派生值 | V01 |
| `subordinates`、`members`、`offices`（及 `_children`、`_subordinates`、`_members`、`_offices`） | 官署 | 反向列表 | I11 |
| `cbdb_*`、`dila_*`、`chgis*` 起首的任何顶层键；`translation`、`c_office_trans`、`cbdb_alt_names` | 专名四子类型、官署 | 授权硬约束，防日后顺手搬进来 | E1（官署报 I08） |
| `external_ids` 中 `wikidata_id` 以外的子键 | 专名四子类型、官署 | 同上 | E1（官署报 I08） |
| `coords` | dynasty、reign、office；place | 只 place 预留，且第一期禁出现 | E1；place 报 P08 |
| `dates` | office、place | 起讫在 `start`／`end` 或沿革项里 | D3 |
| `office_level`、`office_class`、`rank`、`salary`、`base_office_id`、`qualifier`、`institution_ref` | 官署 | 官职专有字段 | I08 |
| `location_id` | 官署 | 第一期禁出现 | I09 |
| `sources`（顶层） | 全部 | 出处一律记 `description.sources`（两库现无） | — |
| `aliases` | 全部 | 旧写法，形状同 `alt_names`，已并入 `alt_names`（两库 10-08 已清零） | — |

## build 派生（只在 `_build/entry/<id>.json`）
| 适用 | 派生字段 | 来源 |
|---|---|---|
| 全部 Entity | `_works` | `Work.authors[].entity_id` 反查；每项 `{work_id, role, title, …}`，`role` 缺则补「撰」 |
| people | `_dynasty_id`／`_dynasty_candidates` | `dynasty` 名在朝代键表里唯一且不歧义命中 → `_dynasty_id`；否则有候选 → `_dynasty_candidates` |
| dynasty | `_children`、`_ancestors`、`_reigns` | `parent_id` 反查；上溯至多 3 级；reign 的 `dynasty_id` 反查 |
| reign | `_dynasty`、`_ruler`、`_index_in_reign`、`_same_name` | `dynasty_id`；`ruler.entity_id`；同朝同帝王年号按起年排序的序号；同名年号 |
| office | `_children`、`_compounds` | 具体条 `parent_id` 反查；`base_office_id` 反查 |
| place | `_children`、`_span` | 沿革项 `parent_id` 反查；各段起讫 |
| 官署 | `_children`、`_subordinates`、`_members`、`_offices` | `parent_id`、`superiors`、`group_ids`、office 的 `institution_ref` 反查 |
| publisher | `_books`、`_subordinates` | `Work／Book／Collection.authors[].entity_id` 反查；下属 publisher 的 `parent_id` 反查 |

已升格的草稿条以正式条为准：不进反查、不进键表，一切 id 引用先经 `promotions/` 换成正式 id。卡片形状与键表（`dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`）见 [derived.md](../derived.md)。
