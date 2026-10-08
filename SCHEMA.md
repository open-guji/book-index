# book-index Schema（schema-v2）

本文是 `book-index` / `book-index-draft` / `book-text` 三仓字段级 Schema 的唯一权威（`book-index-draft/SCHEMA.md` 只是指向本文的指针）。
概念模型见 overview 仓 `项目进展/古籍索引网站/整体设计/整体设计.md`；录入约定见 overview 仓 `项目进展/古籍目录/整体设计/录入规范.md`（两份文档若与本文冲突，以本文为准；它们按 F2-7 §九 C1／C2 另行改写）。

**本版（schema-v2，2026-10-07 起）的设计依据**都在 overview 仓 `项目进展/古籍目录/进度/F-数据结构/`：
`F2-1-关系清单.md`、`F2-2-谁存哪一边.md`、`F2-3-build与派生字段.md`、`F2-7-迁移方案.md`、`F3-2-设计与备选.md`、`F3-3-revision口径.md`；
决定过程见 overview#451。本文与这几份设计文档有出入时，**以设计文档为准并回来改本文**。
迁移期间新旧两套写法并存的对照，见文末〈附一 新旧字段对照表〉；还没有结论的点见〈附三 待定项〉。

---

## 〇、总则：源数据与构建产物

| # | 规则 | 一句话 |
|---|---|---|
| 1 | **一个事实只写一次** | 源数据里一条关系只存一侧；反向、计数、对方题名等展示副本全部由 build 生成。 |
| 2 | **成对关系只写规范方向** | `part_of`／`studies`／`contains_text_of`／`preceded_by` 写在本侧；`has_part`／`studied_by`／`text_carried_by`／`followed_by` 只在构建产物里出现。见〈七、关联词表〉。 |
| 3 | **对称关系存 id 较小的一侧** | `related_works` 的 `related`、`Book.related_books`、`Collection.related_books`／`related_collections`：两条记录 id 按**字符串比较**（Python `a < b`），写在较小者里；另一侧由 build 补。由工具（`bim link`）落笔，人不手选。 |
| 4 | **源档不写 `_` 起首字段** | `_` 起首的都是派生字段，只出现在构建产物 `_build/entry/<id>.json` 里；源档里出现即校验失败（`check_v2.py` V01）。无下划线的旧派生字段（`has_text`、`promoted_to`…）同样不写（V02）。**唯一例外**：`_has_text`、`_has_collated` 暂留源档（build 尚无稳定来源，目录总管 10-07 定）。 |
| 5 | **不写派生／反向列表** | 不写 `Work.books`、`Collection.books`、`Collection.contained_works`、`Entity.works`、`related_works[].title`。成员关系写在成员一侧（`Book.work_id`、`Book.contained_in`、`Work.contained_in`、`Work.authors[].entity_id`）。 |
| 6 | **`authors[].role` 必填**（Work；Book／Collection 自 2026-10-07 起亦然，overview#468） | 不写 role 曾造成 Work 与 Entity 两侧角色不一（F2-1：3,957 条）。 |
| 7 | **分类不在 Work 里** | 分类归属写在 `classification/<分类法>/members/<节点>.json`，Work 档里不写 `classification`。见〈八、分类〉。 |
| 8 | **`_build/` 是构建产物，不是源** | `build/build_derived.py` 读源档生成 `_build/`（不进 git）；`_build/entry/<id>.json`＝源记录＋全部 `_` 派生字段，是网站与 bim 读的「页面就绪条目」。`index/` 也由它生成。见〈九、构建产物〉。 |
| 9 | **读者新旧兼容，先切后拆** | 网站与 bim 读者「新字段（`_x`、类档）优先，没有就回退旧字段」；数据切换之后再删回退分支。build **不产出旧字段别名**（如不再产出 `classification`）。 |
| 10 | **revision 只管「作品是什么」的陈述** | 派生字段、分类归属、反向链变化不 bump `revision`；迁移脚本一律不改 `revision`／`revised_at`。见〈十、记录之共通字段〉。 |

**校验**：
- `.claude/qa/check_v2.py`：查源档里的旧格式残留（V01–V15，及专名子类型 E1／D／R／A／O／P 系列，代码表见脚本头注释与〈专名子类型〉），只读、可 `--paths` 只查 PR 改动的文件。审数据 PR 时必跑：`git diff --name-only origin/main... | python3 .claude/qa/check_v2.py --paths -`，退出码非 0 即有残留。迁移（M1–M4）完成前，存量会大量报出，这是预期。
- `.claude/qa/verify.py`：字段形状、悬空引用、词表等（旧校验，迁移完成后改为调用 build 自校验，F2-7 §九 B8）。

---

## 一、仓里有什么文件

| 路径 | 是什么 | 源／产物 |
|---|---|---|
| `Work/{c1}/{c2}/{c3}/{id}-{题}.json` | 作品记录 | 源 |
| `Work/…/{id}/collated_edition/`、`…/fragments/` | 整理本、辑佚档（不是记录，见〈二·附〉） | 源 |
| `Book/…/{id}-{题}.json` | 版本记录 | 源 |
| `Collection/…/{id}-{题}.json` | 丛编记录 | 源 |
| `Entity/…/{id}-{名}.json` | 人物等实体记录 | 源 |
| `classification/schemes.json`、`classification/<分类法>/tree.json`、`…/members/<节点>.json` | 分类法登记、分类树、各类成员 | 源（只经 `bim classify` 写） |
| `promotions.json` | 草稿 id → 正式 id 对照，升格的唯一权威 | 源 |
| `classific.json` | 旧分类词表；schema-v2 起由 `classification/zongmu/tree.json` 生成，退役中 | 产物 |
| `index/**` | 检索用扁平摘要 | 产物（build 生成，不手改） |
| `_build/**` | 页面就绪条目与分页大列表 | 产物（不进 git） |
| `Collection/**/volume_book_mapping.json`、`zhsy_book_mappings.json` 等 sidecar | 旧的叢编册号对照表 | **废止**：迁移 M1 并入记录、M6 删除（目录总管 10-07 定，#459；F2-7 §六·附原排 M3）。`check_v2.py` V12 |
| `resource*.json`、`recommended.json` | 资源站点目录、首页推荐 | 源（非记录） |

---

## 二、Work（作品）

一部作品的抽象知识内容，不随版本而变。

### 字段表

「谁存」一栏：**本档**＝写在这条 Work 源档里；**他档**＝关系存在对方记录里，本档不写；**build**＝只在 `_build/entry/<id>.json` 里。
「必填」：✔＝必填；空＝可选（缺省即未考／无，不写占位值）。

| 字段 | 谁存 | 取值 | 必填 | 示例 |
|---|---|---|---|---|
| `id` | 本档 | 正式库 12 字符、草稿库 13 字符 base36（见〈十一、ID〉） | ✔ | `"1evl7l48e27ls"` |
| `type` | 本档 | 恒为 `"work"` | ✔ | `"work"` |
| `schema_version` | 本档 | 整数，主记录现为 `1`；Work／Book／Collection／Entity 一律必填，缺或非 `1` 即 `check_v2.py` V15（2026-10-07，overview#473；升格时 bim 自动补） | ✔ | `1` |
| `title` | 本档 | 规范题名，繁体 | ✔ | `"周易"` |
| `subtype` | 本档 | `book`（默认，可省）｜`article`｜`poem`｜`chapter`，见〈Subtype〉 | | `"chapter"` |
| `additional_titles` | 本档 | 同书异名，字符串数组 | | `["春秋左氏傳"]` |
| `original_title` | 本档 | 条目原题与规范题不同时记原题 | | `"毛詩義問"` |
| `title_basis`、`title_emendation` | 本档 | 题名订正的依据与说明 | | |
| `authors[]` | 本档 | `{name, role, dynasty?, entity_id?, source?}`；**`role` 必填**（撰／注／編／舊題撰…）；`entity_id` 指 Entity，Entity 页的作品列表由它反查 | ✔（有撰人时） | `[{"name":"蘇軾","role":"撰","dynasty":"北宋","entity_id":"12x…"}]` |
| `dynasty`、`dynasty_basis` | 本档 | 作品成书朝代（规范名，见〈`dynasty` 規範化〉）与判断依据 | | `"北宋"` |
| `period`、`period_basis` | 本档 | 时代轴枚举（见〈`period`〉）与依据 | | `"song"` |
| `period_upper`、`period_upper_basis` | 本档 | 时代上限 | | |
| `description` | 本档 | Description 对象 `{text, sources}`，面向读者 | | |
| `juan_count` | 本档 | `{number, unit?, description?}` | | `{"number":10,"unit":"卷"}` |
| `measures`、`measure_info` | 本档 | 多维计量数组、展示文本 | | `"四卷二十回"` |
| `additional_works` | 本档 | 主体之外各自计卷的部分 `{book_title, n_juan}` | | |
| `publication_info` | 本档 | `{year, details}` | | |
| `page_count`、`current_location`、`collection_scale`、`appendix` | 本档 | 零星在用（各 ≤4 条），形状同 Collection／Book 同名字段 | | |
| `loss_status`、`loss_status_basis`、`loss_status_note` | 本档 | 存佚枚举 `lost`｜`partially_extant`｜`extant`｜`undetermined` | | `"lost"` |
| `authenticity`、`authenticity_basis` | 本档 | 唯一值 `forged`，只在确定是伪书时写 | | |
| `indexed_by[]` | 本档（被著录一侧） | IndexEntry，见〈IndexEntry〉；`source_bid` 必须指向存在的志书 Work；顺序有意义（同源多条按原序），不可按内容去重 | | |
| `emendated_by[]` | 本档 | IndexEntry，考证／校勘类著作对本书的订正 | | |
| `contained_in[]` | 本档（成员一侧） | `{id, volume_index?, group?, details?}`：本作品收入哪个 Collection；`group`＝本作品在该丛编里所属的组（原 `contained_works[].group`）；`details`＝说明文字（原 `contained_works[].note`）。M1 由丛编侧并入（目录总管 10-07 定，#459） | | `[{"id":"8rl…","volume_index":3,"group":"經部"}]` |
| `related_works[]` | 本档（规范方向一侧） | `{id, relation, note?}`；`relation` 只用〈七〉的「源档可写」词；**不写 `title`**；两侧原各有 note 者迁移时拼成一条 | | `[{"id":"1evl7l48e27ls","relation":"contains_text_of"}]` |
| `preferred_book` | 本档 | Book ID，单值，「推荐版本」；取代旧 `books` 的手排顺序（`_books` 按年代排） | | `"11q…"` |
| `version_graph` | 本档 | 手绘版本传承图（人工策展，6 条） | | |
| `resources[]`、`resource_groups` | 本档 | 同 Book，见〈resources 的 group 字段〉 | | |
| `sources[]` | 本档 | Source 对象 | | |
| `merged_in[]` | 本档（keeper 一侧） | 并条事件日志 `{id, title, at, by, rule, why}`，不是关系，不可派生 | | |
| `merged_from`、`merged_into`、`merge_history` | 本档 | 并条账；`merged_into` 只在墓碑上 | | |
| `ai_note`、`todo`、`review` | 本档 | 见〈ai_note 的用法〉〈記錄之共通欄位〉 | | |
| `revision`、`revised_at`、`updated_at` | 本档 | 见〈十、記錄之共通欄位〉 | ✔（`revision`） | `"1.0.0"` |
| ~~`books`~~ | 他档：`Book.work_id` | build 生成 `_books`、`_edition_count` | 不写 | |
| ~~`classification`~~ | 他档：`classification/<分类法>/members/` | build 生成 `_classifications` | 不写 | |
| ~~`related_works[].title`~~、~~反向词~~ | build | `_related`（双向展开、带对方现行题名） | 不写 | |
| `_` 起首一切 | build | 见〈九〉 | **源档不写** | |

### 示例（新格式）

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
  "juan_count": {"number": 9, "unit": "卷"},
  "measure_info": "九卷",
  "loss_status": "partially_extant",
  "indexed_by": [
    {"source": "隋書經籍志", "source_bid": "1ev…", "title_info": "周易九卷後漢大司農鄭玄注", "summary": "…", "section": "經部/易"}
  ],
  "related_works": [{"id": "1evl7l48e27ls", "relation": "contains_text_of"}],
  "revision": "1.0.0",
  "revised_at": "2026-10-07T00:00:00Z"
}
```

它在 `_build/entry/1evd0000000ab.json` 里会多出 `_related`（含《周易》题名、方向 `out`）、`_catalogs`（隋志的作者朝代）、`_authors`（鄭玄的 Entity 摘要）、`_classifications`（若在某类档里）等；《周易》的产物里则出现一条方向 `in` 的 `text_carried_by` 指向本条——**《周易》的源档一个字不动**。

### 各字段细则

#### 整理本 section 的四個指涉欄位

整理本置於 `Work/{c1}/{c2}/{c3}/{id}/collated_edition/`，每卷一檔，檔內 `sections` 為條目陣列。
條目指向別的記錄有四個欄位，義各不同，不可混用：

| 欄位 | 指向 | 義 |
|---|---|---|
| `work_id` / `work_ids` | Work | 本條所著錄的作品。一條著錄多書時用複數形。 |
| `book_id` | Book | 本條所著錄的是某一具體版本（如小說書目逐版著錄者）。 |
| `collection_id` | Collection | 本條所著錄的是一部**叢書**，而非單一著作。 |
| `target_bid` | Work（書目本身） | **本志所考的那部書目**，如《隋書經籍志考證》各條的 `target_bid` 為《隋書經籍志》。與前二者無關。 |

`target_bid` 之名易生誤解——它不是「本條所指的 book」，而是考證的對象。
凡欲記「本條所指為某具體版本」，一律用 `book_id`。

`collection_id`（2026-08-23 增）之由：書目之中本有專著叢書者——《中國通俗小說
書目》卷九附錄二即〈叢書目〉，其條為《四大奇書》《前後七國志》《怡園五種》
《合刻天花藏七才子書》之屬。此輩庫中以 Collection 記之（叢書非單一著作，其子
書各有其 Work），而節先前一律用 `work_id`，欄名與所指不符。
**一部叢書不得因見於書目而別立一 Work**——那會與其 Collection 記錄相重。

判之之法：所指之 id 在 `index/collections.json` 者即用 `collection_id`。
`chk.py` 驗其存在，並另驗「`work_id` 所指而實為 Collection 者」，其數當為 0。

#### 整理本之 `text_quality.grade`

`collated_edition_index.json` 之 `text_quality.grade` 記其文之來歷與可信度：

| 值 | 義 |
|---|---|
| `source` | **原文照錄**，未經簡繁往返，未加標點。如《經義考》之 kanripo KR2n0011 本 |
| `fine` | 精校標點本 |
| `rough` | 粗校標點本（識典古籍之屬） |
| `ocr` | OCR 未校 |
| `placeholder` | 只有骨架，正文未入 |
| `none` | 無文本 |

`source` 一級另有一效：`chk.py` 之「簡轉繁過度轉換」一驗**跳過**此類整理本。
該驗所捕者是簡→繁往返之誤，原文照錄者無從發生，而原本自有之用字反要落網
——《經義考》文淵閣本「日辰有十幹十二支」之「幹」是本字，「葉氏（世竒）範
通」之「範」是洪範之範，「王氏（範）交廣春秋」之「範」是名不是姓。

#### 輯佚檔（`fragments`）

置於 `Work/{c1}/{c2}/{c3}/{id}/fragments/{title}.json`，`schema_version: 2`。
分層而共用一個結構：**著錄層**（`catalog`）記某書幾家輯過、各得幾條、見於哪些書哪些卷，
皆有據而不含佚文原文；**文本層**（`text`）逐條錄其佚文。得文本則就地填入 `fragments[].text`，
不另立檔，`coverage.level` 是唯一須隨之改動的欄位。

**受控詞彙一律英文**（2026-08 遷移）。此前輯佚檔作中文（著錄層／文本層）而整理本作
`toc`／`text`，同一概念兩套詞。專名（`collector`、`work`、`title`）與散文說明
（`statement`、`note`、`basis`、輯本序原文）仍中文——那是內容，不是詞彙。

| 欄位 | 枚舉 |
|---|---|
| `coverage.level` | `catalog` → `titles` → `text` ／ `text_partial` |
| `text_status` | `recorded`／`not_recorded` |
| `confidence` | `certain`／`uncertain` |
| `provenance` | `secondary`（轉錄自考證書或輯本）／`primary`（已覆核所引原書） |
| `count_unit` | `item`（條）`piece`（篇）`section`（節）`entry`（事）`poem`（首）`juan`（卷） |
| `verify_result` | `out_of_scope`（該輯家體例不收此類書）／`not_found`（遍檢其書而無之） |
| 整理本 section `part` | `main`（正編）／`supplement`（續編）／`appendix`（附） |
| 整理本 section `bian` | `classics`（經編）／`masters`（子編）／`history`（史編）／`supplement`／`appendix` |
| 整理本 section `type` | `reconstruction`（輯本） |

`schema_note` 已去（一千二百三十四份逐字相同，八萬七千餘字），改為指標 `schema_ref`
指向本節。schema 之說明是 schema 之事，不是每條資料之屬性。

主要欄位：

| 欄位 | 義 |
|---|---|
| `work_id` | 本書之 Work ID，須與所在路徑相符 |
| `loss_status` | 存佚，見下表 |
| `statement` | 存佚之敘述（何時著錄、何時亡佚、據何而知） |
| `provenance` | `primary`（已覆核輯本原書）／`secondary`（轉錄自考證書）。<br>現全為 `secondary`；此欄雖恆定而不可去——一旦覆核原書即當改 `primary`，去之則後人須重立。 |
| `based_on[]` | 所據之書：`{source, source_bid, field}` |
| `collectors[]` | 輯家：`{collector, work, work_id, sections, count, count_unit, statement, basis}`。<br>**`count` 是「該輯家輯得幾條」，不是「本庫已錄他幾條」**——二者常不等（《古文瑣語》馬國翰得十五條而本庫只錄一條），校驗時勿相比。本庫所錄之數在 `coverage.fragments_recorded`。<br>`count` 取自輯本序者須防序中之數非其本人所得，見 SKILL「從輯本序裡取條數」。<br>`sections[]` 記本書在該輯佚叢書整理本中的位置 `{file, index, title, part, juan_no, lei}`——一書而正編、續編兩見者，馬氏正編輯之而續編又補，非歧義，故用陣列。<br>**`collector` 不得為空**——一條即斷言「某人輯過此書」，無其人則此斷言落空。<br>`work_id` 繫本庫中該輯佚叢書之 Work。<br>**`attested_count`（2026-08-06 增）與 `count` 不是一件事**：`count` 是該輯家自己輯得幾條；`attested_count` 是**別人的輯本說他輯得幾條**，並以 `attested_count_basis {work, work_id, note}` 記其所出。汪文臺本逐條標「（姚。孫。王。汪。黃）」，據以計得姚氏 419 條——這是汪氏所見，非姚氏自著，亦非本庫已錄（本庫錄自姚本者 420）。三者各為一數，混之則對帳無從做起。<br>此欄之用正在對帳：419 對 420、10 對 10、11 對 11，是兩個獨立來源相符，勝於抽樣。 |
| `collection_attested[]` | 確有輯本而未詳其輯家者：`{basis, work, statement, count, count_unit}`。<br>與 `collectors[]` 分立，因該陣列之一條即斷言「某人輯過此書」，輯家不可空；而「有輯本而不著其人」是另一件事，記於此欄，其據照錄於 `basis`。<br>得其人後當移入 `collectors[]`。校驗時本欄與 `collectors`、`fragments` 同為據，有其一即非空檔。 |
| `other_statements[]` | 與本書相關而**不是輯本序**者（本志篇序、舊注之序、校注序），自 `collectors` 移出者記 `moved_from` |
| `cited_in_summary[]` | 佚文所見之書與部類，尚未析出為逐條者 |
| `fragments[]` | 逐條佚文：`{seq, text, cited_in, collected_by, attested_by, confidence, note}`。<br>**`cited_in` 是陣列**（2026-08-06 統一；此前 780 條作單一物件，已一律包成陣列）——一條佚文常見於數書（「──御覽卷五八一　○　白帖卷六二」），單一物件表不了。每項作 `{raw, book, juan}`：`raw` 是原文照錄，`book` 是還原之全名（御覽→太平御覽），還原不得則為 null，**不猜**。「又卷六五」承前一條之書，還原時須傳前一條之 `book`。<br>`cited_in` 記**佚文從哪部書裡引出來**，`collected_by` 記**哪一位輯家把它輯進自己的書**，二者不同軸，勿混。<br>**`heading` 與 `piece_title` 不是同一件事，勿合併**：`piece_title` 是**這一條佚文自身之題**（嚴可均按撰人編次，一條即一篇，如〈上書諫伐匈奴〉）；`heading` 是**數條佚文共有之標目**（姚之駰按傳主編次，「光武皇帝」下繫四十七條）。一者標識自身，一者標識所屬。<br>`editor_note` 是輯家之案語（姚書原作【…】），是輯家之考，非本書之文，**不得與 `text` 相混**。<br>`text_from` 已去（八百條與 `attested_by` 逐字相同）。 |
| `coverage` | `{level, fragments_attested, fragments_recorded, text_available}`。<br>`level` 四級：`catalog`（僅知幾家輯過）→ `titles`（知輯本各篇之題）→ `text`（正文全錄）／`text_partial`（正文部分錄）。<br>`titles` 現無實例（嚴可均那批已升 `text`），定義保留待用。<br>`fragments_attested` 為 null 者是**未知**，非零——如據叢書目錄立檔，目錄不載條數。<br>**數家所得不同時，`fragments_attested` 取諸家所稱之最大數**，並以 `fragments_attested_note` 記其所以（《古文瑣語》嚴輯十九條、馬輯十五條、章宗源云十三事，取二十五）。 |
| `fragments[]` 之篇目條 | 有 `piece_title` 而 `text` 為 null，是「知其篇而未錄其文」，須並記 `text_status`，否則與「無文」無從分辨。 |

##### 輯佚叢書整理本（`type: fragment_collection`）

輯佚叢書（《玉函山房輯佚書》一類）之整理本，別於書目之 `catalog` 與考證之 `kaozhen`。
一類一檔，section 即一部輯本書，`work_id` 指其所輯之原書。
`coverage.level` 三級：`books_only`（僅知其書）→ `toc`（卷目已備）→ `text`（文本已錄）。
與輯佚檔之 `level` 同為英文而詞不同——彼記「這部書之佚文到了哪一層」，
此記「這部叢書之整理到了哪一層」，二事不同，故不強合。

**section 須自帶 `coverage`。** `fragments: []` 之義為「尚未錄入」而非「無佚文」，
無此欄則二者無從分辨。

雙向：整理本 `section.work_id` → 原書；原書輯佚檔 `collectors[].sections[]` → 整理本之條。

##### `loss_status` 枚舉

一軸而已：**本書之文今日尚存幾何**。欄位不存在 = 今存或未考，不必說明。

| 值 | 中文 | 界說與判準 |
|---|---|---|
| `lost` | 全佚 | **本書之文今日無一字存**——志書著錄其名而已，類書無所引，後人無所輯 |
| `partially_extant` | 殘存 | **確有本書之文存世而非全帙**。傳本殘卷、類書所引之佚文、後人之輯本，三者皆屬之——凡今日尚能讀到本書幾句者即是。泛言「殘缺」而不知所存何文者不足 |
| `extant` | 今存 | 全帙尚存。只在需要推翻既有推定時才明寫 |
| `undetermined` | 未詳 | 考過而不能定。與「欄位不存在」有別——後者是未考 |

**2026-08-21 訂正：輯本改判 `partially_extant`。** 原判準作「原書無一存。類書所引之佚文、
後人之輯本，皆不改其為全佚」，與本欄所宣之軸（「本書之文今日尚存幾何」）不自洽——
有佚文數條存世，「文尚存幾何」之答即非零。原判準實際所用之軸是**傳本是否斷絕**
（傳本尚在而缺卷者為殘存，傳本斷絕而賴他書徵引者為全佚），非「文存幾何」。
二軸不同，混書於一欄則定義自相牴牾。

今復歸本欄所宣之軸：**凡有文存世即 `partially_extant`，一字不存方為 `lost`**。

「傳本是否斷絕」不因此喪失——它由 `fragments` 檔之有無導出（見下「不入本枚舉」之第二條）：

| 現狀 | loss_status | fragments 檔 |
|---|---|---|
| 全帙傳世 | `extant` 或欄位不存在 | 無 |
| 傳本尚在而缺卷 | `partially_extant` | 無 |
| 傳本斷絕，賴類書徵引／後人輯佚 | `partially_extant` | **有** |
| 一字不存，唯志書存其名 | `lost` | 無 |

又：志書原文之「佚」字**不即本欄之 `lost`**。目錄學傳統之「佚」指傳本失傳，
與本欄之軸不同；志書所判記於 `indexed_by[].attested_status_raw`，本欄記本庫之判，
二者本已分立（見 IndexEntry 之 `attested_status` 條「不得逕改本記錄之 `loss_status`」）。

**殘存不用 `fragmentary`。** 西方書目學之 fragmentary 專指「只靠他書徵引之斷片存世」，
而本欄之 `partially_extant` 兼含傳本殘卷與徵引斷片二者，範圍廣於彼，用之則以偏概全。

**不入本枚舉的兩件事：**

- **出土**不是存佚狀態而是路徑。原書久佚而賴簡帛復見者，其狀態即 `extant` 或
  `partially_extant`；出土之事由該 Work 的 Book（簡帛實物）與「出土簡帛」Collection 承載。
  又：出土之書多數（本庫 257 部中 242 部）前所未聞，從無記載可失，本不需要此欄位。
- **有輯本**不是存佚狀態而是補救。由 `fragments` 檔之有無與 `collectors` 是否非空導出。
- **真偽**是另一軸。《古文尚書》今存而偽，《關尹子》今存而偽——併入本枚舉即無從表達。
  真偽由 `authenticity` 承載，見下。

#### `authenticity`（真偽，2026-08-21 增）

```json
"authenticity": "forged",
"authenticity_basis": "string（引提要或解題原文，逐條可驗）"
```

**只有一個值 `forged`，且只在確定是偽書時才寫。省略即無此疑義——這是絕大多數。**

不設 `genuine`。設了就得給七萬條填，而其中六萬九千條本無疑義；
與 `loss_status` 之 `extant` 同理（全庫只有 1 條，省略即今存）。
**只標異常，不標正常**是本庫體例。

##### 「舊題某某撰」不是偽書，不要往這個欄裡塞

這是兩件事，混了就都表達不出來：

| | 說的是什麼 | 怎麼記 |
|---|---|---|
| **舊題撰人** | **撰人之題不確**。書本身不假 | `authors[].role = "舊題撰"`，舊題撰人與實際撰人並列 |
| **偽書** | **書是後人偽造而託之於古** | `authenticity: "forged"` |

「舊題〔朝代〕某某撰」是四庫提要的常規措辭——《別本漢舊儀》「舊題漢議郎東海衛宏
敬仲撰」、《香譜》「舊本不著撰人名氏，左圭《百川學海》題為宋洪芻撰」——**這些都不是
偽書**。庫中實測：舊題撰人 327 條，真偽書約 100 條。

舊題撰人之形態見《西京雜記》`1ev3bcikfdiww`：
`authors[0]` 劉歆·漢·**舊題撰**，`authors[1]` 葛洪·東晉·撰。二人並列，一層不丟。

##### 判偽三戒

判之所據須逐條讀原文，**不可據關鍵詞機械判**。實測中三種假陽性最多：

1. **說的是別的書**——《長安志》提要「慎喜偽託古書」說的是楊慎，不是本志；
   《廣博物志》「《三墳》為毛漸偽撰」說的是它所引之書。
2. **是否定句**——《章申公九事》「知非偽託」、《尉繚》「證其書先秦已成，非後人偽託」、
   《歲華紀麗》「不由震亨之依託」。
3. **是泛論**——《卜法詳考》「其為輾轉依託，可以概見」說的是歷代卜書之通例。

又：**「缺 `period`」不是偽書的信號。** 實測全庫 43.7% 無 `period`，
而有偽託之語者只有 22.9% 無 `period`——後者**反而比全庫更常有**，
因為它們多半有四庫提要。勿以此為據。

##### 與 `period` 的關係

**`period` 一律標成書時代**（實際撰人之時），不標舊題撰人之時。
`period_basis` 須寫明「舊題某某（某代），實某代作，據某某」。
故《關尹子》：`period: song`、`authenticity: forged`、
`authors[0]` 尹喜·先秦·舊題撰——三層信息各得其所。

#### `period`（時代軸，2026-08-06 增）

```
pre-qin / qin-han / three-kingdoms / jin / nanbeichao / sui-tang /
five-dynasties / song / liao-jin-yuan / ming / qing / modern
```

**與 `authors[].dynasty` 分立，不取代之。** `dynasty` 是志書原文（「魏」「宋」「漢」），
改之則失其所本；`period` 是本庫之判，粗粒度而**無歧義**，供選集合之用。
判之所據記於 `period_basis`，逐條可讀。

立此軸之由：庫中 `dynasty` 有八十八種寫法，且歧義是實質的——
魏（曹魏／北魏）、宋（劉宋／趙宋）、周（先秦／北周／後周）、齊（南齊／北齊）、漢（西／東）。
不立此軸，「哪些是秦漢的」都選不出來。

##### 分段之則（2026-08-21 補記）

**以全國性王朝為骨幹，非全國政權按時段歸併。** 二則之外有一例外：

1. **全國性王朝各自成段**：`qin-han`、`sui-tang`、`song`、`ming`、`qing`
2. **非全國政權按時段歸併**：`three-kingdoms`（魏蜀吳）、`nanbeichao`（宋齊梁陳／北魏北齊北周）、
   `five-dynasties`（五代十國）、`liao-jin-yuan`（遼、金、元）
3. **例外：過短之全國王朝併入相鄰段**——秦十五年併入 `qin-han`，隋三十七年併入 `sui-tang`。
   庫中秦僅二十二條、隋僅一百零二條，單立無謂

`jin` 兼二則：西晉（全國）與東晉十六國（分裂）同段。

**明、清不併。** 二代存世著述最多（`ming` 10560、`qing` 15189，合佔全庫六成），
併之則此段大到無從整理。

##### `period` 只可分組，不可排序

分段之則既以政權為骨幹，時間上必有重疊：

| 重疊 | 年數 |
|---|---:|
| `song` × `liao-jin-yuan` | **319（全重疊）** |
| `five-dynasties` × `liao-jin-yuan` | 72 |
| `five-dynasties` × `song` | 19 |
| `three-kingdoms` × `jin` | 15 |
| `nanbeichao` × `sui-tang` | 8 |

遼（907–1125）與北宋同時，金（1115–1234）與南宋同時——宋為全國正統自成一段，
同時之遼金入「非全國政權合併段」，此是分段之則所必致，非缺陷。

**故 `period` 不得據以排序，不得用作時間軸。** 需時序者另立數值軸。

##### `period` 不是 `dynasty` 之函數，也不該是

`dynasty → period` 實測七十七種寫法中六十三種單射，然十四種一對多。
其中三類是**正當的**，正是本軸立此之由：

| 類 | 例 | 何以不同於 dynasty |
|---|---|---|
| 舊題撰人 ≠ 實際撰人 | 《西京雜記》`1ev3bcikfdiww` authors[0]「劉歆·漢·舊題撰」，authors[1] 方是「葛洪·東晉·撰」 | 判 `jin`。機械取 authors[0] 則誤作 `qin-han` |
| 跨代人物 | 《兵書接要別本》`1evfhd9qronpc` 撰人曹操 dynasty「東漢」（生年一五五確在東漢） | 其著作歸 `three-kingdoms` |
| 偽託作品 | 《關尹子》託名尹喜（先秦），實宋人作 | 應判 `song`。**此類尚未處理**，待 `authenticity` 欄 |

**故 `period_basis` 須逐條可讀**——判與 dynasty 相異者，其由必記於此。

判準三重，**皆可自驗**：

1. **粗粒度自消歧**：漢（西／東）皆 `qin-han`、齊（南／北）皆 `nanbeichao`——不必再問。
2. **著錄之志為時代上限**（`period_basis: catalog_bound`）：一書見於某志，其時代不得晚於該志。
   此是硬界非推論——《隋書經籍志》成於唐初，趙宋之書無由入之，故「宋」而見於隋志者必劉宋。
3. **斷代志可逕定**（`period_basis: duandai`）：撰人朝代闕而所著錄之志唯一且為斷代志者。
   何者斷代**以庫中資料自驗**（看其所著錄之書撰人朝代之分佈）：
   明史藝文志 明 98%、清史稿藝文志 清 94%、補晉書藝文志 晉 96%、後漢藝文志 98%、
   三國藝文志 93%、元史藝文志與補遼金元 96%。
   **而宋史藝文志宋僅 51%（唐 18%、漢 6%），是通代非斷代**——初版誤列，
   一舉要把八千三百餘條判為 song，此驗攔下。

   **例外：《清史稿·藝文志》之「輯佚」類目不入斷代之列**（2026-08-21 增）。
   該志各部類下有「輯佚」子目，著錄清人所輯之本——**其原書可極古**：
   《王粲英雄記》（東漢）、《張璠後漢記》（西晉）、《薛瑩後漢書》（三國吳）、
   《王肅國語章句》（三國魏）、《九家舊晉書》《倉頡篇續》《鄭記》之屬皆在焉。
   清史稿之 94% 斷代率是就全志而言，於此子目不成立。

   判別之法：條目之 `ai_note` 載「清史稿藝文志〈某部某類〉輯佚條目」者即是。
   實測本例外攔下 **105 條**——皆唯繫清史稿一志（duandai 之「志唯一」前提成立），
   而書實非清人所作，原判 qing 無據，已撤（見 `known-issues/duandai清史稿漏洞待覈.json`）。

   **並須以 catalog_bound 覆驗**：所定之值不得晚於本條所繫他志之上限。
   實測另攔下 14 條跨志相斥者（如《晉中興書》唯以清史稿判 qing，而其書見於隋志）。

判不出者留 null 並出清單（`known-issues/period未決.json`），**不猜**。

##### 以撰人之代定書之代者，須記撰人之代出自何處（2026-09-24 使用者定）

「書之代取自人、人之代又取自書」會成閉環：entity 之 `dynasty` 本是從其名下某書推出來的，
那書的 `period` 又據「撰人已定代 X」回填，兩邊互為證而其實都沒有證（李淑一案）。

**凡以「撰人已定代 X」為 `period_basis` 者，須同時寫明該 entity 之 `dynasty` 從哪裡來**
——CBDB／史傳／著錄／推定四者之一，如「撰人已定代明（其 dynasty 據 CBDB）」。
記了，閉環就自己顯形；不另立機檢。只治此後之新判，已有者不回頭補。

##### `period_upper`（時代上限，2026-08-21 增）

```json
"period_upper": "string (optional, 同 period 詞表。本書時代之上限——不得晚於此)",
"period_upper_basis": "string (據何志而定，含該志之上限，逐條可驗)"
```

**只給上限，不給下限。** 早期志書亡佚極多，一部漢代之書可能遲至《宋史·藝文志》方首見著錄——
故「首次著錄之志」**不可**當下限用。此點須守死，否則易誤用成「見於宋志即宋書」。

**不設 `period_lower`。**

**題中年號可為下限（2026-08-24 增）。** 上文所戒者，是拿「首次著錄之志」當下限；
書題自身所含之年號則不然——年號者，其事已行而後可名，故題含「熙寧」「開元」者，
其書必不早於該號之元年。此證出於書題，與著錄先後無涉，不犯上戒。

其用在**與上限相夾**：下限與 `period_upper` 同落一代者，其代即定，直接寫入 `period`，
不另立欄位（故仍「不設 `period_lower`」）。如《熙寧葬式》，題中「熙寧」元年 1068 落在
`song`，而其上限亦 `song`，上下既合，代乃定。實測全庫得 317 條。

**施之須防三誤**，皆已見於實測：

| 誤 | 例 | 防法 |
|---|---|---|
| 年號字面本是常語 | 《太極真人九轉還丹經》之「太極」乃道家之名，非睿宗年號；又「天啟」「元貞」「正德」「同光」「元符」皆可作常語 | 立**排除字表**，凡可作常語者不取 |
| 年號同名分屬兩代 | 「太和」「建元」「永平」「甘露」「黃龍」之屬，一名數代 | 同名數代者一概不取（`AMBIG`） |
| 子串偶合 | 《崇天曆》《明天曆》《應天曆》皆宋曆，而字面含元之「天曆」；《大中統類》含「中統」；《賈躭唐七聖曆》含「聖曆」 | 凡**下限晚於上限**者一律棄之——實測 32 條相斥，逐一驗之，無一真相斥，盡是子串偶合。此即以上限為篩，自去其偽 |

**只標於 `period` 為空或存疑者，不全庫標。** `period` 已定而無疑者標之徒增冗餘：

| 情形 | 處置 |
|---|---|
| `period` 有值，且 ≤ 其著錄志之上限 | **不標**——上限是冗餘 |
| `period` 有值，而 > 其著錄志之上限 | **相斥即錯**，先查錯，不標 |
| `period` 為空 | **標**——此時上限是唯一可篩之軸 |

實測（2026-08-21 末）：`period` 為空者 32669 條，其中 30188 條（92.4%）可得上限，2481 條無據。再補出土、子目、描述版本、叢編、歧義朝代五源後，上限覆蓋 31613 條（96.8%），餘 1054 條全無線索——故宮善本舊籍只記「鈔本」而無年者 706、無描述無著錄之空白條 243、有描述而不涉年代者 104、朝鮮 1。此 1054 條無 contained_in 可傳遞（實測可傳遞者 0），暫無他法。

**catalog_bound 作消歧幾乎無用。** 上文判準二舉「『宋』而見於隋志者必劉宋」為例，
實測全庫待消歧之 899 條（宋 842、周 41、蜀 13、魏 3）中僅 **3 條**可解——
歧義寫法之條目多出自宋志、國史經籍志、四庫，其志上限本已 ≥ song，分不開。
catalog_bound 之真價值在**驗證**（實測查出 437 條 `period` 逾限）與**上限標註**，不在消歧。

**陷阱：清代志書之「輯佚」類目。** 《清史稿·藝文志》各部類下有「輯佚」子目，
《四庫全書總目》《經義考》《書目答問》亦大量著錄清人之輯本、注本、校本——
**其所指原書可以極古**。故：

- 不得因見於清代志書即判 `qing`
- 判準三（斷代志）以清史稿為 94% 斷代，**有此漏洞**，據之所定者須覆核
- 實測 `period=qing` 而逾限之 108 條，其所繫：清史稿 73、四庫總目 35、經義考 17、書目答問 15

**上限之六源。** `period_upper` 不限於著錄志，凡可證「其時已有此書」者皆可為上限
（`scripts/period_bounds.py`，取諸源中最緊者）：

| 源 | 判語 | 例 | 實測 |
|---|---|---|---|
| `catalog_bound` | 一書見於某志，其時代不得晚於該志 | 見《直齋書錄解題》→ ≤ song | 28739 |
| `edition_bound` | 版本之年不早於成書之年 | 有「明嘉靖四十一年太醫院刊本」→ ≤ ming | 1021 |
| `excavation_bound` | 簡帛抄寫之年不早於成書之年 | 出清華戰國楚簡 → ≤ pre-qin | 19 |
| 志書子目斷代 | 目錄之類目自言其代者，即斷代之判 | 孫楷第《中國通俗小說書目》「宋元部」→ ≤ liao-jin-yuan | 686 |
| `collection_bound` | 叢編自限所收之代者，其代即上限 | 收入《續修四庫全書》→ ≤ qing | 548 |
| 歧義朝代取最晚解 | 消歧不成，上限猶可得 | 撰人作「宋」（劉宋｜趙宋）→ ≤ song | 600 |

五事須守：

1. **`edition_bound` 不可機械取。** 《周禮》有宋刊本而自是先秦典籍——上限止是上限，
   `period` 已定而不相斥者不動。相斥之判用**年份區間**（`PERIOD_YEARS`）而非 `ORD` 之序：
   `period` 是政權軸，song 與 liao-jin-yuan 全重疊 319 年，序上比會把遼行均《龍龕手鑑》
   （遼人之書而有宋刻本）誤判為相斥。實測相斥由 20 降至 5。
2. **今人影印、整理、景印之叢編不為據**（`MODERN_REPRINT`）——《中華再造善本》
   《續修四庫全書》所收原本可以極古，其叢編之年不限原書。
3. **今人目錄之卷次類目可為據，其書之成年不可為據。** 孫楷第《中國通俗小說書目》
   成於 1933（catalog_bound 得 modern 而無用），然其「宋元部」「明清講史部」自標所收之代，
   是為斷代之判。「存疑目」「附錄」之屬不入此列。
4. **`collection_bound` 取編者自定之收書下限，不取叢編影印之年**，二者與第 2 條不相妨：
   《續修四庫全書》1995 年影印而收書止於辛亥，故所收者無一晚於 qing。
   **世稱之收書範圍須實測覆核**：《玉函山房輯佚書》世稱「輯唐以前佚書」，
   實測所輯兼有宋人之書（《太平寰宇記佚文》《桂海虞衡志佚文》《後山談叢佚文》），
   「唐以前」不足為據，改據輯者之世（馬國翰 1794–1857）定 qing。
5. **歧義朝代名雖不能消歧，仍可得上限**（`AMBIGUOUS_LATEST`）——取諸解中最晚者：
   「宋」或劉宋（nanbeichao）或趙宋（song），無論何解皆 ≤ song。
   實測 600 條由此得上限，正是 catalog_bound 消歧無能為力之殘餘（見上文「899 條僅解 3 條」）。

**上限至軸首者即成定判。** `pre-qin` 為軸之首，無更早之代可容——故上限得 `pre-qin` 者
逕定 `period`，不止標 `upper`。實測 19 條（清華簡 17、郭店 1、上博 1）由此定為 pre-qin。
出土之書多數前所未聞、從無記載可失，志書一路皆無，此源是其唯一可斷之據。

`period` 亦入 `index/works/*.json`，選集合不必逐檔開啟。

#### `dynasty` 規範化（2026-08-08 增）

`dynasty` 是**直接顯示給使用者**的朝代名，現有庫中有一百三十五種寫法，含歧義（宋=劉宋/趙宋、
魏=曹魏/北魏…）、別名（後魏=北魏、姚秦=後秦）、誤錄（年號、帝王廟號誤入朝代欄）、域外
（日本、朝鮮）等問題。**直接規範 `dynasty` 本身**，不另設 `dynasty_norm` 欄位——使用者看到的
就應該是無歧義的學界通用名。

**規範化原則**：
1. **自明性優先**：規範名必須一眼能讀出所屬時段——三國系列必冠「三國」（三國魏、三國蜀、三國吳），南朝系列必冠「南朝」（南朝宋、南朝齊、南朝梁、南朝陳），宋分北宋/南宋。
2. **無歧義優先**：凡一字多朝者必加前綴（魏→三國魏/北魏、宋→南朝宋/北宋/南宋、蜀→三國蜀/前蜀/後蜀）。
3. **參照 CBDB**：規範名以 CBDB DYNASTIES 表為主要參照（冠詞三國、南朝不影響對應）；2026-10-07 起只作人工校對參照，不存 `c_dy` 碼（用戶定，#464）。
4. **保留原文於 `indexed_by[].title_info`**：志書原文（如「毛詩義問十卷魏太子文學劉楨撰」）不受 `dynasty` 規範化影響。
5. **`period` 為派生欄位**：`dynasty` 規範化後，`period` 可由 `dynasty` 自動歸併導出（南朝宋→nanbeichao、三國魏→three-kingdoms）。
6. **判不出者留 null 並出清單**（`known-issues/dynasty未決.json`），**不猜**。

**參考標準**：

| 標準 | 性質 | 是否分北宋/南宋 | 是否覆蓋十六國 | 是否覆蓋遼金西夏 |
|---|---|---|---|---|
| CBDB DYNASTIES 表 | 學術界公認（哈佛/中研院/北大） | 否（在 reign 層分） | 是 | 是 |
| GB/T 47681.2—2026 | 國標（日曆體系代碼） | 否 | 否 | 否 |
| 文物藏品時代分類代碼 | 行業標準 | **是** | 否 | 是 |
| 中研院史語所朝代代碼表 | 機構標準 | 否 | **是** | 否 |

無單一標準完全滿足文獻分類需求，故**以 CBDB 為主體，參考文物標準補南北宋，參考中研院補十六國**。

**規範朝代名完整枚舉**（按時序；2026-10-07 起與草稿庫 `schema-v2` 已入之 139 條 dynasty 條目逐字一致，overview#464）

> 本表首列即 `Entity.subtype=="dynasty"` 條 `primary_name` 之規範名來源（`check_v2.py` D1 讀此表）。條目化後改由 build 從條目生成、本表退為說明，**不得再手寫第二份**。
> 2026-10-07 起已刪 CBDB `c_dy` 列：本庫不與 CBDB 匹配、不存任何 `cbdb_*` 外部 id（用戶定，#464）。
> period 為默認值，**不反寫** `Work.period`；「null」＝無對應 period（非 12 值之一，如元末群雄、域外）。
> 北宋、南宋之上增「趙宋」（兩宋通稱，作上級條）；兩漢、十六國、十國為上級通稱條。

| 規範名 | period | 別名（庫中已有寫法；＊＝ambiguous，單獨不能定位） | 說明 |
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

**域外朝代**（不歸入 period 枚舉，`period` 留 null；日本、江戶時代、朝鮮、新羅、高麗已建 dynasty 條，韓國、英國、美國、比利時是國名不建條，`dynasty` 保持自由文本、`_dynasty_id` 留空）：

| 規範名 | 庫中寫法 | 說明 |
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

**需拆分的歧義朝代**（canonical 逐條判定，不自動歸併）：

| 原文 | 所含政權 | 判定方式 |
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

**跨朝代值**（粗粒度可定 period 者，canonical 逐條判）：

| 原文 | period | 說明 |
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

**垃圾值清理**（誤入朝代欄，應改為正確朝代或留 null）：

| 原文 | 處理 | 說明 |
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

**dynasty_basis**（判斷依據，逐條可驗）：
- `synonym`：同義歸併（三國魏→曹魏、後魏→北魏）
- `entity_death_year` / `entity_birth_year`：作者 Entity 生卒年判定
- `catalog_bound`：著錄志為時代上限
- `duandai`：斷代志可逕定
- `author_propagation`：同作者其他 Work 已判定值傳播
- `manual`：人工覆核

`dynasty` 規範化後同步更新 `index/works/*.json` 與 `index/entities/*.json` 中的 dynasty 欄位。

#### IndexEntry object type（`indexed_by` / `emendated_by` 共用）

```json
{
  "source": "string (著錄該書的目錄／志書／考證書名稱，如「漢書藝文志」「直齋書錄解題」)",
  "source_bid": "string (該目錄書的 Work ID)",
  "title_info": "string (該目錄中的著錄標題原文，如「毛詩義問十卷魏太子文學劉楨撰」)",
  "summary": "string (該目錄中的著錄／解題全文)",
  "section": "string (optional, 該目錄中的分類，如「經部/易類」)",
  "juan_count": "string (optional, 該目錄著錄的卷數原文)",
  "in_note_of": "string (optional, Work ID：本書非該志之正文所著，而見於另一條之注)",
  "attested_status": "string (optional, 該目錄書對此書存佚之判：extant / lost / partial / not_seen)",
  "attested_status_raw": "string (optional, 該書原文之字：存／佚／闕／未見)",
  "attested_status_note": "string (optional, 何以不上升為 loss_status)",
  "misattached": "boolean (optional, 本節非本書之著錄——同題異書誤併)",
  "misattached_note": "string (何以判為錯掛，逐條可驗)"
}
```

`misattached` 之設（2026-08-21）：catalog_bound 覆驗查出一批 Work 之 `period` 逾其
著錄志之上限，而該志之著錄語與本條撰人全不相干——同題異書被併為一條。
如司馬光《書儀》（song）上掛著隋志「《書儀》二卷蔡超撰」，清禪一《法喜集》（qing）
上掛著崇文總目「法喜集二卷」。

**標而不刪，亦不為之新建 Work。** 節之所指究竟何書，多數只有光禿禿的書名與卷數
（「明良集五百卷」），連撰人都無，除題名外無從配對，而題名相同正是當初誤併之由；
為之新建二百餘條極薄之 Work 不可逆，且與「撤薄條目」之向相反。標記則資訊全存，
日後考定即可升格。

**計 `period_upper` 時跳過標記者**（`scripts/period_bounds.py` 之 `tightest()`）——
否則本書之判永遠與非本書之著錄相斥。實測標 222 節（涉 177 條 Work），
`period` 與 `period_upper` 相斥者由 216 降至 38。

清單：`known-issues/著錄錯掛待建.json`。

`attested_status` 之設（2026-08-06）：《經義考》逐書判其存佚（御製題：「次列題注曰存曰闕曰佚曰未見」），
是本庫少見的成批存佚之據。**然不得逕改本記錄之 `loss_status`**——四庫御製題論此書自云
「所注闕佚未見者，今四庫所録往往其書尚存」，即朱彝尊判為佚、為未見者，修四庫時往往尚存。
其判是十七世紀一人之見聞，非事實，故記為「某書如此判」而繫於該源之下。
`not_seen`（未見）尤不可轉為 lost——那是「著者沒見過此書」，與「此書已亡」不同軸。

`in_note_of` 之設（2026-08-06）：《隋書經籍志》正文著見存之書，而以注記「梁有某書幾卷，
某人撰，亡」——梁時尚存而隋時已亡者。此類亡書在志中無獨立條目，只寄於某條之注。
故其 `summary` 是**那一條的原文全行**（含正文之書），而非本書自己的一行。
`in_note_of` 指出寄於誰，覆按時方知該在那一行的哪一段找。
無此欄則 summary 之首書名與本 work 之 title 不符，看起來像資料錯亂。

- `indexed_by`：本書被目錄書／志書**著錄**（文獻學引證，記「某志收有此書」）。
- `emendated_by`：本書被**考證／校勘類著作**校訂（記「某考證書對此書有辨正」），如《漢藝文志考證》《隋書經籍志考證》。二者結構相同，語義不同：前者是登記，後者是校議。

Book 的 `indexed_by` 與 Work 的 `indexed_by` 同結構，記錄該具體版本被目錄書/志書/考證書著錄的條目。場景：通俗小說書目這類目錄書中按版本著錄的條目（如「乾隆甲戌本脂硯齋重評石頭記」「王希廉評紅樓夢一百二十回」）應掛在對應的 Book 上，而非新建 Work。


`measures` 用於補充 `juan_count`，適合通俗小說等需要多維計量（卷+回+集+篇）的作品。

- **`juan_count.number` 是「這個數」，`juan_count.unit` 是「這個數的單位」，兩者同層**
  （2026-09-09 juan-unit 道改；此前這句話寫的是「`juan_count` 側重傳統「卷」維度，
  前端已使用」——**這句話本身就是《羋子》「十八篇」被渲染成「十八卷」那個 bug 的
  根源之一**：文檔一直承諾 `juan_count` 只裝「卷」，但實際錄入從未照這句話做過，
  漢志一類志書著錄的「篇」也一直被塞進同一個 `juan_count.number`。**渲染層讀
  `juan_count.number` 時必須同時讀 `juan_count.unit`，不可再預設「卷」**；
  `unit` 缺鍵時（全庫回填前的過渡狀態）寧可不顯示單位字樣，也不要顯示錯的。
- **枚舉是 18 個真量詞的閉集，不設「其他」桶**：卷｜冊｜篇｜回｜集｜編｜種｜則｜
  部｜章｜函｜首｜筆｜期｜節｜帙｜弄｜件——從全庫 `measure_info` 的「數字＋量詞」
  全量頻次表裡人工篩出（2026-09-09 juan-unit 道；統計見
  `overview/scripts/qa/reports/20260909-juan-unit/report.md` 表二），長尾也各自
  精確、量還很小，並入「其他」等於抹掉信息。
- **「不分卷」類為什麼不填 `unit`**：這批 `measure_info` 原文就是「不分卷」，
  `juan_count.number` 本來就是 `0`——不是「這個數的單位不知道」，是「這部書沒有
  卷這個維度」，填任何 `unit` 都是無的放矢，所以直接不填，也不必另設特殊值。
- `measures` 數組按原書順序排列，每項一個單位，用於**同一部書同時有不止一個計量
  維度**的情形（如通俗小說「六卷十六回」，卷是文本分卷、回是章節結構，兩維度都真）；
  `juan_count` 裝的是其中作為主計量的那一個數，不是另立一套。
- `measure_info` 是人類可讀的拼接展示（供 UI 直接渲染），例如「四卷二十回」、「八集四十回（每集五回）」。
- **已知：`measures[0].unit` 不能盲信為權威源**——2026-09-09 核驗發現 995 條
  `measures[0].unit` 與 `measure_info` 原文不一致（984 條集中在「國立故宮博物院
  善本舊籍」批次，該批 `measures.unit` 被整批錯填成「冊」）。回填 `juan_count.unit`
  一律以 `measure_info` 原文重新抽取為準，`measures` 只當交叉驗證參考。這批批次性
  錯誤本身未修，另行立案。
- `additional_works[].n_juan`（見上文）字面即「卷」，是「主體+附錄各自計卷」的
  另一個既有機制，與這裡的 `juan_count.unit` 不是同一件事，不要混用。

`additional_titles` 用於記錄同書的其他常用書名（別名/異稱）：
- 適用於有多個傳統名稱的經典：如《左傳》=《春秋左氏傳》=《左氏傳》=《春秋左傳》
- 適用於原書與通行名差異：如《春秋古經》=《古文春秋經》
- 與 `Entity.alt_names`（人物別名）平行設計，但 Work 級別僅存名稱字符串（無 type 區分）
- UI 應在搜索時匹配 `title` + `additional_titles` 全集

#### resources 的 group 字段（资源组）

`resources[]` 默认是扁平列表，每条独立。当多个 resource 描述**同一份内容**的不同存储/下载位置时（如：一份 PDF 同时挂在天一生水 / IA / 百度网盘），用 `group` 把它们关联起来。

**核心约定**：
- **同一 `group` 值**：表示是**同一份内容**的不同存储位置（镜像）。点开任意一个，下载下来内容字节完全等价（或仅水印/格式细微差别）。
- **不同 `group` 值**：表示是**不同变体**（如 人文社 1975 黑白本 vs 中華再造善本彩色本，或 完整本 vs 缺页本）。
- **无 `group`**：独立 resource，与现行行为完全一致（如识典/CText 这些独立整理本文本）。

**group_role**：
- `origin`：原始来源（如天一生水原本就有）
- `mirror`：我们做的备份镜像（如我们上传到 IA / 百度网盘）

**group_label / group_description**（推荐方式）：写在 Book/Work 顶层的 `resource_groups` 字典里，避免每条 resource 重复：

```json
{
  "resource_groups": {
    "<group_key>": {
      "label": "string (人类可读小标题，如「人民文学出版社 1975 年影印本」)",
      "description": "string (optional, 一段说明文字。可解释这一组为何独立成组，或它与其他组的区别)"
    }
  }
}
```

**向后兼容**：现有 resource 上的 `group_label` 字段仍读，但优先级低于 `Book.resource_groups[<gk>].label`。新数据写入 `resource_groups`；老数据按需迁移。

**示例**（庚辰本含两组同源资源 + 一条独立文本）：

```json
{
  "resource_groups": {
    "renmin-1975-bw": {
      "label": "人民文学出版社 1975 年影印本",
      "description": "人文社 1975 年首次影印庚辰本，黑白底本，含徐星署购书时附补 64/67 两回（据己卯本）。"
    },
    "zhsy100476-color": {
      "label": "中華再造善本 ZHSY100476 彩色高清",
      "description": "中华再造善本明清编据北大藏底本彩色精印，附胡适民国廿二年题记。"
    }
  },
  "resources": [
    { "id": "shidianguji", "name": "识典古籍", "url": "...", "types": ["text"] },

    { "id": "jiangyu-renmin1975", "group": "renmin-1975-bw", "group_role": "origin",
      "name": "天一生水", "url": "https://dropbox.jiangyu.org/...", "types": ["image"] },
    { "id": "ia-renmin1975", "group": "renmin-1975-bw", "group_role": "mirror",
      "name": "Internet Archive", "url": "https://archive.org/...", "types": ["image"] },
    { "id": "baidu-renmin1975", "group": "renmin-1975-bw", "group_role": "mirror",
      "name": "百度网盘", "url": "https://pan.baidu.com/s/...", "types": ["image"],
      "metadata": { "access_code": "abcd" } },

    { "id": "wikimedia-zhsy100476", "group": "zhsy100476-color", "group_role": "origin",
      "name": "Wikimedia Commons", "url": "...", "types": ["image"] }
  ]
}
```

**多群组同书示例**（己卯本：陶洙补抄本 vs 复原本）：

```json
{
  "resource_groups": {
    "taozhu-original": {
      "label": "陶洙補抄本（國圖藏，灰度膠片）",
      "description": "原稿入民國藏書家陶洙手後，添大量批註、補抄第 21-30 回闕葉等，現存國家圖書館。本組為國圖灰度膠片本，保留陶洙加工痕跡。"
    },
    "shanghai-1981-restored": {
      "label": "上海古籍出版社 1981 年復原影印本",
      "description": "上古社 1981 年影印時，盡可能剔除陶洙添加的批註與補抄痕跡，恢復清乾隆己卯（1759）抄本原貌。本組為現代學界引用最廣的版本。"
    }
  },
  "resources": [
    { "id": "shuge-jimao", "group": "taozhu-original", "group_role": "origin", ... },
    { "id": "nlc-17522", "group": "taozhu-original", "group_role": "origin", ... },
    { "id": "ia-taozhu-original", "group": "taozhu-original", "group_role": "mirror", ... },
    { "id": "baidu-taozhu-original", "group": "taozhu-original", "group_role": "mirror", ... },

    { "id": "jiangyu", "group": "shanghai-1981-restored", "group_role": "origin", ... },
    { "id": "ia-shanghai-1981-restored", "group": "shanghai-1981-restored", "group_role": "mirror", ... },
    { "id": "baidu-shanghai-1981-restored", "group": "shanghai-1981-restored", "group_role": "mirror", ... }
  ]
}
```

**UI 渲染逻辑**（前端实现指引）：
1. 把 `resources` 按 `group` 分桶；无 group 的每条单独成桶
2. 每桶头部：查 `Book.resource_groups[gk]`，渲染 `label`（小标题）+ `description`（小字说明）
3. 桶内列出 resource：站点名 + URL + 提取码（若有），origin 加角标
4. fallback：若 `Book.resource_groups` 未设，从组内某条 resource 读 `group_label`（兼容历史数据）

**向后兼容**：所有不带 `group` 的现有 resource 保持原扁平展示。

---

## 三、Collection（丛编）

一部丛书、丛编或影印汇编。**成员只有一种来源：成员一侧的 `contained_in`**（`Book.contained_in[].id`、`Work.contained_in[].id`、子丛编的 `Collection.contained_in`）。丛编档里不再列成员。

### 字段表

| 字段 | 谁存 | 取值 | 必填 | 示例 |
|---|---|---|---|---|
| `id`、`type`、`schema_version` | 本档 | 同 Work；`type` 恒为 `"collection"` | ✔ | |
| `subtype` | 本档 | `work_collection`｜`book_collection`，见〈Subtype〉 | ✔ | `"book_collection"` |
| `title`、`additional_titles` | 本档 | | ✔（`title`） | `"欽定四庫全書·文淵閣本"` |
| `description` | 本档 | Description 对象 | | |
| `authors[]`、`editors`、`publisher`、`publish_year` | 本档 | 编者、出版者；`authors[]` 形状同 Work，**`role` 必填**（overview#468，2026-10-07） | | |
| `publication_info`、`dating`、`edition` | 本档 | 出版信息；`dating` 形状同 Book | | |
| `current_location`、`holder` | 本档 | Location 对象；`holder` 现藏机构名 | | |
| `count` | 本档 | `{juan, ce, zhong, han, source}`，见下；至少一项非空才写 | | `{"juan":null,"ce":820,"zhong":24,"han":null,"source":"…"}` |
| `juan_count`、`page_count`、`measures`、`measure_info`、`total_works`、`total_volumes`、`sections` | 本档 | 规模与分部；`sections: [{name}]` | | |
| `contains[]` | 本档 | 本丛编的**结构组成部分**（圣谕、进表、总目、选印来源等）`{type, title, work_id?, book_id?, collection_id?, scope?, position?, note?}`，**不是成员** | | |
| `work_id` | 本档 | 本丛编整体对应的伞状作品（7 条） | | `"1ev…"`（《十三經注疏》） |
| `contained_in` | 本档（子丛编一侧） | **Collection ID 字符串数组**（注意：与 Book／Work 的对象数组形状不同） | | `["8rlcsybg2hih"]` |
| `indexed_by[]` | 本档 | IndexEntry | | |
| `related_books`、`related_collections` | 本档（id 较小一侧） | 对称关系，**ID 字符串数组**；只存 id 较小一侧。旧有 3 个对象形（带 `title`／`note`／`type`）由 M2 转成字符串，`title` 丢弃（build 派生），`type`／`note` 非空者列进 M2 报告待定去处（`check_v2.py` V14） | | `["8rlcsybg2hih"]` |
| `resources[]` | 本档 | 同 Book | | |
| `sources`、`ai_note`、`todo`、`review`、`revision`、`revised_at`、`updated_at` | 本档 | 共通字段 | | |
| ~~`books`~~、~~`contained_works`~~ | 他档：成员的 `contained_in` | build 生成 `_members`（分页）、`_member_count`、`_member_type` | 不写 | |
| ~~`classification`~~ | — | **Collection 不分类**（用户 10-07 定） | 不写 | |

**成员关系的数据跟着成员走**：册次（`volume_index`）、该书在本丛编里附带的子目（`sub_items`）写在成员的 `contained_in[]` 项里；部类（`section`）写在 `Book.section`。叢编增减成员**不改**丛编档，也不 bump 丛编的 `revision`。

**`count`（卷／册／种／函分列）**：吸收自 data_new v2 設計（overview `35-data_new詳細對比.md` §四·8、§七·2·3），是網站「收錄進度」狀態色要用的「應收總數」。
- 四項互不隱含、各自可空：`juan`＝卷數、`ce`＝冊數、`zhong`＝收書種數、`han`＝函數（多見於《四庫全書》寫本按函裝箱）。整數或 `null`，**至少一項非空才寫本欄位**，未知一律 `null`，不可用 0 佔位（0 隱含「不分卷」等實際語義，與「未知」不同）。
- `source` 必寫，說明數據取自何處（哪個既有欄位、`description` 原文的哪句話、是否為約數、是否經過訂正）。約數（原文帶「約」「餘」）可以照填，在 `source` 註明是約數；多說並存或量小而相對不確定（如「十餘種」）則本欄位留空，另在校驗腳本的拿不准清單中列出，不臆定。
- 與既有欄位不是同一件事，不互相取代：`juan_count`（頂層）曾被拿來塞冊數（如百衲本「820」實為 820 冊而非 820 卷），是歷史誤記，發現後訂正為 `null`，正確的冊數改記到 `count.ce`；`total_works`／`total_volumes` 若與 `description` 明文的卷冊數矛盾（如某條 `total_volumes` 實際存的是卷數），本欄位一律以 `description` 原文為準，不因與既有欄位同名而照抄。

---

## 四、Book（版本）

一部作品的一个具体版本／藏本／数字化本。**Book 是「它属于哪部作品」「它收在哪个丛编」这两条关系的唯一存储侧。**

### 字段表

| 字段 | 谁存 | 取值 | 必填 | 示例 |
|---|---|---|---|---|
| `id`、`type`、`schema_version` | 本档 | `type` 恒为 `"book"` | ✔ | |
| `title` | 本档 | 版本题名 | ✔ | `"周易正義（文淵閣本）"` |
| `work_id` | 本档（**Work↔Book 的唯一存储侧**） | Work ID；Work 页的版本列表 `_books` 由它反查。草稿 Book 可指向正式 Work | ✔ | `"1evl7l48e27ls"` |
| `edition` | 本档 | 版本名（文献学意义）；不写成 `version` | | `"清乾隆間寫文淵閣四庫全書本"` |
| `edition_type` | 本档 | 十一值闭集，见〈`edition_type`〉 | | `"刻本"` |
| `dating` | 本档 | `{era?, reign?, year?, year_range?, certainty?, source?, basis?, based_on?}`；方案见 overview `项目进展/古籍目录/整体设计/2026-09-年代字段统一方案.md` | | `{"era":"宋","reign":"紹熙","year":1193,"certainty":"inferred","source":"edition","basis":"…"}` |
| `contained_in[]` | 本档（**Book∈丛编的唯一存储侧**） | `{id, volume_index?, details?, sub_items?}`：`id` 丛编 ID；`volume_index` 册次（整数／数组／字符串）；`details` 自由文本；**`sub_items: [str]`（新增，可选）**＝该书在**这个丛编**里附带的子目（如《周易正義》在文淵閣本附《周易略例》），非空字符串数组 | | `[{"id":"8rl…","volume_index":[1,2],"sub_items":["周易略例"]}]` |
| `section` | 本档 | 该版本在所属丛编中的部类（是 `contained_in` 的属性，不是分类） | | `"經部/易類"` |
| `authors[]` | 本档 | 版本层的责任者（刻者、批点者等），形状同 Work，**`role` 必填**（overview#468，2026-10-07） | | |
| `publication_info`、`current_location`、`location_history`、`provenance`、`physical_description`、`base_edition`、`lineage`、`attached_texts` | 本档 | 见下各节；`lineage`／`base_edition` 只在后出者一侧，「谁以我为底本」由 build 生成 `_derived_by` | | |
| `volume_count`、`page_count`、`juan_count`、`measures`、`measure_info` | 本档 | 本版本自身的计量 | | |
| `description`、`additional_titles` | 本档 | | | |
| `indexed_by[]` | 本档 | IndexEntry（按版本著录的书目，如通俗小说书目） | | |
| `resources[]`、`resource_groups` | 本档 | 见下〈resources〉；`id` 可取 `wikisource`（维基文库页面，`types:["text"]`；sidecar `wiki_title` 并入者，可达性按 `validate-resources` 验，未验者在 `details` 注明「頁名取自舊對照表，未驗證」） | | |
| `related_books` | 本档（id 较小一侧） | 对称关系，Book ID 数组 | | |
| `zhsy_id` | 本档 | 中華再造善本编号 | | |
| `metadata` | 本档 | 来源系统原始字段透传，不规范化 | | `{"npm_item_id":"平圖021465"}` |
| `sources`、`merged_from`、`appendix`、`ai_note`、`todo`、`review`、`revision`、`revised_at`、`updated_at` | 本档 | 共通字段 | | |
| `_has_image`；旧 `has_full_text`、`has_digitalization` | build | 由 `resources` 推出 | **源档不写** | |
| `_has_text`、`_has_collated` | **暂留源档**（例外） | 依据在 book-text 整理本／全文，build 还推不出；等文本总管给出稳定来源再迁（目录总管 10-07 定，#459） | | |

### 示例（新格式）

```json
{
  "schema_version": 1,
  "id": "11q0000000abc",
  "type": "book",
  "title": "周易正義",
  "work_id": "1evl7l48e27ls",
  "edition": "清乾隆間寫文淵閣四庫全書本",
  "edition_type": "抄本",
  "dating": {"era": "清", "reign": "乾隆", "certainty": "attested", "source": "edition"},
  "contained_in": [{"id": "8rl…", "volume_index": [7, 8], "sub_items": ["周易略例", "考證"]}],
  "section": "經部/易類",
  "resources": [{"id": "wikisource", "name": "維基文庫", "url": "https://zh.wikisource.org/wiki/周易正義_(四庫全書本)", "types": ["text"]}],
  "revision": "1.0.0"
}
```

**`edition` 與 `sources[].version` 是兩回事**，勿混：
- `Book.edition`（頂層，22,842 條）＝**版本名**，文獻學意義上的「這是哪一個本子」。
- `sources[].version` / `sources[].processor_version`＝**處理程序版本號**（如 `"1.0"`），與書無關。

Book 頂層一律用 `edition`；曾有 276 條誤寫作 `version`，已於整理中歸併。

#### `provenance`（館藏，2026-09-28 增）

```json
"provenance": [
  {"institution": "國立故宮博物院", "call_number": "故善012603", "seals": [], "notes": "", "source": "metadata.npm_item_id"}
]
```

- **形狀照 data_new（v2）精簡**：數組，一書多藏本各一項；`institution` 非空字符串，
  `call_number` 為字符串（可空串）；`seals`／`notes` 可空；`source` 記本項據現行哪個
  欄位機械回填（如 `metadata.npm_item_id`／`current_location`），供覆核時回查。
  來歷與設計取捨見 overview [35 卡](../../overview/项目进展/古籍索引网站/进度/G-工具分发与网站/35-data_new详细对比.md) §四·5、§七·2。
- **與現行欄位的關係**：`provenance` 是新增之現藏機構＋索書號＋藏印之結構化記錄，
  **不取代** `current_location`（現藏地，113 條）與 `location_history`（遞藏史，77 條）——
  三者並存，`current_location`／`location_history` 原樣保留。
- **第一步只機械回填故宮**：`metadata.npm_item_id`（17,540 條，故宮統一編號即索書號）
  → 一項 `{institution:"國立故宮博物院", call_number:<npm_item_id>, source:"metadata.npm_item_id"}`；
  `seals` 按典藏號與資料倉 `open-guji-core/book_index_json`
  `library_data/臺灣故宮博物院善本古籍/`（`holding_id`＝典藏號）對照，對上的把該檔
  「藏印」類鍵填入，對不上的留空數組。`current_location`（約 113 條）裡能機械拆出
  機構＋索書號的一併轉入，拆不了的（多機構混列、無索書號等）不動，另列清單。
  行款（`physical_description`）、`edition_type`、`base_edition` 見 35 卡 §四·6、§四·4，另開卡。
- **校驗**：`.claude/qa/verify.py` 檢查有 `provenance` 的 Book——須為數組，每項
  `institution` 非空字符串、`call_number` 為字符串，否則算敗。

#### `physical_description`、`edition_type`（版本學著錄，2026-09-28 增）

```json
"physical_description": {"leaf_style": "半葉十行行二十字，白口，四周雙邊，單黑魚尾", "binding": "線裝", "dimensions": "框高21.5公分，寬15公分", "condition": "", "source": "…"},
"edition_type": "刻本"
```

接 S2（#129，`provenance` 已落）。承 overview [35 卡](../../overview/项目进展/古籍索引网站/进度/G-工具分发与网站/35-data_new详细对比.md) §四·6、§七·2·2。

- **`physical_description` 形狀照 data_new（v2）精簡**：物件，`leaf_style`（行款：半葉行數、每行字數、版心黑白口、邊欄、魚尾）／`binding`（裝幀：線裝、蝴蝶裝、包背裝、經摺裝…）／`dimensions`（尺寸，多為版框高廣）／`condition`（品相，缺葉、蟲蛀等）皆字符串；`source` 記本項據何而來（哪個現行欄位、哪批資料倉、或「description 原文抽取」），供覆核回查。**全是字符串，未知留空串**；四個內容子欄（`leaf_style`／`binding`／`dimensions`／`condition`）**至少一項非空才寫本物件**，否則整欄位不寫（與 `Collection.count` 同一慣例）。
- **`edition_type` 用受控小詞表**（十一值閉集，不設「其他」以外的兜底）：
  `刻本`／`抄本`／`稿本`／`活字本`／`石印本`／`鉛印本`／`影印本`／`套印本`／`拓本`／`印刷本`／`其他`。
  `印刷本`（2026-09-28 增，overview#233，据 #230 用戶答復）：現代出版社出版、非鉛印之印本，
  如膠印、平版、數碼印刷；與`鉛印本`之別在刷印技法非活鉛字排版。
  推不出者**留空不寫**（欄位不存在＝未考，與全庫「只標異常，不標正常」「判不出者不猜」的慣例一致），不設「不詳」佔位值。
- **回填來源一**（台北故宮 17,540 條，`provenance[].source == "metadata.npm_item_id"` 者）：按 S2 已寫的 `provenance[].call_number`（＝典藏號）與資料倉 `open-guji-core/book_index_json`
  `library_data/臺灣故宮博物院善本古籍/`（`holding_id`＝典藏號）對照，對上的把該檔 `extra` 的
  `行格`＋「；」＋`版式` 併入 `leaf_style`（原樣接續，保留站方措辭，**不挑詞、不重排**——
  只挑邊欄／口／魚尾三類詞會把線口、花口、粗黑口、細黑口與中縫等站方原文丟掉，2026-09-28
  協調者驗收①訂正）、`裝訂形式`（無則退 `裝訂`）→ `binding`、
  `版框高廣`（形如「23.5x14.5公分」，`版框高廣`四字本身即定「先高後廣」之序，故拆列為「版框高23.5公分，廣14.5公分」，不臆測改序）→ `dimensions`、
  `保存現況` → `condition`；`edition_type` 先取該檔 `extra.版本類型`，機械推不出時依次退用該檔 `edition`／`version`／本書自己的 `Book.edition`。
  對不上典藏號、或四個子欄全空者，`physical_description` 不寫。
  **同一 `holding_id` 可能是一函/一冊裝訂多部書之合訂號**（如《船山遺書》《古今說海》各書
  共用一個典藏號，241 部書撞號，2026-09-28 協調者驗收②所指）：須按書名（正規化去書名號、
  尾綴卷數，並歸併脈/脉、岩/巖、弦/絃、閒/閑、注/註等傳統異體字）與候選之 `bookName` 比對
  唯一命中方取用（`backfill_physical_description_npm.py` 的 `pick_record()`），仍二義（多為
  資料倉本身同名重出）或撞不上者**不寫** `physical_description`，列
  `.claude/qa/s2/physical_description-同號多書挑不出清單.json`——**不可依檔案讀入順序
  「後到蓋前到」取最後一條**，那會把甲書的行款／尺寸誤記到乙書名下。
- **回填來源二**（其餘 Book，`edition_type`）：由 `Book.edition` 文字機械推，規則見
  `.claude/qa/s2/backfill_edition_type.py` 的 `classify()`（如「刊本／刻本」→刻本、「鈔本／抄本／寫本」→抄本、
  「聚珍／活字」→活字本、「影印／景印」→影印本 等；「排印」技法兩可，須靠紀年助判——
  光緒／宣統以後，或紀年不詳但明寫「民國」者，歸鉛印本，2026-09-28 增，overview#233）；
  出土簡帛整理本、碑刻殘石、單一「清」字之類無法判別者**留空**，
  不強塞入某一類——這批本不是傳統刻抄印本的版本學意義上的「版」，塞入詞表反而失真。
- **回填來源三**（其餘 Book，`physical_description`，約 46～75 條）：只在 `description.text` 明寫行款原文
  （如「每半葉十行行二十二字，白口，四周單邊，無魚尾」）時抽取 `leaf_style`（偶帶 `dimensions`，如原文明寫
  「板框高19.9公分，寬14.5公分」），抽不全（如行款隨圖文分佈而每行字數不一者，只取半葉行數，不臆補字數）
  或拿不准者不寫，見 `.claude/qa/s2/backfill_physical_description_desc.py`。
- **校驗**：`.claude/qa/verify.py` 檢查——有 `physical_description` 的 Book 須為物件，四內容子欄與 `source`
  皆須為字符串，且四內容子欄至少一項非空；有 `edition_type` 的 Book 須落在上述十詞表內，否則算敗。

#### `base_edition`（底本／配補／參校，2026-09-28 增）

```json
"base_edition": [
  {"role": "底本", "name": "宋淳熙三年閩山阮氏種德堂巾箱本", "source": "dating.based_on+edition切分"},
  {"role": "配補", "book_id": "9897xxxxxxxx", "name": "…", "note": "…", "source": "lineage.derived_from"}
]
```

接 S2c（#190）。承 overview [35 卡](../../overview/项目进展/古籍索引网站/进度/G-工具分发与网站/35-data_new详细对比.md) §四·4、§七·2·2：v2 之 `base_edition[]` 承接現行 `dating.based_on`（273 條）與 `lineage.derived_from`（155 條）。

- **形狀**：陣列，每項 `role`（`底本`／`配補`／`參校`，閉集）、`book_id`（可選，指向本庫已有 Book）、`work_id`（可選，指向本庫已有 Work，用於只知其書未知其本者）、`name`（非空字符串，底本之名，如「宋淳熙三年閩山阮氏種德堂巾箱本」）、`note`（可選，佐證或按語）、`source`（非空字符串，記本項據何而來，供覆核回查）。`book_id`／`work_id` 至多填一項——本次回填兩者皆未用到，因所據底本多係本庫未另建檔之古本。
- **回填來源一**（`dating.based_on`，273 條）：`relation` 為 `翻刻`／`影印`／`傳鈔` 者→`底本`，`配補`者→`配補`；`name` 由 `Book.edition` 原文機械切分——搜該關係對應之動詞（翻刻類：覆刻／覆刊／翻刻／翻刊／重刊／重刻／重雕／翻雕／重摹；影印類：影鈔／影印／景印／影刊／景鈔／摹印；傳鈔類：傳鈔／傳抄；配補：配補），動詞在全文恰一見者取其後之文字為 `name`；「百衲本二十四史」一類（`edition` 作「百衲本·某本」，`dating.based_on` 雖標 `配補`而文中未必有「配補」字樣）另按「百衲本·(底本)(闕卷／原闕…以(配補本)配補)?」切分，可同時得底本、配補兩項。動詞不唯一、切不出、或切得結果過短（僅剩「本」字或標點等無實質內容）者不寫，入候選清單（22 條，多屬「關係動詞置於自身描述之後、未具名底本」，如「…修…重刊本」「…影印本」）。見 `.claude/qa/s2/backfill_base_edition_dating.py`。
- **回填來源二**（`lineage.derived_from`，`ref_type=="book"` 者，107 項）：`ref` 即本庫 Book ID，逐項驗其存在且非自指；按 `relation` 分三類機械對映：
  - →`底本`：翻刻／同系翻刻／翻刻補修／翻刻+改批／影印／石印／拓自／過錄／底本／據以抄錄／據以評／節選／刪節／刪節（學界主流說）／刪改／修訂／增補／截斷（同板印至第百回止）——共 85 項；
  - →`參校`：校改／參校／校改後印／校改加評／批校——共 13 項；
  - →`配補`：配補——1 項；
  - 其餘不寫：`合刊`／`混裝本`（非版本源流關係，語義與本欄無涉，不計入候選）共 4 項；`綜合`／`同系延伸`／`派生（剔田虎王慶+多本配補）`（關係含混，判不出唯一角色）共 4 項入候選清單。
  `ref_type=="hypothetical"`（57 項，`ref` 為內部假設底本代號如 `h_zhi_sisi_dingben`，非本庫 ID，`evidence` 亦無足以機械摘取之底本名）**全部不寫**，入候選清單。
  寫入者 `name` 取目標 Book 之 `edition`（無則退 `title`）；`note` 取原 `evidence`。見 `.claude/qa/s2/backfill_base_edition_lineage.py`。
- **另查**全庫 `description.text` 之「據某本影印」一類説明（影印叢編如四庫、再造善本、續修四庫全書等）：扣除已含於上二源者，只餘 2 條——1 條是他書引本條目為其底本（非本條目自身之底本關係，不算）、1 條原文自注「具體底本待考」（入候選清單）；未見另開回填來源之必要。
- `book_id` 掛連：因所據底本多為本庫未另建檔之古本，本輪以同 `work_id` 之 Book 逐一比對 `edition` 全文是否恰相同試掛，命中稀少（詳見 overview issue #190 驗收評論之統計）。
- 拿不准者（動詞切分失敗、`lineage` 關係含混、假設性底本無名可依、原文自注待考）寫入 overview 倉 `项目进展/古籍目录/进度/S2c-底本候选/candidates.csv`，**不寫本庫**。
- **校驗**：`.claude/qa/verify.py` 檢查——有 `base_edition` 的 Book 須為陣列，每項 `role` 須落在三詞表內、`name` 須為非空字符串、`source` 須為非空字符串；`book_id` 若填須存在於本庫且不得指向本書自身，`work_id` 若填須存在於本庫，否則算敗。

---

## 五、共用对象类型与 Subtype

### Source object type:
```json
{
    "id": "string (e.g., CX8nkEm1UAB)",
    "name": "string",
    "type": "bookID, url, etc",
    "details": "string",
    "position": "string",
    "version": "string (e.g. v0.1)",
    "processor_version": "string (e.g. v0.1)"
}
```
### Location Object type
```json
{
    "name": "string",
    "start_date": "string (YYYY-MM-DD)",
    "end_date": "string (YYYY-MM-DD)",
    "description": "string",
    "source": "Source"
}
```

### Description object type
```json
{
    "text": "string (Overview of the work)",
    "sources": ["Source"]
  }
```

IndexEntry（`indexed_by`／`emendated_by` 共用）见〈二、Work〉的〈IndexEntry object type〉。

### Subtype 字段说明

`subtype` 在 `type` 基础上进一步细分实体类别，便于前端展示、筛选与统计。

#### Work.subtype

| subtype | 含义 | 示例 |
|---|---|---|
| `book` (默认) | 独立成书的作品 | 《漢書》《論語》《紅樓夢》 |
| `article` | 单篇文章 | 《陳情表》《岳陽樓記》 |
| `poem` | 诗词 | 《春望》《水調歌頭·明月幾時有》 |
| `chapter` | 书中被单独拎出研究/索引的章节 | 《漢書·藝文志》《史記·太史公自序》 |

**判定规则**：
- 默认一律标 `book`，志书录入绝大多数都是书。
- 明确是书中一章且被单独索引（有 `related_works.relation == "part_of"`）→ `chapter`。
- 单位是"篇"且 number=1 或属于集部别集的单篇文章 → `article`。
- 单位是"首"或为诗词 → `poem`。

`chapter` 按需创建：不要把《漢書》的每一篇志都拆成 Work，只有被单独研究或作为目录书索引的才升格（例：《漢書·藝文志》需要被引用为 `source`，所以单独建 Work；《漢書·地理志》未被索引就不建）。

#### Collection.subtype

| subtype | 含义 | 示例 |
|---|---|---|
| `work_collection` | 作品的丛编（抽象层，跨版本） | 《二十四史》《四書》《四大名著》《十三經》《十三經注疏》 |
| `book_collection` | 书籍的丛编（具体版本） | 《二十四史百衲本》《欽定四庫全書文渊阁本》《武英殿聚珍版叢書》 |

**判定规则**：
- 有具体 `publication_info.year`（年份而非朝代）、具体 `current_location`、image 类型资源（扫描件）→ `book_collection`。
- 只有作品列表、无具体版本信息 → `work_collection`。
- 一个作品丛编（如《二十四史》）下面可以挂多个书籍丛编（百衲本、武英殿本），后者 `contained_in` 指向前者。

---

## 六、Entity（人物等实体）

抽象概念（作者、地名、朝代等），与书目平级。**Entity 档只存人物自己的信息；「他写了哪些书」由 `Work.authors[].entity_id` 反查**，build 生成 `_works`（含 `role`，取自 Work 一侧）。

### 字段表

| 字段 | 谁存 | 取值 | 必填 | 示例 |
|---|---|---|---|---|
| `id`、`type`、`schema_version` | 本档 | `type` 恒为 `"entity"` | ✔ | |
| `subtype` | 本档 | `people`｜`collective`｜`dynasty`｜`reign`｜`office`｜`place`，见〈Entity.subtype〉；後四種的專有字段見〈專名子類型〉 | ✔ | `"people"` |
| `primary_name` | 本档 | 最通行的名字 | ✔ | `"蘇軾"` |
| `alt_names[]` | 本档 | `{name, type, ambiguous?}`，type 见〈alt_names.type 枚举〉，`ambiguous` 见同节 | | `[{"name":"子瞻","type":"字"}]` |
| `aliases` | 本档 | 旧写法（13 条），形状同 `alt_names`，待并入 `alt_names`（〈附三〉） | | |
| `name_basis` | 本档 | 名字的依据 | | |
| `dynasty`、`dynasty_basis`、`period`、`period_basis` | 本档 | 同 Work 的规范名与时代轴 | | |
| `native_place`、`native_place_basis`、`title_or_office` | 本档 | 籍贯、官职 | | `"山陰"` |
| `birth_year`、`death_year`、`dates` | 本档 | 见〈Entity.dates〉 | | |
| `external_ids` | 本档 | `{cbdb_id, cbdb_match, cbdb_source, wikidata_id?, viaf_id?}` | | |
| `description`、`sources` | 本档 | 出处一律记 `description.sources` | | |
| `merge_history`、`merged_in`、`merged_into`、`retired`、`retired_reason` | 本档 | 并条与退役账 | | |
| `suppressed_fields` | 本档 | 人工确认 CBDB 值有误而清空的字段名 | | `["dynasty"]` |
| `ai_note`、`todo`、`review`、`revision`、`revised_at`、`updated_at` | 本档 | 共通字段（Entity 是否套 revision 机制未定，见 F3-3 §三） | | |
| ~~`works[]`~~ | 他档：`Work.authors[].entity_id` | build 生成 `_works: [{work_id, role, title, …}]` | 不写 | |

#### suppressed_fields（2026-09-26 用户裁：甲案）

人工核过、確認 CBDB 該欄之值有誤而清空者，把欄名列進 `suppressed_fields`，
`cbdb-sync/apply_enrich.py`（補空槽）逢清單裡的欄即繞開，不再拿 CBDB 之值
回填——原行為只認「欄現在是否空」，人清空一次、下一輪 enrich 就自動填回去，
俞安期、謝顯两例皆如此每跑一次就再犯一次。**只影响列名的欄**，其余空槽仍照常補。

`sources` 已定義但庫中無資料；Entity 的出處一律記在 `description.sources`。

#### Entity.external_ids.wikidata_id／viaf_id（2026-09-28 S4b，overview#159）

給有 `cbdb_id` 的 Entity 補 Wikidata 對齊，經 Wikidata 屬性 **P497**（CBDB ID）反查：

- 用 Wikidata 官方 SPARQL 端點一次性批量取全部 `?item wdt:P497 ?cbdb`
  （及 `wdt:P214` VIAF），不逐條請求；腳本見 `.claude/qa/s4/sync_wikidata_ids.py`。
- 按 `cbdb_id` 精確對；**一個 `cbdb_id` 對多個 Wikidata Q 的不寫**（列入衝突清單，
  人工另核）；已有 `wikidata_id` 者**不覆蓋**，與新取值不一致者列入衝突清單。
- `wikidata_id` 形如 `Q\d+`（如 `"Q123456"`）；`viaf_id` 為純數字字串；
  兩者皆 `optional`，缺省表示未取得或未對上，非零值。
- 校驗（`verify.py`）：`wikidata_id` 須匹配 `^Q\d+$`；`viaf_id` 須為純數字字串。

#### Entity.dates（2026-09-28 S4 新 schema 吸收④）

结构化生卒／活动年，逐步取代 `birth_year`／`death_year` 的展示用途——**本步只增不删**，
`birth_year`／`death_year` 原样保留并存，待网站改完展示后另开卡再删。

```json
"dates": {
  "birth": "integer | null（公历年，公元前用负数）",
  "death": "integer | null",
  "floruit": "[起, 止] | null（活动年区间，生卒不详时补）",
  "chinese": "string, optional（原文，如「嘉靖二年—萬曆元年」，无原文材料时省略）",
  "basis": "string（cbdb｜index_year｜現行字段｜…，自由格式凭据备注，非枚举）"
}
```

- `birth`／`death` 与 `floruit` 不共存于同一条：生卒已知就不必补活动年。
- `birth`／`death` 有值时，`basis` 记来源；机械迁移自 `birth_year`／`death_year` 者，
  `basis` 一律 `"現行字段"`。
- `floruit` 只在 `birth`／`death` 双缺、且能从 CBDB 侧另有旁证（如 `index_year`，
  即 `BIOG_MAIN` 的活动年代参考值）时补入，`basis` 记 `"cbdb:index_year"`；
  取不到旁证的不补、留 `dates` 缺省。
- 校验（`verify.py`）：`birth`／`death`／`floruit[0]`／`floruit[1]` 须为整数；
  `birth <= death`（两者皆有时）；`floruit[0] <= floruit[1]`；
  `dates.birth`/`dates.death` 若有值须与 `birth_year`/`death_year` 一致（两者皆有时）。

#### Entity.subtype

| subtype | 含义 | 示例 |
|---|---|---|
| `people` | 人物（作者、注家、编者等） | 蘇軾、王應麟、焦竑 |
| `collective` | 机构/官署/局所等非个人主体 | 郵傳部（hixhd2h9bv4m，`ai_note`："此非個人，乃官署、局所、書院、編…"） |
| `dynasty` | 朝代／政权（2026-10-07 转正，#464） | 趙宋、北宋、後金 |
| `reign` | 年号（2026-10-07 新增） | 建和（東漢）、萬曆（明） |
| `office` | 官职；`office_level` 区分概念条／具体条（2026-10-07 新增） | 知縣（概念）、知縣（趙宋）（具体） |
| `place` | 地名（2026-10-07 转正，第一期无条目） | — |

> 2026-09-09 C-entity 道核实补：production 实测 42 条 `collective`，此前未列入本表。

#### alt_names.type 枚举

活字典，持续扩——机械质检（`scripts/qa/qa_entity.py`）按此表判 WARN，
新增合法值就补进来，长尾罕见值先留 WARN 供人工按需并入，不强求一次穷举。

| type | 含义 | 对应 CBDB ALTNAME_CODES |
|---|---|---|
| `字` | 表字 | 4 |
| `號` | 号/室名别号 | 5 |
| `諡號` | 谥号 | 6 |
| `賜號` | 赐号 | 11 |
| `別名` | 其他别名 | 3 |
| `常用名` | 常用称谓（如「陽明先生」） | — |
| `簡體` | 简体写法 | — |
| `行第` | 排行称谓（如「李十二」） | — |
| `廟號` | 庙号 | — |
| `訛名` | 著录讹误而流传的名 | — |
| `異體` | 异体字写法 | — |
| `封爵` | 封爵称谓 | — |
| `俗姓` | 出家前本姓（僧道人物常见） | — |
| `簡稱` | 简称（如「宋」「漢」）；长度 ≤2 者常需配 `ambiguous` | — |
| `合稱` | 合称（如「兩宋」「春秋戰國」） | — |
| `避諱` | 避讳改字写法 | — |
| `別稱` | 别称（如「蜀漢」「劉宋」） | — |
| `雅稱` | 雅称 | — |
| `全稱` | 全称（**不参与匹配**） | — |
| `異寫` | 异写（用字不同而音义同，如「太平天国」） | — |
| `舊稱` | 旧称（专名子类型用） | — |
| `異稱` | 异称（专名子类型用） | — |
| `今名` | 今名（地名用） | — |

> 2026-10-07（#464）补 `簡稱`…`今名` 十项（专名子类型用，`異體`、`別名` 已有）。
>
> **`alt_names[].ambiguous`**：bool，缺省 false。为 true 表示这个名字**单独不能定位**到本条
> （如「宋」「漢」「魏」「太守」）；匹配时一律出 `ambiguous`、候选全带出，永不 `matched`。
> 写在每一个声称该名的条目上。校验（A1）：带 `ambiguous` 的名字全库须有 ≥2 个条目声称
> （含以它作 `primary_name` 的 dynasty，如「後漢」），否则 WARN（标记多余）。
> 新增之专名子类型里 `alt_names[].type` 不在本表即 ERROR（O12）。
>
> 2026-09-09 C-entity 道核实补以上 6 种：production 全库按出现频次为
> 著錄形(121)／小字(40)／小名(26)／著錄原形(21)／法號(20)／本名(16)／舊著錄形(15)／
> 殘名(13)／異寫(11) 等，长尾还有 20 余种个位数值，未逐一收表，留 WARN 供人工按需并入。

#### 專名子類型：`dynasty`／`reign`／`office`／`place`（2026-10-07，overview#464）

依據：overview `項目進展/古籍目錄/整體設計/專名建檔/給S-字段清單.md`（N 定稿，用戶 10-07 答復 #464）及該目錄 D／O／P 設計檔；與設計檔相左處以清單為準。

**硬約束**（用戶定）：① 不與 CBDB 匹配，**不存任何 `cbdb_*` 外部 id**；條目內容全部自寫，仍按 CC0 發布；CBDB、CHGIS、DILA 只作人工校對參照。② 第一期不填 `wikidata_id`（字段留位，CC0 來源，將來再填）。③ 地名第一期不建條目，只立字段；不帶坐標。④ 官職兩層：每朝一條具體條＋跨朝概念條。

**共用**：`id`、`type`、`subtype`、`schema_version`、`primary_name`（必填）、`alt_names[]`、`description`、`ai_note`、`review`、`revision`、`revised_at`、`updated_at`（同〈十〉）。**源檔一律不寫 `_` 起首字段與反向列表**（`children`、`reigns`、`index_in_reign`、`holders`、`compounds`、`successors`、`people` 等，build 派生，見〈九〉）。

**共用增改**：

1. `alt_names[].type` 新增十項、`alt_names[].ambiguous`，見〈alt_names.type 枚举〉。
2. `Entity.dates` 按 subtype 放行：`people`→`birth／death／floruit`（＋`basis`、`chinese`）；`dynasty`／`reign`→`start／end`（＋`basis`、`chinese`）；`office`／`place` **不用 `dates`**（起訖在 `start／end` 或沿革項裡）。
3. `external_ids` 在四個新子類型裡**只許 `wikidata_id`**（`^Q\d+$`，第一期不填）；出現任何 `cbdb_*`、`chgis_id`、`dila_*` 即校驗失敗。`people` 的 `cbdb_id` 等不受影響。
4. 禁字段：`translation`、`c_office_trans`、`cbdb_alt_names`（授權硬約束，防日後順手搬進來）。

##### `dynasty`（朝代／政權）

| 字段 | 取值 | 必填 | 說明 |
|---|---|---|---|
| `parent_id` | dynasty id | | 單父，上溯深度 ≤3（如 春秋吳→春秋→東周→先秦）；子列表由 build 派生 `_children` |
| `dates` | `{start:int, end:int\|null, basis:str, chinese?:str}` | 中國朝代必填 `start`；域外可缺 | 公元年，公元前負數、無 0 年，閉區間 |
| `period` | 現有 period slug \| null | 中國朝代宜填 | 只作默認值，**不反寫** `Work.period` |

`primary_name` 與〈`dynasty` 規範化〉之〈規範朝代名完整枚舉〉（含〈域外朝代〉表）**逐字一致**；條目化後枚舉改由 build 從條目生成，不得再手寫第二份。

##### `reign`（年號）

| 字段 | 取值 | 必填 | 說明 |
|---|---|---|---|
| `dynasty_id` | dynasty id | ✔（所屬政權無條目時在 `ai_note` 說明） | 頒行當時的政權（天命、天聰取「後金」） |
| `ruler` | `{name:str, entity_id?:str}` | `name` 必填 | `entity_id` 須指向 `people`；庫中無該帝王條時只寫名 |
| `dates` | 同 dynasty | `start` 必填 | 改元當年記為起年 |

`index_in_reign`、干支不寫（build 派生）。同朝同名年號區間不重疊；`(primary_name, dynasty_id, dates.start)` 全庫唯一。

##### `office`（官職，兩層）

| 字段 | 適用層 | 取值 | 必填 |
|---|---|---|---|
| `office_level` | 全部 | `concept`｜`concrete` | ✔ |
| `parent_id` | 具體 | 概念條 id | 有概念時填；**概念條不得有**（概念只一級） |
| `dynasty_ids[]` | 具體 | dynasty id 數組（宋默認「趙宋」，北南宋有變才拆） | 具體 ✔；概念不得有 |
| `function` | 具體 | 本朝職掌（自寫） | 具體 ✔ |
| `office_class` | 具體 | 職事官／差遣／散官／階官／加官／貼職／寄祿官／祠祿官／勳／爵／本官／試秩／憲官／兼職差遣／未詳 | |
| `rank`、`salary` | 具體 | `{text, basis}`（自寫） | |
| `start`、`end` | 具體 | 整數公曆年 | |
| `institution_ref` | 具體 | 官署條 id（`collective_kind=官署`）；不得寫 `COL:<名>` 占位（O14 第二步，2026-10-07 起；新官署先建條） | |
| `base_office_id`、`qualifier{kind, name, target?, note?}` | 具體（固定複合） | `base_office_id` 指同朝**具體**條；`kind` ∈ `institution`／`place`／`mode`／`mode+institution` | 複合時 ✔ |
| `succeeds` | 具體 | 前代概念或具體條 id | 只留字段位，第一期不填 |
| `basis` | 具體 | 本條依據（自由格式） | 具體 ✔ |

概念條不得有 `dynasty_ids`、`rank`、`salary`、`office_class`、`base_office_id`。複合條與其 base 的 `dynasty_ids` 須相交。

##### `collective`·官署（`collective_kind=官署`，兩層＋合稱；2026-10-07 S 定，overview#464 P3c）

官署不另立 subtype，仍是 `collective`，加 `collective_kind` 區分；**只有 `官署` 受下表約束**，其餘取值與缺 `collective_kind` 之舊條（缺省＝`未分`）照舊。設計與裁定見 overview `項目進展/古籍目錄/整體設計/專名建檔/P3c-官署-設計.md`（§十一 N 裁定、§十二 S 定）。

| 字段 | 適用層 | 取值 | 必填 |
|---|---|---|---|
| `collective_kind` | 所有 collective | `官署`｜`書院學校`｜`館局`｜`民間`｜`未分` | 官署 ✔ |
| `institution_level` | 官署 | `concept`（概念）｜`concrete`（每朝具體）｜`group`（合稱，如六部、東宮） | ✔ |
| `parent_id` | 具體 | 官署概念條 id（與 office 同義：具體→概念；概念只一級） | 有概念時填；概念、合稱不得有 |
| `dynasty_ids[]` | 具體 | dynasty id 數組；默認一朝一條，**各字段完全一致**才許多值合併（`ai_note` 標【合併條】） | 具體 ✔ |
| `function` | 具體 | 本朝職掌（自寫，一句即可） | 具體 ✔ |
| `basis` | 具體 | 依據（不得含「待核」） | 具體 ✔ |
| `start`、`end` | 具體 | 整數公曆年；有把握才填 | |
| `superiors[]` | 具體 | `{id, start?, end?, note?}`，`id` 指同朝**具體**官署條；只寫下級→上級（下屬由 build 派生）；隸屬有變用 `start/end` 分段 | |
| `group_ids[]` | 概念或具體 | 合稱條 id；成員→合稱單向。跨朝不變掛概念條，隨朝而變掛具體條 | |
| `description` | 概念、合稱 | 同 Entity 通用 | 概念、合稱 ✔ |
| `succeeds[]`、`location_id` | 具體 | 第一期**只留字段位**：`succeeds` 不填（承繼寫 `description`）；`location_id` 禁出現 | |

- 概念條、合稱條不得有 `dynasty_ids`、`function`、`basis`、`superiors`、`start`、`end`、`parent_id`；合稱條另不得有 `group_ids`（不嵌套），亦不帶朝代。
- 不設 `rank`、`institution_class`；不得有官職專有欄（`office_level`、`office_class`、`rank`、`salary`、`base_office_id`、`qualifier`、`institution_ref`）；`external_ids` 只許 `wikidata_id`（同 E1）。
- 新建官署條不寫舊式 `dynasty`／`period` 字符串（朝代名由 build 自 `dynasty_ids` 派生）。
- `_children`、`_subordinates`、`_members`、`_offices` 由 build 派生，不入源檔（build 實現排在合 main 之後，屬產物契約改動）。
- 跨概念同名之別名（如都察院(明) 之「御史臺」）照 office 規則標 `ambiguous: true`。
- 正式庫已有之官署 collective（兵部、禮部、樞密院…）之原地升格以正式庫補丁為之，**正式庫條不得指草稿 id**。

##### `place`（地名；第一期只立字段，不建條目）

| 字段 | 取值 | 說明 |
|---|---|---|
| `history[]` | `{start, end, dynasty_ids[], name, level, parent_id?, parent_text?, note?}`；非空必填 | 一地一條＋沿革（不拆每朝一條）；上級寫在下級沿革項；`level` ∈ 國／郡／州／府／軍／監／路／道／省／縣／廳／都；`end` ≤1912；項時段不重疊（可有空檔） |
| `modern` | `{text, adcode?, relation, note?}` | 今地對照；`adcode` 為 GB/T 2260 六位碼；`relation` ∈ 同名同地／治所今在／轄域約當／沿用其名而異地／無對應 |
| `predecessors[]` | `{id, kind, year?, note?}`，`kind` ∈ 析出／並入 | 寫在後繼一側 |
| `coords` | 預留 | **第一期禁止出現**；將來只許 Wikidata（CC0）或自測 |

##### 校驗碼（`.claude/qa/check_v2.py`；實現在 `.claude/qa/entity_subtypes.py`，`verify.py` 共用同一份）

ERROR 計殘留，WARN 只報不計（`check_v2.py` 之 summary 分列）。

草稿库查专名时加 `--ref-root <book-index>`：草稿条目的 `dynasty_ids`、`parent_id` 等可以直接指正式库 id（专名升格后的规范写法），引用解析会认正式库的 Entity；跨条目检查（D1 唯一、P09 同名、I10 疑重复等）仍只在本仓内比，两仓同名条不算重复（overview#464，2026-10-07）。

| 碼 | 查什麼 | 級別 |
|---|---|---|
| E1 | 四子類型出現 `cbdb_*`、`chgis_id`、`dila_*`、`translation`、`c_office_trans`、`cbdb_alt_names`；`external_ids` 含 `wikidata_id` 以外之鍵；非 place 之 `coords` | ERROR |
| D1 | dynasty `primary_name` 在規範名枚舉內；全庫唯一 | ERROR |
| D2 | `parent_id` 存在、是 dynasty、無環、上溯深度 ≤3；子朝代 `dates` 落在上級之內（容差 1 年） | ERROR／WARN |
| D3 | `dates` 鍵按 subtype 放行；`start ≤ end`；整數；無 0 年；`period` 為現有 slug；有 `period` 而缺 `start` | ERROR（末項 WARN） |
| R1 | reign 之 `dynasty_id`、`ruler.name`、`dates.start`、唯一性、同朝同名不重疊、`ruler.entity_id` 為 people；`dates ⊂ dynasty.dates`（容差 5 年） | ERROR／WARN（越界 WARN） |
| A1 | `alt_names` 之 `name` 非空、`ambiguous` 為 bool；`ambiguous` 之名全庫 ≥2 條聲稱；無 `ambiguous` 之 dynasty 別名在 dynasty 內全局唯一 | ERROR／WARN |
| O01–O05、O09–O12 | office：O01 `office_level`；O02 具體條 `dynasty_ids`／`function`／`basis` 與概念條禁字段；O03 `office_class`；O04 `parent_id`；O05 `base_office_id`／`qualifier`／dynasty_ids 相交（指向概念條而無 `ai_note` 為 WARN）；O09 `start/end` 整數且 `start ≤ end`；O10 簡稱長度 ≤2（WARN）；O11 同概念下同朝具體條重複（WARN）；O12 `alt_names[].type` 在枚舉內。O06（CBDB 碼防重）已刪；O07 併入 V01；O08 併入 E1 | ERROR／WARN |
| P01–P11 | place：P01 `primary_name`、非空 `history`、`level`；P02 項時段；P03 `parent_id` 存在且為 place、不自引、無環，`parent_text` 與 `parent_id` 並存 WARN；P04 `dynasty_ids` 存在；P05 併入 V01；P06 `modern`；P07 `predecessors`；P08 `coords` 出現即失敗；P09 同名異地組（INFO）、同名同上級鏈疑重複（WARN）；P10 某沿革段寫了 `parent_id`，上級在該段年份內須有沿革段覆蓋（端點相接算覆蓋），否則 WARN，應在空檔處拆段、上級留空（2026-10-07，P5a 試點）；P11 某沿革段之年份須為其 `dynasty_ids` 各朝代起訖之聯集覆蓋（端點相接算覆蓋；朝代缺起訖者不查），否則 WARN——元明、明清之際等交替年份要補掛前朝或拆段（2026-10-07，P5a-3） | ERROR／WARN／INFO |
| I01–I12 | 官署（`collective_kind=官署`）：I01 `collective_kind`／`institution_level` 枚舉；I02 具體條 `dynasty_ids`／`function`／`basis`（不含「待核」）必填、概念與合稱禁欄、概念與合稱 `description` 必填；I03 `parent_id` 指官署概念條；I04 `superiors` 指同朝具體條、不自指、無環、`start/end`（朝代不相交 WARN）；I05 `group_ids` 指合稱條（與概念條重複掛 WARN）；I06 `start/end` 整數、無 0 年、`start ≤ end`（越出朝代 5 年 WARN）；I07 同概念同朝重複（WARN）；I08 外部 id 與官職專有欄；I09 `location_id` 禁、`succeeds` 出現 WARN；I10 同名朝代重疊疑重複（WARN）；I11 派生欄；I12 官職 `institution_ref`：須指官署條、指具體條須朝代相交、指概念條須 `ai_note` 標「待補」（WARN）、官名含部名而指合稱（WARN）、id 不在本庫（WARN）；`COL:<名>` 占位一律 ERROR（O14 第二步，替換 PR draft#97 合入後） | ERROR／WARN |
| V01 | 源檔出現 `_` 起首或 `children`、`reigns`、`index_in_reign` 等派生／反向字段（新子類型不享 `_has_text`／`_has_collated` 豁免） | ERROR |

> 口徑（S 預審，2026-10-07）：上下級區間不合（如戰國止年晚於東周、北朝起年早於南北朝）、年號越出所屬朝代區間，一律 WARN，不是 ERROR。

#### Work.authors.entity_id

每个 `Work.authors[i]` 通过 `entity_id` 引用对应的 people Entity；**这是 Entity↔Work 关系的唯一存储侧**，Entity 档里不再写 `works`。

```json
"authors": [
  {
    "name": "蘇軾",
    "role": "撰",
    "dynasty": "北宋",
    "entity_id": "12xabc..."
  }
]
```

- `name` / `dynasty` / `role` 保留 —— 便于显示、搜索、兜底（entity_id 为空时仍可用）；**`role` 必填**，Entity 页上的角色取自这里。
- 「舊題撰」与「託名」语义不同（传统归属 vs 伪托），不统一（用户 10-07 同意）。
- CBDB 相关信息（`cbdb_id` / `cbdb_match` / `cbdb_source`）**不**存在 Work 里，而是归到 Entity 的 `external_ids`。

---

## 七、關聯詞表（`related_works[].relation`）

**「存儲方向」一栏决定源档写不写这个词。** 成对关系只在规范方向一侧写一次；反向词只出现在构建产物 `_related` 里（`direction: "in"`）。存量里的反向项：M2 先在规范侧补写，M3 删除（`check_v2.py` V04）。

| relation | 存儲方向 | 反向（只在 build 产物中） | 含義 |
|---|---|---|---|
| `part_of` | **源档写**（部分 → 整体） | `has_part` | 整體 ↔ 部分（**確係同一本書之內**的篇卷，如《繫辭》之於《周易》）。<br>版本附屬部帙（外集、別集、附錄之屬）**不循此路**，見〈版本附屬部帙〉一節。 |
| `studies` | **源档写**（注本／研究 → 原典） | `studied_by` | 本書研究、注解、考證某書 |
| `contains_text_of` | **源档写**（承载者 → 被承载的原典） | `text_carried_by` | 本書載有某書之全文（注本載原典之文；一部原典下可有近千承载者，故不存在原典侧） |
| `preceded_by` | **源档写**（续作 → 前作） | `followed_by` | 續作／前作 |
| `related` | **源档写，存 id 较小一侧**（字符串比较） | `related`（另一侧由 build 补） | 泛關聯，語義不明確時的兜底；两侧原各有 note 者拼成一条 `note` |
| `collected_in` | 源档写（单向） | —（build 可生成 `_incoming`） | 收入某彙編（指 Work 或 Collection） |
| `derived_from` | 源档写（单向） | — | 由某書輯出、改編而成 |
| `adapted_from` | 源档写（单向；取代成对的 `has_adaptation`） | `has_adaptation` | 改編自 |
| `pseudepigraph_of` | 源档写（单向；取代成对的 `has_pseudepigraph`） | `has_pseudepigraph` | 偽託於某書 |
| `excerpted_from` | 源档写（单向） | — | 摘錄自 |
| `source_of` | 源档写（单向） | — | 為某書之所本 |
| `suspected_same` | 源档写（单向） | — | 疑與某條同書，待考 |
| `same_entry` | 源档写（单向） | — | 書目中同一條著錄 |

**已归并、不再使用的词**（迁移 M2 机械改写，`check_v2.py` V05）：`commentary_on` → `studies`；`related_to` → `related`。
不在上表的词一律不写（`check_v2.py` V13 报「未识别」）；要加新词先在 overview#451 提。

**成对关联只写规范方向，反向由 build 生成**（取代旧规「成對關聯必須雙向寫入」）。
`collected_in`／`derived_from` 等单向词同样只写一条；需要在对面留痕时**不要**手写反向——build 会在对方产物的 `_related`（`direction:"in"`）或 `_incoming` 里列出。
**`related_works[].title` 不写**：对方题名由 build 取其现行 `title` 回填（旧规「應與目標 Work 的 title 一致」作废，其漂移校验随之作废）。
写关系请用 `bim link A B <relation>`（按规范方向与小 id 规则落笔）。

---

## 八、分类（`classification/`，2026-10-07 起；取代 Work.`classification` 字段）

一个分类法一个目录，分类归属不写在 Work 档里。设计见 overview `F3-2-设计与备选.md`（用户 10-07 定稿）。

```
classification/
  README.md                 格式、命令、校验规则
  schemes.json              全部分类法登记
  zongmu/                   《中國古籍總目》（主分类法）
    tree.json               分类树
    members/zm0810.json     集部／別集類 的成员（一类一档）
  <其他分类法>/ …           结构同上
```

| 文件 | 形状 | 规则 |
|---|---|---|
| `schemes.json` | `[{id, name, primary, exclusive, tree}]`，如 `{"id":"zongmu","name":"中國古籍總目","primary":true,"exclusive":true,"tree":"zongmu/tree.json"}` | `primary:true` 的分类法是 `_classifications[0]`；`exclusive:true`＝一书只能归一类 |
| `<scheme>/tree.json` | `{scheme, name, nodes:[{id, label, parent, level, retired?}]}` | 节点 id（如 `zm0001`）**永不变、永不复用**；改类名只改 `label`；删类＝标 `retired:true` 并移走成员，不删行；数组顺序＝显示顺序 |
| `<scheme>/members/<节点id>.json` | `{node, members:[[work_id, source], …]}` | 一行一条，**按 work_id 排序**；`source`＝来源目录书／原文类目（如 `"經義考/易"`），供回查；**不存 `basis`**（用户默认删，见〈附三〉）；行尾预留可选 `status`（`adopted`｜`candidate`｜`revoked`）口子，本轮不用 |

- **任何节点都是合法归属点**：挂在有子类的节点上＝已分到此层、下面未细分。**不再有「未分類」占位节点**（旧 138 个，543 部迁移时上移到父节点）。
- **Collection 不分类。**
- **写入口只有 `bim classify`**（`assign`／`move`／`rename`／`check`），任何人不手改成员档；并发由排班管写域，万一两道在同一类档末尾追加撞车，`classify check --fix` 合并（两边都留、按 id 重排）。
- **校验（`classify check`，并入 verify）**：① 节点存在且未 retired；② `work_id` 存在于本仓（草稿库可指正式库）；③ 互斥分类法下一部 work 只出现一次；④ 互斥时同一 work 不在两个成员档里。
- **build 回填**：每部 Work 的产物得 `_classifications: [{scheme, node, path, l1, l2, l3, l4, source}]`，**不产出旧字段 `classification`**；读者「`_classifications[0]` 优先、旧 `classification` 兜底」。列表卡片里的分类只写节点 id，不写标签。
- **不进成员档的东西**：`indexed_by[].section`（目录书原文类目，是引文证据）、`Book.section`（丛编内位置）。
- **分类变化不 bump Work 的 `revision`**（F3-3：分类是编排，不是对作品的陈述）。
- 草稿库同构（`book-index-draft/classification/`）；草稿 Work 升格时 `promote` 把它的成员行改 id 搬进正式库类档。

旧字段 `Work.classification` 的形状、`basis` 的 S/A/B/C 含义、09-30 总目词表迁移的归属规则表，见〈附二 已刪之欄位〉；归属规则本身（小说入子部、诗文评入集部…）仍有效，现由 `tree.json` 的节点体现。

---

## 九、构建产物与派生字段（`_build/`、`index/`）

`build/build_derived.py`（Python 标准库；草稿库同一脚本 `--root` 指向）读全部源档＋`classification/`＋`promotions.json`，生成：

| 产物 | 内容 |
|---|---|
| `_build/entry/<id>.json` | **页面就绪条目**＝源记录原样＋全部 `_` 派生字段。网站与 bim 打开一条记录只读这一个文件，不再现场 fetch 别的记录 |
| `_build/members/<cid>/<n>.json` | 丛编成员分页（每页 200） |
| `_build/catalog/<work_id>/<n>.json` | 志书著录成员分页 |
| `_build/lineage/<work_id>.json` | 预汇的版本图 |
| `_hubs.json` | 枢纽条目（被引用超 200 次的丛编／志书／大人物）的名称表；其他产物里对枢纽只写 id |
| `index/**` | 检索用扁平摘要（原 `reindex.py` 并入 build） |

性质：纯函数、可重跑、确定性（同一份源 → 逐字节相同的产物）；`_build/` 不进 git（`.gitignore`）。由网站 `bundle-data.mjs` 打包前调用，bim 本地用 `bim build`。build 自校验：源档里不存在应派生的字段、条数守恒、派生值自洽（`_edition_count == len(_books)`）、悬空引用清单。

### 派生字段清单（只在 `_build/entry/` 里出现，源档一律不写）

| 记录 | 派生字段 | 内容 | 取代的旧源字段 |
|---|---|---|---|
| Work | `_books` | 版本摘要列表，按 `Book.dating` 排，无年代按 id | `Work.books` |
| Work | `_edition_count` | `len(_books)` | 手写 `_edition_count` |
| Work | `_catalogs` | 每个 `indexed_by[].source_bid` 一条：志书题名、作者朝代 | — |
| Work | `_related` | 双向展开的关系 `[{id, title, relation, direction:"out"\|"in", note?}]`，反向词在此出现 | `related_works[].title`、手写反向词 |
| Work／Book | `_collections` | `contained_in` 解出题名 | — |
| Work | `_authors` | 与 `authors[]` 同序，内嵌 Entity 摘要 | — |
| Work | `_classifications` | 见〈八〉 | `Work.classification` |
| Work／Book／Collection | `_has_image`（及 `_has_text`、`_has_collated`） | 由 `resources`、整理本 manifest 推；**`_has_text`／`_has_collated` 迁移期仍以源档旧值为准、暂留源档**（见〈十〉例外） | 手写 `_has_image`、旧 `has_text` 等 |
| Work（志书） | `_member_catalog` | 指向 `_build/catalog/<id>/` | — |
| Book | `_work`、`_siblings`、`_lineage_refs`、`_derived_by`、`_lineage_graph_ref` | 所属作品摘要、同作品其他版本、源流引用、谁以我为底本、版本图 | — |
| Collection | `_members`、`_member_pages`、`_member_count`、`_member_type`、`_children` | 成员（来自成员侧 `contained_in`）、计数、型别、子丛编 | `Collection.books`、`contained_works`、手写 `_member_*` |
| Entity | `_works` | `[{work_id, role, title, …}]`，`role` 取 `Work.authors[].role` | `Entity.works` |
| Entity（dynasty） | `_children`、`_ancestors`、`_reigns` | 子朝代、上级链（由近到远，≤3 层）、所属年号 `[{id, name, start, end, ruler, dynasty}]`（按 start） | —（F6-5b，`build/names.py`） |
| Entity（reign） | `_dynasty`、`_ruler`、`_index_in_reign`、`_same_name` | 所属朝代摘要；帝王摘要（`ruler.entity_id` 有才出）；同一朝代、同一帝王名下按 start 的序号（从 1 起）；全库其他同名年号 | —（同上） |
| Entity（office） | `_children`、`_compounds` | 概念条下的各朝具体条；以本条为 `base_office_id` 的复合条。卡片 `{id, name, level, dynasties}`。~~`_holders`~~（任职人物）暂不产出：库中尚无人物→官职数据 | —（同上） |
| Entity（官署，`collective_kind`＝官署） | `_children`、`_subordinates`、`_members`、`_offices` | 概念→具体（`parent_id` 反查）、下级（`superiors` 反查）、合称成员（`group_ids` 反查）、所属官职（`office.institution_ref` 反查） | —（同上） |
| Entity（place） | `_children`、`_span` | 下辖（`history[].parent_id` 反查，卡片带下级的 start／end）；`{start, end}`＝各沿革段最小起年、最大讫年 | —（同上） |
| Entity（people）／Work | `_dynasty_id`、`_dynasty_candidates` | 按 `dynasty` 名（Work 取 `dynasty`，缺则 `authors[]` 首个）查 `dynasty_reign_keys`：唯一且不歧义给 `_dynasty_id`，否则给候选 id 列表 | —（同上） |
| 构建产物 | `_build/dynasty_reign_keys.json`、`_build/office_keys.json`、`_build/place_keys.json` | 匹配键表（`primary_name`＋`alt_names`，全稱除外，含异体归一形；带 `via`、`ambiguous`；地名另以沿革段当时名、去通名为键，候选带 `segments`、`default`），供文本侧回挂；形状见 overview `专名建档/P4-升格/*-交接.md`。同一条在一个键下只出一次。草稿库 build（带 `--ref-root`）才是全量 | —（同上） |
| 草稿记录 | `promoted_to` | 由 `promotions.json` 回填（index 与产物里） | 手写 `_promoted_to`、`promoted_to` |

字段的精确形状以 overview `F2-3-build与派生字段.md` 与 `F4-2-聚合产物字段表.md` 为准，本表只列名与来源。

---

## 十、記錄之共通欄位

以下欄凡 Work／Book／Collection／Entity 皆有。

| 欄位 | 義 |
|---|---|
| `schema_version` | 主記錄自 `1` 起。**輯佚檔（`fragments`）別為一族，已在 `2`，二者不同源，勿混。** |
| `revision`、`revised_at` | 版本號（`"1.0.0"` 形）與最後改版時間。級別（patch／minor／major）見 overview `项目进展/古籍索引网站/整体设计/2026-05-版本控制与不可变性.md`；**字段口径見下**。缺 `revision` 者（正式庫 1,113 部）是升格漏初始化，另案補。 |
| `updated_at` | 這條最後一次被人碰的時間（ISO 8601）。現值自 git 該檔最後一次提交回填——**不一律填「現在」**，假時間比沒有更壞。 |
| `zhsy_retrieved_at` / `authors[].cbdb_retrieved_at` | 外部對齊之取得時間。現存皆 `null`（批次匯入時未記），**新增對齊必填**。`cbdb_match: none` 者是查而否決，亦有此欄。 |
| `todo` | 條目級待核清單 `[{what, by?, date?}]`；做完即移除該項，不留「已辦」標記。只定義形狀，不批量回填。 |
| `review` | 人工審核狀態 `{status, by?, date?}`，`status` ∈ `unreviewed`｜`reviewed`｜`disputed`；欄位不存在即 `unreviewed`。 |
| `ai_note` | 整理者寫給整理者的注，見〈ai_note 的用法〉。 |
| `_` 起首者 | **源檔一律不寫**。派生欄位只在 `_build/entry/` 裡（清單見〈九〉）。舊規「`_` 欄可寫、校驗重算比對」作廢：源檔出現任何 `_` 欄即 `check_v2.py` V01。<br>**例外（2026-10-07 目錄總管定，#459）**：`_has_text`、`_has_collated` 暫留源檔、M3 不刪不改名——其據在 book-text 整理本／全文，build 尚推不出（實測 295／65 條只有源檔舊值）；待文本總管給出穩定來源再遷。check_v2 對此二欄豁免。 |

### revision 的字段口径（F3-3）

**`revision` 管的是「這部作品『是什麼』的陳述」是否變了**：題名、作者、年代、描述、卷數、存佚、真偽、資源、著錄原文、關係（存儲一側）、並條賬——變了算，按原設計定級別。
**不算**（變了不 bump、也不刷新 `revised_at`）：分類歸屬（`classification`／類檔）、`books`、一切 `_` 派生欄與舊 `has_*`、管理欄（`updated_at`、`revision`、`revised_at`、`schema_version`、`id`、`type`、`path`）。
**未登記的新欄位按「算」處理**；要加不算的欄，須登記進 `NO_BUMP_FIELDS`（overview `F-数据结构/试验/F3/revision_fields.py`）並在卡裡說明。
推論：單向存儲後改一條關係只 bump 存儲一側那一條記錄；Collection 成員增減不 bump 叢編；Book 的 `work_id`、`contained_in`、`lineage`、`base_edition`、`section` 變化算 Book 自身的改版。
**遷移腳本一律不改 `revision`／`revised_at`**（遷移不是作品變化）。

### 派生欄位為何要加底線（沿革）

`has_text` 之現狀曾是「有的對、有的錯、大半沒有」——它與手寫欄長得一模一樣，遂無人知其該不該在、值對不對。2026-08 起派生欄加底線並由 `verify.py` 重算比對；**schema-v2 更進一步，派生欄整個移出源檔**，只在構建產物裡出現，從根上杜絕手寫。

**`index/` 之欄不加底線**——整個檔都是派生產物，檔級已說明此事，欄再加底線是重複。

---

## 十一、ID 类型编码

ID 用 64-bit snowflake 结构，3 bits 标识 type：

| type 值 | 名称 | 含义 |
|:---:|---|---|
| 0 | Book | 具体书籍/版本 |
| 1 | Reserved1 | (保留) |
| 2 | Collection | 丛书 |
| 3 | Work | 作品 |
| 4 | Entity | 抽象实体（人物/地名/朝代...） |
| 5-7 | Reserved | (保留) |

**0-3 用于实体书目，4-7 用于抽象概念。** 见 `book_index_manager/id_generator.py`、`.claude/qa/mintid.py`（base36、小写、`< 2^63`）。

草稿庫的 ID 為 13 字元（status=1），升格後的 Production ID 為 12 字元（status=0）。
**升格的權威對照表是根目錄的 `promotions.json`**；草稿記錄裡**不寫** `promoted_to`／`_promoted_to`（schema-v2 起由 build 回填到 `index/` 與產物）。
校驗關聯是否懸空時，Production ID 不在草稿索引中屬正常，須併入白名單。
「id 較小一側」（對稱關係的存儲規則）按**字符串比較**：同長度的 base36 小寫 id，字符串序與數值序一致。

---

## 十二、录入判准

### 原典與注本：分層與繫連（2026-08-21 決）

一部經有幾百家注。注本**各自成 Work**，以關聯詞繫於原典，不併入原典條。

#### 規則

> `authors[0].role` 為**注、傳、疏、箋、章句、集解、義疏、音義、注疏、集注、
> 補注、校注、正義、疏證、集釋**之屬者，該 Work 是**注本**，
> 必繫 `contains_text_of` 至其原典 Work（寫在注本一側）；原典側之 `text_carried_by` 由 build 生成，**原典源檔不寫**。

**題名**從其志書原題，**唯與原典之題完全同字時**須冠注者名以別之
（《古文尚書》鄭玄注 → 題《古文尚書鄭玄注》）。
題中已有體裁字樣者（《周禮注疏》《春秋穀梁傳集解》）**不必再冠注者名**，冠之反而累贅。

#### 何以不併入原典

本庫已有五十五個原典錨，運轉良好：

| 原典 | 繫其下之注本 |
|---|---:|
| 周易 `1evl7l48e27ls` | 1,041 |
| 偽古文尚書 `1evd3dbcb0nb4` | 386 |
| 論語 `1ev7w0euvaeww` ／ 詩經 `1evl7hsxvr7cw` | 各 379 |
| 孝經 `1evl1xugdoikg` | 300 |
| 左傳 · 漢書 · 禮記 · 周禮 · 儀禮 · 孟子 · 公羊傳…… | 252～93 |

併入即是把一千零四十一部書壓成一條，磁鐵之極致。

#### 一個容易誤判的形態

`authors[0].role` 是「傳」而題名不含其人名者，**未必是注本誤題**——
《左傳》`1ev7vo50ar94w` 的 `authors[0]` 是「左丘明·傳」，那是原典本身的體裁
（左丘明傳《春秋》），不是「左丘明注左傳」。**改題之前先看它是不是錨。**

#### 坊刻編本（纂圖互注之屬）是獨立 Work，不是原典的版本（2026-08-24 使用者定準）

判準只有一條：**成書之結構與內容與原書不一致者，即是一個新的 Work**——
加了注釋是新書（周易鄭玄注不是周易），所加之注即使只是抄他經之語（「互注」）也是
注釋；加圖表（「纂圖」）、加標記層（「重言」「重意」）、彙數家之注而新編門目，皆同。
新 Work 與原典以 `contains_text_of` 相繫。

實例：南宋建陽坊刻《纂圖互注毛詩》——卷首舉要圖二十五幅、正文全錄大小序及毛傳
鄭箋釋文、采左傳三禮為互注、標重言重意（陸元輔：「唐宋人帖括之書」）——結構全非
《毛詩》之舊，是獨立 Work。《纂圖互注揚子法言》《新纂門目五臣音注揚子法言》同。

連帶三則：**(1)** 此類編本之 `authors` 不繫原典撰人（揚雄不是纂圖互注本的編者；
編者不詳即空），**(2)** `period` 從成編之世（坊刻多宋），不從原典撰人之代，
**(3)** 其所掛 Book 須清點——普通原典刊本誤堆於編本條下者，移繫原典（或注本）條。

---

### 一條 Work 記錄代表什麼（2026-08-21 決）

#### 先建 Work、後補 Book 是正常次序

一部書先有作品記錄、日後再補實物記錄，這是本庫的正常工作次序，不是缺陷。

**Work 之來源為版本目錄者（國立故宮博物院善本舊籍、續修四庫全書、
四庫全書存目叢書、中華再造善本之屬），仍是作品記錄，不因來源而降格。**
實測此類 15,185 條中，**12,272 條（81%）是庫中該書的唯一記錄**——
若因其來源是版本目錄就視為「版本條」，等於把八成正當的作品記錄判成雜質。

#### 一部書、數部藏本 → 一個 Work、數個 Book

同一部書在同一部版本目錄中有數部藏本者，應為**一個 Work、數個 Book**，
不是數個 Work。

#### 缺字訂正之後必須回頭查同題

匯入時題名帶缺字者，**彼此比對不上，去重會漏**。庫中實例：
《訒庵集古印存》與《恆軒所見所藏吉金錄》各有二條，同出故宮善本目錄，
一條首字作 U+FFFD 替換符、一條作私用區 PUA 字元，故匯入時「無同名 Work」而各建一條；
分兩次訂正缺字之後題名才相同，重出方才暴露。

**故：訂正缺字之後，須以新題回查全庫同題，不可訂完就算。**

---

### 同題二條，何時是重出、何時是二書（2026-08-22 定）

同題而疑重出者，判之之法**不在題名，在著錄**。以下各條皆自 size=2 同題組
七百六十九次合併與千餘次不併之實測所得，逐條可驗。

#### 一、卷數之異：同志則疑，異志則不疑

| 情形 | 判 |
|---|---|
| 二條同出**一志**而各有全著錄語、卷數復異 | **疑二書**——是該志之兩著錄 |
| 二條分見**二志**而卷數異 | **不作二書之證**——各志所據之本不同，卷數本多歧 |

《褚仲都講疏》十卷／十六卷同出新唐志，是二書；《地理書》陸澄一百五十卷
（國史）與一百四十九卷（隋志）則是一書。**此二者方向相反，不可混用。**

**又有一種卷數之異全非二書之跡**：併者所取乃附錄／別集之卷數。四庫作
「《文正集》二十卷、《別集》四卷、《補編》五卷」，遂切出《范文正集》二十卷
與四卷兩條；《顏魯公集》十五卷／《補遺》一卷、《乖崖集》十二卷／《附錄》一卷
皆同。**此類卷數異反是同一著錄條被切兩次之跡**——且附錄別集依
〈版本附屬部帙〉本不當另立 Work。

#### 二、裸繫一源而無著錄語者，多是重出

一側僅繫一志而 `indexed_by[].title_info` 為空，而該志之全著錄語另一側已有
——是同一著錄條被切兩次。此型於直齋書錄解題尤多。

#### 三、志書之「又」例：同題而別是一書

《舊唐書經籍志》作「《春秋左氏傳例》七卷。**又十五卷，杜預撰。**」
——「又」是志書之例，謂同題而別是一書（別本或他家所撰），**非重出**。

#### 四、《漢志》一名分列二略者是二書

《漢志》同一書名分見諸子略與兵書略者，部類異、篇數亦異，是二書：

| 書 | 諸子略 | 兵書略 |
|---|---|---|
| 師曠 | 小説 六篇 | 隂陽 八篇 |
| 力牧 | 道 二十二篇 | 隂陽 十五篇 |
| 龐煖 | 從横 二篇 | 兵權謀 三篇 |
| 五子胥 | 雜 八篇 | 兵技巧 十篇 |
| 李子 | 法家 三十二篇 | 兵權謀 十篇 |

#### 五、出土簡帛與後世同名之書，只是題名巧合

**併之則兩事俱毀。** 馬王堆帛書《易傳》之〈繫辭〉× 元保八《繫辭》二卷；
阜陽漢簡《大事記》（竹簡編年記事，起西周迄漢初）× 宋呂祖謙《大事記》
二十六卷；出土《脈法》× 元黃大明《脈法》三卷；睡虎地《日書》×
國史經籍志譚融《日書》三卷。

判別之法：其 `description.sources` 或 `ai_note` 載出土整理報告者即是。

#### 六、一方無撰人者，先問其 role

一方有撰人而一方無者，**存者之 role 若為注／傳／疏／集解，則無撰人之一方
疑即原典**——《歸藏》(無撰人) 與《歸藏薛貞注》(薛貞) 是原典與注本之別，
注家有其創作，本為二物，**絕不可併**。role 為撰／編／輯者方可依上列各條續判。

#### 七、撰人異名之辨：看兩名在庫中之份量

撰人名一字之差者，混著真異人與形訛，且真異人多是名家——蘇軾／蘇洵／蘇轍、
陸雲／陸機、曹操／曹丕、阮福／阮元、劉熙／劉珍、毛萇／毛亨、吳鼒／吳鼐。

**分之之法：訛字之名於全庫不繫任何作品，正名則繫十數部。** 以「弱名繫 0 部
且強名繫 ≥5 部」為準方可斷為形訛（朱喜→朱熹、呂楠→呂柟、戴雲→戴震、
王誾運→王闓運、李容→李顒、劉嚴→劉表）。份量相當者一律不併。

**名相含亦未必一人**：《棋品序》陸雲（晉，繫八部）× 陸云公（南朝梁）。

#### 八、比對書名之前必先簡繁歸一

以嚴格相等比對著錄語所題之書名，實測擋下三十九組，逐一看去**三十八組是
假陽性**——異體（龜鑑／龜鑒、寶／寳、歷／歴、略／畧、鉅／钜、祕／秘、
羣／群、決／决）與連書省撰人式著錄（「曾肇曲阜集」對《曲阜集》）。
須以 OpenCC 歸一、補異體表、剝去「梁有」「欽定」等冠首語，方餘真異者。

**且不可用子串比對**：《新刻出像增補搜神記》因「搜神記」是其子串而被放行，
而該條實混裝——題名為明增補本，所繫隋志、舊唐志之著錄語卻作《搜神記》三十卷。

#### 九、合併之際：存者可依源數而取，撰人之名須另判

存者依 `indexed_by` 源多者而取，是常法。**然訛名那一側之著錄源可能反多**
——實測十組形訛中有四組如此，遂使《荊州占》存「劉嚴」而非「劉表」、
《二曲集》存「李容」而非「李顒」。

**故取存者之後，須另判其撰人之名孰正**，訛形入 `alt_names`。
此誤之跡見於 `chk.py`「人物→作品 單向」上升——正名之 Entity 所 claim 之書落了空。

#### 十、合併之後必須同步者

- `index/works/*.json`（title／path／author／role／dynasty／period／juan_count…）
- **`index/books/*.json` 之 `work_id`**——Book 改指而此處未同步，
  `chk.py`「索引欄位不符」即現
- ~~Entity `works[]`~~：schema-v2 起 Entity 不存作品列表，改 `authors[].entity_id` 即足；**但撰人之名孰正須另判**（見上條）
- 隨遷之 `fragments/*.json`：其**檔內 `work_id` 須隨路徑改**，
  且存者之 `ai_note` 須記其檔位（`chk.py` 以 ai_note 含 `fragments/` 為據）
- 隨遷之 `collated_edition/*.json`：只做精準字串替換，不整檔重寫
- **被併者在分類類檔裡的成員行**（`classification/<分類法>/members/`）：改為存者之 id 或刪去（存者已有歸屬時），經 `bim classify`，不手改
- 他條指向被併者之引用，只改**存儲一側**的欄位：`Book.work_id`、`contained_in[].id`、`authors[].entity_id`、規範方向之 `related_works[].id`、`indexed_by[].source_bid`、`Collection.work_id`／`contained_in`；反向與展示副本由 build 重生，不必改
- `index/` 由 build 重生（併入前仍跑 `reindex.py`）

---

### 版本附屬部帙：不新建 Work（2026-08-21 決）

書目書（直齋書錄解題、四庫總目之類）著錄一部集子時，往往在同一條解題下
連記數事：《昌黎集》四十卷、《外集》十卷、《附錄》五卷、《年譜》一卷、
《舉正》十卷……匯入時每事各成一節（section），節題只作《外集》《附錄》，
不成書名。這些節該不該各建一個 Work？**分兩類，判準是「是不是同一本書」，
不是看書名。**

#### 甲、該版本之附屬部帙 —— 不新建 Work

**外集、別集、後集、續集、續編、續稿、內外制集、附錄、目錄、序、雜記、
附益、圖** 之屬，凡與正集**一同刊印、隨本而存**者：

- 書目書說的是「**某某本**所包含者」——即使分冊，也是一起印出來的一部書。
- 這些部帙**歷史上從不被視為單獨的書**，也沒有哪個版本單獨印一部《附錄》
  或《外集》行世。
- 故它們是**該版本之附屬部分**，其信息掛在該版本的 **Book** 上，
  記入 `Book.attached_texts[]`（「隨本附刻之序跋、附錄等」，庫中已用 303 條，
  如《古音叢目》附刻《古音獵要》《古音餘》《古音附錄》），
  **不新建 Work**。

**推論**：`part_of` 只用於**確係同一本書之內**的部分（篇章之於書，如
《繫辭》`part_of`《周易》、《緇衣》`part_of`《禮記`）。書名裡有「別集」
「外集」「續編」二字，不等於它是另一本書，也不等於它是本書之一篇——
**先問是不是同一本書，再定關係詞**。

#### 乙、他人所撰之研究著作 —— 新建 Work，走 `studies`

**年譜、舉正、音義、考異、指要、備要、本義、通例、補注** 之屬，凡**出於
他人之手、可單行**者：

- 直齋韓集條下之《年譜》是**洪興祖**撰、《舉正》是**方崧卿**撰；柳集條下之
  《音釋》《摭異》是**葛嶠**裒集——皆非韓柳自己的文字。
- 說它們 `part_of`《昌黎集》語義即錯：它們不是韓愈集子的一部分，
  是**研究韓集的另一部書**，只是恰好與韓集同刻。
- 故**新建 Work**，在研究著作一側寫 `studies` 繫之（被研究者一側之 `studied_by` 由 build 生成）
  （庫中既有：《史記音義》`studies`《史記》、《何超晉書音義》`studies`《晉書》，音義類 41/42 皆如此）。

#### 判別之問

| 問 | 甲（附屬部帙） | 乙（研究著作） |
|---|---|---|
| 出於誰手？ | 本集作者，或編者所輯本集之遺文 | **他人**所撰 |
| 曾否單行？ | 從未單獨刊行 | 可單行（方崧卿《韓集舉正》四庫別有著錄） |
| 落在哪裡？ | `Book.attached_texts[]` | 新 Work ＋ `studies` |

**兩可者**（如《目錄》：司馬光《通鑑目錄》三十卷四庫別出著錄，是乙；
《政和五禮新儀目錄》隨本而存，是甲）——**以「曾否單行」為斷**，
不能斷者記 `ai_note` 存疑，不強分。

### 「別本」之節：與正條共繫一 Work（2026-08-24 決）

《欽定四庫全書總目》著錄一書之後，每別出一條作「**別本某某**」——
《別本公是集》六卷之於《公是集》五十四卷、《別本農政全書》四十六卷之於
《農政全書》六十卷、《別本讀書蕞殘》二卷之於《讀書蕞殘》三卷……
其提要多自言「與前一本大同小異」。

**別本是同一部書之另一傳本，不是另一部書。** 依本 SCHEMA 之通則
（版本之異落在 Book，不落在 Work），別本之節當**與正條共繫同一 Work**，
不新建。

#### 故其節標 `section_kind: "別本"`

共繫既是對的，`chk.py`〈整理本 section 級磁鐵〉便不當計之——
該驗本為捉「匯入時同名條目未分」而設，別本之共繫是**裁定之果**，非未分之遺。
標此欄，chk 比照 `附屬部帙` 別計而不入磁鐵之數。

| `section_kind` | 何謂 | chk 之待遇 |
|---|---|---|
| `附屬部帙` | 該版本隨本而存之外集、附錄之屬（見上節甲類） | 別計，不入磁鐵 |
| `別本` | 同書之另一傳本，書目別出一條者 | 別計，不入磁鐵 |
| `一書兩著` | **同一書目之中，一書兩出其目**——題同而卷數異，或題異而同指。書目自身之重出，非本庫匯入之失 | 別計，不入磁鐵 |

**認法**：四庫之節題首二字即「別本」，機械可認；然**仍須讀其提要**——
提要言「大同小異」「即前本而多某卷」者是別本，言「別為一時之作」
「節錄本」者不是（此準同姚振宗《隋書經籍志考證》之例，見 N2 道所立）。

#### `一書兩著`：書目自身之重出（2026-08-24 補）

原記「不及者二」——同題而卷數異之「一書兩著」、二節之題確異而同指一書者，
各餘九十、一百八題，皆已逐條裁為正當共繫**而無欄可記**——今補此欄，二者同用之。

**何以合為一欄**：二者之別只在題面（一題同卷異，一題亦異），
而其實同是一事：**書目自己把一部書著錄了兩次**。焦竑《國史經籍志》多取前志
成文，同書兩見尤多（《齊典》五卷／四卷俱題王逸、《朝制要覽》五十卷／十五卷
俱題宋咸、《唐錄政要》十二卷／十三卷俱題凌璠）；姚振宗《隋書經籍志考證》
則每自言之（引錢大昕「一書而兩出」、章宗源「當系重出」）。
既是書目之重出，本庫以一 Work 承之而諸節共繫，正是對的。

**標法**：一組之中**留其書目次第在先者不標**（是為正著），其後重出者標之。
如此該 work 在該書目中只餘一未標之題，磁鐵自消，而重出之事仍見於各節。

**須逐條裁，不得以「同題」機械施之**——同一書目兩見同題而**撰人異**者，
多是二書非一書（《黃庭內景經》梁丘子注與唐自履忠注即其例，二注本各為一書）。
標此欄前須讀其著錄語之撰人與案語。

#### 附記：書目書所述之版本，庫中未必有 Book

直齋著錄之諸本（韓集之李漢序本、方崧卿南安軍本、朱熹校定本；柳集之三本）
**庫中皆無對應 Book 記錄**（`Book.indexed_by` 現無直齋一源）。
故施行甲類之法前，須先定：是為這些版本各建 Book，
還是暫記於母 Work 之該條 `indexed_by[]` 著錄內。**此事未決前不得批量施行。**

---

## 十三、JSON 書寫格式（2026-08-21 定，全庫一律）

| 項 | 約定 |
|---|---|
| 縮排 | **2 空格**。不用 tab，不用 1、不用 4 |
| 非 ASCII | `ensure_ascii=False`——CJK 逕寫本字，不寫 `\uXXXX` |
| 分隔符 | 預設（`": "` 與 `", "`） |
| 鍵序 | **不重排**，保持檔中原序。<br>唯 `index/` 之分片須按 id 排序（新增之鍵插到正確位置，不是附在檔尾） |
| 檔尾 | 一個換行 |

Python 寫法：

```python
open(p, 'w', encoding='utf-8').write(
    json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
```

**為何要定這個**：格式不一致是並行作業最大的機械衝突源。任一工具以自己的縮排
整檔重寫，就把「可自動合併的行級改動」變成「整檔衝突」——全庫七萬餘檔，一次
重寫足以讓所有在飛分支都合不回來。與此相比，縮排取 1 還是 2 並不重要，**一致
才重要**；取 2 是因為全庫既有記錄檔 99% 已是 2，且 CLI 亦寫 2。

修法：`scripts/normalize_json_format.py`（乾跑為預設，`--apply` 才寫；每檔以
`json.loads(新) == json.loads(舊)` 驗語義不變，故不會動到任何一條資料）。
校驗見 `chk.py` 之「JSON 縮排非 2」「JSON 缺檔尾換行」「索引檔鍵未按 id 排序」三項。

**寫腳本時不要再探測縮排。** 過去因庫中兩種縮排並存，各腳本都帶一個
`indent_of()` 去讀 `git show HEAD:<path>` 猜格式——約定既定，逕寫 2 即可。

---

## 十四、索引檔（`index/`）

檔案本身是唯一真實來源，`index/` 是為檢索而生成的扁平副本。**schema-v2 起由 `build/build_derived.py` 生成**（原 `reindex.py` 併入），不手改；數據 PR 不帶 `index/`。

| 路徑 | 內容 | 分片 |
|---|---|---|
| `index/works/{0-f}.json` | 全部 Work | 按 ID 分 16 片 |
| `index/books/{0-f}.json` | 全部 Book | 同上 |
| `index/entities/{0-f}.json` | 全部 Entity | 同上 |
| `index/collections.json` | 全部 Collection | 不分片 |

分片函數（對 ID 逐字元）：`h = 0; for c in id: h = ((h * 31) + ord(c)) & 0xFFFFFFFF` → 片號 `'%x' % (h % 16)`。

索引條目是**扁平的顯示用摘要**，非完整記錄：

```json
{
  "id": "string",
  "type": "string (Work | Book | Collection | Entity ——首字母大寫)",
  "title": "string",
  "path": "string (檔案相對路徑)",
  "author": "string", "role": "string", "dynasty": "string",   // dynasty = 撰人朝代
  "juan_count": "…", "measure_info": "string", "edition": "string",
  "additional_titles": [], "subtype": "string",
  "era": "string", "sort_year": "number",                       // 刊刻朝代 / 排序年，Book·Collection，投影自 dating
  "holder": "string", "has_text": "boolean", "has_image": "boolean",
  "has_collated": "boolean", "promoted_to": "string"   // index/ 之欄不加底線，全檔皆派生
}
```

注意 **`type` 在索引中首字母大寫（`"Work"`），在檔案中全小寫（`"work"`）** ——
這是既定約定，兩邊都不要「改齊」。

`authors` 是陣列，索引只取第一位攤平為 `author` / `role` / `dynasty`。
改動檔案的標題、作者、路徑後，由 build 重生索引即可（build 併入前仍跑 `reindex.py`），否則校驗會報「索引欄位不符」。

**檔名只是 id 之附註，名以記錄內之欄為準**（2026-09-24 使用者定）。
記錄檔名作 `<id>-<題或名>.json`，題名之後改了，檔名與索引之 `path` 未必跟著改
（`reindex.py` 不改檔名；Entity 改過 `primary_name` 者全庫至少 58 條如此）。
這不是缺陷：`path` 指的正是那個檔，`verify.py --membership` 亦過。
**但凡找記錄，以 id 找，或讀索引之 `title`／`primary_name`，不要以檔名 grep 名字**
——愈是改對了名的條目，以檔名愈找不到。改名時順手 `git mv` 並回寫 `path` 可以，不強求。

**兩個「朝代」不是一回事**（2026-09-06 起）：

| 索引欄 | 語義 | 來源 | 例：史記·武英殿本 |
|---|---|---|---|
| `dynasty` | **撰人**的朝代 | `authors[0].dynasty` | 西漢（司馬遷） |
| `era` | **這個本子**的刊刻朝代 | `Book.dating.era` | 清（武英殿） |
| `sort_year` | 年代排序錨點 | `dating.year`，無則 `dating.year_range[0]` | —（題名無年） |

Work 沒有 `era`／`sort_year`（Work 的時代軸是 `period`，成書時代）。
`era` 與 `sort_year` 只是 `dating` 的投影；`reign`／`basis`／`based_on` 留在條目檔，
索引不放。舊欄 `year`（`publication_info.year` 的自由文本）已刪——
UI 執行期型別從不讀它，搜尋分片也不帶，寫了六年沒人消費。
方案：`overview/项目进展/古籍目录/整体设计/2026-09-年代字段统一方案.md`。

---

## 十五、ai_note 的用法

`ai_note` 出現在四類記錄的頂層，是**整理者寫給整理者的注**，不面向讀者：

- 記資料來源與可信度，例：「據網路檢索資料建檔，未核原書」。
- 記存疑與待辦，例：「卷數與通行所記三十一卷不合，待核」。
- 記整理決策，例：「原有非 schema 之頂層欄位 part_of，今改記為 related_works 之 part_of 關係」。

面向讀者的正文一律進 `description.text`，其出處進 `description.sources`。
前端不應渲染 `ai_note`。---

## 附一　新旧字段对照表（供 bim／网站双兼容查阅）

读法一栏是读者在「先切后拆」期间的写法：**新的有就用新的，没有再读旧的**（例：`data._books ?? data.books`）。
「迁移步」对应 overview `F2-7-迁移方案.md` 的 M1–M6；「检查」是 `check_v2.py` 的代码。

| 旧字段（旧位置） | 新位置 | 读者兼容读法 | 迁移步 | 检查 |
|---|---|---|---|---|
| `Work.books[]` | 源：`Book.work_id`；产物：`Work._books`（按年代排）、`_edition_count` | `_books ?? books`（旧的只有 id，要再 fetch） | M3 删 | V03 |
| `Work.books` 的手排顺序 | 丢弃；推荐版本用 `Work.preferred_book` | — | M3 | — |
| `Work._edition_count`（手写） | 产物 `_edition_count` | `_edition_count`（产物恒有） | M3 删 | V01 |
| `Work.related_works[].title` | 删；产物 `_related[].title` | `_related ?? related_works` | M2 删 | V06 |
| `related_works` 反向词 `has_part`／`studied_by`／`text_carried_by`／`followed_by` | 对方源档写规范词 `part_of`／`studies`／`contains_text_of`／`preceded_by`；本侧在产物 `_related`（`direction:"in"`） | 同上 | M2 在规范侧补写、M3 删反向项 | V04 |
| `has_pseudepigraph`／`has_adaptation` | 对方写 `pseudepigraph_of`／`adapted_from` | 同上 | M2 补写、M3 删 | V04 |
| `commentary_on`、`related_to` | `studies`、`related` | 读者两词都认 | M2 | V05 |
| `related` 写在两侧 | 只存 id 较小一侧，note 拼接；另一侧在产物 `_related` | 同上 | M1⑤ 搬 note、M3 删大 id 侧 | V07 |
| `Book.related_books`、`Collection.related_*` 写在两侧 | 只存 id 较小一侧 | 读产物 `_related` 或两侧并集 | M3 | V07 |
| `Work.authors[].role` 缺 | 必填；缺者由 `Entity.works[].role` 回填，两侧都缺或无 `entity_id` 者机械补「撰」（数量单列进 M1 报告） | `role ?? "撰"`（仅展示兜底） | M1② | V08 |
| `Work.classification {l1..l4, basis, source}` | `classification/<scheme>/members/<node>.json` 的 `[work_id, source]`；产物 `_classifications[]` | `_classifications?.[0] ?? classification` | M4 | V09 |
| `classification.basis` | 删（默认，见〈附三〉） | 不读 | M4 | — |
| `classific.json` | `classification/zongmu/tree.json`（`classific.json` 改为其生成物） | 读 `tree.json`，没有再读 `classific.json` | M4 | — |
| 「未分類」占位节点 | 删；挂在父节点即「未细分」 | 读者把「挂中间节点」显示为未细分 | M4 | — |
| `Collection.books[]` | 源：`Book.contained_in[].id`；产物 `Collection._members` | `_members ?? books` | M1① 并入成员侧、M3 删 | V10 |
| `Collection.contained_works[]`（含 `title`、`volume_index`、`group`） | 源：`Work.contained_in[]`（`volume_index`）；产物 `_members` | `_members ?? contained_works` | M1①、M3 | V10 |
| `Collection._member_count`／`_member_type`（手写） | 产物同名字段 | 产物恒有 | M3 | V01 |
| sidecar `volume_book_mapping.json` 等的 `sub_items` | `Book.contained_in[].sub_items` | 读 `sub_items`，没有就不显示 | M1⓪、M6 删表 | V12 |
| sidecar 的 `parent_work_id` | 并入该对 `related` 的 `note`（不升级为 `part_of`） | — | M1⓪ | V12 |
| sidecar 的 `wiki_title` | `Book.resources[]` 一项 `id:"wikisource"` | — | M1⓪ | V12 |
| sidecar 的册号、部类、再造善本编号 | 已在 `Book.contained_in[].volume_index`、`Book.section`、`Book.zhsy_id` | — | 无需并入 | V12 |
| `Entity.works[]` | 源：`Work.authors[].entity_id`（含 `role`）；产物 `Entity._works` | `_works ?? works` | M3 | V11 |
| `Entity.works[].title` | 删；产物 `_works[].title` | 同上 | M2 | V11 |
| `_has_image`（手写） | 产物同名字段 | 产物恒有 | M3 | V01 |
| `_has_text`／`_has_collated`（手写） | **暂留源档**，M3 不删不改名；等文本总管给出稳定来源再迁 | 读源档值 | 未排步 | 豁免 |
| `has_text`／`has_image`／`has_collated`／`has_full_text`／`has_digitalization`（无下划线旧键） | 产物 `_has_*` | `_has_x ?? has_x` | M3 | V02 |
| `_promoted_to`、`promoted_to`、`promoted_at`（记录内） | `promotions.json`；`index/` 与产物里回填 `promoted_to` | 读 `index/` 或 `promotions.json` | M3 | V01／V02 |
| `index/**`（`reindex.py` 生成） | `build_derived.py` 生成 | 不变 | M6 | — |
| `Work.ai_note_fix`／`ai_note2`／`ai_note_periodfix`（各 1 条） | 并入 `ai_note`（F3-3） | — | 未排步（〈附三〉） | — |

**M0（打 tag）、M5（build 全量与 parity 对表）、M6（`index/` 重生）不在源档留下可查的残留**，故无检查代码。

---

### 附一·乙　`_build/` 产物契约（v1，2026-10-07；网站打包依此读，overview#458）

**定为稳定契约**：下列目录布局、字段名、取值形状、分页规格，网站与 bim 可以直接依赖。**任何增删改名、改形状、改分页大小，先在 overview#458 留言通知网站经理，等对方回复后再合**；只新增可选字段算兼容改动，也要先通知。契约版本记在本节标题里，改动时同步加一。

**谁跑、怎么跑**：网站 deploy 在打包前，于检出的 book-index（及 book-index-draft）上执行；产物写临时目录，打包脚本经 `BOOK_INDEX_DERIVED_DIR` 读取；`_build/` 不进 git。只用 Python 标准库，3.11／3.12／3.13 实测产物逐字节相同，正式库全量约 50 秒。

```
python3 build/build_derived.py --out "$BOOK_INDEX_DERIVED_DIR"                       # 正式库
python3 build/build_derived.py --root ../book-index-draft --ref-root . --out <草稿输出目录>   # 草稿库（指向正式记录的 id 由正式库解析）
```
退出码非 0 表示自校验失败，不应继续打包。

**目录布局**

| 路径 | 形状 |
|---|---|
| `entry/<id>.json` | 一条记录一档：源记录原样（不含源里的旧 `_` 字段）＋下表的 `_` 派生字段；草稿记录另有 `promoted_to` |
| `members/<collection_id>/<n>.json` | 丛编成员全表分页，`n` 从 1 起；元素是成员卡片（Work 卡或 Book 卡，带 `t:"work"\|"book"`，另带边属性 `vol`／`group`／`ord`／`section`／`sub`） |
| `catalog/<志书 work_id>/<n>.json` | 志书著录成员分页，`n` 从 1 起；元素 `{id, title, title_info?}` |
| `related/<work_id>/<n>.json` | `_related` 超过 200 条时的余页，**`n` 从 2 起**（第 1 页即条目里的 `_related`） |
| `lineage/<work_id>.json` | 版本图 `{edges:[…], …}`，原样取自源 |
| `_hubs.json` | `{id: {t:"w"\|"c"\|"e", title, dyn?}}`：枢纽条目的名称表 |
| `classific.json` | 由 `classification/zongmu/tree.json` 生成的旧格式分类表（给尚未改读树的旧读者） |
| `index/{works,books,entities}/<0-f>.json`、`index/collections.json` | 检索用扁平摘要，`{id: {…}}`，分片规则同源仓 `index/`（`h=h*31+ord(c) mod 16`），字段规则同 bim `entry_extractor.py` |
| `report.json` | 本次构建的计数与自校验结果（不属契约，只供排查） |

**分页**：每页 200 项（`PAGE`）。`_members` 是 `members/<id>/1.json` 的前 20 项；`_member_pages`、`_related_pages`、`_member_catalog.pages` 给页数。

**枢纽**：被内联引用超过 200 次的丛编／志书／人物，在别处的卡片里只写 `{id, h:1}`（另带边属性），名称到 `_hubs.json` 查。

**派生字段（`entry/` 里）**

| 记录 | 字段 | 形状 |
|---|---|---|
| Work | `_books` | Book 卡片数组，按年代排，无年代按 id |
| Work | `_edition_count` | int，`len(_books)` |
| Work | `_authors` | 与 `authors[]` 同序：`{name, role, dyn?, id?, dates?}`，`id` 为 Entity（枢纽人物只多 `h:1`） |
| Work | `_related` | `{id, relation, direction:"out"\|"in", note?}`＋Work 卡片字段（枢纽为 `h:1`）；`relation` 取本条视角的词（反向词只在此出现）；超 200 时另有 `_related_pages`、`_related_total` |
| Work | `_catalogs` | `{bid, title?, dyn?, section?}`（枢纽志书为 `{bid, h:1, section?}`） |
| Work、Book | `_collections` | `{id, title?, vol?, group?, ord?, sub?}`（枢纽丛编为 `{id, h:1, …}`） |
| Work | `_classifications` | `[{scheme, node, path, l1, l2, l3, l4, source}]`；无分类的 Work 没有此键 |
| Work（志书） | `_member_catalog` | `{pages, total}`，指向 `catalog/<id>/` |
| Work、Book | `_lineage_graph_ref` | 版本图所在 work_id，指向 `lineage/<id>.json` |
| Work、Book、Collection | `_has_image`、`_has_text`、`_has_collated` | bool，只在为真时出现 |
| Book | `_work` | 所属 Work 卡片 |
| Book | `_siblings` | 同作品其他版本的 Book 卡片，至多 40；超出时有 `_siblings_more:true`、`_siblings_total` |
| Book | `_lineage_refs` | `{book_id: …}` 源流引用 |
| Book | `_derived_by` | `{id, rel, title, edition?}`：以本书为底本者 |
| Collection | `_members`、`_member_pages`、`_member_count`、`_member_type`（`"Work"`／`"Book"`／`"mixed"`，无成员时缺）、`_children`（子丛编 `{id, title}`） | 见上 |
| Entity | `_works` | `{work_id, role, title, au?, dyn?, cls?, juan?, img?, txt?, nb?}` |
| 草稿记录 | `promoted_to` | 正式 id（由 `promotions.json` 回填） |

**卡片短键**（F4-2 §二）：Work 卡 `{id, title, dyn?, juan?, au?[≤3], cls?, nb?, img?, txt?}`；Book 卡 `{id, title, edition?, etype?, dating?, y?, holder?, juan?, img?, txt?, nres?, pub?, meas?, from?[], alias?}`；`cls` 是分类节点 id（如 `zm0030`）。值为空的键一律省略，读者按「缺即无」处理。

**样例包**：`build/contract-sample/`（进 git）。正式库 22 条＋草稿库 4 条的 `entry/`、对应 `index/` 行、各自一页 `members/`／`catalog/`／`related/`、`lineage/`、`_hubs.json`、`classific.json`，覆盖丛书、合集、混合丛编、子丛编、志书、跨作品关系（含分页）、分类有无、枢纽、源流、草稿指正式。每条入选理由见 `MANIFEST.json`。由 `build/make_contract_sample.py` 生成，规则固定、可重跑；契约改动时与契约同一个提交重生。

## 附二　已刪之欄位

| 欄位 | 刪於 | 去向／原因 |
|---|---|---|
| `book_contained_in`、`parent_works`（Work）、`history`、`volume_count`（Collection） | 2026-08 | 庫中皆零。`parent_works` 由 `related_works` 之 `part_of` 取代 |
| `Work.books` | schema-v2（M3） | 由 `Book.work_id` 反查，見〈附一〉 |
| `Collection.books`、`Collection.contained_works` | schema-v2（M3） | 成員由成員側 `contained_in` 反查 |
| `Entity.works` | schema-v2（M3） | 由 `Work.authors[].entity_id` 反查 |
| `related_works[].title`、`contained_works[].title`、`Entity.works[].title` | schema-v2（M2） | 展示副本必漂（實測 77＋47 處），由 build 取對方現行題名 |
| 反向關係詞（`has_part`、`studied_by`、`text_carried_by`、`followed_by`、`has_pseudepigraph`、`has_adaptation`）作為源檔值 | schema-v2（M2） | 只在 build 產物出現 |
| `commentary_on`、`related_to` | schema-v2（M2） | 併入 `studies`、`related` |
| `Work.classification` | schema-v2（M4） | 移入 `classification/` 類檔；舊形狀 `{l1, l2, l3, l4, basis, source}`，`basis` 曾為 S（四庫總目類目）／A（`indexed_by[].section` 同名）／B（對照表換算）／C（只到部），實測已漂移（S 中四庫總目僅 44%） |
| 一切源檔內 `_` 起首欄（`_has_text`、`_has_collated` 暫留除外）、`has_text` 等無底線舊派生鍵、記錄內 `promoted_to` | schema-v2（M3） | 移入構建產物 |
| sidecar 對照表（6 份） | schema-v2（M6） | 獨有資訊於 M1 併入記錄 |

**按**：`resource_groups` 與 `volume_count` 在 **Book** 仍為有效欄位；舊版本節曾記「Work 層 `resource_groups` 已刪、庫中零」，實測正式庫 1,770 個 Work 有此欄（2026-10-07），**本版訂正為有效欄位**，形狀同 Book。
留在 spec 裡的死欄位，三年內一定會被某個人重新啟用；需要時自 git 歷史取回。

---

## 附三　待定项（设计文档或 #451 里还没有结论的点；本文不拍板）

| # | 事项 | 现状／默认 | 谁定 |
|---|---|---|---|
| 1 | 分类成员行删不删 `basis` | #451 目录总管两次写「不答按默认删」，用户未明确回复。本文按默认写（成员行只 `[work_id, source]`）；若要保留，行尾加一项枚举即可，格式向后兼容 | 用户 |
| 2 | ~~对称关系「id 较小」用字符串比较还是整数比较~~ | **已对齐**：F6-1 的 `build/v2common.py` 同用字符串比较（`src <= dst`），与本文、`check_v2.py` 一致 | — |
| 3 | ~~Book／Collection 的 `authors[].role` 是否也必填~~ | **已定（用户 10-07，overview#468）**：必填；`check_v2.py` V08 已扩至 Book／Collection（两库实测缺 0） | — |
| 4 | `Work.collections`（1 条，Collection ID 数组） | 与 `Work.contained_in` 同义而形状不同；建议并入 `contained_in`，未见结论，未排迁移步 | 目录总管 |
| 5 | `Entity.aliases`（13 条） | 形状同 `alt_names`，建议并入；未排迁移步 | 目录总管 |
| 6 | `ai_note_fix`／`ai_note2`／`ai_note_periodfix`（各 1 条） | F3-3 说「迁移时并入 `ai_note`」，F2-7 未列入 M 步 | 目录总管 |
| 7 | `Collection.contained_works[].title` 里 47 处「括注撰人消歧」的展示题（如「補後漢書藝文志（顧懷三）」） | M2 删 title 后这类消歧随之消失；要不要在 `Work.contained_in[]` 项里留一个可选展示名，未定（S5 留给目录总管） | 目录总管 |
| 8 | 武英殿 sidecar 顶层信息（`source`、`sections`、`stats`、`ai_note`）的去处 | 目录总管 10-07：**先留着、不并入**；sidecar 留到 M6 才删，删表前再定 | 目录总管 |
| 9 | Entity 是否套 `revision` 机制 | F3-3 §三：不在该卡 | 目录总管 |
| 10 | 志书「本志著录了哪些书」成员页（`_member_catalog`、约 14 MB） | F4：新功能，用户定做不做；不影响其它产物 | 用户 |
| 11 | S1 留下的候选分类（19 条冲突＋3,785 条撤回）进不进成员行 `status` 候选层 | 本轮只留格式口子，不做 | 用户（默认不做） |
| 12 | `Collection.related_collections` 旧对象形里非空的 `type`／`note`（M2 报告列出） | 目录总管 10-07：逐条看后定放处 | 目录总管 |
| 13 | ~~专名子类型的 build 派生字段与 `dynasty_reign_keys.json`~~ | **已实现（F6-5b，2026-10-07）**：`build/names.py`；`_build/report.json` 的 `contract` 由 1 升为 2（纯增量，#458 已通知） | 目录总管 |
