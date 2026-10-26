# 3a-2乙「先拆后并」

来源：`dedup-3a2yi/判定-r2.tsv` 中依据以「先拆后并：」开头的 36 对。这些 Work 各自混挂了同一作者文集的不同编次（卷数、编者、选本不同），
不能整条并，得先按编次拆开，再把与对方同一编次的组并过去。

- `plan.json`：逐 Work 研究所得方案（71 Work、133 组；基线 main 0bb846c325f，执行时对当时 main 逐条核过 Book 集合）。
  `works[wid].groups[]` = {name, stay, books, indexed_by, note}；`merges[]` = {from: "wid:组名" 或 "wid", into, why}；
  `uncertain` 为真的 3 条（d59fsb0hhqf7、d59f6eraibk0、d59fsig98dts）不动。
- `split_works.py`：按方案拆组、组并入、新建 Work（规则见脚本文首）；整 Work 并 Work 出 `batch-whole.json` 交
  `dedup-3a2yi/apply_3a2yi.py`（墓碑）。
- `batch-01/`：台账 `splits.json`（每 Work 留哪组、各组去向、去掉/移走的说明）、`batch-whole.json`、`merges.json`。

结果（2026-10-26）：拆 39 Work，新建 40 Work，20 组并入已有 Work，93 Book 改挂。丁鶴年集 d59f2nk1atxd、d59fxw24cdtt 执行前已由 3a-3 并入 d59f2gpsb2f4，丁鶴年詩集 d59f2gpmdk3k 一簇本批不动（plan 中标 uncertain），待按编次重核。

未做：resources／resource_groups 仍留原 Work，未按版次分（如丁鶴年集的四庫全書本链接随「一卷本（四庫）」组应归丁鶴年詩集）；
d59fxw24cdtt 并入后其下琳琅祕室叢書本 Book 与 d59f2nk1atxd 原有的同版 Book 重出，归 Book 层查重。

抽检（独立 agent，12 Work）：分组、并入、Book 改挂 0 错；首版留原 Work 的字段错 2（说明的卷数与留下编次不符、说明与冊數出自已拆走的再造善本 Book），
另有新 Work 题名照抄原 Work、measure_info 只留正卷、抄了 period_upper／loss_status 等依原著录推出的字段。已改规则重跑：
卷数著录取整段（「六卷附錄一卷」）；本组 Book 题名一致时新 Work 取 Book 题名；说明里藏品编号所在的 Book 拆走时说明（与冊數）随之；
说明开头的卷数合某拆出组的随该组走，否则改成现卷数；新 Work 不抄 period_upper*、loss_status*、emendated_by。
总目著录按条目头卷数归组（条下所列其他版本不另分）。
