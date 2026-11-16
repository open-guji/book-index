# wake-e 第三輪：通名大 Work 穷尽（主題組 E：老子、莊子、列子、荀子、韓非子、孫子、墨子、管子、淮南子、呂覽等諸子）
- 方法：CiNii Books 檢索（`cs_wake_e3.py`，count=200、year_to=1911、古→新，60餘個題名／關鍵詞×5頁，`harvest_wake_e3.py`）→ 以「刊年＋書肆集合」聚簇（`cluster_wake_e3.py`，678簇）→ 與庫內全部日本版 Book（含無年份者）及已用 NCID 比對去重 → 對入選簇逐一抓 NCID 頁（`fetch_wake_e3.py`，約280頁，間隔2.2秒、緩存）核刊記／見返／所藏館 → `build3_wake_e3.py` 建檔。
- Work 歸屬：優先庫內已策展的基礎 Work（道德經d59ezkx8dt6o、莊子d59ezaj2wl4w、荀子、孫子、墨子畢沅校注d59fy103hlvk、淮南鴻烈解d59f24m877d3 等）與庫內已有的日本注本 Work（d59gdu*/d59gdv* 系列、莊子因、武經直解等）；題名無對應 Work 者不硬挂，進 TODO3.tsv。
- 新建 35 條（莊子音義併入main 988g8y6bcw）（見 ledger3.tsv，build 腳本內 FINAL 為清單）；每條掛全部可確認的所藏館（每簇至多抓12筆 NCID）。
- 判準：刊年與書肆須為 CiNii 非括註著錄（`[書肆]`、`[1---]`、`[出版者不明]` 一律不建）；同年同肆但共同發行書肆集合不同者只建主簇；後印、求版、補刻（如淮南鴻烈解額田勝兵衞求版、管子重訂各肆、鬼谷子安永三年各肆）不建或並簇並注；序跋年非刊年者 dating.certainty 標 inferred。
- 去重：除按 Work 查外，以書肆名＋題名對 origin/main 全庫（含不同 Work）grep，查出18條庫內已有（多為庫內 99je93h7* 老子批次，見 TODO3「庫內已有，剔除」行）後剔除。
- 門禁：check_schema ERROR=0。
