# 建前查重统一入口（G1）

所有会**新建 Work** 的车道（L1 续修提要、L3 方志、L4 目录书、C 线新建等）在 `--apply` 前，把候选（题名、首位责任者、键）写成 TSV，过 `guard.py`：

    python3 -I .claude/qa/newwork-guard/guard.py cands.tsv --out hits.tsv --fail-on-dup

状态 DUP／SAMETITLE-DIFFAUTH／NEAR 必须先处理（改挂已有 Work、登记不并、或人看后确认是新书）；PREFIX 是方志「[年号]」前缀不同，不当重复，但人看；NEW 才可建。
归一＝去括注、`scan.VARIANTS` 异体表、opencc t2s、去标点、去末尾卷数。需 `pip install opencc-python-reimplemented`。载入约 1 分钟。
建后仍要跑一次带白名单的 `scripts/dedup-census.py`，未判组应为 0。

指标快照见 `../metrics/`（`history.tsv` 每次追加一行；`sources-*.tsv` 是各 indexed_by 来源的 Work 数，目录书覆盖看板底表）。
