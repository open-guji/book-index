# 墓碑定期清理

并条后被并方留墓碑（`merged_into`）。墓碑只是过渡：策略是先多录书、再并条，并条会留下很多墓碑，合并稳定后整体删掉（用户 2026-11-01 定，当时还没有外部引用我们的 id）。

## 什么时候清

每次大批并条合入、census 一类检查都清零之后，或者每月一次。进行中的并条 PR 合入后再清，免得它们的 diff 对不上。

## 怎么清

1. 拉最新 main，新开分支；`book-text` 也要最新（读它的 `index/texts` 和目录）。
2. 干跑：`python3 .claude/qa/purge-tombstones/purge.py --book-text ../book-text --out /tmp/purge`，看 `保留.tsv`／`删除.tsv`。
3. 真删：加 `--apply`。它会先写 `ledger/purge-<日期>.tsv`（旧 id → 终点，连同墓碑 `merged_basis` 的 rule／at／by／why），再删文件。
4. 跑门禁：`python3 scripts/dedup-census.py --strict --out /tmp/c`、`python3 .claude/qa/verify.py`（看「消失」「墓碑」几行为 0）、`tests/`。提交台账、PR 描述附 `保留.tsv`。

## 脚本保留什么（不删）

- **T**：book-text 的 `index/texts` 键或 `Work/ Book/` 目录里有这个 id——全文挂在它下面，先在 book-text 改名到留存 id 再清。
- **K**：book-text 的 JSON（整理本 section 的 `work_id`、专名文件的 `entity_id`／`href` 等）里还引用这个 id——先在 book-text 改指到留存 id（并同步 `href`、`canonical_name`）再清。11-03 起加，因为 #2124／#2126 清墓碑时没管这类引用，留下 book-text 悬空 id。
- **C**：墓碑上带的 `indexed_by`／`resources`／`related_works`／`sources`／`additional_titles` 在留存条（链末）里找不到——先补进留存条再清。
- **R**：活记录里有字符串值恰等于墓碑 id（并条账与说明字段除外）——先改指留存条。

## 清掉之后

- 旧 id 只留在 `ledger/`（11-03 起记录里不再有 `merged_in`／`merged_from`／`merge_history`，删前的账导出在 `ledger/history-20261103.tsv`、草稿库的在 `ledger/history-draft-20261103.tsv`）；网站对旧 id 不再 308，直接 404。
- 草稿库若还有指向已清墓碑的 id（census `--draft` 的 D），按 `fix_draft.py` 跟一个草稿库 PR。
- 并条脚本（`mergework.py`、`entity_merge.py`）的新批次照旧先留墓碑，账写在墓碑的 `merged_basis` 上，清时进 `ledger/`。

## ledger 各文件

| 文件 | 列 | 来历 |
|---|---|---|
| `purge-<日期>.tsv` | id、type、title、merged_into、final_keeper（11-03 起加 rule、at、by、why） | 每次清墓碑 |
| `history-20261103.tsv`、`history-draft-20261103.tsv` | old_id、keeper、type、field、title、at、by、rule、why、extra | 删并条历史字段前一次性导出（`.claude/qa/merge-history/strip.py`） |

首列都是旧号。`verify.py`、`check-duplicate-audit.py` 靠首列认「消失的 id 是并掉的」。
