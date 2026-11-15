# wake-b：和刻本日本馆藏专项（shard1，160 条 / 119 Work）

方法：NDL Search OpenSearch（`from/until` 刊年限定）按题名＋刊年比对；NDL Search 聚合各馆记录，按记录前缀/SRU 的 seeAlso 与 LIBRARY 分面确定真实馆藏方（NDL=R100000002/039、早大=R000000050、九大=R100000092、京大=R100000105、宫城县图=R000000054 等）。
- 补挂 25 条（ledger 中「補掛」；NDL 已著录的 2 条记「已有」不重复）
- 新建 19 条（刊年＋书肆明确的和刻本；书肆不同但疑同版者各立一条并在 ai_note 互链）
- 其余记「無對應」「存疑」；无年份的故宫“日本钞本”均跳过
- 工具：ndl.py / eras.py / lib.py / pass2.py / patch.py / newbooks.py；台账 ledger.tsv、TODO.tsv
- 抽检 15 条（回看 SRU 记录题名/年/书肆）异质 0。
