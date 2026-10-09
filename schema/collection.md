# Collection（丛编）

一部丛书、丛编或影印汇编。**成员只有一种来源：成员一侧的 `contained_in`**（`Book.contained_in[].id`、`Work.contained_in[].id`、子丛编的 `Collection.contained_in[].id`）。丛编档里不列成员；成员列表、计数、子丛编由 build 生成。

字段表体例见 [README.md §八](README.md#八字段表体例)；共用对象见 [common.md](common.md)。实测为 2026-10-08 正式库全量（85 条；草稿库目前没有 Collection）。

---

## 一、字段表

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | 必填 | 原生 | 记录 id | | bim | `"8rlcsybg2hhf"` |
| `type` | string | 必填 | 原生 | 记录类型 | 恒为 `"collection"` | bim | |
| `schema_version` | integer | 必填 | 原生 | 记录格式版本 | 恒为 `1` | bim | `1` |
| `subtype` | string | 必填 | 原生 | 丛编细类 | `work_collection`｜`book_collection`，见 [§二](#二subtype) | 录入 | `"book_collection"` |
| `title` | string | 必填 | 原生 | 题名 | 繁体 | 录入 | `"武英殿聚珍版叢書"` |
| `additional_titles` | array<string> | 可选 | 原生 | 异名 | | 录入 | `["廣政石經","孟蜀石經"]` |
| `description` | Description | 可选 | 原生 | 介绍 | 见 common.md | 录入 | |
| `authors` | array<Author> | 可选 | 原生 | 编者、主持者 | 见 common.md；**`role` 必填** | 录入 | `[{"name":"紀昀等編","role":"編"}]` |
| `editors` | array<object> | 可选 | 原生 | 现代编辑者 | `[{name, role, dynasty?}]` | 录入 | `[{"name":"張元濟","role":"主編"}]` |
| `publisher`、`publish_year` | string | 可选 | 原生 | 出版者、出版年（现代影印丛编；各 3 条） | 自由文本 | 录入 | `"廣西師範大學出版社"` |
| `publication_info` | object | 可选 | 原生 | 出版信息 | 见 common.md | 录入 | |
| `dating` | object | 可选 | 原生 | 刊刻年代 | 形状同 Book，见 common.md | 录入 | |
| `edition` | string | 可选 | 原生 | 版本名 | | 录入 | `"武英殿本"` |
| `current_location` | Location | 可选 | 原生 | 现藏地 | | 录入 | |
| `holder` | string | 可选 | 原生 | 现藏机构名 | | 录入 | `"天津市圖書館"` |
| `count` | object | 可选 | 原生 | 应收总数：卷／册／种／函分列 | `{juan, ce, zhong, han, source}`，见 [§三](#三count) | 录入 | `{"juan":null,"ce":820,"zhong":24,"han":null,"source":"…"}` |
| `juan_count`、`page_count`、`measures`、`measure_info` | — | 可选 | 原生 | 规模 | 见 common.md〈计量〉 | 录入 | |
| `total_works`、`total_volumes` | integer | 可选 | 原生 | 所收作品数、册数（旧写法，与 `count` 并存） | 正整数 | 录入 | `42` |
| `sections` | array<object> | 可选 | 原生 | 丛编的分部 | `[{name}]` | 录入 | `[{"name":"經部"}]` |
| `contains` | array<object> | 可选 | 原生 | 本丛编的**结构组成部分**（圣谕、进表、总目、选印来源等），**不是成员** | 见 [§四](#四contains) | 录入 | |
| `work_id` | string | 可选 | 原生 | 本丛编整体对应的伞状作品（8 条） | Work id | 录入 | 《十三經注疏》 |
| `contained_in` | array<object> | 可选 | 原生 | 本丛编（子丛编）收在哪个上级丛编 | 每项 `{id}`；**对象形**，与 Book、Work 一致（现存 19 项字符串形为旧写法，见 [legacy.md](legacy.md)） | 录入 | `[{"id":"8rlcsybg2hih"}]` |
| `indexed_by` | array<IndexEntry> | 可选 | 原生 | 被目录书著录 | 见 common.md | 录入 | |
| `related_books` | array<string> | 可选 | 原生 | 对称关联的 Book（存 id 较小一侧） | Book id 字符串数组 | 录入（V07 把关） | |
| `related_collections` | array<string> | 可选 | 原生 | 对称关联的丛编（存 id 较小一侧） | Collection id 字符串数组；只能写丛编 id | 录入（V07 把关） | `["8rlcsybg2hi6"]` |
| `resources` | array<Resource> | 可选 | 原生 | 外部资源 | 见 common.md | 录入 | |
| `sources`、`ai_note`、`todo`、`review` | — | 可选 | 原生 | 共通字段 | 见 common.md | 录入 | |
| `revision`、`revised_at`、`updated_at` | string | `revision` 必填 | 原生 | 共通字段 | 见 common.md | bim | `"1.0.0"` |
| 一切 `_` 起首 | — | **源档不写** | 派生 | `_members`、`_member_pages`、`_member_count`、`_member_type`、`_children`、`_related`、`_has_image` 等 | 见 [derived.md](derived.md) | build | |
| ~~`books`~~、~~`contained_works`~~ | — | **不写** | — | 成员列表：由成员的 `contained_in` 反查 | — | — | |
| ~~`classification`~~ | — | **不写** | — | Collection 不分类 | — | — | |

**成员关系的数据跟着成员走**：册次（`volume_index`）、该书在本丛编里附带的子目（`sub_items`）、原序（`details` 里的 `叢編原序 N`）写在成员的 `contained_in[]` 项里；部类写在 `Book.section`。丛编增减成员**不改**丛编档，也不 bump 丛编的 `revision`。

---

## 二、`subtype`

| 值 | 含义 | 例 |
|---|---|---|
| `work_collection` | 作品的丛编（抽象层，跨版本） | 《二十四史》《四書》《四大名著》《十三經》《十三經注疏》 |
| `book_collection` | 书籍的丛编（具体版本） | 《二十四史百衲本》《欽定四庫全書·文淵閣本》《武英殿聚珍版叢書》 |

判定：有具体出版年份（而非朝代）、具体现藏地、影像类资源（扫描件）→ `book_collection`；只有作品列表、无具体版本信息 → `work_collection`。一个作品丛编（《二十四史》）下可以挂多个书籍丛编（百衲本、武英殿本），后者的 `contained_in` 指向前者。实测：`book_collection` 69、`work_collection` 16。

---

## 三、`count`

网站「收录进度」要用的应收总数。

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `juan` | integer｜null | 必填 | 卷数 |
| `ce` | integer｜null | 必填 | 册数 |
| `zhong` | integer｜null | 必填 | 收书种数 |
| `han` | integer｜null | 必填 | 函数（多见于《四庫全書》写本按函装箱） |
| `source` | string | 必填 | 数据取自何处（哪个既有字段、`description` 原文哪句话、是否约数、是否经过订正） |

- 四项互不隐含、各自可空；**至少一项非空才写本字段**。未知一律 `null`，不可用 0 占位（0 隐含「不分卷」等实际语义）。
- 约数（原文带「約」「餘」）可照填并在 `source` 注明；多说并存或量小而不确定（如「十餘種」）则留空，不臆定。
- 与 `juan_count`、`total_works`、`total_volumes` 不是一件事，不互相取代：`juan_count` 曾被拿来塞册数（百衲本「820」实为 820 册），发现后订正为空、正确册数记到 `count.ce`；各字段与 `description` 原文矛盾时，本字段以原文为准。
- 现存 4 条 `count` 为 `null`（不合「至少一项非空才写」），列入修正方案。

---

## 四、`contains`

丛编本身的结构组成部分，**不是成员**。

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `type` | string | 必填 | 部分的类型 | `subwork`（附属子作品）｜`preface`（卷首前置文字：圣谕、进表、凡例等）｜`main_corpus`（正书主体）｜`per_book_tiyao`（每书卷首提要）｜`selected_from`（选印来源）｜`absent`（应有而缺） |
| `title` | string | 必填 | 部分名称 | `"聖諭"`、`"進表"`、`"欽定四庫全書總目"` |
| `scope` | string | 必填 | 范围 | 自由文本：`"1 卷"`、`"卷首前置"`、`"每書卷首嵌入"` |
| `position` | string | 可选 | 位置 | `前置`｜`後置` |
| `work_id`、`book_id`、`collection_id` | string | 可选 | 对应的库内记录 | id |
| `own_work_id` | string | 可选 | 本部分作为独立作品时的 Work id | id |
| `related_work_id` | string | 可选 | 相关作品（如该部分是某书的一部分） | id |
| `categorization` | string | 可选 | 分类方式说明 | `"按經、史、子、集四部四十四類分次"` |
| `note` | string | 可选 | 说明 | 自由文本 |
