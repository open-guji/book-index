# wake-h：和刻本日本館藏專項（shard7，190 條）

方法：按題名查 NDL Search OpenSearch（`ndl.py`，結果緩存在 ndl_cache.json），以刊年（和曆換算，`match.py`）、書肆、責任者過濾候選；入選者取 NDL Search 書目頁（`hold.py`）或 CiNii Books 書頁所列館藏機構與請求記號。`apply.py` 對已有 Book 的 provenance 追加日本館藏（不動原中國館藏），revision patch +1，ai_note 追加依據。
- 補挂 24 條（另有 3 條年份相合但書肆未證，降為存疑）；新建 0（NDL 古典籍中該 Work 下缺失的日本版本，因 NDL 全部經 429 限流、時間所限，未做；留作後續）。
- 無對應／存疑見 ledger.tsv，存疑原因見 TODO.tsv。
- 近現代（昭和／大正）影印排印本、故宮無明確版本的「日本鈔本」一律不處理；已有日本館藏的 Book 不動。
