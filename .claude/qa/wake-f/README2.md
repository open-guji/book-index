# wake-f（shard5）第二輪：補庫內缺的日本版本
- 範圍：shard5 涉 115 個 Work；先按 origin/main 取各 Work 下既有 Book，再用 NDL OpenSearch（title，≤1911 年過濾）逐 Work 掃描（scan2.py／q2.py，緩存 /tmp/wf_cache，串行間隔 ≥2.2s、退避）。
- 候選逐條用 NDL 書目頁＋CiNii NCID 頁（hold.py）核刊年、刊者、所藏館；build2.py 寫入。
- 結果：新建 7 條（詩人玉屑1、易經蒙引1、古文眞寶後集4、救急選方1），均有「刊年＋刊者＋所藏館」；弱證與疑重複見 TODO2.tsv。
- 自查：7 條全部對書目頁回看，異質 0。
- 經驗：NDL 頁面偶發 503，須重試；題名相同的 Work 要先看 Work 作者（老子解例）；R100000136 條目的 NCID 所藏須取「document.write(libraryFilteringSource)」之後段。
