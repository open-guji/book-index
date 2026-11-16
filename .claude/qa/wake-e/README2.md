# wake-e 第二輪：補庫里缺的日本版本（shard4，147 個 Work）
對分片內每個 Work 以 NDL Search OpenSearch（`any=<題名> 和古書`＋`title`/`creator`/`from-until`）取日本古典籍記錄（col.py，緩存、間隔2.2秒、指數退避），再取 CiNii Books NCID 頁核對刊記與所藏館（ncid.py）。判準：同題＋責任者＋刊年＋刊者（書肆）；與庫內該Work下既有Book刊年相同者一律視為既有；僅憑年份或刊者不明者不建。
- 新建 28 條（韻鏡10、古京遺文3、桑家漢語抄2、鶴林玉露2、孟子或問2、孫真人備急千金要方2，餘各1），每條掛全部可確認的日本館藏，ledger2.tsv 為台賬，build2.py 為建檔腳本。
- 未建項與原因見 TODO2.tsv（疑同版約13類、證弱若干）。
- 抄本僅取有抄寫者＋年份（奧書）的；同刊年異刊者的另立並在 description 互見。
- 門禁：check_schema ERROR=0。
