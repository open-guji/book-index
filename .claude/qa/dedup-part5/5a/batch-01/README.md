# 去重方案部分 5a/5d 第 1 批：同源记录重复建档（2026-10-25）

基线（main 3c74b45）：live Book 383,166；同 Work 去掉管理欄后全欄相同 8 组；同 Work 共享总目源记录 id 36 组（含 src_manual 伪 id 1 组）。
5d「双晋升」在本库即表现为同源记录两个正式 Book，与 5a 同一份清单；promotions 无一对多重复（check_promo_dup 0）。

口径：同 Work＋共享 sources[].id＋去掉 id／管理欄／ai_note／sources／indexed_by 后全欄相同＋indexed_by 摘要里责任者一致。
首轮 13 组经独立子 agent 全检：佛說須賴經 3 组（白延譯／支施崘譯，两种译本）判 DIFF → 剔除并补上「责任者一致」一条，余 10 组全 SAME、无损。
（Work d59fybkjl3i8 佛說須賴經疑把两种译本混为一个 Work，交部分 3/4。）
不碰：同源但 contained_in 不同的 3 组（頤道堂詩選、續方言、點蒼山人詩鈔，属「拆回丛书版次错并」串）；其余差异较多的同源组登记。

结果：10 组，keeper 并入 sources／indexed_by／provenance／contained_in／resources 并集，被并者留墓碑；promotions 4 处改指 keeper。脚本同 5c（merge_books.py）。

注：当时脚本实际漏并 sources／indexed_by／provenance，已在 ../../backfill/ 回补。
