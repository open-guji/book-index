# 部分 4 候选清单（基线 main 3c74b458，2026-10-25）

- `4a-alpha-*.json`：4a-α 叢書子目→同作者单行本，3,505 组／4,914 条被并（`../cand_alpha.py`，字段 bulei/keeper/losers/evidence）。經史两部由部分 4 串做；子、集、未分类让给「4a-α乙」。**子目-甲 等其他串请跳过本清单里的 Work id**（这些簇由 4a-α 一次并入单行本）。
- `4b-alpha-*.json`：全无责任者组里按丛书撰者推定同作者的子目互并，488 组／759 条（`../cand_beta.py`）。已让给「子目-甲1/甲2」，部分 4 串不再做。
- `4c-有更准候选-*.json`：国图「挂最接近 Work」的 Book 里，另一同题候选与国图著者或年份更合的 90 个（`../audit_4c.py`，只是机械初筛，改挂须逐条核）。
- `4c-国图有著者却挂异作者Work-*.json`：国图著录有责任者、却挂在别的作者名下 Work 且没有更合候选的 605 个（多为方志不同修纂者、同题异书）。元组：(book, 国图题名, 国图责任者, 版本项, 现挂 Work 题名, 现挂首位责任者, 同题候选数)。处置待 4c 领取串研究（可能需新建 Work，须先经用户口径）。
- 重跑：`P4WORK=<目录> python3 load.py`；`python3 scripts/dedup-census.py --out $P4WORK/census`；再跑 cand_alpha.py／cand_beta.py／audit_4c.py。
