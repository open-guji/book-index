# 新-子目异名-經 第 2 批（172 簇，並入 239 條）

基線 main `18969516b0`。判定見 `../README.md`；本批＝`clusters-a24525e1.json` 按組號排序第 178 簇以後，加第 1 批撤出的 13 組，共 190 簇；其中 18 簇已有成員被他線並走（成墓碑），整簇跳過，實落 172 簇。

- 生成／實施／墓碑鏈／善後同第 1 批（`../mkbatch.py`、`../apply_yiming.py --apply`、`../fix_my_chains.py --apply` 改指 186 座舊墓碑、`../../dedup-subitem/post.sh`）。
- 手工善後：keeper d59fxx7gz85c（孟子講義）related_works 指向本批被並者 d59fxx7gz85e 的一項刪去（同簇 keeper d59fxx7gz85d 已在列）；草稿庫兩條墓碑（1exp12pdf4dfo 鄭氏三禮目錄、1exp03i7c5nuo 論語詩）merged_into 指本批被並者，改指 keeper（draft 另 PR）。
- 門禁（與同 PR 的子目甲余 b-01 合併台賬跑）：audit-merge-ledger T/L/P/R/D 全 0；check_v2 0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；build_derived OK。

回滾：revert 本 PR（及 draft PR）。
