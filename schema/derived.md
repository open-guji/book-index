# 构建产物与派生字段（`_build/`、`index/`）

> 状态：网站确认中（overview#496 请网站经理核）

本档是构建产物的**唯一权威说明**：每个 `_` 派生字段、每种卡片、每个产物文件的形状、来源与出现条件。
以 `build/build_derived.py`、`build/names.py`、`build/v2common.py` 的**现行实现**（契约 3）为准；文档与代码不一致时文档追代码，代码自相矛盾处照现状写，列在〈十二、待 build 统一〉。
例子取自 `build/contract-sample/`（进 git 的契约样例包）与正式库 10-09 全量 build 实测。

源档格式见 [README.md](README.md) 与各记录档；源档里仍有的旧派生字段见 [legacy.md](legacy.md)。

目录：
[一、谁跑、怎么跑](#一谁跑怎么跑) ·
[二、产物目录布局](#二产物目录布局) ·
[三、常量与通则](#三常量与通则) ·
[四、卡片短键](#四卡片短键) ·
[五、派生字段全表](#五派生字段全表) ·
[六、分页文件与版本图](#六分页文件与版本图) ·
[七、`_hubs.json` 与 `classific.json`](#七_hubsjson-与-classificjson) ·
[八、`index/`](#八index) ·
[九、匹配键表](#九匹配键表) ·
[十、自校验与 `report.json`](#十自校验与-reportjson) ·
[十一、契约版本与改契约的规矩](#十一契约版本与改契约的规矩) ·
[十二、待 build 统一](#十二待-build-统一) ·
[十三、沿革](#十三沿革)

---

## 一、谁跑、怎么跑

| 项 | 说明 |
|---|---|
| 谁跑 | 网站 deploy 在打包前，在检出的 book-index（以及 book-index-draft）上执行；产物写到临时目录，打包脚本通过 `BOOK_INDEX_DERIVED_DIR` 读取。bim 在本地用 `bim build`。数据 PR 审阅时可以用 `--check-only` 只做校验 |
| 依赖 | 只用 Python 标准库；3.11／3.12／3.13 实测产物逐字节相同 |
| 输入 | 本仓 `Work/`、`Book/`、`Collection/`、`Entity/` 下的记录（恰好三层分片下、带 `id` 的 `.json`；更深层的文件按 sidecar 跳过，计入 `report.json` 的 `sidecars_ignored`）；`classification/`（有才读）；升格对照（根目录 `promotions.json` 与分片 `promotions/*.json` 都认，两者都在时取并集、分片优先） |
| 耗时 | 正式库全量约 50 秒（原记录）；10-09 在 2 核云端会话加 `--hub-check` 实测 3 分 19 秒 |
| 不进 git | `_build/` 写在 `.gitignore` 里。仓里提交的 `index/` 是另一份（见〈八〉），默认不改 |

```
python3 build/build_derived.py --out "$BOOK_INDEX_DERIVED_DIR"                                  # 正式库
python3 build/build_derived.py --root ../book-index-draft --ref-root . --out <草稿输出目录>        # 草稿库
python3 build/build_derived.py --check-only [--hub-check] [--strict]                            # 只校验，不写任何文件
```

| 参数 | 作用 |
|---|---|
| `--root` | 数据仓根，默认本仓 |
| `--ref-root`（可多次） | 只读参照仓。草稿库 build 时指向正式库：草稿记录引用的正式 id（如草稿 Book 的 `work_id` 指正式 Work）由参照仓解析；升格对照也从参照仓读（`promotions` 只在正式库根）。参照仓的记录参与反查与卡片，**但不为参照仓记录产出 `entry/`** |
| `--out` | 输出目录，默认 `<root>/_build` |
| `--check-only` | 只校验：不写产物，也不写 `report.json`，摘要打印到标准输出 |
| `--strict` | 源档里还有旧派生字段、旧反向字段也算失败（见〈十〉） |
| `--hub-check` | 加跑「改枢纽名牵动几个产物文件」自校验（多一次全量重算） |
| `--hub N` | 枢纽阈值，默认 200 |
| `--write-index` | 另把 `index/` 写回仓内 `index/`（默认只写 `<out>/index/`） |

**退出码**：`0` 成功；`1` 自校验失败（`report.json` 的 `fatal` 非空，标准错误输出打印 `FAIL: …`），不应继续打包；`2` 是命令行参数错误（argparse）；未捕获的异常同样以非 0 退出。

**确定性**：纯函数，同一份源 → 逐字节相同的产物。

| 项 | 规则 |
|---|---|
| `_build/` 下的 JSON（`entry/`、分页、`lineage/`、`_hubs.json`、`classific.json`、三个键表） | 紧凑格式（分隔符 `,` 与 `:`，无空格）、`sort_keys`、非 ASCII 直接写本字、文件尾一个换行 |
| `report.json` | `indent=1`、`sort_keys`、文件尾一个换行；不含时间戳 |
| `index/` 分片 | 不是紧凑格式，见〈八〉 |
| 列表顺序 | 每个列表都按固定键排序（各字段的排序规则见〈五〉） |
| 增量写 | 只重写内容有变的文件；`entry/`、`members/`、`catalog/`、`related/`、`lineage/` 下不再产出的旧文件会删除，空目录一并删除（`index/`、`_hubs.json`、键表不做删除） |

---

## 二、产物目录布局

路径相对于输出目录（默认 `_build/`）。

| 路径 | 什么时候有 | 形状 | 自契约 |
|---|---|---|---|
| `entry/<id>.json` | 本仓每条记录一档（不为参照仓记录产出） | 源记录去掉所有 `_` 起首键与 `promoted_to`，再加〈五〉的派生字段；草稿 Work／Book 另有 `promoted_to` | v1 |
| `members/<collection_id>/<n>.json` | 有成员的丛编；`n` 从 **1** 起 | 成员卡片数组，每页至多 200 项，见〈六〉 | v1 |
| `catalog/<志书 work_id>/<n>.json` | 被别的 Work 以 `indexed_by[].source_bid` 指向的 Work（志书）；`n` 从 **1** 起 | 著录成员数组，每页至多 200 项，见〈六〉 | v1 |
| `related/<work_id>/<n>.json` | Work 的 `_related` 超过 200 项时；`n` 从 **2** 起（第 1 页就是 entry 里的 `_related`） | Work `_related` 元素数组，每页至多 200 项 | v1 |
| `lineage/<work_id>.json` | 该 Work 下有 Book 的 `lineage.derived_from`／`related_to` 项带 `ref`（或旧 `book_id`）时 | `{work_id, nodes, edges}`，见〈六〉 | v1 |
| `_hubs.json` | 总是 | `{id: {t, title?, dyn?}}`，见〈七〉 | v1 |
| `classific.json` | 有 `classification/` 且有 `primary` 分类法时 | 旧格式分类词表（数组），见〈七〉 | v1 |
| `index/works/<0-f>.json`、`index/books/<0-f>.json`、`index/entities/<0-f>.json`、`index/collections.json` | 总是 | `{id: 条目}`，见〈八〉 | v1 |
| `dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json` | 总是（全量 build）；草稿库带 `--ref-root` 时才含正式库的专名，才是全量 | 见〈九〉 | v2 |
| `report.json` | 不带 `--check-only` 时 | 计数与自校验结果；**不属契约**，只供排查，见〈十〉 | — |

正式库 10-09 实测：`entry/` 206,496 档（Work 119,527、Book 54,477、Collection 85、Entity 32,407），产物文件共 207,521 个（不计 `index/`）；`members/` 191 页、`catalog/` 797 页、`related/` 24 页、`lineage/` 8 档；枢纽 59 个。

仓根的 `index.json`（`{"books":{},"collections":{},"works":{}}`）不是 build 产出的。

---

## 三、常量与通则

| 常量 | 值 | 在哪 | 管什么 |
|---|---|---|---|
| `HUB` | `200` | build_derived.py | 枢纽阈值：入度 **大于** 200 者为枢纽（`--hub` 可改） |
| `PAGE` | `200` | build_derived.py | `members/`、`catalog/`、`related/` 每页项数 |
| `MEMBER_HEAD` | `20` | build_derived.py | 丛编 entry 里 `_members` 只带第 1 页的前 20 项 |
| `SIBLINGS_MAX` | `40` | build_derived.py | Book `_siblings` 上限 |
| `HUB_CHECK_MAX` | `6` | build_derived.py | `--hub-check`：改一个枢纽名，牵动的产物文件数上限 |
| `DEFAULT_ROLE` | `"撰"` | build_derived.py | Entity `_works[].role` 缺省时补的值 |
| `CONTRACT` | `3` | build_derived.py | 契约版本，写进 `report.json` 的 `contract` |
| `KEYS_VERSION` | `1` | names.py | 三个键表的 `version` |
| `NORMALIZE` | `{"尙":"尚","郞":"郎","戸":"戶","叅":"參","秘":"祕","歴":"曆","淸":"清"}` | names.py | 键表异体归一，三表共用，原样写进各表的 `normalize` |
| `LEVEL_ORDER` | `concept` 0、`group` 1、`concrete` 2，其余 3 | names.py | `office_keys` 候选排序 |
| `PLACE_SUFFIX` | `縣 州 府 軍 路 道 省 廳` | names.py | 地名「去通名」：以这些字结尾、且全名至少 3 字者，去掉末字另作一键 |
| `PLACE_RANK` | `縣`1、`廳`1、`州`2、`軍`2、`監`2、`府`3、`郡`3、`路`4、`道`4、`省`5、`國`5；其余 9 | names.py | 地名默认候选：取级别最低者 |

**`clean()` 丢空值**（build_derived.py 的卡片、派生对象都经过它）：值为 `None`、`""`、`[]`、`{}`、`False` 的键一律省略；因为 Python 里 `0 == False`，**值为 `0`（及 `0.0`）的键也省略**。默认只保留 `id`（即使为空）；个别调用另指定必留的键（`_catalogs` 留 `bid`，`lineage` 边留 `from`／`to` 或 `a`／`b`，`_classifications` 留 `scheme`、`node`、`path`、`l1`–`l4`，`_hubs.json` 留 `t`）。读者一律按「缺即无」处理：`img` 缺即无影像，`nb` 缺即 0 个版本。

**names.py 的 `_clean()`** 只丢 `None`、`""`、`[]`、`{}`，**保留 `0` 与 `false`**（专名卡片、键表候选用它）。

**枢纽**：入度 > `HUB` 的记录是枢纽。入度计法：Work ＝ 其下 Book 数＋参与的规范关系边数（`related_works` 规范化后，每条边两端各计 1）＋（志书）著录成员数；Entity ＝ 以其为 `authors[].entity_id` 的 Work 数；Collection ＝ 成员数＋参与的关系边数。Book 不计入度。入度按 build 看到的全部记录算（草稿库 build 时含参照仓记录，所以草稿库的 `_hubs.json` 里可以有正式 id）。
枢纽在**会引用它的卡片里**只写 `{"id": …, "h": 1}`，再加该处的边属性（`role`、`vol`、`section`、`relation`、`direction` 等）；名称到 `_hubs.json` 查。例（`988fyztvri` 的 `_collections`）：`{"h":1,"id":"8rlb6yi1ecqo","sub":["補傳","臨濟宗旨"],"vol":1052}`。
用枢纽写法的地方：Book `_work`、`_collections`、Collection `_children`、Work `_related` 里的 Work／Collection 卡片、Book／Collection `_related` 里的 Collection 卡片、`_catalogs`、`_authors`、`catalog/` 页、专名派生字段里的各种卡片。
**不用**枢纽写法（总写完整卡片）的地方：`_books`、`_siblings`、`_members` 与 `members/` 页、Entity `_works`、Book／Collection `_related` 里的 Book 卡片、`_derived_by`、`_lineage_refs`、`lineage/` 的 `nodes`。正式库 10-09：枢纽 59 个（Work 49、Collection 6、Entity 4）。

**`promoted_to` 解析**：升格对照从本仓与各 `--ref-root` 读，本仓优先；每项的值是字符串，或对象里依次取 `production_id`、`to`、`official_id`、`id`。

**专名 id 换算**（names.py）：已升格的草稿专名（在升格对照里）以正式条为准——不进反查、不进键表、不另派生；一切专名 id 引用先经升格对照换成正式 id 再解析。

---

## 四、卡片短键

卡片是派生字段与分页文件里的元素。键名短，值为空的键按〈三〉省略。

### 4.1 Work 卡（`work_card`）

用于：Book `_work`、Work `_related` 中的 Work、Collection `_members`（另加 `t`）、Entity `_works`（`id` 改名为 `work_id`，另加 `role`）。

| 短键 | 类型 | 源字段 | 规则 |
|---|---|---|---|
| `id` | string | `id` | 必有 |
| `title` | string | `title` | |
| `dyn` | string | `dynasty`、`authors[].dynasty` | 顶层 `dynasty` 非空则取它；否则取 `authors[]` 中**第一个**有非空 `dynasty` 的作者的值（不限第 1 位） |
| `juan` | number | `juan_count` | `juan_count` 是对象取 `.number`，是数字取本身；非数字、布尔、0 都不出 |
| `au` | array<string> | `authors[].name` | 取 `authors` 前 3 项中的 `name`（先截前 3 项再滤掉无名者，故至多 3 个） |
| `cls` | string | `classification/` 成员档 | 该 Work 第一条分类行的节点 id（如 `"zm0524"`）。分类行顺序：`primary` 分类法在前，其余按分类法 id；同一分类法内按成员档文件名、档内行序。**无 `classification/` 目录时**退回旧字段 `Work.classification`，值为数组 `[l1, l2 或 null]` |
| `nb` | integer | `Book.work_id` 反查 | 该 Work 的 Book 数；0 不出 |
| `img` | `true` | `resources[].types`／`type`、其 Book 的 `resources`、源 `_has_image` | Work 自身或其任一 Book 的 resources 含 `image`，或源档 `_has_image` 为真 |
| `txt` | `true` | 同上、源 `_has_text` | 同上，看 `text` 与源档 `_has_text` |

例（`988fyztvri` 的 `_work`）：`{"au":["釋惠洪"],"cls":"zm0524","dyn":"南宋","id":"d59f2hte73sw","img":true,"juan":1,"nb":1,"title":"禪林僧寶傳","txt":true}`

### 4.2 Book 卡（`book_card`）

用于：Work `_books`、Book `_siblings`、Collection `_members`（另加 `t`、`section` 与边属性）、Book／Collection `_related`（另加 `t`、`relation`、`direction`）、`lineage/` 的 `nodes`。Book 卡**从不**写成枢纽形。

| 短键 | 类型 | 源字段 | 规则 |
|---|---|---|---|
| `id` | string | `id` | 必有 |
| `title` | string | `title` | |
| `edition` | string | `edition` | |
| `etype` | string | `edition_type` | |
| `dating` | string | `dating.era`、`dating.reign` | `era` 与 `reign` 中是非空字符串（或整数）者，按此顺序用一个半角空格连接，如 `"清 乾隆"`；只有一项就是那一项（如 `"乾隆"`、`"清"`） |
| `y` | integer | `dating.year_range`、`dating.year` | **先取 `year_range[0]`**（数组非空且首项为整数），否则取 `year`（整数）；都没有不出 |
| `holder` | string | `current_location` | 是对象取 `name`，没有 `name` 取 `text`；是字符串取本身 |
| `juan` | number | `juan_count` | 同 Work 卡 |
| `img` | `true` | `resources`、源 `_has_image` | 本 Book 的 resources 含 `image`，或源档 `_has_image` 为真 |
| `txt` | `true` | `resources`、源 `_has_text` | 同上，看 `text` |
| `nres` | integer | `resources` | `resources` 项数；0 不出 |
| `pub` | string｜integer | `publication_info.year` | `publication_info` 是对象、其 `year` 是字符串或整数时原样取 |
| `meas` | string | `measure_info` | 是字符串才取 |
| `from` | array<string> | `lineage.derived_from[]` | `ref_type` 缺省或为 `"book"` 的项的 `ref`（旧写 `book_id`），去重、按 id 排序 |
| `alias` | string | `lineage.alias` | 是字符串才取 |

`resources` 的类型判定（`img`、`txt`、`_has_image`、`_has_text` 共用）：取每项 `types`（字符串数组）的全部值，再加上旧单值 `type`（原样当一个类型值）。

例（`96kzk3xvk0` 的 `_derived_by` 指向的程甲本，作为 `_siblings` 元素）：`{"dating":"清 乾隆","edition":"程甲本","from":["96kzk3xvk0","96kzl60tts"],"holder":"多家收藏","id":"96kzkdm8e8","img":true,"juan":120,"nres":7,"pub":"1791","title":"新鐫全部繡像紅樓夢","txt":true,"y":1791}`

### 4.3 Entity 卡（`ent_card`，用于 Work `_authors`）

| 短键 | 类型 | 源字段 | 规则 |
|---|---|---|---|
| `id` | string | `id` | |
| `name` | string | `primary_name` | 随后被作者项自己的 `name` 覆盖（见 `_authors`） |
| `dyn` | string | `dynasty` | 随后被作者项自己的 `dynasty` 覆盖（作者项有值时） |
| `dates` | object｜string | `dates` | 是对象或字符串才取，原样 |

### 4.4 Collection 卡（`coll_card`）

`{id, title?}`，`title` 取丛编 `title`。用于 `_collections`（另加边属性）、Collection `_children`、Work `_related` 中的 Collection、Book／Collection `_related` 中的 Collection（另加 `t`、`relation`、`direction`）。枢纽丛编写 `{id, h:1}`。

### 4.5 专名卡片（names.py，经枢纽规则）

| 卡片 | 形状 | 源字段与规则 |
|---|---|---|
| dynasty 卡 | `{id, name, start?, end?}` | `name`＝`primary_name`；`start`／`end`＝`dates.start`／`dates.end`（整数才取） |
| reign 卡 | `{id, name, start?, end?, ruler?, dynasty?}` | `ruler`＝`ruler.name`；`dynasty`＝`dynasty_id` 所指朝代条的 `primary_name` |
| office 卡 | `{id, name, level?, dynasties?}` | `level`＝`office_level`，没有则 `institution_level`（官署条也用此卡）；`dynasties`＝`dynasty_ids` 各条的 `primary_name`（解不出名的跳过） |
| place 卡 | `{id, name, start?, end?}` | `start`／`end`＝该地各 `history[]` 段的最小 `start`、最大 `end`（同 `_span`） |
| people 卡 | `{id, name, dyn?}` | `dyn`＝`dynasty` |

例（`hixi1ubk35z8` 三國吳的 `_reigns` 首项）：`{"dynasty":"三國吳","end":229,"id":"hixi1ubl0vmo","name":"黃武","ruler":"孫權","start":222}`

---

## 五、派生字段全表

列说明：**出现**——「总是」（值可能是空数组）／「为真才有」／条件；**产物**——都在 `entry/<id>.json`，另注分页文件；**自**——契约版本（v1 基础，v2 专名派生，v3 Book／Collection `_related`）。

**过渡期取并集**：源档里还有旧反向字段（`Work.books`、`Entity.works`、`Collection.books`、`Collection.contained_works`）时，build 把它们与成员侧（`Book.work_id`、`Work.authors[].entity_id`、`*.contained_in`）取并集，所以迁移前后产物的关系集合相同。正式库 10-09 这些旧字段已全数删除，这一段空转。

### 5.1 Work

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_books` | array<Book 卡> | 总是 | `Book.work_id` 反查（并旧 `Work.books`）。排序：有年代者在前，按 Book 卡 `y` 的取法（`year_range[0]` 优先，否则 `year`）升序；年代相同或都无年代按 id | entry | v1 |
| `_edition_count` | integer | 总是 | `len(_books)` | entry | v1 |
| `_authors` | array<`{name?, role?, dyn?, id?, h?, dates?}`> | 总是 | 与 `authors[]` 同序，非对象项跳过。每项基础为 `{name: authors[].name, role: authors[].role, dyn: authors[].dynasty}`（空者省略；**role 缺不补**）；`entity_id` 解得到 Entity 时先放 Entity 卡（或枢纽 `{id, h:1}`），再用基础值覆盖其 `name`、`dyn` | entry | v1 |
| `_catalogs` | array<`{bid, title?, dyn?, section?}`>，枢纽志书为 `{bid, h:1, section?}` | 总是 | 按 `indexed_by[]` 顺序，取 `source_bid` 解得到 Work 者，同一 `source_bid` 只取第一次出现。`title`＝志书题名；`dyn`＝志书的 Work 卡 `dyn` 取法；`section`＝该 `indexed_by` 项的 `section`（非空字符串） | entry | v1 |
| `_related` | array<Work 卡或 Collection 卡＋`{relation, direction, note?}`>；对方是枢纽时为 `{id, h:1, relation, direction, note?}` | 总是 | 本库全部 `related_works[]`（对方须是 Work 或 Collection，否则计悬空）先规范化：旧词 `commentary_on`→`studies`、`related_to`→`related`；反向词换成规范词并对调两端；`related` 存到 id（字符串比较）较小一端。每条规范边在存储端出 `direction:"out"`、词为规范词；在另一端出 `direction:"in"`、成对词取反向词（`part_of`↔`has_part`、`studies`↔`studied_by`、`contains_text_of`↔`text_carried_by`、`preceded_by`↔`followed_by`、`pseudepigraph_of`↔`has_pseudepigraph`、`adapted_from`↔`has_adaptation`），`related` 与单向词（`collected_in`、`derived_from`、`same_entry`、`suspected_same`、`excerpted_from`、`source_of`）及词表外的词**原词不变**。`note`：两侧写的 note 合并，规范侧在前，去空、去重、去被包含者，以 `；` 连接。排序：`relation`、`direction`、`id`。超过 200 项时 entry 只留前 200 | entry；余页 `related/<id>/<n>.json` | v1 |
| `_related_total` | integer | `_related` 超过 200 项时 | 全部关联项数 | entry | v1 |
| `_related_pages` | integer | 同上 | 总页数（含 entry 里的第 1 页） | entry | v1 |
| `_collections` | array<Collection 卡＋`{vol?, sub?, group?, ord?}`>，枢纽为 `{id, h:1, …}` | 总是 | 先按本条 `contained_in[]` 顺序（对方须是 Collection，同一丛编只取一次），边属性取该项：`vol`＝`volume_index`、`sub`＝`sub_items`、`group`＝`group`、`ord`＝`details` 里「叢編原序 N」的 N（整数）；再把只见于丛编侧旧字段的丛编按 id 补在后面 | entry | v1 |
| `_classifications` | array<`{scheme, node, path, l1, l2, l3, l4, source?}`> | 有 `classification/` 且该 Work 有成员行时 | 分类成员档 `[work_id, source]`。`path`＝节点到根的标签链（根在前）；`l1`–`l4`＝`path` 补 `""` 到 4 项；`source`＝成员行第二项。顺序同 Work 卡 `cls` | entry | v1 |
| `_member_catalog` | `{total, pages}` | 本 Work 是志书（有别的 Work 的 `indexed_by[].source_bid` 指它）时 | 著录成员数、页数 | entry；成员在 `catalog/<id>/<n>.json` | v1 |
| `_has_image` | `true` | 为真才有 | Work 或其任一 Book 的 resources 含 `image`；或源档 `_has_image`／`has_image` 为真 | entry | v1 |
| `_has_text` | `true` | 为真才有 | Work 或其任一 Book 的 resources 含 `text`；或源档 `_has_text`／`has_text` 为真（源档值见 [legacy.md](legacy.md)） | entry | v1 |
| `_has_collated` | `true` | 为真才有 | **只看源档** `_has_collated`／`has_collated` 为真（resources 推不出整理本） | entry | v1 |
| `_lineage_graph_ref` | string，形如 `"lineage/<work_id>.json"` | 本 Work 产出了 `lineage/` 文件时 | 见〈六·版本图〉 | entry | v1 |
| `_dynasty_id` | string（dynasty 条 id） | 条件：见右 | 朝代名取 Work 卡 `dyn` 的取法（顶层 `dynasty` 优先，其次第一个有朝代的作者）；在 `dynasty_reign_keys` 里查该名（查不到再查异体归一形），只留 `subtype:"dynasty"` 的候选；恰好 1 个 id 且无候选带 `ambiguous` → 出 `_dynasty_id` | entry | v2 |
| `_dynasty_candidates` | array<string>（按 id 排序） | 条件 | 同上，候选多于 1 个或带 `ambiguous` 时出候选 id 列表；查不到两者都不出 | entry | v2 |
| `promoted_to` | string（正式 id） | 本条在升格对照里时（草稿记录） | 升格对照 | entry | v1 |

例：`d59ezak6jq4g`（左傳）`_related_total: 233`、`_related_pages: 2`，第 2 页在 `related/d59ezak6jq4g/2.json`，首项 `{"direction":"in","id":"d59f2pu2ujgh","relation":"text_carried_by","title":"春秋左氏講義"}`。
`d59dgrrusb28`（欽定四庫全書）的 `_related` 里 `{"au":["吳慰祖"],"direction":"out","dyn":"中華人民共和國","id":"d59f2ofmrsw1","relation":"preceded_by","title":"四庫採進書目"}` 是本条存储的规范边；`{"au":["商務印書館"],"direction":"in","dyn":"民國","id":"d59dh4mvgqgw","nb":1,"relation":"derived_from","title":"四庫全書珍本初集"}` 是对方存储的单向词，原词不变。
`_classifications` 例（`d59ezak6jq4g`）：`{"l1":"經部","l2":"春秋類","l3":"","l4":"","node":"zm0076","path":["經部","春秋類"],"scheme":"zongmu","source":"漢書藝文志/六藝略／春秋"}`。

### 5.2 Book

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_work` | Work 卡，枢纽为 `{id, h:1}` | `work_id` 解得到 Work（含参照仓）时 | `work_id` | entry | v1 |
| `_siblings` | array<Book 卡>，至多 40 | 与 `_work` 同时出现（可为 `[]`） | 同一 Work 的其他 Book，排序同 `_books`，取前 40 | entry | v1 |
| `_siblings_more` | `true` | 其他版本超过 40 时 | | entry | v1 |
| `_siblings_total` | integer | 同上 | 其他版本总数（不含本条） | entry | v1 |
| `_collections` | 同 Work `_collections` | 总是 | 同 Work | entry | v1 |
| `_related` | array<（Book 卡或 Collection 卡）＋`{t, relation:"related", direction}`> | 有对称关联时才有 | 本库（含参照仓）所有 Book、Collection 的 `related_books`、`related_collections` 里的 id（字符串、非自身、对方是 Book 或 Collection）两侧并集。`t`＝`"book"`／`"collection"`；`direction`＝`"out"` 本条源档写了这一项，`"in"` 只有对方写了（两侧都写时两边都是 `"out"`）。按对方 id 排序；不分页 | entry | **v3** |
| `_lineage_refs` | object `{book_id: {title?, edition?}}` | 有可解析的引用时 | `lineage.derived_from[]` 与 `lineage.related_to[]` 各项的 `ref`（旧写 `book_id`），对方须是 Book（不看 `ref_type`）；值取对方 `title`、`edition` | entry | v1 |
| `_derived_by` | array<`{id, title?, edition?, rel?}`> | 有别本以本条为底本时 | 别的 Book 的 `lineage.derived_from[]` 中 `ref_type` 缺省或为 `"book"`、`ref`（或 `book_id`）指向本条者；`rel`＝该项 `relation`。按对方 id 排序 | entry | v1 |
| `_has_image` | `true` | 为真才有 | 本条 resources 含 `image`，或源档 `_has_image`／`has_image` 为真 | entry | v1 |
| `_has_text` | `true` | 为真才有 | 本条 resources 含 `text`，或源档 `_has_text`／`has_text` 为真 | entry | v1 |
| `_has_collated` | `true` | 为真才有 | 只看源档 `_has_collated`／`has_collated` | entry | v1 |
| `_lineage_graph_ref` | string `"lineage/<work_id>.json"` | 所属 Work 下任一 Book 的 `lineage.derived_from` 或 `related_to` 非空时（本条自己没有也出） | 见〈十二〉第 5 条 | entry | v1 |
| `promoted_to` | string | 草稿记录在升格对照里时 | 升格对照 | entry | v1 |

例：`988fxodt6s`（周曰校重刊本）`"_siblings_more":true,"_siblings_total":49`，其 `_work` 的 `nb` 为 50。
`96kzk3xvk0` 的 `_derived_by`：`[{"edition":"程甲本","id":"96kzkdm8e8","rel":"底本","title":"新鐫全部繡像紅樓夢"}]`。
`96kzirvbwg` 的 `_lineage_refs`：`{"96kzj1joqo":{"edition":"己卯本","title":"脂硯齋重評石頭記"}}`。

### 5.3 Collection

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_members` | array<成员卡>，至多 20 | 总是（无成员为 `[]`） | `members/<id>/1.json` 的前 20 项，成员卡形状见〈六〉 | entry | v1 |
| `_member_count` | integer | 总是 | 成员总数（无成员为 `0`） | entry | v1 |
| `_member_pages` | integer | 总是 | 成员页数；**无成员为 `0`**，此时没有 `members/<id>/` | entry | v1 |
| `_member_type` | `"Work"`｜`"Book"`｜`"mixed"` | 有成员时 | 成员全是 Book 为 `"Book"`、全是 Work 为 `"Work"`、两者都有为 `"mixed"`（注意首字母大写，与成员卡的小写 `t` 不同） | entry | v1 |
| `_children` | array<Collection 卡>，枢纽为 `{id, h:1}` | 有子丛编时 | 别的 Collection 的 `contained_in[]` 指向本条（`contained_in` 项是字符串或 `{id,…}` 都认），按 id 排序 | entry | v1 |
| `_related` | 同 Book `_related` | 有对称关联时 | 同 Book | entry | **v3** |
| `_has_image`／`_has_text` | `true` | 为真才有 | 本条 resources；或源档旧值 | entry | v1 |
| `_has_collated` | `true` | 为真才有 | 只看源档旧值 | entry | v1 |

正式库 10-09：85 个丛编中 9 个无成员（`_member_pages: 0`、无 `_member_type`）。
例：`8rlcsybg2hhd` 的 `_children`：`[{"id":"8rlcsybg2hhe","title":"二十四史"},{"h":1,"id":"8rlcsybg2hhf"},{"id":"8rlcsybg2hhg","title":"武英殿十三經注疏"}]`；`8rlb6yi1ecqo` 的 `_related`：`[{"direction":"out","id":"8rlcsybg2hi6","relation":"related","t":"collection","title":"四庫全書珍本（臺灣商務再續本）"}]`。
Collection 的 `_related` 只来自 `related_books`／`related_collections`；Work 的 `related_works` 指向丛编的边（如 `collected_in`）只出现在 Work 一侧的 `_related`。

### 5.4 Entity 通用

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_works` | array<Work 卡（`id` 改名 `work_id`）＋`role`> | 总是（所有 subtype，可为 `[]`） | `Work.authors[].entity_id` 反查（并旧 `Entity.works`）；同一 Work 多次署名取第一个非空 `role`。`role` 缺则补 `"撰"`（计入 `report.json` 的 `notes`）。Work 卡总是完整卡、不用枢纽形。排序：`cls`（旧数组形取首项）、`title`、`work_id` | entry | v1 |

例（`hixhcvhrh4ow` 傅以漸）：`{"au":["傅以漸"],"dyn":"清","img":true,"nb":1,"role":"序","title":"順治十五年會試錄","work_id":"d59f2my204jk"}`。

以下专名派生字段（5.5–5.10）由 names.py 产出；**已升格的草稿专名不产出**（以正式条为准），`_works` 仍照出。

### 5.5 dynasty

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_children` | array<dynasty 卡> | 有子朝代时 | 别的 dynasty（以及 office、官署——同一张反查表）的 `parent_id` 指向本条；排序：有 `dates.start` 者在前、按 start、再按 id | entry | v2 |
| `_ancestors` | array<dynasty 卡>，至多 3 项 | 有上级时 | 沿 `parent_id` 上溯，由近到远，遇环停止 | entry | v2 |
| `_reigns` | array<reign 卡> | 有年号时 | reign 的 `dynasty_id` 指向本条；排序同 `_children` | entry | v2 |

例：`hixi1ubjgow0`（三國）`_children`：`[{"end":265,"id":"hixi1ubk35za","name":"三國魏","start":220},{"end":263,"id":"hixi1ubk35z9","name":"三國蜀","start":221}]`；`hixi1ubk35z8`（三國吳）`_ancestors`：`[{"end":280,"id":"hixi1ubjgow0","name":"三國","start":220}]`。

### 5.6 reign

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_dynasty` | dynasty 卡 | `dynasty_id` 解得到时 | `dynasty_id` | entry | v2 |
| `_ruler` | people 卡 `{id, name, dyn?}` | `ruler.entity_id` 解得到时 | `ruler.entity_id` | entry | v2 |
| `_index_in_reign` | integer（从 1 起） | 有 `ruler.name` 时 | 同一 `dynasty_id`、同一 `ruler.name` 下的年号按 `dates.start`（无起年者在后）、id 排序后的序号 | entry | v2 |
| `_same_name` | array<reign 卡> | 全库有其他同名年号时 | 全库 `primary_name` 相同的其他 reign，按 start、id 排序 | entry | v2 |

例：`hixi1ubkeejj`（建元）`"_dynasty":{"end":8,"id":"hixi1ubkeeiw","name":"西漢","start":-206},"_index_in_reign":1`，`_same_name` 首项 `{"dynasty":"前趙","end":315,"id":"hixi1ublncpa","name":"建元","ruler":"劉聰","start":315}`。

### 5.7 office

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_children` | array<office 卡> | 概念条下有具体条时 | 具体条的 `parent_id` 反查；按 id 排序 | entry | v2 |
| `_compounds` | array<office 卡> | 有复合条时 | 以本条为 `base_office_id` 的复合条；按 id 排序 | entry | v2 |

`_holders`（任职人物）不产出：库中还没有人物→官职数据。
例（草稿 `1jb8ajoi663uo` 參知政事）：`_children` 首项 `{"dynasties":["趙宋"],"id":"1jb8ajoi9wydc","level":"concrete","name":"參知政事"}`。

### 5.8 官署（`subtype:"collective"` 且 `collective_kind:"官署"`）

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_children` | array<office 卡> | 有时 | 具体官署条的 `parent_id` 反查（概念→具体）；按 id | entry | v2 |
| `_subordinates` | array<office 卡> | 有时 | 别的官署条 `superiors[].id` 反查（下级）；按 id | entry | v2 |
| `_members` | array<office 卡> | 有时 | 别的官署条 `group_ids[]` 反查（合称的成员）；按 id | entry | v2 |
| `_offices` | array<office 卡> | 有时 | office 条的 `institution_ref` 反查（所属官职）；按 id | entry | v2 |

四个字段的卡片都是 office 卡（官署条的 `level` 取 `institution_level`）。
例：`hixi1ubqbwuz`（六部）`_members` 首项 `{"id":"hixi1ubqbwv1","level":"concept","name":"兵部"}`；草稿 `1jb8bl20cxpmo`（東宮）`_offices`：`[{"dynasties":["唐"],"id":"1jb8awb96vuv4","level":"concrete","name":"太子少保"}]`。

### 5.9 place

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_children` | array<place 卡> | 有下辖时 | 别的 place 的 `history[].parent_id` 反查；按 id。卡片带下级自己的 `start`／`end` | entry | v2 |
| `_span` | `{start?, end?}` | 有任一段起讫年时 | 各 `history[]` 段整数 `start` 的最小值、整数 `end` 的最大值 | entry | v2 |

例（草稿 `1jb8kgdh3pse8` 浙江省）：`"_span":{"end":1912,"start":1366}`，`_children` 首项 `{"end":1912,"id":"1jb8kgdh3psel","name":"杭州","start":621}`。

### 5.10 people（及 Work）的 `_dynasty_id`／`_dynasty_candidates`

| 字段 | 类型／精确形状 | 出现 | 由哪些源字段算出 | 产物 | 自 |
|---|---|---|---|---|---|
| `_dynasty_id` | string | 条件 | people 取本条 `dynasty`；Work 见 5.1。查法同 5.1 | entry | v2 |
| `_dynasty_candidates` | array<string> | 条件 | 同上 | entry | v2 |

例：`hixhd2h9bdye`（歐陽修，`dynasty:"北宋"`）→ `"_dynasty_id":"hixi1ubk35zj"`。`dynasty_reign_keys` 里 `宋` 一键下有 `南朝宋`、`宋（輔公祏）`、`趙宋`、`北宋` 等多个带 `ambiguous` 的候选，写 `宋` 的人物只得 `_dynasty_candidates`。
正式库 10-09：people 有 `_dynasty_id` 21,261 条、`_dynasty_candidates` 2,509 条；Work 69,950 条、6,474 条。

---

## 六、分页文件与版本图

**`members/<cid>/<n>.json`**：成员卡数组，每页 200 项，`n` 从 1 起。成员来自成员侧 `Book.contained_in[]`、`Work.contained_in[]`（并旧 `Collection.books`、`contained_works`）。

| 键 | 说明 |
|---|---|
| Book 卡或 Work 卡的全部短键 | 完整卡片，不用枢纽形 |
| `t` | `"book"`／`"work"` |
| `section` | 仅 Book 成员：`Book.section`（非空字符串） |
| `vol`、`sub`、`group`、`ord` | 边属性，取自成员的 `contained_in` 项（同〈五〉`_collections`）；同一成员对同一丛编有多项时依次合并、后项覆盖 |

排序：先 `t`（`book` 在 `work` 前），再「有 `ord` 的在前」，再按 `ord`，再按 id。
例（`8rlb6yi1ecqo` 首页中的一项）：`{"dating":"清 乾隆","edition":"欽定四庫全書·文淵閣本","etype":"抄本","id":"988fyztvri","img":true,"nres":3,"section":"史部","sub":["補傳","臨濟宗旨"],"t":"book","title":"僧寶傳","txt":true,"vol":1052,"y":1736}`

**`catalog/<志书 work_id>/<n>.json`**：著录成员数组，每页 200 项，`n` 从 1 起。

| 键 | 类型 | 说明 |
|---|---|---|
| `id` | string | 著录成员 Work id |
| `h` | `1` | 成员是枢纽时；此时无 `title` |
| `title` | string | 成员 Work 题名（非枢纽时） |
| `section` | string | 成员 `indexed_by` 项的 `section` |
| `title_info` | 原样 | 成员 `indexed_by` 项的 `title_info` |
| `attested_status` | 原样 | 成员 `indexed_by` 项的 `attested_status` |

同一成员对同一志书有多个 `indexed_by` 项时取第一项。排序：`section`（无者按空串）、id。
例：`{"attested_status":"lost","id":"d59f23nvs7pc","section":"儀禮","title":"喪服譜鄭玄注","title_info":"《喪服譜注》（鄭𤣥）"}`（`catalog/d59f2mel8d1d/1.json`）。

**`related/<work_id>/<n>.json`**：Work `_related` 第 201 项起的余页，元素同 `_related`，`n` 从 2 起。

**`lineage/<work_id>.json`（版本图）**：`{work_id, nodes, edges}`。

| 键 | 说明 |
|---|---|
| `work_id` | 本 Work id |
| `nodes` | Book 卡数组：先是本 Work 的全部 Book（顺序同 `_books`），再按边出现顺序补上边所指、不属本 Work 但库里有的 Book |
| `edges` | 由本 Work 各 Book 的 `lineage` 生成，项须是对象且带 `ref`（或旧 `book_id`）：`derived_from` 项 → `{from: ref, to: 本 Book, rel?: relation, ref_type?, confidence?}`；`related_to` 项 → `{a: 本 Book, b: ref, rel?: relation, ref_type?}`。按各边 JSON（键排序）字符串排序 |

`derived_from` 边不论 `ref_type` 都收进 `edges`。没有一条边时不出文件，该 Work 也没有 `_lineage_graph_ref`。
例（`lineage/d59dh3vo9af4.json` 的边）：`{"confidence":"consensus","from":"96mid1ogzk","ref_type":"book","rel":"影印","to":"96mmyltp1c"}`；（`lineage/d59df01avcw0.json`）：`{"a":"96kzirvbwg","b":"96kzj1joqo","rel":"兄弟本"}`。

---

## 七、`_hubs.json` 与 `classific.json`

**`_hubs.json`**：`{id: {t, title?, dyn?}}`，键按 id 排序，覆盖 build 看到的全部枢纽（草稿库 build 时可含正式 id）。

| 键 | 说明 |
|---|---|
| `t` | 记录类型首字母小写：`"w"`、`"c"`、`"e"`；代码按类型取首字母，也可以是 `"b"`（见〈十二〉第 6 条） |
| `title` | `title`，没有则 `primary_name`（Entity） |
| `dyn` | Work 取 Work 卡 `dyn` 的取法；其余取 `dynasty` |

例：`"8rlcsybg2hhf":{"t":"c","title":"武英殿聚珍版叢書"}`。

**`classific.json`**：旧分类词表，给还没改读 `tree.json` 的旧读者。取 `primary` 分类法（`zongmu`）树上全部未 `retired` 的叶节点，按树里的节点顺序，每项 `{cata_l1, cata_l2, …}` 是该叶到根的标签链。例：`{"cata_l1":"經部","cata_l2":"總類","cata_l3":"石經之屬"}`。

---

## 八、`index/`

检索用扁平摘要，网站搜索与 bim 列表读它。字段规则逐字照 bim `entry_extractor.py`（`build_index_entry`／`build_entity_index_entry`），另加 `has_collated`。`index/` 的键不加下划线：整个文件都是派生产物。

**分片**：

| 类型 | 文件 |
|---|---|
| Work | `index/works/<h>.json` |
| Book | `index/books/<h>.json` |
| Entity | `index/entities/<h>.json` |
| Collection | `index/collections.json`（单文件，不分片） |

`h` 是 id 的哈希：`h = 0`，对 id 每个字符 `h = (h*31 + ord(c)) & 0xFFFFFFFF`，最后 `h % 16`，写成小写十六进制一位（`0`–`f`）。与 bim `storage.shard_of` 相同。
每个文件是 `{id: 条目}`，键按 id 排序；条目内的键序按下表（不排序）。

**格式**：沿用目标文件现有的缩进（看第二行的前导空格，默认 2）与「文件尾有无换行」；目标文件不存在时缩进 2、**文件尾无换行**（见〈十二〉第 7 条）。只写有变的文件。默认写 `<out>/index/`；`--write-index` 另写回仓内 `index/`。仓内 `index/` 提交在 git 里，现有分片都是缩进 2、文件尾一个换行。

**条数守恒**：`index/` 条目总数必须等于 `entry/` 数，否则失败。

### 8.1 Work、Book、Collection 条目

| 键 | 必有／可选 | 来源字段 | 取法 |
|---|---|---|---|
| `id` | 必有 | `id` | |
| `title` | 必有 | `title` | 缺则 `"未命名"` |
| `type` | 必有 | — | `"Work"`／`"Book"`／`"Collection"`（首字母大写） |
| `path` | 必有 | — | 记录文件相对仓根的路径，分隔符 `/`，如 `"Work/g/c/g/d59dh4069gcg-欽定四庫全書薈要分架圖.json"` |
| `author` | 可选 | `authors[0].name` | 只看第 1 位作者；`authors[0]` 不是对象时取其字符串形；`authors` 本身是字符串时取它 |
| `era` | 可选 | `dating.era` | 非空字符串 |
| `sort_year` | 可选 | `dating.year`、`dating.year_range` | **先取 `year`**（整数，非布尔），否则 `year_range` 是两项数组且首项是整数时取首项（与卡片 `y` 的先后相反，见〈十二〉第 2 条） |
| `holder` | 可选 | `current_location` | 是对象取 `name`（不看 `text`）；是字符串取本身 |
| `dynasty` | 可选 | `authors[].dynasty`、`dynasty` | **撰人朝代**：`authors[]` 中**第一个**有非空 `dynasty` 的作者的值（不限第 1 位），没有再取顶层 `dynasty`。与卡片 `dyn`（成书朝代，顶层优先）语义不同，不统一，见〈十二〉第 1 条 |
| `role` | 可选 | `authors[0].role` | |
| `juan_count` | 可选 | `juan_count` | 对象取 `.number`，数字取整；0 不出 |
| `measure_info` | 可选 | `measure_info` | 真值原样 |
| `additional_titles` | 可选 | `additional_titles` | 字符串数组；对象项取其 `book_title` |
| `attached_texts` | 可选 | `attached_texts` | 同上 |
| `has_text` | 可选（`true`） | `resources` | **只看本条 resources**：有 `types` 数组且非空时看其中有无 `text`；否则看旧单值 `type` 是否为 `text` 或 `text+image`。不看源档 `_has_text`，Work 也不并其 Book（见〈十二〉第 3 条） |
| `has_image` | 可选（`true`） | `resources` | 同上，看 `image`（旧 `type` 为 `image` 或 `text+image`） |
| `has_collated` | 可选（`true`） | `_has_collated`、`has_collated` | 源档值为真 |
| `edition`、`subtype`、`period`、`loss_status`、`original_title`、`work_id` | 可选 | 同名 | 真值原样 |
| `promoted_to` | 可选 | 源档 `_promoted_to`、`promoted_to`、升格对照 | 按此先后取第一个非空者；四类记录都出 |

例（草稿 `11sfkchnpaigw`）：`{"author":"董誥","dynasty":"清","edition":"清嘉慶二十一年揚州刻本（內府本）","era":"清","has_image":true,"holder":"清華大學圖書館","id":"11sfkchnpaigw","juan_count":1000,"measure_info":"一千卷","path":"Book/i/g/w/11sfkchnpaigw-欽定全唐文清嘉慶二十一年揚州刻本內府本.json","role":"等奉敕編","sort_year":1816,"title":"欽定全唐文","type":"Book","work_id":"d59f2nqla48x"}`（样例包里按键排序展示）。

### 8.2 Entity 条目

| 键 | 必有／可选 | 来源字段 | 取法 |
|---|---|---|---|
| `id` | 必有 | `id` | |
| `type` | 必有 | — | **小写 `"entity"`**（其余三类首字母大写） |
| `subtype` | 必有 | `subtype` | 缺则 `"people"` |
| `primary_name` | 必有 | `primary_name` | 缺则 `""` |
| `path` | 必有 | — | 同上 |
| `dynasty` | 可选 | `dynasty` | 真值 |
| `birth_year`、`death_year` | 可选 | 顶层同名字段 | 不为 null 时原样 |
| `cbdb_id` | 可选 | `external_ids.cbdb_id` | 不为 null 时原样 |
| `period` | 可选 | `period` | 真值 |
| `promoted_to` | 可选 | 同 8.1 | |

例：`{"birth_year":1609,"cbdb_id":59084,"death_year":1665,"dynasty":"清","id":"hixhcvhrh4ow","path":"Entity/4/o/w/hixhcvhrh4ow-傅以漸.json","period":"qing","primary_name":"傅以漸","subtype":"people","type":"entity"}`

---

## 九、匹配键表

`dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`：供文本侧按名回挂专名条。每次全量 build 都产出；草稿库 build 带 `--ref-root` 时才含正式库专名、才是全量。

**共同外形**：

```
{"version": 1, "count": {…}, "normalize": {NORMALIZE 表}, "keys": {键: [候选, …]}}
```

| 表 | `count` 的键 |
|---|---|
| dynasty_reign_keys | `keys`（键数）、`dynasty`、`reign`（条数） |
| office_keys | `keys`、`office`、`官署`、`multi_candidate_keys`（候选多于 1 的键数） |
| place_keys | `keys`、`place`、`multi_candidate_keys`、`default_marked`（有 `default` 候选的键数） |

**键从哪来**：每条的 `primary_name`（`via:"primary_name"`）与 `alt_names[]` 中 `type` 不是 `全稱` 的 `name`（`via` 取该别名的 `type`，无 type 为 `"alt"`；别名带 `ambiguous:true` 则候选带 `ambiguous:true`）。每个名同时以原形与 `NORMALIZE` 归一形为键。同一条在一个键下只出现一次（按 id 顺序处理，先出现的 `via` 胜）。`keys` 按键排序。

**dynasty_reign_keys 候选**（收 `subtype` 为 `dynasty`、`reign` 者）：`{id, subtype, primary_name, via, ambiguous?, start?, end?}`，`start`／`end` 取 `dates`；reign 另有 `dynasty_id`、`dynasty`（朝代名）、`ruler?`（`ruler.name`）；dynasty 另有 `parent_id?`。排序：dynasty 在前，再按 `start`（无者当 0）、id。
例：`"康熙":[{"dynasty":"清","dynasty_id":"hixi1ubjrxga","end":1722,"id":"hixi1ubqbwun","primary_name":"康熙","ruler":"愛新覺羅玄燁","start":1662,"subtype":"reign","via":"primary_name"}]`

**office_keys 候选**（收 office 与官署）：`{id, subtype: "office"|"官署", level?, primary_name, via, ambiguous?, dynasty_ids?, dynasties?, parent_id?, base_office_id?, institution_ref?, qualifier?, office_class?, rank?}`。`level` 取 `office_level`／`institution_level`；`dynasties` 是 `dynasty_ids` 各条的名；`qualifier` 原样（其 `target` 换成正式 id）；`rank` 取 `rank.text`。排序：office 在前，再按 `LEVEL_ORDER`、id。
例：`"三省":[{"id":"hixi1ubqbwv0","level":"group","primary_name":"三省","subtype":"官署","via":"primary_name"}]`

**place_keys 候选**（收 place）：键源按先后为 `primary_name` → 别名（全稱除外）→ 沿革（各 `history[]` 段的当时名 `name`，`via:"沿革"`）→ 去通名（前面各名以 `PLACE_SUFFIX` 结尾且至少 3 字者去末字，`via:"去通名"`）。候选 `{id, subtype:"place", primary_name, via, level?, start?, end?, modern?, segments?, ambiguous?, default?}`：`level`＝最后一段的 `level`；`start`／`end`＝各段最小起年、最大讫年；`modern`＝`modern.text`；`segments`＝以沿革名（及其去通名形）命中时，该名对应的各段 `{name_then, start?, end?, level?, parent_id?, parent?, dynasties?}`。排序：只靠去通名命中者在后，其余按 `start`、id。
**`default`**：一个键有 2 个以上候选时至多标一个——① 恰有一个候选是 `primary_name` 命中，标它；② 否则取 `PLACE_RANK` 最低的候选 L（最低级不止一个则不标），仅当其余候选都在 L 的沿革上级链闭包里时标 L；③ 其余不标。
正式库 10-09 还没有 place 条，`place_keys.json` 的 `keys` 为空。

---

## 十、自校验与 `report.json`

**算失败（写进 `fatal`，退出码 1）**：

| 项 | 说明 |
|---|---|
| 条数守恒 | 本仓源记录数 ＝ `entry/` 数；`index/` 条目数 ＝ `entry/` 数 |
| 派生值自洽 | `_edition_count ＝ len(_books)`；成员各页合计 ＝ `_member_count`；`_members` ＝ 第 1 页前 20 项；`_related` 分页合计 ＝ `_related_total`；`catalog/` 各页合计 ＝ `_member_catalog.total` |
| 卡片可解析 | `_related`、`_collections`、`_children`、`_siblings`、`_books`、`_works`（按 `work_id`）、`_catalogs`（按 `bid`）、`_work`、带 `id` 的 `_authors`、各 `members/`／`catalog/` 页里每张卡片的 id 都能解到记录；带 `h:1` 的都在 `_hubs.json` |
| 读档问题 | 读不了的文件、无 `id`、`type` 与所在目录不符、同 id 重复 |
| 分类档校验 | 成员档名 ＝ 其 `node`；节点存在且未 `retired`；`exclusive` 分类法一部只出现一次；成员行是本仓或参照仓的 Work |
| 源档里的未知 `_` 字段 | 除准留的 `_has_text`、`_has_collated` 与下面的旧派生字段外，源档出现任何 `_` 起首字段 |
| `--strict` | 源档仍有旧派生字段或旧反向字段（`LEGACY_DERIVED`、`LEGACY_REVERSE`；有 `classification/` 时 Work 里残留 `classification` 也算） |
| `--hub-check` | 某类改枢纽名牵动的产物文件超过 `HUB_CHECK_MAX`（6） |

**只报不挡**（写进 `report.json`，不影响退出码；`--strict` 时第 2、3 项改为挡）：
1. 悬空引用 `dangling`：`Book.work_id`、`Book.contained_in`、`Book.lineage.derived_from`、`Work.authors.entity_id`、`Work.contained_in`、`Work.related_works`、`Work.indexed_by.source_bid`、`Collection.contained_in` 及各旧反向字段，只报本仓记录引出的。
2. `LEGACY_DERIVED`：源档里迄 M3 前仍有的旧派生字段——Work `_edition_count`、`_has_image`、`_promoted_to`、`_promoted_at`；Book `_has_image`、`_promoted_to`、`_promoted_at`；Collection `_member_count`、`_member_type`、`_has_image`；Entity `_promoted_to`、`_promoted_at`。build 照算（entry 里以重算值为准），计数进 `source_fields.legacy_underscore_fields`，与重算值之差进 `legacy_vs_rebuilt`（不比 `_promoted_*`、`_has_collated`）。
3. `LEGACY_REVERSE`：源档里的旧反向／副本字段——Work `books`、`has_text`、`has_image`、`has_collated`、`promoted_to`；Book `has_text`、`has_image`、`has_collated`、`promoted_to`；Collection `books`、`contained_works`、`has_text`、`has_image`；Entity `works`、`promoted_to`。
4. `notes`：如「`_has_text` 僅憑源裡舊值（resources 推不出）」（正式库 10-09：295 条）、「`_has_collated` 僅憑源裡舊值」（65 条）、「Entity._works 缺 role（以「撰」補）」。
5. `index.drift_vs_repo_index`：仓内现有 `index/` 与重生值逐字段之差（草稿库数据 PR 不带 `index/`，差得多是预期）。

**`--hub-check`**：Collection、Work、Entity 各取本仓入度最大的枢纽，在内存里给名字加后缀重算全部产物，数变了几个文件；结果进 `report.json` 的 `hub_check: [{type, id, indegree, changed, files（前 10）, ok}]`。正式库 10-09：`8rlcsybg2hhl`（入度 17,540）、`d59frnrt4lxc`（29,218）、`hixhd2h9bdqq`（380）各牵动 2 档。

**`report.json` 的键**：`contract`、`root`、`records`、`entries`、`files_total`、`pages`、`hubs`、`hub_threshold`、`sidecars_ignored`、`load_problems`、`dangling`（每类 `{count, sample（前 50）}`）、`source_fields`、`legacy_vs_rebuilt`、`notes`、`self_check_errors`（前 200）、`self_check_error_count`、`classification`、`hub_check`（有时）、`fatal`、`index`（`{files, entries, drift_vs_repo_index}`）。不属契约，可随时增减。

---

## 十一、契约版本与改契约的规矩

**契约**：本档〈二〉到〈九〉的目录布局、字段名、取值形状、分页规格、键表形状，网站与 bim 可以直接依赖。契约版本写在 `report.json` 的 `contract`（`CONTRACT` 常量）。

| 版本 | 日期 | 变化 |
|---|---|---|
| 1 | 2026-10-07 | 基础契约（overview#458）：`entry/`、`members/`、`catalog/`、`related/`、`lineage/`、`_hubs.json`、`classific.json`、`index/`；Work／Book／Collection／Entity 的基础派生字段 |
| 2 | 2026-10-07 | 纯增量：专名派生字段（dynasty、reign、office、官署、place 各字段，people 与 Work 的 `_dynasty_id`／`_dynasty_candidates`）与 `dynasty_reign_keys.json`、`office_keys.json`、`place_keys.json`（overview#464、#458） |
| 3 | 2026-10-08 | 纯增量：Book、Collection 加 `_related`（`related_books`／`related_collections` 两侧并集）（overview#458） |

**改契约的规矩**：任何增删、改名、改形状、改分页大小，**先在 overview#458 留言通知网站经理，等对方回复后再合**；只新增可选字段也算改契约，同样要先通知。改动时：`CONTRACT` 加一、本档〈十一〉表加一行、记入 [CHANGELOG.md](CHANGELOG.md)，并在同一个提交里用 `build/make_contract_sample.py` 重生 `build/contract-sample/`。
`report.json` 的内容、`notes` 的措辞不属契约。

**样例包** `build/contract-sample/`（进 git）：正式库 29 条＋草稿库 8 条的 `entry/`、对应 `index/` 行、各自一页 `members/`／`catalog/`／`related/`、`lineage/`、`_hubs.json`、`classific.json`；覆盖丛书、合集、混合丛编、子丛编、志书、跨作品关系（含分页）、分类有无、枢纽、源流、草稿指正式、专名派生。每条入选理由见 `MANIFEST.json`。规则固定、可重跑。

---

## 十二、待 build 统一

以下是代码现状里自相矛盾或易误读之处。文档照现状写；读者按现状读，build 改了之后同步改本节与〈五〉〈八〉。

| # | 现状 | 影响 |
|---|---|---|
| 1 | **朝代：两个字段，有意不同**（overview#496 §六-1，目录经理 10-09 定）：`index/` 的 `dynasty` 是**撰人朝代**（第一个有朝代的作者优先，再顶层）；卡片 `dyn`、`_hubs.json` 的 `dyn`、Work 的 `_dynasty_id` 是**成书朝代**（顶层 `dynasty` 优先，再第一个有朝代的作者）。正式库 10-09 实测 216 部 Work 两者不同：多为作者朝代更细（元末明初／明）或成书与撰人本异（今本竹書紀年 南朝梁／明），故不统一。bim `entry_extractor`、ui `storage.ts` 同此取法 | 搜索列表显示撰人朝代，页面显示成书朝代；读者勿当作同一字段 |
| 2 | **年份取法不一**：`index/` 的 `sort_year` 取 `dating.year` 优先、再 `year_range[0]`（且要求 `year_range` 恰两项）；卡片 `y` 与 `_books`／`_siblings` 排序取 `year_range[0]` 优先、再 `year` | 两者都有的 Book，列表排序年与卡片年不同 |
| 3 | **有无全文／影像取法不一**：`index/` 的 `has_text`／`has_image` 只看本条 `resources`（认旧 `type:"text+image"`），不看源档 `_has_text`，Work 也不并其 Book；entry 的 `_has_text`／`_has_image` 与卡片 `txt`／`img` 看源档旧值、Work 并其 Book，但旧单值 `type` 只按原值比，`"text+image"` 不算 `text` 也不算 `image`。正式库 10-09：Work 条目 `has_text` 11,511 vs `_has_text` 12,003；`has_image` 18,926 vs `_has_image` 20,540 | 搜索筛「有全文」与页面徽标不一致 |
| 4 | **`promoted_to` 范围不一**：entry 里只有 Work、Book 出 `promoted_to`；`index/` 四类都出 | 已升格草稿 Collection（目前草稿库无 Collection）、Entity 的页面拿不到正式 id，要读 `index/` |
| 5 | **`_lineage_graph_ref` 可能指向不存在的文件**：Book 只要所属 Work 下任一 Book 的 `lineage.derived_from`／`related_to` 非空就出；Work 的版本图要求至少一项是对象且带 `ref`／`book_id`，否则不出文件。正式库 10-09 实测 180 处引用全部有对应文件 | 读者打开 `lineage/` 文件要容忍 404 |
| 6 | **`_hubs.json` 的 `t` 可能是 `"b"`**：代码按类型首字母取 `t`；现行入度只计 Work、Collection、Entity，Book 不会成为枢纽，实测只有 `w`／`c`／`e` | 读者应把 `t` 当开放值 |
| 7 | **新建 `index/` 文件尾无换行**：输出目录里还没有该分片时按缩进 2、无尾换行写出（如新的 `--out` 目录）；仓内已有分片沿用其原格式 | 与全库「文件尾一个换行」约定不一 |
| 8 | **place 级别「都」在 `PLACE_RANK` 里缺失**：`level` 枚举有 `都`，`PLACE_RANK` 没有，按 9（最高）计，永远不会被选为「最低一级」的默认候选；`監` 在表内 | 涉及「都」的同名地名默认候选可能不标 |
| 9 | **holder 取法不一**：卡片 `holder` 对象取 `name`、无则 `text`；`index/` 只取 `name` | 只写 `current_location.text` 的 Book 搜索列表无馆藏 |
| 10 | **校验口径**：`.claude/qa/verify.py` 的 `MEMBER_TYPES` 含 `"Collection"`，build 只产出 `"Work"`／`"Book"`／`"mixed"`；verify 还允许源档写 `_edition_count`（只核值），build 把它列为旧派生字段（`--strict` 时算失败） | 两个校验器对同一份数据结论不同 |
| 11 | **Work 卡 `cls` 有两种类型**：有 `classification/` 时是节点 id 字符串，没有时退回 `[l1, l2]` 数组（正式库、草稿库都已有 `classification/`，实际只出字符串） | 读者按字符串读即可 |

---

## 十三、沿革

早期设计（overview 的 F2-3、F4-2）里与现行实现不同的写法——`_members_total`、关联项的 `rel`／`dir` 短键、150／300 的分页大小、`_incoming`、Entity `_works` 分页、`_catalogs` 用 `source_bid` 作键——均已作废，以本档为准。
