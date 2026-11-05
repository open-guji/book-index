# 存疑中「已挂 1 个 Collection」的隐性错并 Book（2026-11-05）

split_hidden 留下的 102 个存疑。`split_held.py` 按 Collection.sources 的 id 等于哪个丛书实例头记录 id 判挂靠：该实例那组留在原 id 并保留 contained_in，其余组拆成新 Book（不挂 Collection）。
结果：拆 80 个原 Book、新建 162；17 个丛书实例 <2 不动；5 个不在本工具范围（无丛书源记录带馆藏 3、人工终判 2）。0 个对不上 Collection。
抽检（独立子 agent，20 个原 Book）：错拆 0、provenance 错归漏重 0、keeper/Collection 0、字段误改 0；5 个「该并未并」疑似——keeper 挂「廣四十家小說四十種」(318hu54j3xgw681k)，新条属「廣四十家小說」(nyaokpkz1rjdbcd3)，版本项同为民國四年上海文明書局石印本、馆藏 5 家相同，只丛书名差「四十種」，按「丛书名相同才并」的口径保守不并，待用户定。
