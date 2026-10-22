# 僧道、帝王与异体人名：本轮新增五案

基线 `bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca`。本目录只追加研究，原 `cases-all.json` 32 confirmed、7 open、5 separate 冻结不变。新增 **1 confirmed、3 open、1 separate**；唯一确认案有 1 个 loser，尚未应用。

| 案号 | 对象 | 裁定 | 关键证据与保留理由 |
|---|---|---|---|
| PRV-H001 | 唐菩提流志／释菩提流志 | confirmed | 《大宝积经》总目署唐释菩提流志；DILA A001358列该经及不空羂索咒心经。释为前缀。保留原note及unreviewed，只合人物，不改译书角色。 |
| PRV-H002 | 北魏菩提流支／留支及两释氏前缀条 | open | 名称同一已获DILA A001357支持，但现行引用存在求那跋陀罗、般若留支异译污染；先拆来源/版本，再整体并人。 |
| PRV-H003 | 北魏流支与唐流志 | separate | 两个DILA权威号、时代和译书范围有别；梵文均可能Bodhiruci不能用作合并理由。 |
| PRV-H004 | 唐玄宗名下《晦菴先生所定古文孝经句解》 | open | CiNii通志堂本与名古屋馆藏皆署朱申；本库故宫贈善023860条却署玄宗，疑合册责任者串接。须核该特定故宫记录及卷首。 |
| PRV-H005 | 吴骞／吴鶱 | open | 拜经楼著述及上图URI支持同人异写，但keeper挂有清雍正间刻当涂吴氏家训笺释；海宁吴骞生1733，产生年龄矛盾，须先排同名异人或版本误年。 |

## 本轮新增污染证据

- `d59f2q855gcg` 同一Work收《补宋书艺文志》求那跋陀罗译与《补魏书艺文志》同本异译，而authors仅菩提留支。
- `d59f9bl4cs1y` 原摘要明确辨瞿昙留支即般若留支；`d59f9bl4o0lk`、`d59f2q3vkpoi` 亦保留两译者争议，不宜继承现有entity_id作为无误证据。
- `d59f2pz70k5e` 总目明确净意菩萨造、菩提流支译，当前role却作撰；旧经录“建武三年出”的归属也需再核。
- `d59fxsymfytd` 家训原著与笺释原文分列吴时举／吴骞；不可因为实体名同而把两役或两人并成海宁藏书家。

## 核验与文件

`cases.json` 提供实际ID、原始路径、SHA256、逐案证据和下一步；`original-records.json.gz` 保存173份完整原档，`manifest.json` 列全部哈希。`references.json` 扫描本地Work/Book/Collection真实authors[].entity_id，并对11个指定Work收集Book.work_id。两名唐代实体实际仅keeper有1条Work引用，loser当前零引用；不能把其旧note的“三部”写成现行引用数。

本轮源档SHA256复验通过；新confirmed成员与旧32组无交集；原生数据和Git均未修改。`machine_decision`仅在PRV-H001提供；跨库book-text、schema和官方派生索引尚未执行，主会话须先完成这些门槛。其他四案没有机器合并许可。

本目录可由 `build_evidence.py` 从相同基线重建；脚本不改原生档，若以后基线变动应先保存当前证据、比对变更，不能直接覆盖当作同次核验。

公开来源见 `sources.json`。DILA与两馆藏页本轮已打开核验；吴骞教育百科只检得搜索摘要，已如实标明，年龄矛盾主要由本库生年与本库版本著录构成，不假称看过原书。
