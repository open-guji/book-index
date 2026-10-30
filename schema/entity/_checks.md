# Entity：校验码总表

总览与子类型索引见 [../entity.md](../entity.md)。各子类型文件末尾另列该类型自己的码。

专名子类型校验（E、D、R、A、O、P、I 系列，及 V01 对新子类型的加严）实现在 `.claude/qa/entity_subtypes.py`，`check_v2.py` 与 `verify.py` 共用同一份。只对专名子类型（含 seal、publisher）与带 `collective_kind` 的 collective 生效；people、无 `collective_kind` 的旧 collective 不受这些码约束。ERROR 计残留；WARN 只报不计；INFO 只出清单。

草稿库查专名时加 `--ref-root <book-index>`：草稿条目的 `dynasty_ids`、`parent_id` 等可以直接指正式库 id（专名升格后的规范写法），引用解析会认正式库的 Entity；跨条目检查（D1 唯一、P09 同名、I10 疑重复等）仍只在本仓内比，两仓同名条不算重复。

```bash
find Entity -name '*.json' | python3 .claude/qa/check_v2.py --paths - --summary
# 草稿库：
find Entity -name '*.json' | python3 <book-index>/.claude/qa/check_v2.py --root . --ref-root <book-index> --paths - --summary
```

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| E1 | 专名四子类型 | 出现 `cbdb_*`、`chgis*`、`dila_*`、`translation`、`c_office_trans`、`cbdb_alt_names`；`external_ids` 含 `wikidata_id` 以外的键，或 `wikidata_id` 不合 `^Q\d+$`；非 place 出现 `coords` | ERROR |
| D1 | dynasty | `primary_name` 非空、在规范朝代名枚举内、全库唯一（读不到规范名表时跳过枚举比对） | ERROR |
| D2 | dynasty | `parent_id` 存在、是 dynasty、无环、上溯深度 ≤3（ERROR）；子朝代 `dates` 落在上级之内，容差 1 年（WARN） | ERROR／WARN |
| D3 | dynasty、reign、office、place | `dates` 键按 subtype 放行（office／place 有 `dates` 即错）；`start`／`end` 为整数、无 0 年、`start ≤ end`；dynasty 的 `period` 是现有 slug（ERROR）；有 `period` 而缺 `start`（WARN） | ERROR／WARN |
| R1 | reign | `dynasty_id` 必填且指 dynasty（缺而 `ai_note` 有说明为 WARN）；`ruler.name` 非空；`ruler.entity_id` 指 people；`dates.start` 必填整数；`(primary_name, dynasty_id, start)` 唯一；同朝同名年号区间不重叠（以上 ERROR）；`dates` 越出所属朝代，容差 5 年（WARN） | ERROR／WARN |
| A1 | 专名四子类型、官署 | `alt_names` 为数组、每项 `name` 非空、`ambiguous` 为 bool；无 `ambiguous` 的 dynasty 别名在 dynasty 内全局唯一（以上 ERROR）；`ambiguous` 之名全库 ≥2 条声称（WARN） | ERROR／WARN |
| O01 | office | `office_level` ∈ `concept`／`concrete` | ERROR |
| O02 | office | 具体条 `dynasty_ids` 非空且指 dynasty、`function`／`basis` 非空；概念条禁字段 | ERROR |
| O03 | office | `office_class` 在 15 值内 | ERROR |
| O04 | office | `parent_id` 指 office 概念条；概念条不得有 `parent_id` | ERROR |
| O05 | office | `base_office_id` 存在、是 office、不自指、无环、与本条 `dynasty_ids` 相交；有 `base_office_id` 则必有 `qualifier`；`qualifier.kind` 在 4 值内、`name` 非空（以上 ERROR）；`base_office_id` 指概念条而 `ai_note` 未说明（WARN） | ERROR／WARN |
| O09 | office | `start`／`end` 为整数且 `start ≤ end` | ERROR |
| O10 | office | `簡稱` 长度 ≤2，须确认不与他概念重名 | WARN |
| O11 | office | 同一概念下同朝具体条重复 | WARN |
| O12 | 专名子类型、官署 | `alt_names[].type` 在 25 值枚举内 | ERROR |
| P01 | place | `primary_name` 非空；`history` 为非空数组；各项为对象、`level` 在 14 值内、`name` 非空 | ERROR |
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
| I12 | office | `institution_ref`：`COL:<名>` 占位（ERROR）；须指官署条（ERROR）；指具体条须与官职朝代相交（ERROR）；指概念条须 `ai_note` 标「待補」（WARN）；官名含部名而指合称（WARN）；id 不在本库（WARN） | ERROR／WARN |
| S01 | seal | `primary_name`、`seal_text` 非空；`seal_kind` 在 5 值内；`description.sources` 非空 | ERROR |
| S02 | seal | `dynasty_ids` 非空且指 dynasty；`start`／`end` 为整数且 `start ≤ end`；`seal_style`／`seal_form` 在枚举内 | ERROR |
| S03 | seal | `owner_ids`／`institution_ids` 为 id 数组且指向存在的 Entity，不得指 seal／dynasty（ERROR）；指墓碑（WARN） | ERROR／WARN |
| S04 | seal | `appears_in` ≤20 条、`ref_type` ∈ Book／Work、`id` 在库内存在、不重复 | ERROR |
| S05 | seal | `images` 每项 `file`＋`credit`＋`license`（闭集）＋`source_url`、≤8、`file` 路径规范；`owner_ids` 只能指 people／collective／office，`institution_ids` 只能指 collective；出现其他子类型专属字段（含 `dates`、`dynasty`、`period`） | ERROR |
| S06 | seal | `images[].file` 在 book-index-asset 中不存在（本地有 `BOOK_INDEX_ASSET_ROOT` 或并列的 `../book-index-asset` 才核；没有该仓就跳过，CI／verify 不硬依赖另一仓） | ERROR |
| K01 | publisher | `publisher_kind` 在 6 值内；`kind_also`／`status` 在枚举内；`primary_name` 非空；`description.sources` 非空 | ERROR |
| K02 | publisher | 古代类 `dynasty_ids` 非空且各指 dynasty；`現代出版社`不得写 `dynasty_ids` | ERROR |
| K03 | publisher | `start`／`end` 为非 0 整数且 `start ≤ end` | ERROR |
| K04 | publisher | `locations[]` 形状；`place_id` 须指 place（ERROR）、指墓碑（WARN） | ERROR／WARN |
| K05 | publisher | `owners[]={id, role}`，`id` 指 people／collective；`parent_id` 指 publisher／collective、不自指、publisher 链无环（ERROR）；指墓碑（WARN） | ERROR／WARN |
| K06 | publisher | 禁字段（见[publisher](publisher.md)） | ERROR |
| K07 | publisher | `external_ids` 只许 `wikidata_id`／`isbn_publisher_code` | ERROR |
| K08 | publisher | 写了 `start`／`end` 而缺 `dates_basis` | WARN |
| K09 | publisher | 同名＋同类别＋同朝代集重复，疑重复建档 | WARN |
| V01 | 全部 | 源档出现 `_` 起首字段；专名四子类型另查无下划线的派生名（见[禁字段](_forbidden-derived.md#源档不写)）；`_has_text`／`_has_collated` 豁免已收回 | ERROR |
| V11 | 全部 | 源档有 `works` | ERROR |
| V15 | 全部 | 缺 `schema_version` 或其值不是整数 `1` | ERROR |
| V16 | 全部 | `description.sources` 不是数组，或元素既非字符串亦非对象 | ERROR |

- 已废的码：O06（CBDB 码防重）已删；O07 并入 V01；O08 并入 E1；P05 并入 V01。
- 口径：上下级区间不合（如战国止年晚于东周、北朝起年早于南北朝）、年号越出所属朝代区间，一律 WARN，不是 ERROR。
- 10-08 实测基线：正式库 ERROR 0，WARN 9（D2 2、D3 2、R1 5）；草稿库（带 `--ref-root`）ERROR 0，WARN 113（A1 16、D2 2、D3 2、O10 88、R1 5），INFO 38（P09）。

`verify.py` 另查以下各项（无码，出计数；「是否计成败」一列说明）：

| 查什么 | 说明 | 是否计成败 |
|---|---|---|
| `dates` 合法性 | 见[dates 按子类型放行](_dates-external-ids.md#dates-按子类型放行)末 | 一律计 |
| `external_ids` 合法性 | `wikidata_id`、`viaf_id` 形状，见[external_ids 子键](_dates-external-ids.md#external_ids-子键) | 一律计 |
| `todo`、`review` 形状 | 见[通用字段](_common.md) | 一律计 |
| entities 索引漂移 | `index/` 里的 `primary_name`、`dynasty`、`birth_year`、`death_year`、`period` 与源档不一致（`birth_year`／`death_year` 比的是源档 `dates.birth`／`dates.death`） | 一律计 |
| `Work.authors[].entity_id` 悬空 | 指向不存在的 Entity | `--strict` 时计 |
| 专名校验码与 V 系列 | 同上表，与 check_v2 共用实现（verify 不带 `--ref-root`） | 专名码的 ERROR 一律计；V 系列 ERROR `--strict` 时计；WARN／INFO 只报数 |
| 朝代与生卒世纪明显不合 | people 的 `dynasty` 与 `birth_year`／`death_year`／`dates.birth`／`dates.death` 在宽容 ±40 年外不合（源档只读 `dates.*`，`birth_year`／`death_year` 指 `index/` 里的同名键）；史学惯例常以主要活动或卒年所属朝代标注 | 只报数，不计 |
