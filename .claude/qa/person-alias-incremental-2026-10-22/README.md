# 四组人物增量并条（2026-10-22）

基于main `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`，只实施本批四组，旧PR #1213映射不复用。研究证据见PR #1215及本目录evidence。身份依据与整个著作/版本合并分开，本批不并任何Work或Book。

| 保留人物 | 墓碑人物 | 当前Work作者引用改写 |
|---|---|---:|
| 钱易 | 钱希白 | 1 |
| 喻樗 | 喻子材 | 1 |
| 释篆玉 | 篆玉 | 1 |
| 唐菩提流志 | 释菩提流志 | 0 |

8 Entity、3 Work变动；保留四个最小墓碑、merged_in与全部原字段署源台账，增补别称。作者原署name/role不改；北魏菩提流支不在范围。喻子材旧建档ai_note逐字保存在merges.json对应original_records；唐译师两侧断代依据和建档历史均在keeper与台账保留。不改日期或替换已有外部身份号。

## 引用与索引

完整归档扫描：正式714388文件、草稿563825文件、文本190821文件（3.93GB原始内容）。正式库仅3处现行Work引用；promotions和分类零命中。草稿仅两历史TSV，无活动JSON引用；文本零命中，所以本批无需另开草稿或文本迁移PR。扫描固定SHA、字节计数、匹配pointer与历史行证据均在reference-scans。官方审计未传--draft，输出的D=0不能冒充其已扫描草稿；草稿结论由独立完整归档扫描支持。

调用官方build_derived.index_entry/write_index刷新受影响Entity索引：2分片、2条墓碑投影移除已删除的dynasty/period；其他6个人物和3 Work投影不变。保留墓碑索引，不手工删ID。全库main原有79779条记录未入仓内旧index，与本批无关，不在小批PR补齐；比较前后builder报告确保未新增漂移。

## 复现与验证

在固定base完整checkout：`python .claude/qa/person-alias-incremental-2026-10-22/apply.py`先dry-run，`--apply`写11文件；然后运行同目录`update_index.py`更新2个索引分片。脚本校验固定HEAD及全部SHA256前置，不在漂移main上盲用。

- `verify_fields.py`补足官方audit对people独有字段的覆盖缺口：完整原owner字段留存、别称、历史、来源/标识、日期稳定和Work仅改指。
- `audit-merge-ledger.py --ledger <本目录>/merges.json --base origin/main`：T/L/P/R必须零错误。
- `.claude/qa/check_v2.py --paths -`仅输入changed-native-paths.txt中的11条真实路径。
- `scripts/check-classification.py`全分类检查。
- `build/build_derived.py --check-only --text-index <book-text>/index/texts`全量写前/写后核验。

所有结果文件与validation-summary.json为本批验证依据。PR提交不等于已合入main。
