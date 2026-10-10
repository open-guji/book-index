# Work（作品）

一部作品的抽象知识内容，不随版本而变。版本是 Book（[book.md](book.md)），一部书数个藏本＝一个 Work、数个 Book。
什么样的东西立一条 Work、原典与注本怎么分、同题二条何时并，见 [cataloging-rules.md](cataloging-rules.md)。

字段表体例见 [README.md §八](README.md#八字段表体例)；共用对象（Author、IndexEntry、Resource 等）见 [common.md](common.md)。实测为 2026-10-08 两库全量普查（正式库 Work 119,527 条，草稿库 36,721 条）。

---

## 一、字段表

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | 必填 | 原生 | 记录 id | base36 小写；正式库 12 字符、草稿库 13 字符（见 README §四） | bim | `"d59f2mp0flz6"` |
| `type` | string | 必填 | 原生 | 记录类型 | 恒为 `"work"` | bim | `"work"` |
| `schema_version` | integer | 必填 | 原生 | 记录格式版本 | 恒为 `1` | bim | `1` |
| `title` | string | 必填 | 原生 | 规范题名 | 繁体 | 录入 | `"周易"` |
| `subtype` | string | 可选 | 原生 | 作品细类 | `book`（缺省，可省）｜`article`｜`poem`｜`chapter`，见 [§三](#三subtype) | 录入 | `"chapter"` |
| `additional_titles` | array<string> | 可选 | 原生 | 同书异名 | 字符串数组 | 录入 | `["春秋左氏傳"]` |
| `original_title` | string | 可选 | 原生 | 条目原题（与规范题不同时） | 原文照录 | 录入 | `"毛詩義問"` |
| `title_basis` | string | 可选 | 原生 | 改题的依据 | 自由文本 | 录入 | |
| `title_emendation` | object | 可选 | 原生 | 题名订补（志书原文有缺字、衍字时） | `{raw, emended?, fill?, status, basis}`；`status` ∈ `已補`｜`去衍空`｜`闕疑`；`fill` 为补入的字（可为 `null`） | 录入 | `{"raw":"康泓道人單道開傳","emended":"單道開傳","status":"已補","basis":"…"}` |
| `authors` | array<Author> | 条件：有责任者时必填 | 原生 | 责任者 | 见 [common.md〈Author〉](common.md#一authorauthors-的元素)；**`role` 必填** | 录入 | `[{"name":"蘇軾","role":"撰","dynasty":"北宋"}]` |
| `dynasty` | string | 可选 | 原生 | 作品成书朝代（显示用） | 规范朝代名，见 [common.md〈朝代与时代轴〉](common.md#九朝代与时代轴) | 录入 | `"北宋"` |
| `dynasty_basis` | string | 条件：有 `dynasty` 时宜写 | 原生 | 朝代判定依据 | 自由文本，宜以代码起首（同上） | 录入 | `"author_propagation"` |
| `period` | string | 可选 | 原生 | 时代轴 | 12 值，见 common.md | 录入 | `"song"` |
| `period_basis` | string | 条件：有 `period` 时必填 | 原生 | 判定依据 | 自由文本 | 录入 | `"據 authors[0].dynasty「北宋」"` |
| `period_upper` | string | 可选 | 原生 | 时代上限 | 12 值 | 录入 | `"song"` |
| `period_upper_basis` | string | 条件：有 `period_upper` 时必填 | 原生 | 上限依据 | 自由文本 | 录入 | `"catalog_bound：…"` |
| `description` | Description | 可选 | 原生 | 面向读者的介绍 | 见 common.md | 录入 | |
| `juan_count` | object | 可选 | 原生 | 主计量 | `{number, unit?, description?}`，见 common.md〈计量〉 | 录入 | `{"number":10}` |
| `measures` | array<object> | 可选 | 原生 | 多维计量 | `[{number, unit, note?}]` | 录入 | `[{"number":10,"unit":"卷"}]` |
| `measure_info` | string | 可选 | 原生 | 计量显示文本 | 自由文本 | 录入 | `"十卷"` |
| `additional_works` | array<object> | 可选 | 原生 | 主体之外各自计卷的部分 | `[{book_title, n_juan?}]` | 录入 | `[{"book_title":"附錄","n_juan":1}]` |
| `publication_info` | object | 可选 | 原生 | 成书／刊行信息 | 见 common.md〈publication_info〉 | 录入 | `{"year":"明"}` |
| `loss_status` | string | 可选 | 原生 | 存佚：本书之文今日尚存几何 | `lost`｜`partially_extant`｜`extant`｜`undetermined`，见 [§二](#loss_status存佚) | 录入 | `"lost"` |
| `loss_status_basis` | string | 可选 | 原生 | 存佚判定依据 | 自由文本 | 录入 | |
| `loss_status_note` | string | 可选 | 原生 | 存佚说明（如查无辑本的过程） | 自由文本 | 录入 | |
| `authenticity` | string | 可选 | 原生 | 真伪：只在确定是伪书时写 | 唯一值 `forged` | 录入 | `"forged"` |
| `authenticity_basis` | string | 条件：有 `authenticity` 时必填 | 原生 | 判伪依据（引提要或解题原文，逐条可验） | 自由文本 | 录入 | |
| `indexed_by` | array<IndexEntry> | 可选 | 原生 | 被目录书／志书著录（本侧是被著录的一侧） | 见 [common.md〈IndexEntry〉](common.md#二indexentryindexed_by--emendated_by-的元素)；`source_bid` 须指向存在的志书 Work；顺序有意义，不可按内容去重 | 录入 | |
| `emendated_by` | array<IndexEntry> | 可选 | 原生 | 被考证／校勘类著作订正 | 同上 | 录入 | |
| `contained_in` | array<object> | 可选 | 原生 | 本作品收入哪些丛编（成员一侧；**Work∈Collection 的唯一存储侧**） | 每项 `{id, volume_index?, group?, details?}`，见 [§四](#四contained_in) | 录入 | `[{"id":"8rlcsybg2hhh","volume_index":"第6卷","details":"叢編原序 15"}]` |
| `related_works` | array<object> | 可选 | 原生 | 与其他记录的关系（规范方向一侧） | 每项 `{id, relation, note?}`；`relation` 只用 [§五](#五关联词表) 的「源档可写」词；**不写 `title`** | 录入 | `[{"id":"d59f2mp0flz4","relation":"contains_text_of"}]` |
| `preferred_book` | string | 可选 | 原生 | 推荐版本 | 本 Work 名下一个 Book 的 id（现存 0 条） | 录入 | |
| `version_graph` | object | 可选 | 原生 | 人工策展的版本传承图配置 | 见 [§六](#六version_graph) | 录入 | |
| `resources` | array<Resource> | 可选 | 原生 | 外部资源 | 见 common.md〈Resource〉 | 录入 | |
| `resource_groups` | object | 可选 | 原生 | 资源组说明 | 见 common.md | 录入 | |
| `sources` | array<Source> | 可选 | 原生 | 数据来源 | 见 common.md（现存 5 条，皆空数组） | 录入 | |
| `collection_scale` | object | 可选 | 原生 | 丛书类作品的规模（作为本库著录进度尺） | `{stated, books, source, indexed_in_库, note}`：`stated` 原文、`books` 所辑书数、`indexed_in_库` 库中已著录数（4 条） | 录入 | `{"stated":"五百九十三種七百三十八卷","books":593,…}` |
| `appendix` | array<object> | 可选 | 原生 | 附录说明 | `[{title, text}]`（1 条） | 录入 | |
| `current_location`、`page_count` | object | 可选 | 旧（暂留） | 零星在用（各 3 条，值皆为空），形状同 Book | 见 [legacy.md](legacy.md) | — | |
| `merged_in`、`merged_from`、`merged_into`、`merge_history` | — | 可选 | 原生 | 并条账 | 见 [common.md〈并条账〉](common.md#七并条账) | bim、录入 | |
| `ai_note`、`todo`、`review` | — | 可选 | 原生 | 共通字段 | 见 common.md〈共通管理字段〉 | 录入 | |
| `revision`、`revised_at`、`updated_at` | string | `revision` 正式库必填 | 原生 | 共通字段 | 见 common.md | bim | `"1.0.0"` |
| `_has_text`、`_has_collated` | boolean | 可选 | 已删 | 有全文／有整理本；源档不再写，产物由 build 从 resources＋book-text 推（check_v2 V01 报） | 见 [legacy.md](legacy.md) | build | `true` |
| 其余 `_` 起首 | — | **源档不写** | 派生 | `_books`、`_edition_count`、`_related`、`_catalogs`、`_authors`、`_collections`、`_classifications` 等 | 见 [derived.md](derived.md) | build | |
| ~~`books`~~ | — | **不写** | — | 版本列表：由 `Book.work_id` 反查 | — | — | |
| ~~`classification`~~ | — | **不写** | — | 分类：写在 `classification/` 类档 | 见 [classification.md](classification.md) | — | |

### 示例

```json
{
  "schema_version": 1,
  "id": "1evd0000000ab",
  "type": "work",
  "title": "周易鄭玄注",
  "authors": [{"name": "鄭玄", "role": "注", "dynasty": "東漢", "entity_id": "1j9…"}],
  "dynasty": "東漢",
  "period": "qin-han",
  "period_basis": "據 authors[0].dynasty「東漢」",
  "juan_count": {"number": 9},
  "measure_info": "九卷",
  "loss_status": "partially_extant",
  "indexed_by": [
    {"source": "隋書經籍志", "source_bid": "1ev…", "title_info": "周易九卷後漢大司農鄭玄注", "summary": "…", "section": "經部/易"}
  ],
  "related_works": [{"id": "1evl7l48e27ls", "relation": "contains_text_of"}],
  "revision": "1.0.0",
  "revised_at": "2026-10-07"
}
```

它在 `_build/entry/1evd0000000ab.json` 里会多出 `_related`（含《周易》题名、方向 `out`）、`_catalogs`（隋志的题名与朝代）、`_authors`（鄭玄的 Entity 摘要）、`_classifications`（若在某类档里）等；《周易》的产物里则出现一条方向 `in` 的 `text_carried_by` 指向本条——**《周易》的源档一个字不动**。

---

## 二、各字段细则

### `loss_status`（存佚）

只有一根轴：**本书之文今日尚存几何**。字段不存在＝今存或未考，不必说明。

| 值 | 中文 | 界说与判准 |
|---|---|---|
| `lost` | 全佚 | 本书之文今日无一字存——志书著录其名而已，类书无所引，后人无所辑 |
| `partially_extant` | 残存 | 确有本书之文存世而非全帙。传本残卷、类书所引之佚文、后人之辑本，三者都算——凡今日还能读到本书几句的就是。泛言「残缺」而不知所存何文者不足 |
| `extant` | 今存 | 全帙尚存。只在需要推翻既有推定时才明写 |
| `undetermined` | 未详 | 考过而不能定。与「字段不存在」有别——后者是未考 |

**有辑本即 `partially_extant`**：凡有文存世就是 `partially_extant`，一字不存才是 `lost`。「传本是否断绝」由辑佚档之有无导出，不入本枚举：

| 现状 | `loss_status` | 辑佚档 |
|---|---|---|
| 全帙传世 | `extant` 或不写 | 无 |
| 传本尚在而缺卷 | `partially_extant` | 无 |
| 传本断绝，赖类书征引／后人辑佚 | `partially_extant` | **有** |
| 一字不存，唯志书存其名 | `lost` | 无 |

- 志书原文的「佚」字**不即** `lost`。目录学传统之「佚」指传本失传，与本字段之轴不同；志书所判记在 `indexed_by[].attested_status_raw`，本字段记本库之判，二者分立。
- 残存不用 `fragmentary`：西方书目学的 fragmentary 专指「只靠他书征引之断片存世」，而 `partially_extant` 兼含传本残卷与征引断片。
- **不入本枚举**的三件事：**出土**是路径不是状态（原书久佚而赖简帛复见者，状态即 `extant` 或 `partially_extant`，出土之事由该 Work 的 Book 与「出土简帛」Collection 承载）；**有辑本**是补救不是状态；**真伪**是另一轴，由 `authenticity` 承载。

### `authenticity`（真伪）

```json
"authenticity": "forged",
"authenticity_basis": "（引提要或解题原文，逐条可验）"
```

**只有一个值 `forged`，且只在确定是伪书时才写；省略即无此疑义**——这是绝大多数。不设 `genuine`（设了就得给全库填）。只标异常，不标正常。

「舊題某某撰」不是伪书，不要往这个字段里塞：

| | 说的是什么 | 怎么记 |
|---|---|---|
| 舊題撰人 | 撰人之题不确，书本身不假 | `authors[].role = "舊題撰"`，舊題撰人与实际撰人并列 |
| 伪书 | 书是后人伪造而托之于古 | `authenticity: "forged"` |

如《西京雜記》`1ev3bcikfdiww`：`authors[0]` 劉歆·漢·舊題撰，`authors[1]` 葛洪·東晉·撰。二人并列，一层不丢。实测：舊題撰人 327 条，真伪书约 100 条。

与 `period`：`period` 一律标成书时代（实际撰人之时），`period_basis` 写明「舊題某某（某代），實某代作，據某某」。如《關尹子》：`period: song`、`authenticity: forged`、`authors[0]` 尹喜·先秦·舊題撰——三层信息各得其所。判伪的方法（判伪三戒）见 [cataloging-rules.md](cataloging-rules.md)。

### `additional_titles`

同书的其他常用书名（别名、异称）：如《左傳》＝《春秋左氏傳》＝《左氏傳》＝《春秋左傳》；《春秋古經》＝《古文春秋經》。与 `Entity.alt_names` 平行，但 Work 只存名称字符串，不分类型。检索应匹配 `title`＋`additional_titles` 全集。

---

## 三、`subtype`

| 值 | 含义 | 例 |
|---|---|---|
| `book`（缺省） | 独立成书的作品 | 《漢書》《論語》《紅樓夢》 |
| `article` | 单篇文章 | 《陳情表》《岳陽樓記》 |
| `poem` | 诗词 | 《春望》《水調歌頭·明月幾時有》 |
| `chapter` | 书中被单独拎出研究、索引的章节 | 《漢書·藝文志》《史記·太史公自序》 |

判定：
- 缺省即 `book`，可不写；志书录入的绝大多数是书。
- 明确是书中一章且被单独索引（有 `related_works` 的 `part_of`）→ `chapter`。
- 单位是「篇」且数为 1、或属集部别集的单篇文章 → `article`。
- 单位是「首」或为诗词 → `poem`。
- `chapter` 按需创建：不要把《漢書》每一篇志都拆成 Work，只有被单独研究或作为目录书索引的才建（《漢書·藝文志》要被引作 `source`，所以单独建；《漢書·地理志》未被索引就不建）。

实测正式库：缺省 116,544、`article` 2,525、`poem` 320、`chapter` 110、显式 `book` 28。

---

## 四、`contained_in`

本作品收入哪个丛编。**成员关系的数据跟着成员走**：丛编档里不列成员，丛编的成员列表由 build 从成员一侧反查（`Collection._members`）。丛编增减成员不改丛编档。

| 字段 | 类型 | 必填 | 含义 | 取值 | 例 |
|---|---|---|---|---|---|
| `id` | string | 必填 | 丛编 id | Collection id | `"8rlcsybg2hhh"` |
| `volume_index` | integer｜array<integer>｜string | 可选 | 本作品在该丛编里的册次／卷次 | 整数、整数数组，或原文字符串（如 `"第6卷"`） | `3` |
| `group` | string | 可选 | 本作品在该丛编里所属的组 | 丛编内自定的组键（实测：`hanzhi_yiwenzhi`、`non_hanzhi`） | `"hanzhi_yiwenzhi"` |
| `details` | string | 可选 | 说明文字 | 自由文本；**`叢編原序 N`**（N 为整数）表示本作品在丛编原书中的次序，build 据以给成员排序 | `"叢編原序 15"` |

Book 的 `contained_in` 多一个 `sub_items`，见 [book.md](book.md)。

---

## 五、关联词表

`related_works[]` 的每一项 `{id, relation, note?}`：`id` 是对方记录（Work，`collected_in` 时也可是 Collection）。

**存储方向决定源档写不写这个词。** 成对关系只在规范方向一侧写一次，反向词只出现在构建产物的 `_related` 里（`direction: "in"`）。对称关系存 id 较小的一侧。规划中的写入口 `bim link A B <relation>`（按规范方向与小 id 规则落笔）尚未实现；现在手写或脚本写，由 `check_v2.py` V04／V05／V07／V13 把关。

### 成对关系（6 对）

| 源档写（规范方向） | 反向词（只在产物里） | 含义 |
|---|---|---|
| `part_of`（部分 → 整体） | `has_part` | 整体与部分：**确系同一本书之内**的篇卷，如《繫辭》之于《周易》。版本附属部帙（外集、别集、附录之属）不走此路，见 cataloging-rules.md〈版本附属部帙〉 |
| `studies`（注本、研究 → 原典） | `studied_by` | 本书研究、注解、考证某书 |
| `contains_text_of`（承载者 → 被承载的原典） | `text_carried_by` | 本书载有某书之全文（注本载原典之文；一部原典下可有近千承载者，所以不存在原典一侧） |
| `preceded_by`（续作 → 前作） | `followed_by` | 续作与前作 |
| `adapted_from`（改编者 → 原作） | `has_adaptation` | 改编自 |
| `pseudepigraph_of`（伪托之作 → 所托之书） | `has_pseudepigraph` | 伪托于某书 |

### 对称关系

| 词 | 存储 | 含义 |
|---|---|---|
| `related` | 存在 id 较小的一侧（字符串比较）；另一侧由 build 在 `_related` 补出同词 | 泛关联，语义不明确时的兜底；两侧原各有 note 者拼成一条 `note`（以「；」分隔） |

### 单向关系（6 个，只写一侧，无反向词）

| 词 | 含义 |
|---|---|
| `collected_in` | 收入某汇编（指 Work 或 Collection） |
| `derived_from` | 由某书辑出、改编而成 |
| `excerpted_from` | 摘录自 |
| `source_of` | 为某书之所本 |
| `suspected_same` | 疑与某条同书，待考 |
| `same_entry` | 书目中同一条著录 |

单向词的对面在产物 `_related` 里以**原词**、`direction: "in"` 出现（不另生成 `_incoming`）。需要在对面留痕时**不要**手写反向。

### 不写的词

- 反向词 `has_part`、`studied_by`、`text_carried_by`、`followed_by`、`has_adaptation`、`has_pseudepigraph`（`check_v2.py` V04）。
- 已归并的旧词：`commentary_on` → `studies`，`related_to` → `related`（V05）。
- 不在上表的词一律不写（V13 报「未识别」）；要加新词先在 overview#451 提。
- `related_works[].title` 不写（V06）：对方题名由 build 取其现行 `title` 回填。

实测正式库（项数）：`contains_text_of` 4,211、`collected_in` 3,374、`related` 1,178、`studies` 339、`part_of` 238、`preceded_by` 26、`derived_from` 9、`same_entry` 8、`adapted_from` 5、`pseudepigraph_of` 4，其余个位数。

---

## 六、`version_graph`

人工绘制的版本传承图配置（正式库 6 条：《金瓶梅》《西遊記》《三國演義》《封神演義》《水滸傳》《紅樓夢》）。网站据它画图；图中的 Book 节点与边来自各 Book 的 `lineage`（build 汇成 `lineage/<work_id>.json`，见 [derived.md](derived.md)），本字段只管分组、着色、假想节点与显示集合。

| 字段 | 类型 | 含义 |
|---|---|---|
| `enabled` | boolean | 是否启用 |
| `title`、`description` | string | 图题、说明（含依据的研究） |
| `layout` | string | 布局方向，实测皆为 `"LR"` |
| `groups` | array<object> | 分组 `[{id, label, color, description?}]`；`color` 为 `#rrggbb` |
| `node_groups` | object | Book id → 组 id |
| `hypothetical_nodes` | array<object> | 假想节点（已佚的祖本等）`[{id, label, year?, year_range?, year_uncertain?, group?, derived_from?, note?}]`；`id` 以 `h_` 起首 |
| `excluded_books`、`excluded_reason` | array<string>、string | 不入图的 Book 及原因 |
| `default_collection` | string | 默认显示集合的键 |
| `collections` | object | 显示集合 `{<键>: {label, description, groups?}}`（实测键：`core`、`all`、`printed`） |
| `core_books`、`core_hypotheticals` | array<string> | 核心模式显示的 Book、假想节点 |

---

## 七、不写在 Work 里的东西

| 东西 | 在哪 |
|---|---|
| 版本列表 | 各 Book 的 `work_id`；产物 `_books`、`_edition_count` |
| 分类 | `classification/<分类法>/members/<节点>.json`；产物 `_classifications` |
| 作者「写了哪些书」 | `authors[].entity_id`；Entity 产物 `_works` |
| 关系的反向一侧、对方题名 | 产物 `_related` |
| 丛编成员列表 | 成员一侧的 `contained_in`；丛编产物 `_members` |
| 升格后的正式 id | `promotions/`；产物与索引里的 `promoted_to` |
| 整理本、辑佚档 | book-text 仓，见 [text-files.md](text-files.md) |
