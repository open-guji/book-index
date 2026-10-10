# book-index 格式定义（schema-v2 终版）

本目录是 `book-index`（正式库）、`book-index-draft`（草稿库）两仓记录格式的**唯一权威**。
`book-index/SCHEMA.md` 与 `book-index-draft/SCHEMA.md` 都只是指向本目录的目录页。
本目录自洽：读懂这里的文档不需要再翻 overview 仓的设计文档；设计过程与决定记录见 [CHANGELOG.md](CHANGELOG.md) 所列 issue。

格式有变，先改本目录（文档＋`json/` 下的 JSON Schema），再改数据、代码；改动记入 CHANGELOG。

---

## 一、各档索引

| 档 | 讲什么 |
|---|---|
| [README.md](README.md) | 总则、源档与产物的界线、文件布局、ID、版本号、JSON 书写格式、校验入口、字段表体例（本档） |
| [common.md](common.md) | 多类记录共用的对象与字段：`authors[]`、IndexEntry（`indexed_by`／`emendated_by`）、`resources[]`、Description、Source、Location、计量、`dating`、共通管理字段（`revision` 口径等）、朝代与时代轴（`dynasty` 规范名全表、`period`、`period_upper`）、`ai_note` 用法 |
| [work.md](work.md) | Work（作品）字段全表与细则；关联词表（`related_works[].relation`） |
| [book.md](book.md) | Book（版本）字段全表与细则 |
| [collection.md](collection.md) | Collection（丛编）字段全表与细则 |
| [entity.md](entity.md) | Entity（人物与专名）：通用字段；people／collective（含官署）／dynasty／reign／office／place 各子类型字段表；校验码 |
| [classification.md](classification.md) | 分类法目录 `classification/` 的三种文件 |
| [promotions.md](promotions.md) | 升格对照表 `promotions/` 分片 |
| [text-files.md](text-files.md) | 整理本与辑佚档（已迁 book-text）：去处与接口 |
| [derived.md](derived.md) | 构建产物 `_build/` 与 `index/`：每个派生字段的形状、来源、所在产物；build 契约版本 |
| [legacy.md](legacy.md) | 旧字段、旧写法：现存条数、读者兼容读法、何时由谁删 |
| [cataloging-rules.md](cataloging-rules.md) | 录入判准（一条 Work 代表什么、原典与注本、同题重出、版本附属部帙、别本等）；不是格式，但录入时与格式同读 |
| [CHANGELOG.md](CHANGELOG.md) | 自 schema-v2（2026-10-07）起的格式变化 |
| [json/](json/) | 机器可读版（JSON Schema 2020-12）：`work`、`book`、`collection`、`entity` 各一份，`common`（共用 `$defs`）、`classification`、`promotions`，派生产物 `derived-entry`（`_build/entry/`）与 `index`（`index/`） |

---

## 二、总则

| # | 规则 | 说明 |
|---|---|---|
| 1 | **一个事实只写一次** | 源档里一条关系只存一侧；反向关系、计数、对方题名等展示副本全部由 build 生成。 |
| 2 | **成对关系只写规范方向** | `related_works` 的六对成对词（`part_of`、`studies`、`contains_text_of`、`preceded_by`、`adapted_from`、`pseudepigraph_of`）写在本侧；反向词（`has_part`、`studied_by`、`text_carried_by`、`followed_by`、`has_adaptation`、`has_pseudepigraph`）只出现在构建产物里。见 [work.md〈关联词表〉](work.md#关联词表)。 |
| 3 | **对称关系存 id 较小的一侧** | `related_works` 的 `related`、`Book.related_books`、`Collection.related_books`／`related_collections`：两条记录的 id 按**字符串比较**（Python `a < b`），写在较小者里；另一侧由 build 补。（规划中的写入口 `bim link` 尚未实现，现由 `check_v2.py` V07 把关。） |
| 4 | **源档不写 `_` 起首字段** | `_` 起首的都是派生字段，只出现在构建产物 `_build/entry/<id>.json` 里。**无例外**（`_has_text`、`_has_collated` 的暂留豁免已于 2026-10-10 收回，源档已无，见 [CHANGELOG.md](CHANGELOG.md)）。无下划线的旧派生字段（`has_text`、`promoted_to` 等）同样不写。 |
| 5 | **不写派生列表与反向列表** | 不写 `Work.books`、`Collection.books`、`Collection.contained_works`、`Entity.works`、`related_works[].title`。成员关系写在成员一侧：`Book.work_id`、`Book.contained_in`、`Work.contained_in`、`Collection.contained_in`、`Work.authors[].entity_id`。 |
| 6 | **`authors[].role` 必填** | Work、Book、Collection 的 `authors[]` 每项都要写 `role`。 |
| 7 | **分类不写在 Work 里** | 分类归属写在 `classification/<分类法>/members/<节点>.json`。见 [classification.md](classification.md)。Collection 不分类。 |
| 8 | **`_build/` 是构建产物，不是源** | `build/build_derived.py` 读源档生成 `_build/`（不进 git）与 `index/`。网站与 bim 读 `_build/entry/<id>.json`（源记录＋派生字段）。见 [derived.md](derived.md)。 |
| 9 | **读者先切后拆** | 网站与 bim「新字段有就用新的，没有再回退旧字段」；数据切换完成后再删回退分支。build 不产出旧字段的别名。各旧字段的兼容读法见 [legacy.md](legacy.md)。 |
| 10 | **`revision` 只管「作品是什么」的陈述** | 派生字段、分类归属、反向链的变化不 bump `revision`；迁移脚本一律不改 `revision`／`revised_at`。口径见 [common.md〈revision〉](common.md#revision-口径)。 |
| 11 | **只标异常，不标正常；判不出不猜** | 可选字段缺省即「未考／无」，不写占位值（`null`、`""`、`0`、「不詳」）。判不出的留空，另出清单。 |

---

## 三、源档与产物

| 路径 | 是什么 | 源／产物 | 谁写 |
|---|---|---|---|
| `Work/{c1}/{c2}/{c3}/{id}-{题名}.json` | 作品记录 | 源 | 录入、bim |
| `Book/{c1}/{c2}/{c3}/{id}-{题名}.json` | 版本记录 | 源 | 录入、bim |
| `Collection/{c1}/{c2}/{c3}/{id}-{题名}.json` | 丛编记录（草稿库目前没有 Collection） | 源 | 录入、bim |
| `Entity/{c1}/{c2}/{c3}/{id}-{名}.json` | 人物与专名记录 | 源 | 录入、bim |
| `classification/schemes.json`、`classification/<分类法>/tree.json`、`…/members/<节点>.json` | 分类法登记、分类树、各类成员 | 源 | 录入工具；规划中的写入口 `bim classify` 尚未实现，见 classification.md |
| `promotions/<草稿 id 末 2 位>.json` | 草稿 id → 正式 id 对照（仅正式库） | 源 | 只经 bim `PromotionsStore` |
| `resource.json`、`resource-site.json`、`resource-catalog.json`、`resource-collection.json` | 资源站点目录（不是记录） | 源 | 人工 |
| `recommended.json` | 网站首页推荐（不是记录） | 源 | 人工 |
| `classific.json` | 旧分类词表，由 `classification/zongmu/tree.json` 生成，退役中 | 产物 | build |
| `index/**`、`index.json` | 检索用扁平摘要 | 产物（提交在仓里，但不手改） | build |
| `_build/**` | 页面就绪条目与分页大列表 | 产物（不进 git） | build |

**路径分片**：`{c1}/{c2}/{c3}` 是 id 的末三个字符，按原序（如 `d59fryqsp3bb` → `Work/3/b/b/`；bim `storage.shard_dirs`）。文件名 `<id>-<题名>.json` 里的题名只是附注，**名以记录内的字段为准**；改名后文件名可以不跟着改，找记录一律按 id。

**记录文件的判定**：恰好在 `<类型>/{c1}/{c2}/{c3}/` 下、带 `id` 与 `type` 的 `.json` 是记录。更深层的 `.json` 不是记录（现存 0 个）。

**整理本、辑佚档不在本仓**：2026-08-26 已迁到 book-text 仓，格式归 book-text，见 [text-files.md](text-files.md)。

**sidecar 已删**：旧的叢编册号对照表（`volume_book_mapping.json` 等 6 份）已在迁移 M6 并入记录后删除，不再存在。

---

## 四、ID

ID 是 64 位 snowflake，base36 小写编码，数值 `< 2^63`。

| 库 | status 位 | 长度（实测，base36 不补前导零） |
|---|---|---|
| 正式库 | 0 | Book 10 字符（类型位为 0，高位全零）；Work、Collection、Entity 12 字符 |
| 草稿库 | 1 | 一律 13 字符 |

长度只是编码的结果，校验以「base36 小写、数值 < 2^63、类型位与记录类型一致」为准（`validate-ids`），不以长度判库。

记录类型占 3 位：

| 值 | 类型 |
|---|---|
| 0 | Book |
| 1 | 保留 |
| 2 | Collection |
| 3 | Work |
| 4 | Entity |
| 5–7 | 保留 |

0–3 用于书目实体，4–7 用于抽象概念。铸号用 bim `id_generator.py` 或 `.claude/qa/mintid.py`。

- 草稿记录可以引用正式 id（如草稿 Book 的 `work_id` 指正式 Work）；校验悬空引用时正式 id 不在草稿索引中属正常。
- 「id 较小一侧」按字符串比较；同长度的 base36 小写 id，字符串序与数值序一致。
- 升格的权威对照是 `promotions/`（见 [promotions.md](promotions.md)）；草稿记录里不写 `promoted_to`。

---

## 五、三种版本号

| 版本号 | 在哪 | 管什么 | 现值 |
|---|---|---|---|
| `schema_version` | 每条记录顶层（Work／Book／Collection／Entity 必填） | 记录格式的大版本 | `1` |
| `revision` | 每条记录顶层（正式库必填） | 这条记录内容的版本（`"主.次.补"`），口径见 [common.md〈revision〉](common.md#revision-口径) | 新记录 `"1.0.0"` |
| build 契约版本 `contract` | `_build/report.json` 的 `contract` | 构建产物（`_build/`）的形状 | `3` |

格式文档自身不另设版本号：以 CHANGELOG 的日期条目为准。

---

## 六、JSON 书写格式（全库一律）

| 项 | 约定 |
|---|---|
| 缩进 | 2 个空格 |
| 非 ASCII | 直接写本字（`ensure_ascii=False`），不写 `\uXXXX` |
| 分隔符 | 默认（`": "`、`", "`） |
| 键序 | 不重排，保持文件原序；`index/` 分片按 id 排序 |
| 文件尾 | 一个换行 |

```python
open(p, 'w', encoding='utf-8').write(
    json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
```

格式一致才能让并行作业的改动按行合并；一个工具按自己的缩进整档重写，就会让所有在飞分支冲突。`_build/` 产物不受此约定约束（紧凑格式、键排序，见 [derived.md](derived.md)）。

---

## 七、校验入口

| 脚本 | 查什么 | 用法 |
|---|---|---|
| `schema/check_schema.py` | 按 `schema/json/` 的 JSON Schema 校验记录形状（未登记的键、枚举外的值、必填缺失）；全库跑时另查分类目录与 promotions 分片；`--build DIR` 校验构建产物。旧字段、旧写法报 WARN，其余报 ERROR | `python3 schema/check_schema.py [--root 仓] [--draft] [--paths -] [--json 报告]`；`--build <build 输出目录>` |
| `.claude/qa/check_v2.py` | 旧格式残留（V01–V16）与专名子类型校验码（E1、D、R、A、O、P、I 系列） | `git diff --name-only origin/main... \| python3 .claude/qa/check_v2.py --paths -` |
| `.claude/qa/verify.py` | 悬空引用、跨记录一致性、派生值与索引漂移 | `python3 .claude/qa/verify.py` |
| `build/build_derived.py` | 构建并自校验（条数守恒、派生值自洽、卡片 id 可解析） | `python3 build/build_derived.py --check-only` |

审数据 PR 时 `check_v2.py` 必跑；`check_schema.py` 宜跑（`--paths` 只查改动的文件），ERROR 须为 0，WARN 是已知旧写法（见 [legacy.md](legacy.md)）。

`check_schema.py` 只用标准库，自带 2020-12 的一个子集校验器，另认两个扩展关键字：`x-legacy: true`（旧字段或旧写法，报 WARN）、`x-legacy-values`（枚举外的已知旧值，报 WARN）。`x-legacy` 写成 `"keep"` 表示旧写法但定为长期保留（如 `indexed_by[]` 的志书证据层），报 INFO（code `legacy-keep`），不计入 WARN；汇总行为 `ERROR n　WARN n　INFO n`。跨记录的检查（引用存在、无环、唯一、规范名逐值比对）不在 JSON Schema 里，由 `check_v2.py`、`verify.py`、build 自校验做。标准 JSON Schema 校验器（如 Python `jsonschema`）也能读这些文件，但会忽略两个扩展关键字。

---

## 八、字段表体例

每类记录一张字段表，一个字段一行，列固定为：

| 列 | 写什么 |
|---|---|
| 字段 | 键名；嵌套写作 `a.b`、数组元素写作 `a[].b` |
| 类型 | `string`、`integer`、`number`、`boolean`、`object`、`array<…>`、或本目录定义的对象名（如 `Author`、`IndexEntry`）；可多型时用 `｜` 分隔 |
| 必填 | **必填**／**可选**／**条件**（写明条件）；「正式库必填」表示草稿库可省 |
| 性质 | **原生**（录入或工具写入的事实）／**派生**（只在产物里）／**旧（暂留）**（现存数据里还有、新数据不写，见 legacy.md） |
| 含义 | 一句话 |
| 取值 | 枚举写全；格式、单位、范围；自由文本写「自由文本」 |
| 谁写 | **录入**（人或录入脚本）／**bim**（工具自动写）／**build**／**迁移**（一次性脚本，已跑完） |
| 例 | 取自真实数据，照录原文 |

- 「必填」以外的字段缺省即「未考／无」，不写占位值。
- 字段说明用简体；字段值、枚举值、引文、例子照数据原文（多为繁体），如 `舊題撰`、`刻本`、`三國魏`。
- 「实测」数字注明库与日期，例：「正式库 10-08：1,113 条」。
