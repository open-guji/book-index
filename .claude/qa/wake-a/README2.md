# wake-a 第二輪：補庫中缺的日本版本（2026-11-15）
- 範圍：shard0 的 134 個 Work。每個 Work 用 CiNii Books OpenSearch（`title=<題名>&year_to=1912`，JSON）查 1912 前日本印本，輔以 NDL OpenSearch（`any=<題名> 和古書`）；請求串行、間隔≥2s、緩存於 /tmp/wa2cache。
- 篩選：題名（異體字歸一）＋責任者＋刊年＋日本書肆俱備；以 NCID 的 JSON 取註記（刊記／見返／跋）核定版本，按「刊年＋主書肆」歸簇，不同館各自獨立著錄的 NCID 併入同一條並各掛所藏館。僅收1867年以前；書肆靠別名、只憑年份、責任者不符（標注本／譯本）、與庫內既有版本疑同版者一律不建，記入 TODO2.tsv。
- 結果：新建 22 條（91 條日本館藏），台賬 ledger2.tsv；跳過原因分布與疑似重複見 TODO2.tsv（含 1 條他 Work 下的同版：禮記 993fnd63gh，待補掛）。
- 查重：對 origin/main 全庫「題名＋刊年／年號」查過（含他 Work），無同版；晏子春秋天保三年補刻本與 988fz70c92 另立互見。
- 腳本：fetch2.py（NDL）、fetch3.py（CiNii）、fetch4.py（NCID 詳情）、analyze2/3.py（候選聚類）、spec2.py（逐條規格與依據）、build2.py（`--apply` 寫入）；機器號 wake-a。
- 抽檢：寫入後隨機回看 15 條對應 CiNii 頁面（題名、刊年、書肆、館藏）全部相符，異質 0。
