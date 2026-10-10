# Book（版本）

一部作品的一个具体版本、藏本或数字化本。**Book 是「它属于哪部作品」「它收在哪个丛编」这两条关系的唯一存储侧**：Work 页的版本列表、丛编页的成员列表都由 build 从 Book 反查。

字段表体例见 [README.md §八](README.md#八字段表体例)；共用对象见 [common.md](common.md)。实测为 2026-10-08 两库全量普查（正式库 Book 54,477 条，草稿库 68,144 条）。

---

## 一、字段表

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `id` | string | 必填 | 原生 | 记录 id | base36 小写；正式库 10 字符、草稿库 13 字符（见 README §四） | bim | `"988g9cugwd"` |
| `type` | string | 必填 | 原生 | 记录类型 | 恒为 `"book"` | bim | `"book"` |
| `schema_version` | integer | 必填 | 原生 | 记录格式版本 | 恒为 `1` | bim | `1` |
| `title` | string | 必填 | 原生 | 版本题名 | 自由文本，繁体 | 录入 | `"周易正義"` |
| `work_id` | string | 必填 | 原生 | 所属作品（**Work↔Book 的唯一存储侧**） | Work id；草稿 Book 可指正式 Work | 录入 | `"1evl7l48e27ls"` |
| `edition` | string | 可选 | 原生 | 版本名（文献学意义上「这是哪一个本子」） | 自由文本；不写成 `version` | 录入 | `"清乾隆間寫文淵閣四庫全書本"` |
| `edition_type` | string | 可选 | 原生 | 版本类型 | 11 值闭集，见 [§二](#edition_type)；推不出不写 | 录入 | `"刻本"` |
| `dating` | object | 可选 | 原生 | 刊刻／抄写年代 | 见 [common.md〈dating〉](common.md#六dating-与-publication_info) | 录入 | `{"era":"宋","reign":"紹熙","year":1193,"certainty":"inferred","source":"edition","basis":"…"}` |
| `publication_info` | object | 可选 | 原生 | 出版信息 | 见 common.md | 录入 | `{"year":"清乾隆間"}` |
| `contained_in` | array<object> | 可选 | 原生 | 收在哪些丛编（**Book∈Collection 的唯一存储侧**） | 每项 `{id, volume_index?, details?, sub_items?}`，见 [§三](#三contained_in) | 录入 | `[{"id":"8rl…","volume_index":[7,8],"sub_items":["周易略例"]}]` |
| `section` | string | 可选 | 原生 | 该版本在所属丛编中的部类（是 `contained_in` 的属性，不是分类） | 丛编自身的部类名，原文照录 | 录入 | `"經部/易類"` |
| `authors` | array<Author> | 可选 | 原生 | 版本层的责任者（刻者、批点者、序跋者等） | 见 common.md；**`role` 必填** | 录入 | |
| `juan_count` | object | 可选 | 原生 | 本版本的主计量 | `{number, unit?, description?, source?}` | 录入 | `{"number":10,"unit":"卷"}` |
| `measures`、`measure_info` | — | 可选 | 原生 | 多维计量、计量显示文本 | 见 common.md〈计量〉 | 录入 | |
| `volume_count` | object | 可选 | 原生 | 册数 | `{number, description?}` | 录入 | `{"number":32,"description":"32冊"}` |
| `page_count` | object | 可选 | 原生 | 页数 | `{number, description?, source?}` | 录入 | |
| `provenance` | array<object> | 可选 | 原生 | 馆藏：现藏机构＋索书号＋藏印 | 见 [§四](#provenance馆藏) | 录入 | |
| `physical_description` | object | 可选 | 原生 | 版本学著录：行款、装帧、尺寸、品相 | 见 [§五](#physical_description) | 录入 | |
| `base_edition` | array<object> | 可选 | 原生 | 底本／配补／参校（只在后出者一侧） | 见 [§六](#base_edition) | 录入 | |
| `lineage` | object | 可选 | 原生 | 版本源流（只在后出者一侧） | 见 [§七](#lineage) | 录入 | |
| `current_location` | Location | 可选 | 原生 | 现藏地 | 见 common.md〈Location〉 | 录入 | `{"name":"西安碑林"}` |
| `location_history` | array<object> | 可选 | 原生 | 递藏史、知见藏本 | 每项 `{location?, name?, item_id?, url?, description?, note?, source?, acckey?}` | 录入 | |
| `attached_texts` | array<object> | 可选 | 原生 | 本版本附带的其他文本 | `[{book_title}]` | 录入 | `[{"book_title":"周易略例"}]` |
| `description` | Description | 可选 | 原生 | 介绍 | 见 common.md | 录入 | |
| `additional_titles` | array<string> | 可选 | 原生 | 版本异名 | 字符串数组 | 录入 | |
| `indexed_by` | array<IndexEntry> | 可选 | 原生 | 按版本著录的书目（如通俗小说书目） | 见 common.md〈IndexEntry〉 | 录入 | |
| `resources` | array<Resource> | 可选 | 原生 | 外部资源 | 见 common.md；`id` 可取 `wikisource`（维基文库页面，`types:["text"]`） | 录入 | |
| `resource_groups` | object | 可选 | 原生 | 资源组说明 | 见 common.md | 录入 | |
| `related_books` | array<string> | 可选 | 原生 | 对称关联的其他 Book（存 id 较小一侧） | Book id 数组 | 录入（V07 把关） | `["96l2nocd1c"]` |
| `zhsy_id` | string | 可选 | 原生 | 中華再造善本编号 | 原文照录 | 录入 | |
| `metadata` | object | 可选 | 原生 | 来源系统原始字段透传，不规范化 | 实测键：`npm_item_id`（故宫统一编号）、`npm_acckey`、`nlc_bid`、`nlc_call_number` | 录入 | `{"npm_item_id":"平圖021465"}` |
| `sources` | array<Source> | 可选 | 原生 | 数据来源 | 见 common.md | 录入 | |
| `merged_from` | array<string> | 可选 | 原生 | 并入本条的 Book id | id 数组 | bim | |
| `appendix` | array<object> | 可选 | 原生 | 附录说明 | `[{title, text}]` | 录入 | |
| `ai_note`、`todo`、`review` | — | 可选 | 原生 | 共通字段 | 见 common.md | 录入 | |
| `revision`、`revised_at`、`updated_at` | string | `revision` 正式库必填 | 原生 | 共通字段 | 见 common.md | bim | |
| `_has_text`、`_has_collated` | boolean | 可选 | 已删 | 有全文／有整理本；源档不再写，产物 `_has_text`／`_has_collated` 由 build 从 resources＋book-text 推（check_v2 V01 报） | 见 [legacy.md](legacy.md) | build | |
| 其余 `_` 起首 | — | **源档不写** | 派生 | `_work`、`_siblings`、`_collections`、`_related`、`_lineage_refs`、`_derived_by`、`_has_image` 等 | 见 [derived.md](derived.md) | build | |

### 示例

```json
{
  "schema_version": 1,
  "id": "11q0000000abc",
  "type": "book",
  "title": "周易正義",
  "work_id": "1evl7l48e27ls",
  "edition": "清乾隆間寫文淵閣四庫全書本",
  "edition_type": "抄本",
  "dating": {"era": "清", "reign": "乾隆", "certainty": "attested", "source": "edition", "basis": "…"},
  "contained_in": [{"id": "8rl…", "volume_index": [7, 8], "sub_items": ["周易略例", "考證"]}],
  "section": "經部/易類",
  "resources": [{"id": "wikisource", "name": "維基文庫", "url": "https://zh.wikisource.org/wiki/周易正義_(四庫全書本)", "types": ["text"]}],
  "revision": "1.0.0"
}
```

**`edition` 与 `sources[].version` 是两回事**：`Book.edition`＝版本名；`sources[].version`／`processor_version`＝处理程序版本号（如 `"1.0"`），与书无关。曾有 276 条误写作 `version`，已归并。

---

## 二、`edition_type`

11 值闭集，推不出者**留空不写**（不设「不詳」占位值）：

| 值 | 说明 |
|---|---|
| `刻本` | 雕版印本（刊本、刻本、覆刻、翻刻等） |
| `抄本` | 钞本、写本 |
| `稿本` | 稿本 |
| `活字本` | 活字、聚珍 |
| `石印本` | 石印 |
| `鉛印本` | 铅活字排印；「排印」技法两可，光绪、宣统以后或纪年不详而明写「民國」者归此 |
| `影印本` | 影印、景印 |
| `套印本` | 套印 |
| `拓本` | 拓本 |
| `印刷本` | 现代出版社出版、非铅印的印本（胶印、平版、数码印刷）；与 `鉛印本` 之别在印刷技法非活铅字排版 |
| `其他` | 以上皆不合者 |

出土简帛整理本、碑刻残石、只有一个「清」字之类无法判别者留空，不强塞入某一类。正式库实测：刻本 26,532、抄本 12,950、稿本 2,328、鉛印本 1,933、石印本 769、活字本 747、印刷本 288、套印本 158、影印本 86、拓本 44，其余为 `其他`。

---

## 三、`contained_in`

| 字段 | 类型 | 必填 | 含义 | 取值 | 例 |
|---|---|---|---|---|---|
| `id` | string | 必填 | 丛编 id | Collection id | `"8rlcsybg2hhl"` |
| `volume_index` | integer｜array<integer>｜string | 可选 | 册次 | 整数、整数数组或原文字符串 | `[1, 2]` |
| `details` | string | 可选 | 说明 | 自由文本；`叢編原序 N` 表示本书在丛编原书中的次序（build 据以排序） | |
| `sub_items` | array<string> | 可选 | 本书在**这个丛编**里附带的子目 | 非空字符串数组 | `["周易略例"]` |

`section`（部类）写在 Book 顶层，不在 `contained_in` 项里。丛编增减成员只改成员的 `contained_in`，不改丛编档，也不 bump 丛编的 `revision`。

---

## 四、`provenance`（馆藏）

```json
"provenance": [
  {"institution": "國立故宮博物院", "call_number": "故善012603", "seals": [], "notes": "", "source": "metadata.npm_item_id"}
]
```

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `institution` | string | 必填 | 现藏机构 | 非空，繁体机构名 |
| `call_number` | string | 必填 | 索书号 | 字符串，可为空串 |
| `seals` | array<string> | 必填 | 藏印 | 可为空数组 |
| `notes` | string | 必填 | 说明 | 可为空串 |
| `source` | string | 必填 | 本项据现行哪个字段、哪批数据回填，供覆核回查 | 如 `metadata.npm_item_id` |

- 一书多藏本各一项。
- 与 `current_location`（现藏地）、`location_history`（递藏史）并存，不取代它们。
- 故宫 17,540 条由 `metadata.npm_item_id`（故宫统一编号即索书号）机械回填，`seals` 按典藏号与故宫资料对照填入。草稿库 9 万余项来自《中國古籍總目》馆藏著录，`call_number` 皆为空串。

---

## 五、`physical_description`

```json
"physical_description": {"leaf_style": "半葉十行行二十字，白口，四周雙邊，單黑魚尾", "binding": "線裝", "dimensions": "版框高21.5公分，廣15公分", "condition": "", "source": "…"}
```

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `leaf_style` | string | 必填（可空串） | 行款：半叶行数、每行字数、版心黑白口、边栏、鱼尾，**原样保留站方措辞，不挑词、不重排** |
| `binding` | string | 必填（可空串） | 装帧：线装、蝴蝶装、包背装、经折装…… |
| `dimensions` | string | 必填（可空串） | 尺寸，多为版框高广；「23.5x14.5公分」拆写为「版框高23.5公分，廣14.5公分」，不改序 |
| `condition` | string | 必填（可空串） | 品相：缺叶、虫蛀等 |
| `source` | string | 必填 | 本项据何而来（现行字段、哪批资料、或「description 原文抽取」） |

四个内容子字段（`leaf_style`、`binding`、`dimensions`、`condition`）**至少一项非空才写本对象**，否则整个字段不写。全是字符串，未知留空串。
回填须防「同一典藏号是一函多书的合订号」：须按书名唯一命中才取用，不可按文件读入顺序「后到盖前到」。

---

## 六、`base_edition`

```json
"base_edition": [
  {"role": "底本", "name": "宋淳熙三年閩山阮氏種德堂巾箱本", "source": "dating.based_on+edition切分"},
  {"role": "配補", "book_id": "9897xxxxxxxx", "name": "…", "note": "…", "source": "lineage.derived_from"}
]
```

| 字段 | 类型 | 必填 | 含义 | 取值 |
|---|---|---|---|---|
| `role` | string | 必填 | 关系 | `底本`｜`配補`｜`參校` |
| `name` | string | 必填 | 底本之名 | 非空 |
| `book_id` | string | 可选 | 指库中已有 Book | 须存在，不得指本书自身 |
| `work_id` | string | 可选 | 只知其书未知其本时指 Work | 须存在；与 `book_id` 至多填一项 |
| `note` | string | 可选 | 佐证或按语 | 自由文本 |
| `source` | string | 必填 | 本项据何而来 | 实测：`dating.based_on+edition切分`、`lineage.derived_from` |

「谁以我为底本」不写，由 build 生成 `_derived_by`。

---

## 七、`lineage`

版本源流，写在后出者一侧。各 Book 的 `lineage` 由 build 汇成作品的版本图 `lineage/<work_id>.json`；Work 的 `version_graph` 管分组与显示。

| 字段 | 类型 | 含义 | 取值 |
|---|---|---|---|
| `category` | string | 版本类别 | 自由文本（实测：刻本、石刻、抄本、评本、拓本、影印、排印、簡本、石印本……） |
| `year`、`year_range`、`year_text`、`year_uncertain` | integer、array<integer>、string、boolean | 年代 | |
| `status` | string | 存佚 | `extant`｜`fragment`｜`lost` |
| `extant_juan` | string | 现存卷回 | 自由文本 |
| `alias` | array<string> | 简称、俗称（如「甲戌本」） | |
| `note` | string | 说明 | |
| `derived_from` | array<object> | 所出之本 | 每项 `{ref, ref_type, relation, confidence, evidence?}`，见下 |
| `related_to` | array<object> | 非源流的关联（合刊、兄弟本、同源……） | 每项 `{book_id?, ref?, ref_type?, relation, confidence?, evidence?}` |

`derived_from[]`：
- `ref`：`ref_type` 为 `book` 时是库中 Book id；为 `hypothetical` 时是假想底本代号（`h_` 起首，见 Work 的 `version_graph.hypothetical_nodes`）。
- `relation`：自由文本（实测：翻刻、過錄、校改、據以評、刪節、參校、刪改、合刊、底本……）。
- `confidence`：`certain`｜`consensus`｜`probable`｜`disputed`。
- `evidence`：依据。
