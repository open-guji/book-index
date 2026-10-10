# 共用对象与共用字段

本档收多类记录共用的对象类型与字段。各记录档（[work.md](work.md)、[book.md](book.md)、[collection.md](collection.md)、[entity.md](entity.md)）的字段表引用这里的对象名。
字段表体例见 [README.md §八](README.md#八字段表体例)。实测数字为 2026-10-08 两库全量普查。

目录：
[一、Author](#一authorauthors-的元素) ·
[二、IndexEntry](#二indexentryindexed_by--emendated_by-的元素) ·
[三、Resource](#三resourceresources-的元素与-resource_groups) ·
[四、Description、Source、Location](#四descriptionsourcelocation) ·
[五、计量](#五计量) ·
[六、dating 与 publication_info](#六dating-与-publication_info) ·
[七、并条账](#七并条账) ·
[八、共通管理字段](#八共通管理字段) ·
[revision 口径](#revision-口径) ·
[九、朝代与时代轴](#九朝代与时代轴)

---

## 一、Author（`authors[]` 的元素）

Work、Book、Collection 的 `authors[]` 同形。Work 的 `authors[]` 是责任者（撰者、注者、编者……）；Book 的是版本层的责任者（刻者、批点者、序跋者……）；Collection 的是编者、出版主持者。

`authors[].entity_id` 是 **Entity↔Work（Book、Collection）关系的唯一存储侧**：Entity 页上「他的作品」由 build 按它反查（`Entity._works`），Entity 档里不写作品列表。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `name` | string | 必填 | 原生 | 责任者之名，照著录原文或规范名 | 非空 | 录入 | `"蘇軾"` |
| `role` | string | 必填 | 原生 | 责任方式 | 开放词表，见下「role 取值」 | 录入 | `"撰"` |
| `dynasty` | string | 可选 | 原生 | 责任者所属朝代 | 宜用规范朝代名（[§九](#九朝代与时代轴)）；现存仍有志书原文写法（`宋`、`漢`、`魏`）与空串，见 [legacy.md](legacy.md) | 录入 | `"北宋"` |
| `entity_id` | string | 可选 | 原生 | 对应的 Entity id（people 或 collective） | Entity id；草稿记录可指正式 id | 录入、bim | `"hixhd2h9biza"` |
| `source` | Source｜string | 可选 | 原生 | 本条责任者著录的出处 | Source 对象（多为 `{"name":"中國古籍總目","type":"url","details":"http://data.library.sh.cn/entity/person/…"}`）；字符串旧写法（原 Work 33、Book 19）已于 2026-10-09 改为 `{"name": …}` | 录入 | 见例 |
| `name_basis` | string | 可选 | 原生 | 名字取定的依据 | 自由文本 | 录入 | |
| `dynasty_basis` | string | 可选 | 原生 | 朝代判定的依据 | 自由文本 | 录入 | |
| `role_basis` | string | 可选 | 原生 | 责任方式判定的依据 | 自由文本 | 录入 | |
| `original_name` | string | 可选 | 原生 | 著录原文之名（`name` 已规范化时保留原文） | 自由文本 | 录入 | `"脂砚斋 等 评"` |
| `note` | string | 可选 | 原生 | 关于本责任者的说明 | 自由文本 | 录入 | `"副總纂"` |
| 其余键 | — | — | 旧（暂留） | `cbdb_id`、`cbdb_match`、`cbdb_source`（应在 Entity 的 `external_ids`）；`title_or_office`、`courtesy_name`、`alt_names`、`entity_basis`、`sources`、`birthplace`、`ai_note`、`alias`、`additional_names`、`official`、`name_note` | 见 [legacy.md](legacy.md) | — | |

**role 取值**：开放词表，录志书原文的责任方式，不设闭集（实测正式库 470 种、草稿库 281 种）。规则：

- 必填，非空字符串，**一律汉字**；不得写英文（`"author"` 等，现存 16 条，列入修正方案）。
- 有专门含义的三个值：
  - `撰`：最常见的著作方式。build 遇缺 `role` 时也以 `撰` 补（只用于展示兜底，源档仍须写）。
  - `舊題撰`：传统题署的撰人，实际撰人存疑或另有其人；与实际撰人并列。见 [work.md〈authenticity〉](work.md#authenticity真伪)。
  - `託名`：伪托之名。与 `舊題撰` 语义不同（伪托 vs 传统归属），二者不合并。
- 正式库高频值（前 30，次数）：撰 85,621、輯 4,024、編 2,811、作 2,441、注 1,260、修 966、跋 918、纂修 900、選 404、評 398、校 373、譯 347、整理 336、舊題撰 310、纂 290、等纂修 138、等奉敕撰 135、題詞 121、題識 107、編次 87、評點 85、等撰 70、選評 68、等編 67、題詩 57、訂 55、繪 53、奉敕撰 51、傳 51、等修 48。

**例**（Work）：

```json
"authors": [
  {"name": "劉歆", "role": "舊題撰", "dynasty": "西漢"},
  {"name": "葛洪", "role": "撰", "dynasty": "東晉", "entity_id": "hixhd2…"}
]
```

---

## 二、IndexEntry（`indexed_by[]`／`emendated_by[]` 的元素）

- `indexed_by`：本记录被目录书／志书**著录**（记「某志收有此书」）。写在被著录的一侧（Work、Book、Collection）。
- `emendated_by`：本记录被**考证／校勘类著作**订正（记「某考证书对此书有辨正」），如《漢藝文志考證》《隋書經籍志考證》。只在 Work 上。
- 二者形状相同，语义不同：前者是登记，后者是校议。
- **顺序有意义**：同一源多条时按原书次序排；不可按内容去重。
- Book 的 `indexed_by` 记该具体版本被书目按版本著录的条目（如通俗小说书目著录「乾隆甲戌本脂硯齋重評石頭記」），这种条目挂在 Book 上，不新建 Work。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `source` | string | 必填 | 原生 | 著录本书的目录书／志书／考证书之名 | 书名 | 录入 | `"隋書經籍志"` |
| `source_bid` | string | 条件：该目录书在库中有 Work 时必填 | 原生 | 该目录书的 Work id | Work id，须存在 | 录入 | `"d59f2mp0flz6"` |
| `title_info` | string | 必填 | 原生 | 该目录中的著录标题原文 | 原文照录 | 录入 | `"毛詩義問十卷魏太子文學劉楨撰"` |
| `summary` | string | 必填 | 原生 | 该目录中的著录／解题全文 | 原文照录 | 录入 | |
| `section` | string | 可选 | 原生 | 该目录中的类目 | 原文类目，层级以 `/` 分隔 | 录入 | `"經部/易類"` |
| `section_basis` | string | 可选 | 原生 | `section` 的推得依据 | 自由文本 | 录入 | |
| `author_info` | string | 可选 | 原生 | 该目录中的撰人著录原文 | 原文照录 | 录入 | `"字貴與，樂平人"` |
| `juan_count` | string | 可选 | 原生 | 该目录著录的卷数原文 | 原文照录 | 录入 | `"一卷"` |
| `juan` | string | 可选 | 原生 | 本条在该目录书中的卷次 | 原文照录 | 录入 | |
| `volume` | string | 可选 | 原生 | 本条在该目录书（影印本）中的册次 | 自由文本 | 录入 | |
| `page` | string | 可选 | 原生 | 本条在该目录书中的页码 | 自由文本 | 录入 | |
| `edition` | string | 可选 | 原生 | 该目录书著录的版本 | 原文照录 | 录入 | |
| `catalog_no` | string | 可选 | 原生 | 该目录书的条目编号 | 原文照录 | 录入 | |
| `note` | string | 可选 | 原生 | 整理者关于本条著录的说明 | 自由文本 | 录入 | |
| `in_note_of` | string | 可选 | 原生 | 本书不是该志正文所著，而是寄于另一条之注时，那一条的 Work id | Work id | 录入 | 见下 |
| `attested_status` | string | 可选 | 原生 | 该目录书对此书存佚之判 | `extant`｜`lost`｜`partial`｜`not_seen` | 录入 | `"lost"` |
| `attested_status_raw` | string | 条件：有 `attested_status` 时必填 | 原生 | 原文之字 | 原文照录（实测：佚、未見、存、亡、闕） | 录入 | `"佚"` |
| `attested_status_note` | string | 可选 | 原生 | 何以不上升为本记录的 `loss_status` | 自由文本 | 录入 | |
| `misattached` | boolean | 可选 | 原生 | 本节不是本书的著录（同题异书误并） | 只写 `true` | 录入 | `true` |
| `misattached_note` | string | 条件：`misattached` 为真时必填 | 原生 | 何以判为错挂，逐条可验 | 自由文本 | 录入 | |
| 其余键 | — | — | 旧（暂留） | `merged_from`、`text`、`self_note`、`commentaries`、`comment`、`category`、`additional_comment`、`link_basis`、`ai_note` | 保留不删（多为志书原文证据），见 [legacy.md](legacy.md) | — | |

**`attested_status`**：《經義考》逐书判其存佚（「次列題注曰存曰闕曰佚曰未見」），是本库少见的成批存佚依据。**但不得据此直接改本记录的 `loss_status`**——四库御製題自云「所注闕佚未見者，今四庫所録往往其書尚存」，即朱彝尊判为佚、为未见者，修四库时往往尚存。其判是十七世纪一人的见闻，所以只记为「某书如此判」并系于该源之下。`not_seen`（未见）尤其不可转为 `lost`：那是「著者没见过此书」，与「此书已亡」不同轴。

**`in_note_of`**：《隋書經籍志》正文著录见存之书，而以注记「梁有某書幾卷，某人撰，亡」——梁时尚存、隋时已亡者。这类亡书在志中没有独立条目，只寄于某条之注。所以它的 `summary` 是**那一条的原文全行**（含正文之书），而不是本书自己的一行；`in_note_of` 指出寄于哪条，覆按时才知道该在哪一行的哪一段找。

**`misattached`**：catalog_bound 覆验时查出一批 Work 的 `period` 晚于其著录志的上限，而该志的著录语与本条撰人全不相干——同题异书被并为一条。如司马光《書儀》（song）上挂着隋志「《書儀》二卷蔡超撰」；清禪一《法喜集》（qing）上挂着崇文总目「法喜集二卷」。处理是**标而不删，也不为之新建 Work**：节所指何书多数只有书名与卷数，无从配对；新建两百余条极薄的 Work 不可逆。标记则信息全存，日后考定即可升格。计算 `period_upper` 时跳过标记者。实测标 222 节（涉 177 条 Work）。

---

## 三、Resource（`resources[]` 的元素）与 `resource_groups`

Work、Book、Collection 都可有 `resources[]`：这部书在外部站点上的影像、文本、实物、书目入口。站点目录见仓根 `resource-site.json` 等（不是记录）。

### Resource 字段

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | 必填 | 原生 | 资源标识；常用站点名作 id（同一记录内不必唯一） | 自由文本，ASCII 小写与连字符为宜 | 录入 | `"wikisource"` |
| `name` | string | 必填 | 原生 | 站点或资源名，供显示 | 自由文本 | 录入 | `"維基文庫"` |
| `short_name` | string | 可选 | 原生 | 短名，供窄处显示 | 自由文本 | 录入 | `"國圖"` |
| `url` | string | 条件：可在线访问者必填 | 原生 | 入口地址 | URL | 录入 | |
| `types` | array<string> | 必填 | 原生 | 资源内容类型，可多值 | `image`（影像）｜`text`（文本）｜`physical`（实物馆藏记录）｜`catalog`（书目入口）｜`annotated`（带注释的整理本） | 录入 | `["image"]` |
| `details` | string | 可选 | 原生 | 说明（卷册范围、来源、可达性） | 自由文本 | 录入 | `"頁名取自舊叢編對照表，未驗證"` |
| `group` | string | 可选 | 原生 | 资源组键：同一 `group` 值＝同一份内容的不同存储位置（镜像） | 记录内自定的键，指向 `resource_groups` 的键 | 录入 | `"renmin-1975-bw"` |
| `group_role` | string | 条件：有 `group` 时必填 | 原生 | 本条在组内的角色 | `origin`（原始来源）｜`mirror`（我们做的备份镜像）｜`derivative`（据原始来源加工的衍生件）｜`source`（旧写法，等同 `origin`，1 条） | 录入 | `"origin"` |
| `metadata` | object | 可选 | 原生 | 来源站点的原始字段透传，不规范化 | 键随站点而异，见下 | 录入 | `{"nlc_fid":"…"}` |
| `volumes` | array<object>｜object | 可选 | 原生 | 分册入口 | 数组项 `{volume, url?, imagecount?, file?, wiki_url?, tw_url?, status?, group?, group_id?, description?, label?, pages?}`；对象形是「按规律生成分册地址」的描述（`url_template`、`start`、`end`、`step` 等） | 录入 | |
| `expected_volumes` | integer | 可选 | 原生 | 应有册数（`volumes` 不全时用于标进度） | 正整数 | 录入 | `26` |
| `root_type` | string | 可选 | 原生 | 资源根类型（标记「书目入口」型资源） | `catalog` | 录入 | `"catalog"` |
| `color_mode` | string | 可选 | 原生 | 影像色彩 | `color`｜`bw` | 录入 | `"color"` |
| `note`、`source_label` | string | 可选 | 原生 | 说明、来源标签（各 1 条） | 自由文本 | 录入 | |
| `type` | string | — | 旧（暂留） | 单值的内容类型（`types` 的前身） | `image`｜`text`｜`physical` | — | 读者按 `types ?? [type]` 读，见 [legacy.md](legacy.md) |
| ~~`group_label`~~ | — | **不写** | — | 组标签：已改写在 `resource_groups[<组>].label`（现存 0，读者已不读） | — | — | |

**`metadata` 常见键**（透传，不校验内容）：国图 `nlc_fid`／`nlc_bid`／`nlc_book_id`／`nlc_volume_id`／`nlc_aid`；故宫 `acckey`／`item_id`／`call_number`；国书数据库 `kokusho_bid`／`iiif_manifest`／`holder`；识典等文本站 `check_type`（`粗校`｜`AI整理`｜`精校`）／`paragraph_count`／`total_page`／`version`／`has_translation`；其余 `edition`、`publisher`、`year`、`format`（`PDF`｜`DjVu`）、`volume`、`note`、`digital_pages`、`access_code`（网盘提取码）、`commons_category`、`holding`、`shanben_no`、`completeness`、`page_range` 等。新站点要加键不必改格式文档，但同一站点同一含义的键要沿用已有名。

### `resource_groups`（记录顶层）

多个 resource 描述同一份内容的不同存储位置时，用 `group` 把它们关联起来，并在记录顶层的 `resource_groups` 里给每组一个小标题和说明。Work、Book 都可有此字段。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `resource_groups` | object | 可选 | 原生 | 组键 → 组说明 | 键即 `resources[].group` 的值 | 录入 | 见下 |
| `resource_groups.<组键>.label` | string | 必填 | 原生 | 组的小标题 | 自由文本 | 录入 | `"人民文学出版社 1975 年影印本"` |
| `resource_groups.<组键>.description` | string | 可选 | 原生 | 这一组为何独立成组、与其他组的区别 | 自由文本 | 录入 | |

- 同一 `group` 值＝同一份内容的不同存储位置：下载下来内容字节等价（或仅水印、格式细微差别）。
- 不同 `group` 值＝不同变体（如人文社 1975 黑白本 vs 中華再造善本彩色本；完整本 vs 缺页本）。
- 无 `group`＝独立资源（如识典、CText 这类独立整理本文本）。
- 显示：按 `group` 分桶，无 group 的每条单独成桶；桶头用 `resource_groups[gk].label`＋`description`；桶内列站点名、URL、提取码，`origin` 加角标。

```json
{
  "resource_groups": {
    "renmin-1975-bw": {"label": "人民文学出版社 1975 年影印本", "description": "人文社 1975 年首次影印庚辰本，黑白底本……"}
  },
  "resources": [
    {"id": "shidianguji", "name": "识典古籍", "url": "…", "types": ["text"]},
    {"id": "jiangyu-renmin1975", "group": "renmin-1975-bw", "group_role": "origin", "name": "天一生水", "url": "…", "types": ["image"]},
    {"id": "ia-renmin1975", "group": "renmin-1975-bw", "group_role": "mirror", "name": "Internet Archive", "url": "…", "types": ["image"]},
    {"id": "baidu-renmin1975", "group": "renmin-1975-bw", "group_role": "mirror", "name": "百度网盘", "url": "…", "types": ["image"], "metadata": {"access_code": "abcd"}}
  ]
}
```

`resources` 推出的派生量（`_has_image`、`_has_text`）由 build 计算，见 [derived.md](derived.md)。

---

## 四、Description、Source、Location

### Description（`description`）

面向读者的介绍。Work、Book、Collection、Entity 都可有。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `text` | string | 必填 | 原生 | 介绍正文 | 自由文本，面向读者 | 录入 | |
| `sources` | array<string｜object> | 必填（可为空数组） | 原生 | 正文的出处 | 元素为字符串（出处简述，多为书名）或对象，见下 | 录入 | `["千頃堂書目"]` |

`sources[]` 的元素两种形状都合法（overview#473），新写入按需选用，存量不迁移：

- **字符串**：出处简述，通常就是书名。存量主流。
- **对象**：两种写法并存——
  - Source 对象 `{name, type, details, …}`（见下），Entity 多用此形；
  - 引文对象 `{title, url?, details?, source_bid?}`：`title` 为出处全称（如「孫楷第《中國通俗小說書目》卷四·明清小說部乙·烟粉」），`source_bid` 指库中该书的 Work。

读者：字符串当作名称显示；对象取 `title ?? name` 显示、有 `url`／`details` 时作链接。

正式库实测（元素数）：Work 字符串 93,290、对象 665；Book 530／34；Collection 35／23；Entity 8／5,771（含 `description.sources` 的 Source 对象）。

### Source（`sources[]` 与他处的出处对象）

记录顶层的 `sources[]`（数据来源，多见于 Book：正式库 33,891 条，草稿库 68,118 条）、`authors[].source` 等用此形。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | 可选 | 原生 | 来源中的条目标识 | 自由文本 | 录入 | |
| `name` | string | 必填 | 原生 | 来源名称 | 自由文本 | 录入 | `"中國古籍總目（上圖聯合目錄）"` |
| `type` | string | 可选 | 原生 | 来源形态 | 实测只有 `url`；另可为 `bookID` | 录入 | `"url"` |
| `details` | string | 可选 | 原生 | 地址或细节 | 自由文本／URL | 录入 | `"https://gj.library.sh.cn/unionCatalogue/…"` |
| `position` | string | 可选 | 原生 | 在来源中的位置 | 自由文本 | 录入 | |
| `version` | string | 可选 | 原生 | **处理程序**的版本号（与书的版本无关） | 自由文本 | 录入 | `"1.0"` |
| `processor_version` | string | 可选 | 原生 | 处理程序版本 | 自由文本 | 录入 | `"script-v1"` |

`sources[].version` 是处理程序版本号，`Book.edition` 才是版本名，二者勿混。

### Location（`current_location`、`location_history[]`）

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `name` | string | 必填 | 原生 | 所在地（机构、地点） | 自由文本 | 录入 | `"西安碑林"` |
| `description` | string | 可选 | 原生 | 说明 | 自由文本 | 录入 | |
| `start_date`、`end_date` | string | 可选 | 原生 | 起止时间 | `YYYY`、`YYYY-MM-DD` 或空串 | 录入 | `"1911"` |
| `source` | string｜Source | 可选 | 原生 | 出处 | 实测多为来源代号字符串（`src_manual` 等） | 录入 | `"src_manual"` |

`Book.location_history[]` 的元素另有 `location`、`item_id`、`url`、`note`、`acckey` 键，见 [book.md](book.md)。

---

## 五、计量

| 字段 | 类型 | 在哪 | 含义 | 取值 |
|---|---|---|---|---|
| `juan_count` | object | Work、Book、Collection | 主计量：一个数＋单位 | `{number, unit?, description?, source?}`，见下 |
| `measures` | array<object> | Work、Book、Collection | 多维计量，按原书顺序 | `[{number, unit, note?}]` |
| `measure_info` | string | Work、Book、Collection | 人可读的计量拼接，供界面直接显示 | 自由文本，如 `"四卷二十回"`、`"八集四十回（每集五回）"` |
| `page_count` | object | Work、Book、Collection | 页数 | `{number, description?, source?}` |
| `volume_count` | object | Book | 册数 | `{number, description?}` |
| `additional_works` | array<object> | Work | 主体之外各自计卷的部分 | `[{book_title, n_juan?}]`，`n_juan` 字面即「卷」 |

**`juan_count`**：

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `number` | integer | 必填 | 这个数 | 非负整数；`0` 只用于「不分卷」（这部书没有卷这个维度） |
| `unit` | string | 可选 | 这个数的单位 | 18 个量词的闭集：`卷`｜`冊`｜`篇`｜`回`｜`集`｜`編`｜`種`｜`則`｜`部`｜`章`｜`函`｜`首`｜`筆`｜`期`｜`節`｜`帙`｜`弄`｜`件`；「不分卷」不填 |
| `description` | string | 可选 | 计量的原文或说明 | 自由文本 |
| `source` | string | 可选 | 出处代号 | 自由文本 |

- `number` 与 `unit` 同层：**读 `number` 时必须同时读 `unit`，不可预设「卷」**（《羋子》「十八篇」曾被显示成「十八卷」）。`unit` 缺时宁可不显示单位字样。
- 现状：Book 有 `unit`（正式库 21,530 条，其中 `册` 4 条为异体旧写）；Work 尚未回填（0 条）。
- 汉志一类著录的「篇」也放在 `juan_count.number`，靠 `unit` 区分。

**`measures`**：同一部书同时有不止一个计量维度时用（如通俗小说「六卷十六回」，卷是文本分卷、回是章节结构）。`juan_count` 是其中作为主计量的那一个，不另立一套。`measures[].unit` 实测还有 `頁`、`段`、`幅`、`條`、`折`、`石`、`字`、`葉`、`卷首` 等少量值，不在上面的闭集内。已知 `measures[0].unit` 不能盲信：正式库曾查出 995 条与 `measure_info` 原文不一致（多在「國立故宮博物院善本舊籍」批次，整批错填成「冊」），回填 `juan_count.unit` 一律以 `measure_info` 原文重新抽取为准。

`additional_works[].n_juan` 是「主体＋附录各自计卷」的机制，与 `juan_count.unit` 不是一件事。

---

## 六、`dating` 与 `publication_info`

### `dating`（Book、Collection）

本版本（本丛编）的刊刻／抄写年代，结构化记录。索引里的 `era`、`sort_year` 只是它的投影。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `era` | string | 可选 | 原生 | 朝代（刊刻之朝，非撰人之朝） | 朝代名；实测：清、明、日本、宋、元、民國、朝鮮、金、唐、漢、隋、五代、三國 | 录入 | `"清"` |
| `reign` | string | 可选 | 原生 | 年号 | 年号原文；未知可为空串 | 录入 | `"乾隆"` |
| `year` | integer | 可选 | 原生 | 公历年 | 整数，公元前为负 | 录入 | `1193` |
| `year_range` | array<integer> | 可选 | 原生 | 年代区间 | `[起, 止]`，起 ≤ 止；与 `year` 不并存 | 录入 | `[1736, 1795]` |
| `certainty` | string | 必填（有 `dating` 时） | 原生 | 确定程度 | `attested`（原书或著录明载）｜`inferred`（据版本名等推定）｜`uncertain`（存疑） | 录入 | `"inferred"` |
| `source` | string | 必填（有 `dating` 时） | 原生 | 依据来自哪里 | `edition`（据版本名）｜`catalog`（据书目著录） | 录入 | `"edition"` |
| `basis` | string | 必填（有 `dating` 时） | 原生 | 判定依据，逐条可读 | 自由文本 | 录入 | |
| `based_on` | object | 可选 | 原生 | 所据底本的年代（翻刻、影印、传钞、配补之本） | `{era, reign, year?, relation}`；`relation` ∈ `翻刻`｜`影印`｜`傳鈔`｜`配補` | 录入 | `{"era":"宋","reign":"淳熙","relation":"翻刻"}` |
| `later_repair` | object | 可选 | 原生 | 后修补版的朝代 | `{era}` | 录入 | `{"era":"明"}` |

底本关系的结构化记录已改在 `Book.base_edition`（见 [book.md](book.md)），`dating.based_on` 照留。

### `publication_info`（Work、Book、Collection）

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `year` | string | 可选 | 出版／刊刻时间的原文 | 自由文本（朝代名、年号纪年、公历年、区间都有） |
| `year_iso` | string | 可选 | 公历年 | 数字字符串 |
| `details` | string | 可选 | 说明 | 自由文本 |
| `publisher` | string | 可选 | 出版者 | 自由文本 |
| `place` | string | 可选 | 出版地 | 自由文本 |
| `source` | string | 可选 | 出处代号 | 自由文本 |

`publication_info.year` 是自由文本，界面不据它排序；排序用 `dating`。

---

## 七、并条账

两条记录被认定为同一部（重出）时并成一条：保留者（keeper）记事件，被并者留墓碑。

| 字段 | 类型 | 在哪 | 性质 | 含义 | 取值 |
|---|---|---|---|---|---|
| `merged_in` | array<object> | keeper（Work、Entity） | 原生 | 并条事件日志（事件，不是关系，不可派生） | 每项 `{id, title, at, by, rule, why}`；可另带 `author`、`title_info`、`indexed_by_moved[]`、`books_moved[]`、`measure_info`、`note`、`reason`。早期有 34 项只写了被并者 id 字符串 |
| `merged_into` | string | 墓碑 | 原生 | 并入了哪一条 | 记录 id。**只在墓碑上** |
| `merged_from` | array<string> | keeper（Work、Book） | 原生 | 并入本条的记录 id | id 数组（原 1 条字符串旧写已于 2026-10-09 改为数组） |
| `merge_history` | array<object> | keeper（Work、Entity） | 原生 | 早期的并条账 | Work：`{date, merged_from, title, reason}`；Entity 见 [entity.md](entity.md) |

`merged_in[]` 主要键：`id` 被并者 id；`title` 被并时的题名；`at` 时间（ISO 8601）；`by` 执行者代号（道名、`S`、`coordinator` 等）；`rule` 规则名；`why` 逐条理由。

---

## 八、共通管理字段

Work、Book、Collection、Entity 都有。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | 必填 | 原生 | 记录 id | 见 [README §四](README.md#四id) | bim | `"d59f2mp0flz6"` |
| `type` | string | 必填 | 原生 | 记录类型 | `work`｜`book`｜`collection`｜`entity`（小写） | bim | `"work"` |
| `schema_version` | integer | 必填 | 原生 | 记录格式大版本 | 恒为 `1` | bim | `1` |
| `revision` | string | 正式库必填 | 原生 | 记录内容的版本 | `"主.次.补"`，三段非负整数；新记录 `"1.0.0"`；口径见下 | bim | `"1.1.0"` |
| `revised_at` | string | 有 `revision` 时必填 | 原生 | 最后一次改版的日期 | `YYYY-MM-DD` | bim | `"2026-10-08"` |
| `updated_at` | string | 可选 | 原生 | 最后一次被人碰的时间 | ISO 8601（实测有带时区、带 `Z`、只写日期三种） | bim | `"2026-08-24T00:00:00+00:00"` |
| `ai_note` | string | 可选 | 原生 | 整理者写给整理者的注，不面向读者 | 自由文本，见下 | 录入 | |
| `todo` | array<object> | 可选 | 原生 | 条目级待核清单 | `[{what, by?, date?}]`，`what` 非空；做完即移除该项，不留「已办」标记 | 录入 | |
| `review` | object | 可选 | 原生 | 人工审核状态 | `{status, by?, date?}`；`status` ∈ `unreviewed`｜`reviewed`｜`disputed`；缺即 `unreviewed` | 录入 | `{"status":"unreviewed"}` |
| `zhsy_retrieved_at`、`authors[].cbdb_retrieved_at` | string | 可选 | 原生 | 外部对齐的取得时间 | ISO 8601；新增对齐时必填（现存 0 条） | 录入 | |
| `_` 起首一切 | — | 源档不写 | 派生 | 见 [derived.md](derived.md) | 无例外（`_has_text`、`_has_collated` 豁免已收回，见 [CHANGELOG.md](CHANGELOG.md)） | build | |

**`updated_at`**：现值自 git 该档最后一次提交回填，**不一律填「现在」**，假时间比没有更坏。

**`ai_note`**：
- 记资料来源与可信度，例：「據網路檢索資料建檔，未核原書」。
- 记存疑与待办，例：「卷數與通行所記三十一卷不合，待核」。
- 记整理决策，例：「原有非 schema 之頂層欄位 part_of，今改記為 related_works 之 part_of 關係」。

面向读者的正文一律写进 `description.text`，出处写进 `description.sources`。前端不渲染 `ai_note`。

### revision 口径

**`revision` 管的是「这部作品『是什么』的陈述」有没有变。** 人或脚本对作品下的判断与事实变了算；派生的副产品（反向链、聚合、计数、分类归属）与管理字段不算。

| | 字段 |
|---|---|
| **算**（变了要 bump，并刷新 `revised_at`） | 题名族 `title`、`additional_titles`、`original_title`、`title_basis`、`title_emendation`；`authors`；年代 `dynasty*`、`period*`、`period_upper*`；描述 `description`、`ai_note`、`juan_count`、`measure_info`、`measures`、`subtype`、`publication_info`、`appendix`、`collection_scale`、`current_location`、`page_count`；存佚真伪 `loss_status*`、`authenticity*`；资源与谱系 `resources`、`resource_groups`、`version_graph`、`additional_works`、`sources`；著录 `indexed_by`、`emendated_by`；存储侧关系 `related_works`、`contained_in`；并条账 `merged_in`、`merged_from`、`merged_into`、`merge_history`。Book 另有 `work_id`、`contained_in`、`section`、`lineage`、`base_edition`、馆藏、影像、册数 |
| **不算**（变了不 bump，也不刷新 `revised_at`） | 分类归属（`classification/` 类档）；一切 `_` 字段与旧 `has_*`；旧 `books`、`contained_works`、`promoted_to`、`promoted_at`；管理字段 `updated_at`、`revision`、`revised_at`、`schema_version`、`id`、`type`、`path` |

- **未登记的新字段按「算」处理**。要加「不算」的字段，须登记进 bim `book_index_manager/revision_fields.py` 的 `NO_BUMP_FIELDS`，并在卡里说明。bim `save_item` 存档时调用它判断要不要 bump。
- 级别（bim `save_item(..., bump=…)`，缺省 `patch`）：

  | 级别 | 何时 | 例 |
  |---|---|---|
  | `patch`（1.0.x） | 不改变知识内容的修复 | 错字、字段顺序整理、URL 格式调整、繁简异体统一 |
  | `minor`（1.x.0） | 新增、补全、修正知识内容 | 加 resource、加 `indexed_by`、补 lineage 来源、加 description 段落、修正作者朝代、调整 `related_works` |
  | `major`（X.0.0） | 评级升级或重大重构 | 初次升格＝`1.0.0`；整理本由粗校升精校；版本谱系图重大调整；同 Work 下并／拆 Book |

  拿不准 patch 还是 minor 选 minor；拿不准 minor 还是 major 先问目录经理。同一天多次 patch，`revision` 照加、`revised_at` 不变。跨记录的 id 改写（bim `rewrite_references`，升格、并条时）是机械动作，不 bump。
- 推论：单向存储后，改一条关系只 bump 存储侧那一条记录；Collection 成员增减不 bump 丛编；丛编自己的题名、`contains[]`、说明变化算。
- 迁移脚本一律不改 `revision`／`revised_at`（迁移不是作品变化）。
- 草稿库记录可不写 `revision`（实测 Work、Book 全缺）；升格时 bim 补 `"1.0.0"`。正式库缺 `revision` 即错。

---

## 九、朝代与时代轴

记录里有三个时间字段，各管一件事：

| 字段 | 在哪 | 是什么 | 取值 |
|---|---|---|---|
| `dynasty` | Work 顶层、`authors[].dynasty`、Entity | **直接显示给读者**的朝代名 | 规范朝代名（下表首列） |
| `period` | Work、Entity | 本库判定的**时代轴**：粗粒度、无歧义，供选集合 | 12 值枚举，见下 |
| `period_upper` | Work | 时代上限：本书不得晚于此 | 同 `period` 词表 |

判法（怎么定 `dynasty`、`period`、`period_upper`，以及 `dynasty_basis`／`period_basis` 该写什么）见 [cataloging-rules.md〈时代与朝代的判法〉](cataloging-rules.md)。

### `period`（12 值）

```
pre-qin  qin-han  three-kingdoms  jin  nanbeichao  sui-tang
five-dynasties  song  liao-jin-yuan  ming  qing  modern
```

| 值 | 范围 |
|---|---|
| `pre-qin` | 先秦（上古至战国） |
| `qin-han` | 秦、西汉、新、东汉（秦十五年并入） |
| `three-kingdoms` | 三国魏、蜀、吴 |
| `jin` | 西晋、东晋、十六国 |
| `nanbeichao` | 南朝宋齐梁陈、北朝北魏东魏西魏北齐北周 |
| `sui-tang` | 隋、唐（隋三十七年并入）、武周 |
| `five-dynasties` | 五代十国 |
| `song` | 北宋、南宋 |
| `liao-jin-yuan` | 辽、西夏、金、蒙古、元 |
| `ming` | 明 |
| `qing` | 清（含后金） |
| `modern` | 中华民国、中华人民共和国 |

- 分段以全国性王朝为骨干，非全国政权按时段归并；明、清不并（二代存世著述最多，合占全库六成）。
- **`period` 只可分组，不可排序**：段与段在时间上有重叠（`song` 与 `liao-jin-yuan` 全重叠 319 年），需时序者另用数值年。
- 与 `dynasty` 分立：`dynasty` 是显示用的朝代名；`period` 是本库之判。`period` 不是 `dynasty` 的函数（舊題撰人、跨代人物、伪托作品三类正当地不同）。
- 一律标**成书时代**（实际撰人之时），不标舊題撰人之时。
- 判不出留空（不写 `null` 占位为宜；现存 8 条 `null`）。

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `period` | string | 可选 | 时代轴 | 上表 12 值 |
| `period_basis` | string | 条件：有 `period` 时必填 | 判定依据，逐条可读；与 `dynasty` 相异者必记其由；以「撰人已定代 X」为据者，须写明该撰人之代从哪里来（CBDB／史传／著录／推定） | 自由文本（常见起首：`據 authors[0].dynasty「…」`、`catalog_bound`、`duandai`） |
| `period_upper` | string | 可选 | 时代上限：只给上限，不给下限；只标在 `period` 为空或存疑者 | 12 值之一 |
| `period_upper_basis` | string | 条件：有 `period_upper` 时必填 | 据何而定（含该志的上限），逐条可验 | 自由文本（常见起首：`catalog_bound：…`、`edition_bound`、`excavation_bound`、`collection_bound`） |

不设 `period_lower`。

### `dynasty` 与 `dynasty_basis`

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `dynasty` | string | 可选 | 朝代名 | **规范朝代名**（下表首列，或〈域外朝代〉表首列）。现存仍有歧义与非规范写法（`宋`、`魏`、`漢`、`國朝`、`當代`、空串等），列入修正方案，见 [legacy.md](legacy.md) |
| `dynasty_basis` | string | 条件：有 `dynasty` 时宜写 | 判定依据 | 自由文本；宜以下列代码之一起首：`synonym`（同义归并）｜`entity_death_year`／`entity_birth_year`（据作者生卒年）｜`catalog_bound`（著录志为上限）｜`duandai`（断代志可径定）｜`author_propagation`（同作者他书已判值传播）｜`manual`（人工覆核）；代码后可接 `:` 与说明 |

**规范化原则**：

1. **自明性优先**：规范名一眼能读出所属时段——三国系列冠「三國」（三國魏、三國蜀、三國吳），南朝系列冠「南朝」（南朝宋、南朝齊、南朝梁、南朝陳），宋分北宋、南宋。
2. **无歧义优先**：凡一字多朝者必加前缀（魏→三國魏／北魏，宋→南朝宋／北宋／南宋，蜀→三國蜀／前蜀／後蜀）。
3. **参照 CBDB**：规范名以 CBDB DYNASTIES 表为主要参照，另参考文物藏品时代分类代码补北宋／南宋、参考中研院史语所朝代代码表补十六国。CBDB 只作人工校对参照，不存 `c_dy` 码（overview#464）。
4. **志书原文不受影响**：原文保留在 `indexed_by[].title_info`。
5. 判不出留空，另出清单，不猜。

**规范名就是 `Entity.subtype=="dynasty"` 条目的 `primary_name`**，二者逐字一致（`check_v2.py` D1 查）。条目化之后此表改由 build 从 dynasty 条目生成，不得再手写第二份。下表的 `period` 列只是该朝代的默认值，**不反写** `Work.period`；`null`＝无对应 period（不在 12 值之内，如元末群雄）。北宋、南宋之上设「趙宋」（两宋通称，作上级条）；兩漢、十六國、十國为上级通称条。

#### 规范朝代名全表

| 规范名 | period | 别名（库中已有写法；＊＝ambiguous，单独不能定位） | 说明 |
|---|---|---|---|
| 上古傳說 | pre-qin | 上古傳說 | 三皇五帝 |
| 上古 | pre-qin |  | 上古泛稱 |
| 夏 | pre-qin |  |  |
| 商 | pre-qin |  |  |
| 西周 | pre-qin |  |  |
| 東周 | pre-qin |  |  |
| 春秋 | pre-qin |  |  |
| 戰國 | pre-qin |  |  |
| 先秦 | pre-qin | 漢前、漢以前 | 漢以前泛稱 |
| 春秋齊 | pre-qin |  | 諸侯國 |
| 春秋晉 | pre-qin |  |  |
| 春秋吳 | pre-qin |  |  |
| 春秋魯 | pre-qin |  |  |
| 戰國齊 | pre-qin |  |  |
| 戰國楚 | pre-qin |  |  |
| 戰國趙 | pre-qin |  |  |
| 秦 | qin-han | 贏秦 | 贏秦=嬴秦之訛 |
| 西漢 | qin-han |  |  |
| 新 | qin-han |  | 新莽（王莽） |
| 東漢 | qin-han | 東漢末、後漢(東漢別稱) |  |
| 兩漢 | qin-han | 前後漢 | 西漢與東漢的合稱 |
| 玄漢 | qin-han | 漢＊ | 劉玄所建，年號更始，後為赤眉所滅 |
| 赤眉 | qin-han |  | 新末赤眉軍所立政權，年號建世 |
| 三國魏 | three-kingdoms | 曹魏 |  |
| 三國蜀 | three-kingdoms | 蜀漢 |  |
| 三國吳 | three-kingdoms | 孫吳 |  |
| 三國 | three-kingdoms |  | 通稱，不拆 |
| 西晉 | jin |  |  |
| 東晉 | jin |  |  |
| 晉 | jin |  | 兩晉通稱 |
| 前涼 | jin |  | 十六國之一 |
| 前秦 | jin |  | 十六國之一 |
| 後秦 | jin | 姚秦 | 姚秦=後秦（姚萇） |
| 西燕 | jin |  | 十六國之一 |
| 北涼 | jin |  | 十六國之一，末期入南北朝 |
| 十六國 | jin |  | 五胡所建諸政權的通稱 |
| 成漢 | jin | 大成 | 氐人李氏據蜀，初號成，後改漢；屬十六國 |
| 前趙 | jin | 趙＊、漢趙 | 匈奴劉氏所建，初號漢；屬十六國 |
| 代 | jin | 拓跋代 | 鮮卑拓跋氏之代國；屬十六國 |
| 後趙 | jin | 趙＊、石趙 | 羯人石氏所建；屬十六國 |
| 前燕 | jin | 燕＊ | 鮮卑慕容氏所建；屬十六國 |
| 冉魏 | jin | 魏＊ | 冉閔所建，國號魏；屬十六國 |
| 後燕 | jin | 燕＊ | 慕容垂所建；屬十六國 |
| 西秦 | jin | 秦＊、乞伏秦 | 鮮卑乞伏氏所建；屬十六國 |
| 後涼 | jin | 涼＊ | 氐人呂氏所建；屬十六國 |
| 南涼 | jin | 涼＊ | 鮮卑禿髮氏所建；屬十六國 |
| 南燕 | jin | 燕＊ | 慕容德所建，都廣固；屬十六國 |
| 西涼 | jin | 涼＊ | 李暠所建，都敦煌酒泉；屬十六國 |
| 桓楚 | jin | 楚＊ | 桓玄篡晉所建，國號楚 |
| 胡夏 | jin | 夏＊、赫連夏、大夏＊ | 匈奴赫連氏所建，國號夏；屬十六國 |
| 北燕 | jin | 燕＊ | 高雲、馮跋所建；屬十六國 |
| 南朝宋 | nanbeichao | 劉宋、宋(劉) |  |
| 南朝齊 | nanbeichao | 南齊 |  |
| 南朝梁 | nanbeichao | 南梁 |  |
| 南朝陳 | nanbeichao | 陳 |  |
| 南朝 | nanbeichao |  | 通稱 |
| 北魏 | nanbeichao | 後魏 | 亦稱元魏 |
| 北齊 | nanbeichao |  |  |
| 北周 | nanbeichao |  |  |
| 北朝 | nanbeichao |  | 通稱 |
| 南北朝 | nanbeichao |  | 通稱，不拆 |
| 東魏 | nanbeichao | 魏＊ | 高歡所控北魏孝靜帝政權，都鄴；屬北朝 |
| 西魏 | nanbeichao | 魏＊ | 宇文泰所控北魏文帝政權，都長安；屬北朝 |
| 侯漢 | nanbeichao | 漢＊ | 侯景篡梁所建，國號漢 |
| 西梁 | nanbeichao | 梁＊、後梁＊ | 蕭詧所建的附庸政權，與南朝梁並稱 |
| 隋 | sui-tang |  |  |
| 唐 | sui-tang |  |  |
| 鄭（王世充） | sui-tang | 鄭 | 隋末王世充所建 |
| 武周 | sui-tang | 周＊、大周＊ | 武則天改唐為周的政權，夾於唐中 |
| 夏（竇建德） | sui-tang | 夏＊、竇夏 | 隋末河北義軍首領竇建德所建 |
| 魏（李密） | sui-tang | 魏＊ | 隋末李密據洛口所建，瓦崗軍所奉 |
| 涼（李軌） | sui-tang | 涼＊ | 隋末李軌據河西所建 |
| 梁（梁師都） | sui-tang | 梁＊ | 隋末梁師都據朔方所建，倚突厥 |
| 楚（林士弘） | sui-tang | 楚＊ | 隋末林士弘據江西所建 |
| 秦（薛舉） | sui-tang | 秦＊ | 隋末薛舉據隴西所建 |
| 定楊（劉武周） | sui-tang | 定楊、劉武周 | 隋末劉武周據馬邑所建政權，無正式國號 |
| 梁（蕭銑） | sui-tang | 梁＊ | 隋末蕭銑據江陵一帶所建 |
| 燕（高開道） | sui-tang | 燕＊ | 隋末高開道據北平一帶所建 |
| 梁（沈法興） | sui-tang | 梁＊ | 隋末沈法興據江南所建 |
| 楚（朱粲） | sui-tang | 楚＊ | 隋末朱粲據荊襄所建 |
| 許（宇文化及） | sui-tang | 許 | 隋末宇文化及弒煬帝後所建 |
| 吳（李子通） | sui-tang | 吳＊ | 隋末李子通據江淮所建 |
| 漢（劉黑闥） | sui-tang | 漢＊、漢東 | 唐初劉黑闥承竇建德餘部所建 |
| 宋（輔公祏） | sui-tang | 宋＊ | 唐初輔公祏於江南所建 |
| 大燕（安祿山） | sui-tang | 大燕＊、燕＊ | 安史之亂中安祿山所建，歷四帝 |
| 秦（朱泚） | sui-tang | 秦＊ | 唐德宗時朱泚所建 |
| 楚（李希烈） | sui-tang | 楚＊ | 唐德宗時淮西節度使李希烈所建 |
| 漢（朱泚） | sui-tang | 漢＊ | 朱泚由秦改稱的國號 |
| 大齊（黃巢） | sui-tang | 大齊＊、齊＊ | 唐末黃巢起義所建政權 |
| 後梁 | five-dynasties |  | 五代朱溫 |
| 後唐 | five-dynasties |  |  |
| 後晉 | five-dynasties |  |  |
| 後漢 | five-dynasties |  | 五代劉知遠（東漢亦稱後漢，個別宜核） |
| 後周 | five-dynasties |  |  |
| 五代 | five-dynasties |  | 通稱，不拆 |
| 前蜀 | five-dynasties |  | 十國之一 |
| 後蜀 | five-dynasties |  | 十國之一 |
| 楊吳 | five-dynasties | 吳(楊) | 十國之一 |
| 南唐 | five-dynasties |  | 十國之一 |
| 吳越 | five-dynasties |  | 十國之一 |
| 閩 | five-dynasties | 閩國 | 十國之一 |
| 十國 | five-dynasties |  | 五代時南方與河東諸政權的通稱 |
| 馬楚 | five-dynasties | 楚＊ | 馬氏據湖南；屬十國 |
| 南漢 | five-dynasties |  | 劉氏據嶺南；屬十國 |
| 南平 | five-dynasties | 荊南、北楚 | 高氏據荊南；屬十國 |
| 北漢 | five-dynasties |  | 劉崇據河東；屬十國 |
| 大燕（劉守光） | five-dynasties | 大燕＊、燕＊ | 五代初劉守光據幽州所建 |
| 北宋 | song |  |  |
| 南宋 | song |  |  |
| 趙宋 | song | 兩宋、南北宋、宋＊ | 宋代的通稱，以別於南朝劉宋 |
| 遼 | liao-jin-yuan |  |  |
| 西夏 | liao-jin-yuan |  |  |
| 金 | liao-jin-yuan |  |  |
| 蒙古 | liao-jin-yuan |  | 蒙古汗國至元 |
| 元 | liao-jin-yuan |  |  |
| 偽齊 | liao-jin-yuan | 齊＊、劉齊、大齊＊ | 金扶持劉豫（1130-1137） |
| 西遼 | liao-jin-yuan |  | 耶律大石西遷所建 |
| 北元 | liao-jin-yuan |  | 元亡後退據漠北的政權 |
| 北遼 | liao-jin-yuan |  | 遼末耶律淳於燕京所建，不久即亡 |
| 明 | ming |  |  |
| 清 | qing | 清末 |  |
| 後金 | qing |  | 滿洲人入關前政權，1616 年努爾哈赤建，1636 年皇太極改國號為清 |
| 中華民國 | modern | 民國、民初 |  |
| 中華人民共和國 | modern | 當代、現代、近代 |  |
| 天完 | null |  | 紅巾軍徐壽輝所建 |
| 大周 | null | 周＊、大周＊ | 張士誠據江浙所建政權 |
| 韓宋 | null |  | 紅巾軍韓山童、韓林兒所建 |
| 大漢 | null |  | 陳友諒所建政權 |
| 明夏 | null | 夏＊ | 明玉珍據四川所建政權 |
| 大順 | null |  | 李自成所建農民政權 |
| 南明 | null |  | 明亡後南方的明宗室政權 |
| 大西 | null |  | 張獻忠所建農民政權 |
| 吳周 | null |  | 吳三桂在衡州稱帝所建政權 |
| 太平天國 | null | 太平天国 | 洪秀全所建的農民政權 |

#### 域外朝代

不归入 period 枚举，`period` 留空。日本、江戶時代、朝鮮、新羅、高麗已建 dynasty 条；韓國、英國、美國、比利時是国名，不建条，`dynasty` 保持自由文本、`_dynasty_id` 留空。

| 规范名 | 库中写法 | 说明 |
|---|---|---|
| 日本 | 日本、日 | |
| 江戶時代 | 日本江戶時代、日本寶永年間 | 寶永為江戶時代年號 |
| 朝鮮 | 朝鮮、朝鮮（明） | 李氏朝鮮，1392–1897 |
| 高麗 | 高麗 | 高麗王朝，918–1392；2026-10-07 起從朝鮮拆出（CBDB c_dy=14，與朝鮮前後相繼，#464） |
| 新羅 | 新羅 | 朝鮮三國之一 |
| 韓國 | 韓國 | |
| 英國 | 英國 | |
| 美國 | 美國 | |
| 比利時 | 比利時 | |

#### 需拆分的歧义朝代（逐条判定，不自动归并）

| 原文 | 所含政权 | 判定方式 |
|---|---|---|
| 宋 | 南朝宋(nanbeichao) / 北宋(song) / 南宋(song) | entity 生卒年 + 著錄志上限 + 作者已知朝代 |
| 魏 | 三國魏(three-kingdoms) / 北魏(nanbeichao) | period 三國志/魏書交叉驗證 |
| 漢 | 西漢(qin-han) / 東漢(qin-han) | period 同屬 qin-han（粗粒度自消歧），canonical 逐條判 |
| 周 | 先秦周(pre-qin) / 北周(nanbeichao) / 後周(five-dynasties) | 逐條判定 |
| 齊 | 南朝齊(nanbeichao) / 北齊(nanbeichao) | period 同屬 nanbeichao，canonical 逐條判 |
| 梁 | 南朝梁(nanbeichao) / 後梁(five-dynasties) | 逐條判定 |
| 吳 | 春秋吳(pre-qin) / 三國吳(three-kingdoms) / 楊吳(five-dynasties) | 逐條判定 |
| 蜀 | 三國蜀(three-kingdoms) / 前蜀(five-dynasties) / 後蜀(five-dynasties) | 逐條判定 |
| 國朝 | 隨編目之朝而異（本庫多清、亦有明） | 按 source 判 |
| 當代 / 近代 / 現代 | 時段詞，多指晚清至民國 | 逐條判 |

#### 跨朝代值（粗粒度可定 period 者，逐条判）

| 原文 | period | 说明 |
|---|---|---|
| 秦漢 | qin-han | 跨秦、漢 |
| 隋唐 | sui-tang | 跨隋、唐 |
| 齊梁 | nanbeichao | 跨南齊、梁 |
| 金元 | liao-jin-yuan | 跨金、元 |
| 遼金元 | liao-jin-yuan | 跨遼、金、元（合稱，不建條；2026-10-07 補，#464） |
| 宋、齊 | nanbeichao | 跨劉宋、南齊 |
| 明末清初 | null | 跨 ming/qing，逐條判 |
| 宋末元初 | null | 跨 song/liao-jin-yuan，逐條判 |
| 元末明初 | null | 跨 liao-jin-yuan/ming，逐條判 |

#### 垃圾值清理（误入朝代栏，应改为正确朝代或留空）

| 原文 | 处理 | 说明 |
|---|---|---|
| @ / ? / 不詳 / 未詳 | → null | 缺失/佔位 |
| 明0 | → 明 | OCR 衍字 |
| 高宗乾隆 / 清 乾隆 / 清 高宗 | → 清 | 帝王廟號+年號誤入 |
| 世宗雍正 | → 清 | 同上 |
| 道光 | → 清 | 年號誤入 |
| 康熙四十八年 | → 清 | 紀年誤入 |
| 玄宗 | → 唐 | 帝王廟號誤入 |
| 廬陵鳳林書院 | → null | 書院名 |
| 西洋 | → null | 地域 |
| 梁天竺 | → null | 地域（天竺=印度） |
