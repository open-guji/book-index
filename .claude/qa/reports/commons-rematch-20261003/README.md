# Commons 资源重匹配（2026-10-03）

本轮补入 **3,054 条 Work 影像资源**，每个 Work 一条代表性扫描文件。全部链接经 Commons 在线 API 确认存在，MIME 与扫描文件 SHA-1 均与快照相符。已有资源完整保留。修改停在独立分支，交草稿 PR 审查。

## 数据与范围

| 项目 | 数量或版本 |
|---|---|
| book-index 基线 | `dde7426d22fa5772fd52135500d3835e7884b222`（main） |
| 源仓 | `open-guji-core/wiki-commons-book-data` |
| 源仓提交 | `9b5a59d3b5ad089cac90871f6643575ab86c551b` |
| 快照完整性 | 44 个数据文件，逐文件 SHA-256、大小、行数全部相符 |
| 遍历扫描文件 | 1,533,167 |
| Work 索引总数 | 95,037 |
| 有书名候选的 Work | 27,386 |
| 书名相关扫描文件 | 596,520 |
| 候选中原有 Commons 资源的 Work | 12,383 |
| 新增资源 | 3,054 |
| 仍待人工判断的无 Commons 候选 Work | 11,949 |
| 比对字典 | 官方 OpenCC 1.4.2，`jp2t` → `t2s` |

只有匹配键进行繁简转换；条目题名、作者和原有字段均保留原字串。候选按索引题名和别名检索，证据取各扫描文件自己的著录字段，未使用书籍聚合层的代表作者。

## 判准与复查

1. 书名精确对应；文件有独立 title 时，title 也须对应，仅剥离明确的卷册数量后缀。
2. 人名在作者字段边界处精确匹配，并核对明确标出的作者朝代。拒绝姓名子串和共享汉字的模糊分数。吴、宋、周、金等姓氏不先行剥离。
3. Work 的具名作者均须获得该文件支持。源作者字段在扣除已支持的人名、朝代及职责后，仍有无法解释的汉字内容者暂缓，以防混入其他书的作者或书名。
4. 多书分类、仅卷首、作者无证、已佚书冲突、同一文件对应多个 Work，以及同一扫描 SHA-1 对应多个 Work，均不自动写入。
5. 每条保留卷册和版本元数据，注明链接只到单个扫描文件，全书齐备情况未核。此轮补 Work 资源，未据书名推定具体 Book 版本关系。

多轮复查中，修正了姓氏被当朝代剥离、代表文件误选卷首、国图等来源作者字段混合著录三类问题。初稿按 26 个来源各抽一条的清单见 `stratified-sample.json`，其中《周易王弼注》的字段同时著录《尚书》《毛诗》，已暂缓；《杜工部詩千家注》源具名作者超出 Work 已记作者，也留待人工判断。

## 校验结果

- **在线逐条检查：3,054/3,054 通过**，链接无失效或改名，扫描哈希相符。首次 API 限流后降低请求频率，保留成功结果续跑，未把请求失败当成链接失效。
- **全量结构对账：3,054/3,054 通过**。Work 仅追加 `resources`、将 `_has_image` 设为 true；索引仅同步 `has_image`。所有原有字段、原有资源和索引成员逐项与基线比较相等。
- **全库 verify.py：写入前后均 OK**。索引漂移、悬空、形状不合均为 0。原有 103 条单向边、2 条 Collection 标题漂移、178 条作者朝代与世纪提示，前后数值相同。
- **重跑全量匹配：新增 0 条**。相关扫描文件仍为 596,520，候选中有 Commons 的 Work 为 15,437，恰比基线多 3,054。
- **新增反例检查：28/28 通过**，覆盖同名异书、朝代冲突、姓氏、人名子串、两侧作者不全、聚合作者污染、多书文件、卷首和已佚书。
- **原有测试按环境拆跑**：工作树中 244 项通过、1 项因未指定文本仓路径跳过；4 项隔离测试硬性要求 `.git` 是目录且主索引干净，在主 checkout 补跑 4/4 通过。共 248 项通过。未修改这些原有测试。
- **git diff --check 通过**。保留两个原本为单空格缩进的 JSON 文件的既有格式，避免带入六万余行无关格式变化。

## 审查文件

`plan.json`（6.7MB）、`work-verdicts.json`（5.1MB）、`deferred-examples.json`（12.4MB）是过程账，为免数据仓膨胀不随合并入 main；原件保留在 PR #7 首个提交 `718b66cc`（`refs/pull/7/head`），下表链接可直接查看，需要时 `git show 718b66cc:<路径>` 取回。

| 文件 | 内容 |
|---|---|
| `additions.csv` | 3,054 条新增资源的书名、ID、作者凭据、扫描册次、版本及链接 |
| [`plan.json`](https://github.com/open-guji/book-index/blob/718b66cc5fd207b14a4ee19f463691728028b214/.claude/qa/reports/commons-rematch-20261003/plan.json)（仓外） | 每条源记录、完整新增 resource、原条目 SHA-256、匹配代码指纹 |
| `live-check.json` | 每个 pageid 的在线文件名、MIME、扫描 SHA-1 和核验结果 |
| [`work-verdicts.json`](https://github.com/open-guji/book-index/blob/718b66cc5fd207b14a4ee19f463691728028b214/.claude/qa/reports/commons-rematch-20261003/work-verdicts.json)（仓外） | 27,386 个候选 Work 的逐类文件判定计数 |
| [`deferred-examples.json`](https://github.com/open-guji/book-index/blob/718b66cc5fd207b14a4ee19f463691728028b214/.claude/qa/reports/commons-rematch-20261003/deferred-examples.json)（仓外） | 每个 Work／判定类别的代表证据，以及多 Work 歧义记录 |
| `stratified-sample.json` | 初稿按来源抽查的 26 条记录及最终去向 |
| `idempotence.json` | 写入后全量重跑的零新增结果 |
| `validation-baseline.txt` / `validation-after.txt` | 全库检查前后日志 |

## 复现

扫描用的中间候选缓存放在仓外，不提交。以下命令从仓根执行；创建新计划默认不写元数据。`--apply` 必须在计划的基线提交上执行，且所有条目已完成在线核验。

```powershell
uv run python -X utf8 ../book-index-crawler-cache/wiki-commons-book-data/scripts/verify.py
uv run --with opencc python -X utf8 .claude/qa/rematch_commons.py --source ../book-index-crawler-cache/wiki-commons-book-data --cache ../book-index-crawler-cache/commons-rematch-20261003.jsonl --report ../book-index-crawler-cache/new-commons-plan
uv run python -X utf8 .claude/qa/check_commons_live.py ../book-index-crawler-cache/new-commons-plan --finalize --resume
uv run --with opencc python -X utf8 .claude/qa/rematch_commons.py --audit
uv run --with opencc --with pytest python -X utf8 -m pytest tests/test_rematch_commons.py -q
uv run python -X utf8 .claude/qa/verify.py
```

`--audit` 读 `plan.json`，运行前先从 `718b66cc` 取回到本目录，且只在计划基线之上、未合入其它改动的分支上成立；重做匹配请将 `--report` 指向新目录，以保留本轮审计账。
