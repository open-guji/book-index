# 冯时行／冯当可：全量跨仓引用预检

目标 loser：`hixhd2h9bun9`。三仓最新 main SHA已通过 GitHub API核定，各自完整固定SHA归档逐常规文件扫描，另检查全部归档文件路径。扫描脚本保留，可传`--ids`重跑。

| 仓库 | 固定SHA | 文件数 | 字节数 | 结论 |
|---|---|---:|---:|---|
| book-index | c6dd8356d613fc5614beb88f0a61a3d04cfb069e | 714388 | 1433560429 | 人物自身、易论作者引用、官方索引分片 |
| book-index-draft | 87f1ecaba6e1967aabd6a232e254f072e28d4ac8 | 563825 | 347309046 | 仅历史人物键表TSV；无活动JSON或路径引用 |
| book-text | 55b066c17440cb9987b492c657e24354c42df420 | 190821 | 3933084785 | 内容及路径均零命中 |

正式库唯一需要改指的结构引用：`Work/y/2/o/d59f2heaqy2o-易論.json /authors/0/entity_id`。作者原署名及name_basis全部保留。草稿历史TSV原样保留，证据压为gzip，解压后SHA256可对照scan.json，不需要草稿修复PR。正式库自身墓碑ID及keeper历史ID也不全局替换。

本报告只证明本ID的全引用扫描，不证明所有人物／作品可合并。正式落地必须另有字段台账、写后T/L/P/R、schema、分类、官方索引及全量builder。
