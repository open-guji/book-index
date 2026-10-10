# 整理本与辑佚档（book-text 仓）

整理本（旧称 `collated_edition/`）与辑佚档（`fragments/`）**不在 book-index、book-index-draft 两仓**，在 [`open-guji/book-text`](https://github.com/open-guji/book-text) 仓。它们不是记录，是文本；**格式由文本总管管，权威在 book-text**。本档只讲：

1. 它们现在在哪、何时迁走（§一）；
2. book-index 记录与它们的接口——book-index 一侧要知道的字段（§二）；
3. 迁出时的格式快照，供对照（§三，**不是权威**）。

---

## 一、现在在哪

### 位置与归属

| 项 | 现状（book-text main `624950ba`，2026-10-08） |
|---|---|
| 仓 | `open-guji/book-text`，与 book-index **共用同一套 snowflake id**，靠 id 互指 |
| 条目目录 | `<Work\|Book>/<c1>/<c2>/<c3>/<id>/`，分片同 book-index（id 尾三字符，bim `storage.shard_dirs()`） |
| 整理本 | 条目目录下的一个**版本**：`manifest.json` 里 `kind: "collated"` 的那一项，放在 `default/`（整理本排第一时）或 `collated/`；版本目录内 `index.json`（章目录，旧 `collated_edition_index.json`）＋ `001.md`、`002.md`…＋同名 `001.json`… |
| 辑佚档 | `Work/<c1>/<c2>/<c3>/<id>/fragments/<书名>.json` |
| 索引 | `index/texts/{0-f}.json`（各条目版本清单汇总）、`index/fragments/{0-f}.json`（辑佚档汇总） |
| 写入与发布 | 写入口是文本总管的排班；上线只由网站总管做 |

实测（book-text main，2026-10-08）：有文本的条目 8,796 个（`index/texts`）；其中 `kind: "collated"` 的版本 65 个（64 个在 `default/`、1 个在 `collated/`），另 `kind: "self_collated"` 1 个（Book `96mid1ogzk`）；辑佚档 1,264 份。book-index、book-index-draft 两仓工作树里 `collated_edition/`、`fragments/` 目录数为 0。

### book-text 里的现行格式说明

| 文件 | 讲什么 |
|---|---|
| `book-text/README.md` | 目录结构、版本、与 book-index 之系连、校验、授权、迁入由来 |
| `book-text/CLAUDE.md` | 目录（manifest、版本目录、主版本怎么定）、提交与 PR 流程 |
| `book-text/docs/VERSIONING.md` | `original` 文本／标点／实体三条线的版本号 |
| `book-text/docs/ORIGINAL.md` | `original` 一章有哪些层文件 |

结构改版规格见 overview#307（2026-09-30 起：`collated_edition/` 改为版本目录，`full_text/<key>/` 并入，`index/collated`、`index/full_text` 停用）。

### 迁走的经过（证据）

| 日期 | 仓 | commit | 事 |
|---|---|---|---|
| 2026-08-26 | book-index | `4ba4799cb55` | 迁前格式归一（卷档入 `juan/NNN.json`、清单更名 `index.json`），「book-text 拆分之預備」 |
| 2026-08-26 | book-index | `036a055dd37` | 「文本移出：整理本／輯佚／全文／抓取素材遷入 book-text」：删 3,971 档（`collated_edition` 2,421 档 106.6 MB、`fragments` 1,250 档 8.0 MB、`sources` 148 档、`Book/<id>/full_text` 152 档）；搬前逐档 sha256 双向核对 |
| 2026-08-26 | book-text | `386320e..1524af8` | 同一批文本迁入（37 个 commit，按分片分批） |
| 2026-09-06 | book-index | `fbabc0209a5` | 「删除误建在本仓的整理本资产（已搬入 book-text）」：2026-09-03 起误建在 book-index 的 12 部補志整理本 992 档（已搬入 book-text `17232ab`），连同 08-26 时暂留的 `Work/d/1/c/d59f2mel8d1c/collated_edition/_working/` |
| 2026-09-30 | book-text | （overview#307） | `collated_edition/` 改为条目目录下的版本目录 |

注：book-index 的 git 历史已于 2026-10-03 压缩（`6a41ae1eda`，压缩前 main 为 `dbc235b517`），上表 book-index 的 commit 不在 main 的祖先链上，要按 `dbc235b517` 取（`git fetch --depth=1800 origin dbc235b517535e7f9ca95e7859ff41a72b620142`）。压缩时的树里已无 `collated_edition/`、`fragments/`。

---

## 二、book-index 与它们的接口

### 记录一侧的字段

| 字段 | 在哪 | 与文本的关系 |
|---|---|---|
| `_has_collated` | Work 源档（暂留，见 [legacy.md](legacy.md)） | 「有整理本」。**唯一真指 book-text 目录的字段**：正式库 10-08 为真 65 条，与 book-text 的 65 个 `kind: "collated"` 版本逐一对应。build 从 book-text 的 `index/texts`（`kind` 为 `collated`／`self_collated`，`quality` 不是 `none`／`placeholder`）推出产物 `_has_collated`，参数 `--text-index`（工作包 C）；`index/` 里写作 `has_collated`，同口径 |
| `_has_text` | Work、Book 源档（暂留） | 「有全文」。build 产物里的 `_has_text` ＝ `resources[].types` 含 `text`（Work 另并其 Book）**或** book-text 的 `index/texts` 里有该 id（或其 Book）且版本 `quality` 不是 `none`／`placeholder`（沿 `merged_into` 解析，悬空 id 记入 `report.json` 的 `dangling_text_ids`）；给了 `--text-index` 就不再认源档旧值。**不等于「book-text 有此条目」**：正式库 10-08 实测，Work `_has_text` 为真 10,677 条，其中 3,755 条 book-text 无此条目；book-text 有条目的 Work 8,783 条，其中 1,861 条 `_has_text` 不为真 |
| `resources[]` 中 `types` 含 `text` 者 | Work、Book | 外部全文资源（维基文库、识典、ctext 之属），格式见 [common.md〈Resource〉](common.md)。与 book-text 的文件无直接对应 |
| `_has_image` | 产物 | 只由 `resources[].types` 含 `image` 推得，与 book-text 无关 |

来源已定为 `index/texts`（overview#506 工作包 C）；源档里的 `_has_text`／`_has_collated` 待数据道删除（工作包 D）后收回豁免（E）；见 [legacy.md](legacy.md)。注意 `index/texts` 条目目前**不带 `quality`**（在各条 `manifest.json`），build 读到有 `quality` 字段才过滤；需文本总管让 `build_texts_index.py` 把 `quality` 写进去。

### 文本一侧指向记录的字段

整理本的每个条目（section）指向别的记录有四个字段，义各不同，不可混用。book-index 一侧要知道它们，是因为**并条、改指、删条时 book-text 里的这些 id 要跟着改**（见 [cataloging-rules.md〈同题二条〉第 10 条](cataloging-rules.md)），也因为跨仓校验按它们查悬空：

| 字段 | 指向 | 义 |
|---|---|---|
| `work_id` / `work_ids` | Work | 本条所著录的作品。一条著录多书时用复数形。 |
| `book_id` | Book | 本条所著录的是某一具体版本（如小说书目逐版著录者）。 |
| `collection_id` | Collection | 本条所著录的是一部**丛书**，而非单一著作。 |
| `target_bid` | Work（书目本身） | **本志所考的那部书目**，如《隋書經籍志考證》各条的 `target_bid` 为《隋書經籍志》。与前二者无关。 |

- `target_bid` 之名易生误解——它不是「本条所指的 book」，而是考证的对象。凡欲记「本条所指为某具体版本」，一律用 `book_id`。
- **一部丛书不得因见于书目而别立一 Work**——那会与其 Collection 记录相重。所指之 id 在 Collection 里者即用 `collection_id`；「`work_id` 所指而实为 Collection 者」其数当为 0。

辑佚档一侧指向记录的字段：`work_id`（本书 Work，须与所在路径相符）、`collectors[].work_id`（该辑佚丛书的 Work）、`based_on[].source_bid`、`attested_count_basis.work_id`。

另：book-index 记录里有些说明文字引用 book-text 路径，如 `indexed_by[].section_basis` 的「類目據 `Work/…/collated_edition/…`」（正式库 10-08：1,480 余条），`ai_note` 里的 `fragments/` 档位。路径是写下时的旧路径，不随 book-text 改版而改。

### 跨仓校验

`book-index-draft/.claude/skills/hanzhi-curation/scripts/chk-cross.py --text-root ../book-text --meta ../book-index`（见 book-text README「校驗」）。每一验都印其扫了几档，扫 0 档与全过输出一样，先看扫档数。

---

## 三、迁出时的格式快照（供对照，权威在 book-text）

> 以下是 book-index `SCHEMA.md` 在 2026-10-07 时记载的整理本与辑佚档格式，照录事实，转为简体。2026-09-30 book-text 改版后，路径与清单名已变（`collated_edition_index.json` → 版本目录的 `index.json`，卷档 → `NNN.json`／`NNN.md`），字段是否仍如此以 book-text 为准。

### 3.1 整理本之 `text_quality.grade`

整理本清单（旧 `collated_edition_index.json`，今版本目录 `index.json`）之 `text_quality.grade` 记其文之来历与可信度：

| 值 | 义 |
|---|---|
| `source` | **原文照录**，未经简繁往返，未加标点。如《經義考》之 kanripo KR2n0011 本 |
| `fine` | 精校标点本 |
| `rough` | 粗校标点本（识典古籍之属） |
| `ocr` | OCR 未校 |
| `placeholder` | 只有骨架，正文未入 |
| `none` | 无文本 |

`source` 一级另有一效：`chk.py` 之「简转繁过度转换」一验**跳过**此类整理本。
该验所捕者是简→繁往返之误，原文照录者无从发生，而原本自有之用字反要落网
——《經義考》文淵閣本「日辰有十幹十二支」之「幹」是本字，「葉氏（世竒）範
通」之「範」是洪範之範，「王氏（範）交廣春秋」之「範」是名不是姓。

### 3.2 整理本 section 的四个指涉字段

见上〈§二 文本一侧指向记录的字段〉。补充：

`collection_id`（2026-08-23 增）之由：书目之中本有专著丛书者——《中國通俗小說書目》卷九附录二即〈叢書目〉，其条为《四大奇書》《前後七國志》《怡園五種》《合刻天花藏七才子書》之属。此辈库中以 Collection 记之（丛书非单一著作，其子书各有其 Work），而节先前一律用 `work_id`，栏名与所指不符。

判之之法：所指之 id 在 `index/collections.json` 者即用 `collection_id`。`chk.py` 验其存在，并另验「`work_id` 所指而实为 Collection 者」，其数当为 0。

section 另有 `section_kind`（`附屬部帙`／`別本`／`一書兩著`），判法见 [cataloging-rules.md〈「別本」之节〉](cataloging-rules.md)。

### 3.3 辑佚档（`fragments`）

置于 `Work/{c1}/{c2}/{c3}/{id}/fragments/{title}.json`，`schema_version: 2`（与记录的 `schema_version` 不同族，勿混）。
分层而共用一个结构：**著录层**（`catalog`）记某书几家辑过、各得几条、见于哪些书哪些卷，
皆有据而不含佚文原文；**文本层**（`text`）逐条录其佚文。得文本则就地填入 `fragments[].text`，
不另立档，`coverage.level` 是唯一须随之改动的字段。

**受控词汇一律英文**（2026-08 迁移）。此前辑佚档作中文（著录层／文本层）而整理本作
`toc`／`text`，同一概念两套词。专名（`collector`、`work`、`title`）与散文说明
（`statement`、`note`、`basis`、辑本序原文）仍中文——那是内容，不是词汇。

| 字段 | 枚举 |
|---|---|
| `coverage.level` | `catalog` → `titles` → `text` ／ `text_partial` |
| `text_status` | `recorded`／`not_recorded` |
| `confidence` | `certain`／`uncertain` |
| `provenance` | `secondary`（转录自考证书或辑本）／`primary`（已复核所引原书） |
| `count_unit` | `item`（条）`piece`（篇）`section`（节）`entry`（事）`poem`（首）`juan`（卷） |
| `verify_result` | `out_of_scope`（该辑家体例不收此类书）／`not_found`（遍检其书而无之） |
| 整理本 section `part` | `main`（正编）／`supplement`（续编）／`appendix`（附） |
| 整理本 section `bian` | `classics`（经编）／`masters`（子编）／`history`（史编）／`supplement`／`appendix` |
| 整理本 section `type` | `reconstruction`（辑本） |

`schema_note` 已去（一千二百三十四份逐字相同，八万七千余字），改为指标 `schema_ref`
指向格式说明（现存档内值为 `SCHEMA.md#輯佚檔fragments`）。schema 之说明是 schema 之事，不是每条资料之属性。

主要字段：

| 字段 | 义 |
|---|---|
| `work_id` | 本书之 Work ID，须与所在路径相符 |
| `loss_status` | 存佚，枚举与判法见 [work.md](work.md)、[cataloging-rules.md〈loss_status〉](cataloging-rules.md) |
| `statement` | 存佚之叙述（何时著录、何时亡佚、据何而知） |
| `provenance` | `primary`（已复核辑本原书）／`secondary`（转录自考证书）。<br>现全为 `secondary`；此栏虽恒定而不可去——一旦复核原书即当改 `primary`，去之则后人须重立。 |
| `based_on[]` | 所据之书：`{source, source_bid, field}` |
| `collectors[]` | 辑家：`{collector, work, work_id, sections, count, count_unit, statement, basis}`。<br>**`count` 是「该辑家辑得几条」，不是「本库已录他几条」**——二者常不等（《古文瑣語》馬國翰得十五条而本库只录一条），校验时勿相比。本库所录之数在 `coverage.fragments_recorded`。<br>`count` 取自辑本序者须防序中之数非其本人所得，见 SKILL「從輯本序裡取條數」。<br>`sections[]` 记本书在该辑佚丛书整理本中的位置 `{file, index, title, part, juan_no, lei}`——一书而正编、续编两见者，马氏正编辑之而续编又补，非歧义，故用数组。<br>**`collector` 不得为空**——一条即断言「某人辑过此书」，无其人则此断言落空。<br>`work_id` 系本库中该辑佚丛书之 Work。<br>**`attested_count`（2026-08-06 增）与 `count` 不是一件事**：`count` 是该辑家自己辑得几条；`attested_count` 是**别人的辑本说他辑得几条**，并以 `attested_count_basis {work, work_id, note}` 记其所出。汪文臺本逐条标「（姚。孫。王。汪。黃）」，据以计得姚氏 419 条——这是汪氏所见，非姚氏自著，亦非本库已录（本库录自姚本者 420）。三者各为一数，混之则对账无从做起。<br>此栏之用正在对账：419 对 420、10 对 10、11 对 11，是两个独立来源相符，胜于抽样。 |
| `collection_attested[]` | 确有辑本而未详其辑家者：`{basis, work, statement, count, count_unit}`。<br>与 `collectors[]` 分立，因该数组之一条即断言「某人辑过此书」，辑家不可空；而「有辑本而不著其人」是另一件事，记于此栏，其据照录于 `basis`。<br>得其人后当移入 `collectors[]`。校验时本栏与 `collectors`、`fragments` 同为据，有其一即非空档。 |
| `other_statements[]` | 与本书相关而**不是辑本序**者（本志篇序、旧注之序、校注序），自 `collectors` 移出者记 `moved_from` |
| `cited_in_summary[]` | 佚文所见之书与部类，尚未析出为逐条者 |
| `fragments[]` | 逐条佚文：`{seq, text, cited_in, collected_by, attested_by, confidence, note}`。<br>**`cited_in` 是数组**（2026-08-06 统一；此前 780 条作单一对象，已一律包成数组）——一条佚文常见于数书（「──御覽卷五八一　○　白帖卷六二」），单一对象表不了。每项作 `{raw, book, juan}`：`raw` 是原文照录，`book` 是还原之全名（御覽→太平御覽），还原不得则为 null，**不猜**。「又卷六五」承前一条之书，还原时须传前一条之 `book`。<br>`cited_in` 记**佚文从哪部书里引出来**，`collected_by` 记**哪一位辑家把它辑进自己的书**，二者不同轴，勿混。<br>**`heading` 与 `piece_title` 不是同一件事，勿合并**：`piece_title` 是**这一条佚文自身之题**（嚴可均按撰人编次，一条即一篇，如〈上書諫伐匈奴〉）；`heading` 是**数条佚文共有之标目**（姚之駰按传主编次，「光武皇帝」下系四十七条）。一者标识自身，一者标识所属。<br>`editor_note` 是辑家之案语（姚书原作【…】），是辑家之考，非本书之文，**不得与 `text` 相混**。<br>`text_from` 已去（八百条与 `attested_by` 逐字相同）。 |
| `coverage` | `{level, fragments_attested, fragments_recorded, text_available}`。<br>`level` 四级：`catalog`（仅知几家辑过）→ `titles`（知辑本各篇之题）→ `text`（正文全录）／`text_partial`（正文部分录）。<br>`titles` 现无实例（嚴可均那批已升 `text`），定义保留待用。<br>`fragments_attested` 为 null 者是**未知**，非零——如据丛书目录立档，目录不载条数。<br>**数家所得不同时，`fragments_attested` 取诸家所称之最大数**，并以 `fragments_attested_note` 记其所以（《古文瑣語》嚴輯十九条、馬輯十五条、章宗源云十三事，取二十五）。 |
| `fragments[]` 之篇目条 | 有 `piece_title` 而 `text` 为 null，是「知其篇而未录其文」，须并记 `text_status`，否则与「无文」无从分辨。 |

`loss_status` 与辑佚档的关系：「传本是否断绝」由辑佚档之有无导出——传本断绝、赖类书征引／后人辑佚者，`loss_status` 为 `partially_extant` 且**有**辑佚档；「有辑本」不是存佚状态，由辑佚档之有无与 `collectors` 是否非空导出（见 [cataloging-rules.md〈loss_status〉](cataloging-rules.md)）。

### 3.4 辑佚丛书整理本（`type: fragment_collection`）

辑佚丛书（《玉函山房輯佚書》一类）之整理本，别于书目之 `catalog` 与考证之 `kaozhen`。
一类一档，section 即一部辑本书，`work_id` 指其所辑之原书。
`coverage.level` 三级：`books_only`（仅知其书）→ `toc`（卷目已备）→ `text`（文本已录）。
与辑佚档之 `level` 同为英文而词不同——彼记「这部书之佚文到了哪一层」，
此记「这部丛书之整理到了哪一层」，二事不同，故不强合。

**section 须自带 `coverage`。** `fragments: []` 之义为「尚未录入」而非「无佚文」，
无此栏则二者无从分辨。

双向：整理本 `section.work_id` → 原书；原书辑佚档 `collectors[].sections[]` → 整理本之条。
