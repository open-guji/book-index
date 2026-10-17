# seal（印章，GUJI-538）

总览与子类型索引见 [../entity.md](../entity.md)。

## 真实示例

下列路径都是本仓真实文件（`tests/test_entity_examples.py` 逐条核实存在）；「index」列是派生分片索引，键即该条 id。分片编号会随重建变动，以测试核实为准。

| 示例 | 源档 | index | 演示什么 |
|---|---|---|---|
| 文淵閣寶 `hixi6zykf4ea` | [Entity/4/e/a/hixi6zykf4ea-文淵閣寶.json](../../Entity/4/e/a/hixi6zykf4ea-文淵閣寶.json) | [index/entities/2.json](../../index/entities/2.json) | 官印（文淵閣寶）：`institution_ids` 指文淵閣、带 `images` 印影（图在 book-index-asset 仓） |
| 乾隆御覽之寶 `hixi6zykf4eb` | [Entity/4/e/b/hixi6zykf4eb-乾隆御覽之寶.json](../../Entity/4/e/b/hixi6zykf4eb-乾隆御覽之寶.json) | [index/entities/3.json](../../index/entities/3.json) | 鑒藏印（乾隆御覽之寶）：`owner_ids` 指印主（清高宗）、`usage_scope` 与 `description.sources` 的写法 |
| 金澤文庫印 `hixi7176qbr4` | [Entity/b/r/4/hixi7176qbr4-金澤文庫印.json](../../Entity/b/r/4/hixi7176qbr4-金澤文庫印.json) | [index/entities/e.json](../../index/entities/e.json) | 日本藏印（金澤文庫印）：非中国朝代的印章条怎么写 |

一枚（一种）印章一条。`primary_name` 是印章通名（如「文淵閣寶」），`seal_text` 是印面文字（印文），**两者分开**：通名可含「印」「寶」等泛称，印文按印面所见照录（异体照录，不简化）。id 沿用 Entity 通则（`mintid.py --type Entity`），分片同其他 Entity。遵守[总说](../entity.md)的三条专名硬约束（无 `cbdb_*`、`external_ids` 只许 `wikidata_id`、无坐标）。

| 字段 | 类型 | 必填 | 性质 | 含义 | 取值 | 谁写 | 例 |
|---|---|---|---|---|---|---|---|
| `seal_text` | string | **必填** | 原生 | 印文（印面文字） | 非空；按印面所见照录，异体照录不简化；与 `primary_name` 通名分开 | 录入 | `"文淵閣寶"` |
| `seal_kind` | string | **必填** | 原生 | 印章类别 | `官印`｜`私印`｜`鑒藏印`｜`齋館印`｜`其他`（鑒藏印即收藏／鑒賞印，不另设「收藏印」） | 录入 | `"官印"` |
| `dynasty_ids` | array<id> | **必填** | 原生 | 启用时所属朝代 | dynasty id 数组，默认一朝一条；不写旧式 `dynasty`／`period` 字符串 | 录入 | `["hixi1ubjrxga"]`（清） |
| `description` | object | **必填** | 原生 | 介绍与出处 | 同通则，`sources` 非空；来源不实的字段一律留空，不编造 | 录入 | `{"text":"…","sources":[{"title":"…"}]}` |
| `start`、`end` | integer | 可选 | 原生 | 启用／停用年 | 公元年，无 0 年，`start ≤ end`；不确定不写，说明进 `description.text` | 录入 | |
| `seal_style` | string | 可选 | 原生 | 朱白 | `朱文`｜`白文`｜`朱白相間` | 录入 | `"朱文"` |
| `seal_script` | string | 可选 | 原生 | 印面字体 | 篆／隸／楷等，短文本 | 录入 | `"篆書"` |
| `seal_form` | string | 可选 | 原生 | 印形 | `方`｜`圓`｜`橢圓`｜`長方`｜`異形` | 录入 | `"方"` |
| `material` | string | 可选 | 原生 | 质地 | 短文本 | 录入 | `"玉"`（示意） |
| `size` | string | 可选 | 原生 | 尺寸 | 文本，如「長×寬 mm」 | 录入 | `"50×50 mm"`（示意） |
| `usage_scope` | string | 可选 | 原生 | 用途／钤用范围 | 一句话 | 录入 | `"鈐於文淵閣本《四庫全書》各冊首卷第一頁"` |
| `owner_ids` | array<id> | 可选 | 原生 | 印主 | 指向 people／collective／office 的 Entity id，**不写裸名字**；年号不是印主（乾隆印主指清高宗本人那条 people） | 录入 | |
| `institution_ids` | array<id> | 可选 | 原生 | 所属机构 | 指向 collective（如文渊阁）的 Entity id | 录入 | `["hixi6zykf4e8"]` |
| `appears_in` | array<object> | 可选 | 原生 | 代表例：此印见于哪些书 | **本期只作代表例，≤20 条、以 Book 为主**；不是全量钤印清单（全量见 Book 侧 `provenance[].seal_marks`，见下〈与 Book、asset 仓的关系〉） | 录入 | |
| `appears_in[].ref_type` | string | **必填** | 原生 | 引用类型 | `Book`｜`Work` | 录入 | `"Book"` |
| `appears_in[].id` | string | **必填** | 原生 | 书的 id | 库内存在、不重复（S04） | 录入 | `"988g52c000"` |
| `appears_in[].position` | string | 可选 | 原生 | 钤印位置 | 短文本 | 录入 | `"首卷第一頁"` |
| `appears_in[].note` | string | 可选 | 原生 | 说明 | 自由文本 | 录入 | `"據通例，未逐冊核對"` |
| `images` | array<object> | 可选 | 原生 | 印影 | ≤8 张；图本身不进本仓，在 **open-guji/book-index-asset** 仓；限额长边≤1600px、单张≤300KB、webp | 录入 | |
| `images[].file` | string | **必填** | 原生 | 图文件路径 | 相对 asset 仓根，固定为 `entity/{id末3位逐位分片}/{id}/{序号}.webp`（id `hixi6zykf4ea` → `entity/4/e/a/hixi6zykf4ea/1.webp`） | 录入 | `"entity/4/e/a/hixi6zykf4ea/1.webp"` |
| `images[].credit` | string | **必填** | 原生 | 署名／来源说明 | 自由文本 | 录入 | `"維基共享資源〈…〉"` |
| `images[].license` | string | **必填** | 原生 | 许可 | 闭集 `公有領域`｜`CC0`（印影入库须公有领域） | 录入 | `"公有領域"` |
| `images[].source_url` | string | **必填** | 原生 | 原始出处网址 | URL | 录入 | `"https://commons.wikimedia.org/wiki/File:…"` |
| `images[].note` | string | 可选 | 原生 | 取图说明 | 取得日期、裁切、尺寸等 | 录入 | `"取 250px 縮略圖轉 webp"` |

归属单向：印→印主／机构，反向（某人有哪些印）由 build 派生；禁用 `dates`、`dynasty`、`period`、`native_place*`、`history`、`ruler` 等其他子类型专属字段（S05）。校验码见[校验码](_checks.md)S01–S06。

**与 Book、asset 仓的关系（查印章从这里开始）**：
- **印章条本身**（本节）只记这一种印：印文、类别、朝代、印主、印影。
- **某书有哪些印**不写在印章条，写在具体馆藏本上：`Book.provenance[].seal_marks[]`，每项 `{seal_id, position?, note?, source?}`，`seal_id` 指向本节的印章条（见 [book.md〈四、provenance〉](../book.md#四provenance馆藏)）；旧 `provenance[].seals`（字符串数组）保留为著录原文。校验码 B-S01…B-S05 在 `check_v2.py` Book 段。
- 印章条的 `appears_in` 只是代表例（≤20）；全量待 `seal_marks` 回填后由 build 派生，不手写。
- **印影图**放在 **open-guji/book-index-asset** 仓，本仓只存 `images[]` 元数据；S06 校验文件是否存在（本地无该仓则跳过）。
- 并条：印章条被合并时，`entity_merge.py` 同步改繫全库 `seal_marks[].seal_id`。

## 校验码

| 码 | 适用 | 查什么 | 级别 |
|---|---|---|---|
| S01 | seal | `primary_name`、`seal_text` 非空；`seal_kind` 在 5 值内；`description.sources` 非空 | ERROR |
| S02 | seal | `dynasty_ids` 非空且指 dynasty；`start`／`end` 为整数且 `start ≤ end`；`seal_style`／`seal_form` 在枚举内 | ERROR |
| S03 | seal | `owner_ids`／`institution_ids` 为 id 数组且指向存在的 Entity，不得指 seal／dynasty（ERROR）；指墓碑（WARN） | ERROR／WARN |
| S04 | seal | `appears_in` ≤20 条、`ref_type` ∈ Book／Work、`id` 在库内存在、不重复 | ERROR |
| S05 | seal | `images` 每项 `file`＋`credit`＋`license`（闭集）＋`source_url`、≤8、`file` 路径规范；`owner_ids` 只能指 people／collective／office，`institution_ids` 只能指 collective；出现其他子类型专属字段（含 `dates`、`dynasty`、`period`） | ERROR |
| S06 | seal | `images[].file` 在 book-index-asset 中不存在（本地有 `BOOK_INDEX_ASSET_ROOT` 或并列的 `../book-index-asset` 才核；没有该仓就跳过，CI／verify 不硬依赖另一仓） | ERROR |

另适用全 Entity 通用码 E1、A1、O12（专名子类型）与 V01／V11／V15／V16，见 [校验码总表](_checks.md)。
