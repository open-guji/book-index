# 存疑中「已挂 ≥2 个 Collection」的隐性错并 Book（2026-11-05）

`split_held2.py`（split_held.py 的推广）：每个 Collection 须恰好对上一组丛书实例；每组挂对上它的 Collection（可 0 个）。
「廣四十家小說四十種」(318hu54j3xgw681k) 与「廣四十家小說」(nyaokpkz1rjdbcd3) 同为民國四年上海文明書局石印本、馆藏全同，按用户 11-05 定视为同一组。
结果：拆 47 个原 Book、新建 218；23 个归并后仅 1 组不动；仍存疑 7（无丛书源记录带馆藏疑单行本混入 4、人工终判 3，见 存疑.tsv）。
抽检（独立子 agent，20 个）：错拆 0、provenance／contained_in 错误 0；7 个「该并未并」即上述廣四十家小說模式，已按归并口径重做；2 个存疑未并（文林綺繡五種 995bh8gkqo 光緒十一年融經館刻本／八杉齋校刻本；994xavrnr5 鴻寶齋石印本／點石齋石印本，刊刻者不同，待用户定）；edition_type／dating／publication_info 因取自旧聚簇代表记录，拆后清空（设计内）。
