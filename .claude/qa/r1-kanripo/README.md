# R1 Kanripo 全文链接挂接

1. `git clone --depth 1 https://github.com/kanripo/KR-Catalog <dir>`
2. `python3 -I .claude/qa/r1-kanripo/match.py <dir> tier.tsv`（A 撰人相合且同题唯一；B 题名≥4字、Work 无撰人且同题唯一；其余不挂）
3. `python3 -I .claude/qa/r1-kanripo/apply.py tier.tsv [--apply]`，再 `python3 -I scripts/update-site-stats.py --apply`

2026-11-13 首批：KR-Catalog 10,148 种；A 2,593、B 1,301；写入 3,843 个 Work（同一 Work 多个 KR 号只挂第一个）。抽检 28 条（A、B 各 14）全为同书。
未挂：同题多 Work、同题异撰人（约 1,700，人看）、库里没有（约 2,400，可作新建候选，须过 newwork-guard）。
