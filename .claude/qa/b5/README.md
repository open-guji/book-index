# B5：馆藏资源匹配（overview#394）

匹配与写入脚本。过程账（匹配表、抽检明细、画像、报告）在 `open-guji-core/book_index_json` 的 `library_data/_匹配/`，不放本仓。

| 脚本 | 作用 |
|---|---|
| `common.py` | 题名／责任者归一化（OpenCC 繁简、日文新字体与异体折叠）、读 Work／Book／各馆数据 |
| `profile.py`、`profile_md.py` | 各馆画像 |
| `match_nlc.py` | 匹配（`SRC=` 切换输入），三档：确定／存疑／无 |
| `verify_sample.py`、`verify_npm.py`、`report_nlc.py` | 抽检（回馆方详情页取页并排）与明细渲染 |
| `reconcile_npm.py` | 用本仓既有 Book 的馆藏号反查 |
| `glm_test.py` | 外部模型（GLM）对照 |
| `apply_nlc.py` | 把國圖數字古籍确定档写进 `Work.resources`（`--apply`），并对着 git HEAD 审计（`--audit`） |

复现国图写入：

```
python3 .claude/qa/b5/match_nlc.py <输出目录>        # 生成匹配表（或直接用 book_index_json 里已出的 匹配表.tsv）
python3 .claude/qa/b5/apply_nlc.py --table <匹配表.tsv> --plan /tmp/plan.json --apply
python3 .claude/qa/b5/apply_nlc.py --table <匹配表.tsv> --plan /tmp/plan.json --audit
python3 .claude/qa/verify.py && python3 .claude/qa/backrefs.py --audit
```
