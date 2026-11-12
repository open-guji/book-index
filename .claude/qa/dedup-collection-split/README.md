# Collection 补建后续做存疑 Book（L2，11-12）

对象：U1-c 之前列为存疑的 Book：隐性错并拆分存疑 102、拆回二存疑 59、Collection 补建批4／5 存疑 69（去重后共 207 个）。
盘点结果（Collection 补建后）：130 个其实已是单版本且已挂对 Collection（当时只是 Collection 还没建），不用动；其余 77 个用 `split_after_collection.py` 处理。
口径同 split_hidden：一个 Book＝一个版本；不同丛书实例＝不同版本；同丛书名（去「N 种」「（别名）」）且版本项相同的几个丛书头算同一版本，一起挂。
- 多版本的拆开，每部分挂其丛书头对应的 Collection；原挂靠里不在目标内的（故宫善本舊籍、文淵閣本）留给馆藏机构匹配的部分，匹配不到给保留原 id 的部分；非总目 item 的 provenance（metadata.npm_item_id）跟挂靠部分走。
- 归一化后只有 1 组的：只追加 contained_in。
- 不处理的（仍存疑，登记在 batch-01/存疑.tsv）：provenance 分不干净 10、单版本但已挂的 Collection 与总目丛书头不符 11（挂的是故宫善本舊籍／文淵閣，总目记录属另一丛书版本，Book 可能混了不同版本，不动）、人工终判 3、无丛书源记录（带馆藏 3、不带 1）。
用法：`split_after_collection.py --parsed <parsed> --only <id 文件> --out <批目录> [--apply]`。不再写 index/。
