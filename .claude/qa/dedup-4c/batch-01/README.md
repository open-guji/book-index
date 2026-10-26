# 4c 第 1 批：国图「挂最接近 Work」的 Book 复核（2026-10-26）

基线：main aaa3e9aa05 重算 1,968 个国图 Book（ai_note 记「前輪未能確定歸屬」或「同題多書」，5c 已并走 72 个）；落数据时以 main 1d86693567 为底，333 条定案逐条核过 Book／现挂／目标仍有效。

## 流程
1. `table.py`：国图责任者（繁化、拆人名与责任方式）对各同题候选 Work 的 authors、人物别名、总目著者原文；附年号、同年 Book、同著者异题 Work。
2. `mkreview.py`：选 686 个逐条判（他候选著者合 55、现挂著者异 478、现挂无著者 55、现挂与他候选皆合 57、国图无著者但他候选同年／年号合 41）。其余 1,282 个维持现挂（国图无著者且无年份证据 1,037、现挂著者唯一相合 191 等）。
3. 第一道：10 个子 agent 按口径判 KEEP／MOVE／NEW／UNSURE。
4. 第二道：另 6 个子 agent 对全部 363 条 MOVE／NEW 独立逐条复核（CONFIRM 327、CHANGE 7、退回 KEEP 26、UNSURE 3）。退回多因第二道统一口径「重复 Work 之间不搬」；真正判错（改目标或存疑）10 条，约 2.8%。
5. `apply_4c.py --apply`：改 Book.work_id（ai_note 记依据，revision 升次版），新建 Work 用 mintid 机器号 2035，新 Work 入 index；新建 Work 与原挂同题 Work 记分立于 `dedup-judged/4c.tsv`。

## 口径
- 注本各自成 Work（schema/cataloging-rules.md 第一节）：国图本为某注本，先找注本 Work 改挂；找不到而现挂是原典则维持；注本、译本不新建。
- 新建 Work 只用于撰／纂修／輯／編层面确属另一部书（含方志不同修次），且库内按著者与题名查无合适 Work。
- 重复 Work 之间不搬（Work 并条单元并时 Book 自然跟走）；例外：叢書子目 Work → 同书单行 Work。

## 结果
- 改挂已有 Work 305 个，新建 Work 28 个（28 个 Book），共改 333 个 Book。
- 维持 247，存疑 106（`存疑.tsv`，多为方志版本项空、责任者库内查无，定不了修次）。
- 全部判定与两道理由：`all-verdicts.json`；落地清单：`decisions.json`、`ledger.tsv`（含前置 sha256）、`new_works.json`。

## 留给其他单元的
复核中发现的重复 Work（如《後漢書》d59fy9wythj4／d59f28715gqo，《孟子》集注 d59fxxkb9on6／d59f2hgl5lhd，《周禮》d59fxxlbsg76／d59f23nz7toh 等）见 all-verdicts.json 各条 reason，交 Work 并条单元。国图 Book 本就未入 index/books（main 既有缺口），本批不补。
