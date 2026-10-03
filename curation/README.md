# curation/ —— 人工策展数据

放网站要用、又不属于任何一条 Work／Book／Entity 记录的**人工选编数据**。目前只有 `read-home.json`。

## read-home.json（阅读首页策展，overview#321／#308 B 块）

给 `/read` 首页用。生成脚本 `build_read_home.py`（选目、导语、分组、版本系统写在脚本顶部常量里，能算的都现算）。

```
python3 curation/build_read_home.py --text-root ../book-text          # 重新生成
python3 curation/build_read_home.py --text-root ../book-text --check  # 只比对
```

**可读**的口径（#308 定）：book-text 里有 `<Work|Book>/<c1>/<c2>/<c3>/<id>/manifest.json` 的条目；
不分整理本／转录全文，统称「文本」。**可读集会随 book-text 入库增长，重新生成即可刷新**
（文件顶部 `readable` 记生成时的数量）。

### 顶层

| 键 | 含义 |
|---|---|
| `schema` | 固定 `read-home/1`；字段有增删时升号 |
| `readable` | `{total, work, book}` 生成时的可读条目数（Work／Book 各多少） |
| `picks` | 推荐阅读，6 部，按 `order` |
| `topics` | 专题分组，数组，**按稿子顺序**：史志目录、书目与考证、丛书、档案、史书与史料、诗文集、子书与辑佚 |
| `famous` | 名著与版本，6 张作品卡 |
| `not_readable_dropped` | 稿里点了名、但当前**不可读**所以没放进 `topics` 的条目（见下）。网站不用读它，给维护者看 |

### picks[]

`order`、`id`、`kind`（`Work`／`Book`，该 id 是什么记录）、`title`（记录原题名）、`type_label`（作品类型，卡片标签）、
`slip`（竖排题签短名）、`blurb`（一句导语）。`kind=Book` 的另有 `edition`（版本名）、`work_id`。
六部的 id 都核过存在且可读；导语中的事实（回数、篇数、卷数、部数）对过库内 description／manifest。

### topics[]

`key`、`label`、`layout`（`shelf` 书脊架／`list` 平铺）、`items[]`。每项：

| 字段 | 含义 |
|---|---|
| `id` | **进组 id**：该条目可读就用它自己；条目是 Book 而它自己无文本、所属 Work 有文本（#307 迁移后文本挂在 Work 上）时改用 **Work id**，并记 `via_book`（稿里原来点的 Book id）。只有 Book 可读、没有可读 Work 的，用 Book id（现在没有这种） |
| `kind` | `Work`／`Book` |
| `title` | 记录原题名（繁体，同一题名多部时要靠作者区分，如五部《補晉書藝文志》） |
| `text_count` | 这部作品站内有几份文本 ＝ 作品自身 manifest 的版本数 ＋ **同 `work_id` 且可读**的 Book 的 manifest 版本数。Book 项只算自己的 |
| `via_book` | 可选，见上 |
| `period_of`、`orig` | **仅 `shizhi`（史志目录）**：`period_of` 所志朝代（劉宋＝南朝宋，宋＝赵宋；补志里撰者看 Work 的 `authors`）；`orig` 是否正史原志（false＝后人补撰） |

`shizhi` 的 `items` 已按所志朝代时序排好（书脊架顺序），同朝代多部的相对顺序照稿。

### famous[]

每张卡一部作品：`work_id`、`title`（卡片显示名）、`record_title`、`work_readable`（作品自身有无文本）、
`own_texts[]`（作品自身的文本：`key`／`kind`／`label`／`source_name`，卡片上标 `source_name`，如「開源古籍」）、
`text_count`（同 topics 口径）、`edition_count`（库内该作品名下全部 Book 数，**不只可读的**）、`systems[]`。

`systems[]`：`name`（版本系统名，如「脂本」「程本」；司馬法只有一类，为空串）、`editions[]`：
`book_id`、`short`（版本短名，如「甲戌本」）、`readable`（该 Book 自己有无文本；false 的只是目录里有这个本子，
站内读不了，卡上可画成不可点的签）、`edition`（记录里的 `edition` 原文）。

**版本系统名与短名从哪来**：book-index 有各 Book 的 `lineage`（承袭关系、`alias` 别名），但**没有「系统」这一层的名字**，
所以系统名照稿手工维护在 `build_read_home.py` 的 `FAMOUS`；短名对过 `Book.edition`／`lineage.alias`。以后要改，改脚本重新生成。

### 当前数据口径与已知缺口（2026-10-01 生成）

- 可读 7,130（Work 7,126＋Book 4）。稿里的 78 部专题，当前可读 **75 部**，不可读的 3 部列在 `not_readable_dropped`：
  《四庫全書總目提要補正》、《明實錄·紅格鈔本》、《楚辭》（Book 与所属 Work 都还没有 manifest，等文本入库）。
- 稿里 39 部「可读 Book」，迁移后只有 4 个 Book 有 manifest（甲戌本、程甲本、程乙本、貫華堂本）；其余书的文本现在挂在 Work 上，
  所以专题里多数条目是 Work id（`via_book` 记着原 Book）。`famous` 里没有 manifest 的 Book 版本 `readable=false`。
- 红楼梦这个 Work 本身没有文本（`work_readable=false`），可读的是 3 个 Book。

## 校验

`tests/test_read_home.py`：结构、id 存在、无重复、picks 6 部、史志书架 28 部且带 `period_of`／`orig`、famous 的 Book 确属其 Work。
设环境变量 `BOOK_TEXT_DIR` 指向 book-text 后，再核「进组 id 均可读」和 `text_count` 与 manifest 一致。
