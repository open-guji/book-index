# 新-子目异名-經 第 1 批（164 簇，並入 204 條）

基線 main `a24525e184`。判定見 `../README.md`；本批取 `clusters-a24525e1.json` 按組號排序前 177 簇；合 main 時與他線同改一 Work 的 13 組整組撤出（`撤出组.tsv`，`../sync_main.sh`），留第 2 批從 main 重算，實落 164 簇。

- 生成：`../mkbatch.py <cl-01.json> jing-01 --base a24525e184`；實施：`../apply_yiming.py batch.json --apply`（包裝 `../../dedup-confirmed-163/apply_batch.py`：著錄並入、Book 改掛、引用與分類成員改指，被並者留墓碑；衝突欄保留 keeper 值、被並值入台賬；被並者原 ai_note／description 記 `loser_original_notes`）。
- 墓碑鏈：`../fix_my_chains.py batch.json --apply` 把指向本批被並者的 154 座舊墓碑改指新 keeper，並記入 keeper `merged_in`（via）。
- 善後與門禁：`../../dedup-subitem/post.sh`：postfix_common、index 定點刷新、草稿庫同步（無引用）；check_v2 0、check-classification 0、audit-merge-ledger T/L/P/R/D 全 0（WARN Q：被並者 ai_note 未保留 204，原文在台賬；首位責任者不同 193，多為子目一側無撰人）、check_promo_dup 0、check-duplicate-audit PASS、build_derived OK。
- 抽檢：見 `../抽检/`（整單元 95 簇同意 95）。

回滾：revert 本 PR。
