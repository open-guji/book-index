# 新-子目异名-史：第 1 批（220 簇，并入 247 条）

基线 main `a5a863461a`。口径与工具见 `../README.md`。`../mkbatch.py ../clusters-a5a863461a.json` 去掉核对存疑 c137、c308，按簇号取前半 220 簇；keeper 优先单书著录、自身有撰人、非丛书编者错位者（d59fxyuymhhc 燕蘭小譜 撰人错位，不作 keeper）。

- 实施：`../apply.py batch.json --apply`，善后与门禁 `../../dedup-subitem/post.sh`。
- 门禁：check_v2（782 档）ERROR 0；check-classification 0；audit-merge-ledger T/L/P/R/D 全 0（WARN：被并者 ai_note 未保留 247，原文在台账 loser_original_notes；首位责任者不同 243，多为一侧缺撰人；题名异体 5）；check_promo_dup 0；check-duplicate-audit PASS；build_derived --check-only OK；草稿库无引用。
- 抽检：并前 441 簇逐簇子 agent 核（`../抽检/out0-5.tsv`）；并后独立子 agent 抽 40 簇，同书 40/40、数据 40/40 正确（`../抽检/post1_out.tsv`）。

回滚：revert 本 PR。
