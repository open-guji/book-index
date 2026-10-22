# 集部 20:22：5个全新Work对，2确认／1分立／2待核

固定main为`c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本轮研究10个Work，新增 **2 confirmed、1 separate、2 open**；确认冗余Work数2，执行就绪0，原生修改与合并均0。没有复审此山、敬业堂及T2000九案，不涉及旧1876映射或BOOK-0010。未触及#1216人物数据与冯时行独立审计。

| Case | Work IDs | 判定 | 范围结论 |
|---|---|---|---|
| COL-2022-001 | d59f2hfub6rm / d59f2hsp84ch | confirmed | 格齋是现存一卷格齋四六的截题；不能向已佚三松類稿全集传递 |
| COL-2022-002 | d59f2nj89r7l / d59f2njfrg8x | confirmed | 青溪／青谿／清谿漫稿为倪岳24卷主集传题差异，补遗1卷另保留 |
| COL-2022-003 | d59f2gnyfzsw / d59f2hrydpmo | separate | 16卷诗文全集与宋百家诗存1卷诗选分立；短题Work顶层20卷是待修范围污染 |
| COL-2022-004 | d59f2gotyyo1 / d59f2gpw1wxs | open | 30卷内外题确同，但文集Work聚合5卷抄本，须拆清来源范围 |
| COL-2022-005 | d59f2nkla0ht / d59fsejqvr46 | open | 半轩12卷兼补遗与6卷旧钞关系未明，不能因先生称谓或同作者判全范围同一 |

## 两个新确认

**格斋。** [四库书前及正文](https://zh.wikisource.org/wiki/格齋四六_(四庫全書本))明确一卷、王子俊、102首，并以完整题名进入正文。[总目卷159](https://zh.wikisource.org/zh-hant/四庫全書總目提要/卷159)网页标点把四六置于书名号外，当前`d59f2hfub6rm/indexed_by/0/title_info`恰承该形式。这是可定位的截题重复，不是只凭两条摘要相同。王子俊字材臣/才臣在文本有用字差异，不产生新作者；两条现共用`hixhd2h9bn3s`。书前只说所存四六属于已佚类稿的一种，因此本案限定于现存一卷，不扩张到三松类稿全体。

**青溪。** [总目卷170清谿条](https://zh.wikisource.org/zh-hant/四庫全書總目提要/卷170)与[四库青谿漫稿书前目录](https://zh.wikisource.org/wiki/青谿漫稿_(四庫全書本))分别提供清与青的实际书题；24卷目录、倪岳字舜咨、奏议59篇及具体奏题对应。现两条共用作者`hixhd2h9bjyw`。旧`d59f2nj89r7l/indexed_by/1/note`把青/清称作简繁转换，这一解释错误，应保留旧值后改为该书的传题差异。其`indexed_by/2/title_info`另记补遗1卷，执行时仍须留在版本/附件层次；本案未宣称各抄刻本逐字同版。

## 一个明确的选本边界

**佩韦斋。** [全集书前](https://zh.wikisource.org/zh-hant/佩韋齋文集_(四庫全書本))记俞庸裒得16卷，诗7卷文9卷；后附辑闻4卷应另书。目录确实也称佩韋齋集，故短题本身可以指全集。然而`d59f2hrydpmo/indexed_by/0`唯一来源是宋百家诗存1卷本，[曹庭栋原序](https://zh.wikisource.org/zh-hant/宋百家詩存_(四庫全書本))明确选录，[卷38](https://zh.wikisource.org/zh-hant/宋百家詩存_(四庫全書本)/卷38)用短题列诗，并在作者小传另说原集16卷。这支持将该选本与诗文全集分立。

这里的separate针对可证的两个范围，并非称短题永远不同书。短题Work顶层`juan_count/measures/measure_info`仍是20卷，与唯一来源1卷矛盾；应先读历史和Book分源修复，不能把20改1后便声称完成全部挂接核验。俞德邻为同作者；俞庸辑全集与曹庭栋选诗的责任不能抹平，更不能把辑闻4卷吞入。

## 两个有具体下一步的待核案

**剡源。** [同一四库页面](https://zh.wikisource.org/wiki/剡源集_(四庫全書本))提要题剡源集、目录题剡源文集，30卷题名同一已证；提要还明确28卷旧编、周仪重辑30卷、黄宗羲选4卷。问题落在`d59f2gotyyo1/indexed_by/2`的5卷清抄本。[八千卷楼书目](https://www.shidianguji.com/book/CADAL02091230/chapter/1mfkjlz78ks9y)实际并列30卷集、5卷文集与4卷文钞，足以否定“卷数差只是标题简省即可忽略”的捷径。仍需上图/南图5卷抄本目录、序跋和首末；检索结果提到甲乙丙丁戊分集只是线索，本轮未据此作确认。

**半轩。** [四库书前及目录](https://zh.wikisource.org/zh-hant/半軒集_(四庫全書本))实作12卷，列补遗；主Work顶层14卷应与各来源分层核对。上述八千卷楼目录又并列14卷与12卷补遗2卷，说明不能把统计粒度混用。[傅斯年馆藏清单](https://dap.ihp.sinica.edu.tw/digitization/53/?page=7)独立证实条码165211为王行半轩集6卷旧钞本，已数字化。这里并未打开影像，WorldCat仅返回空壳，不把“数字化”冒称“已阅”。应先比六卷本篇目与12卷本及补遗，再决定是否重分卷同书。旧`merged_in`含`d59f6eigqqkg`历史必须完整保留。

## 验证与执行门槛

`build_checkpoint.py`只读打开现有SQLite；manifest基线等于固定main，完整树SHA256匹配。10个Work与5个作者Entity原始UTF-8字节SHA256、Git blob SHA1及固定main树条目逐一相符：15同字节、0漂移、0墓碑。`original-records.json`保留完整原档；`formal-rules-main.md`从固定main对象读取。`overlap-check.json`扫描所有既有cases得到0命中，五案均无替代关系。12个参考来源逐项关联工具快照；7份原始工具响应（含失败/无关检索线索）由`evidence-manifest.json`散列，绝不当作原PDF散列。

所有case均明确`execution_hold=true`、`execution_mapping=null`。本轮未清点Book和全型别引用、草稿/promotions、book-text；没有误报schema、T/L/P/R、分类、官方索引或builder绿灯。下一步须重新核最新main，逐Book范围与来源建无损字段台账，完整检查正式库/草稿/text联动，形成可重复的脚本与前置SHA256映射，实际写后再运行正式规则全部检查，最后小批PR交付。确认题名同一不等于执行门槛已过。
