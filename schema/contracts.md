# 契约索引（C1–C6）

> overview#606 Schema落地 B6 交付。一张表回答三件事：**每份契约谁产出、谁消费、以什么为准、用什么机器核对**。
> 改契约前先看这里：消费方列出的人都要通知（改 C2 先在 overview 留言通知网站经理，见 `derived.md` 〈十一〉）。
> 本表是总计划 §五 的落地副本；两处不一致时以本表为准，并回头修总计划。

| # | 契约 | 产出 | 消费 | 格式定义 | 检查命令 |
|---|---|---|---|---|---|
| C1 | 源记录 schema（Work/Book/Collection/Entity） | book-index、book-index-draft | build_derived、bim Python/ui、web 脚本 | `schema/*.md`、`schema/json/*.schema.json`（book-index） | `check_schema.py`、`check_v2.py` |
| C2 | build 产物 `_build/`（契约版本 `CONTRACT`，现 3） | `build_derived.py` | web `derived.mjs`、索引器（`BOOK_INDEX_DERIVED_DIR`＋`SOURCE_COMMIT`） | `schema/derived.md`、`schema/json/derived-entry.schema.json` | `build_derived.py --check-only`；索引器准入（退出码 5） |
| C3 | `index/` 分片（entities/works/books/collections） | `build_derived.py --write-index` | bim 存储、web 搜索与首页、ui | 同 C2＋bim `entry_extractor.py` 口径 | `drift_vs_repo_index` 为空；**B6 对拍** |
| C4 | 文本格式（manifest、`index/texts`、版本 `index.json`、章 md/json、char/cord/punct/entity/norm/decision） | book-text | `--text-index`、web 打包、ui `TextReader` | guji-format `spec/00–08`、`schemas/` | `validate_text_format.py --strict`、`validate-collated.py`、guji-format `check-schemas.py` |
| C5 | npm 包 `book-index-ui` 版本 | bim `publish-ui.yml` | web `nextjs/package.json` | 版本号＋CHANGELOG | `curl /api/version` 的 `bimUi`＝最新已发版 |
| C6 | 网站契约字段表 | web `ops/data-contract.mjs` | verify.yml `contract`、data.yml `package` | 同文件 | `npm run test:contract`（e2e）、`ops/tests/data-contract.test.mjs` |


## 对拍与验收入口

| 要核对什么 | 命令（book-index 仓根） |
|---|---|
| 数据里还有没有旧键（S2 闸） | `python3 scripts/legacy-scan.py . ../book-index-draft` |
| 四处 index 条目提取口径一致（C3） | `python3 -m pytest tests/test_golden_parity.py -q`；bim、web 各有同名用例，读各自拷贝的 `tests/golden/entries.json` |
| 读侧还有没有旧读法（bim、web） | `scripts/schema-landed-check.sh readers`，命中须逐行落在 `scripts/legacy-allow.txt`（每行写理由，≤5 行） |
| 全部验收（总计划 §八 V1–V7） | `scripts/schema-landed-check.sh`（加 `ONLINE=1` 含线上 `/api/version`） |
| 契约样例包（C2，给网站做 contract 测试） | `build/contract-sample/`，用 `build/make_contract_sample.py` 重生；bim `ui/tests/unit/fixtures/contract-sample`、web `ops/tests/fixtures/data-contract/v2` 是下游拷贝，改契约后三处同日同步 |

## 黄金样例怎么维护

- 官方副本：`tests/golden/entries.json`（本仓）；格式 `[{name, type, record, expect_index_entry, negative}]`，详见 `tests/golden/README.md`。
- 下游拷贝头注释写来源 sha；加例先改本仓，再同步。
- 已知口径差异用 strict xfail 登记在各端测试的 `KNOWN_RED_UNTIL`，读法删掉那一步合并时会变红，逼着删名字。
