# 子部四组新案（2026-10-22 T2022）

固定研究主线 `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本轮完整读取8份活动Work原档，审4组新pair：**2 confirmed、1 separate、1 open；正式合并0、原生数据修改0。** 全部 `execution_ready=false`。新案不替代旧案，`supersedes=[]`；不仅 broad 的 `old_cases` 为空，还扫描本审计树所有既有 `cases.json`，没有文件同时含任一新pair两端ID。

| 案号 | 两侧ID | 裁决 | 依据与限制 |
|---|---|---|---|
| MR-2022-001 | d59fxryzim80 / d59fybbiy8sg | confirmed | 䖷籛𤭏筆／䖷籛□筆，明楊慎；缺字侧原著录为⿰谷瓦，并明确记□的解码。与𤭏对应，說郛载体相接；不能把叢書整部并入子书。 |
| MR-2022-002 | d59fxzsh2ozl / d59fy5oui39c | confirmed | 陰陽管見，明何瑭一卷；相同责任与卷数，外部馆目实开确认百陵學山、學海類編两个载体。曝書亭辑本为另一版本，不能并Book为同版。 |
| MR-2022-003 | d59f2ng8w4ci / d59fxrwiv8jl | separate | 三遂平妖傳四卷二十回／墨憨齋批點北宋三遂平妖傳四十回；后者明确馮夢龍增補。不能删去题名修饰后视为同一范围。 |
| MR-2022-004 | d59fxuca40zm / d59fxwc307b5 | open | 不空罥／羂索神變真言經核心著录同为唐菩提流志译三十卷，但长记录聚合四译者、另两位菩萨造论责任。17条实例必须逐源核清，暂不整包合并。 |

## 证据强度与新发现

**缺字案最适合进入下一轮小批执行准备。** 缺字侧原 `indexed_by[0].title_info` 是「䖷籛（⿰谷瓦）筆」，`ai_note` 明记缺字解码；不是根据模糊方框猜书名。两条同楊慎person URI，一侧指說郛本，另一侧是說郛及說郛續容器子目。[焦竑跋](https://www.shidianguji.com/zh/book/7556499731703136306/chapter/1lgle66bjzndm)实开列楊慎著述，题作䖷籛瓻筆；[法兰西学院馆目](https://omnia.college-de-france.fr/discovery/fulldisplay/alma990003459400107166/33CDF_INST%3A33CDF_INST)搜索摘录为䖷籛𤭏筆一卷，直接打开失败。[CHISE字结构](https://www.chise.org/est/view/character/%F0%A4%AD%8F)搜索摘录核𤭏=⿰谷瓦，实开失败。后二者均未夸大为已实读全文。父叢書含原编及续编，仍须核具体子卷，保留子目卷数缺载。

**陰陽案是同书不同载体。** [CiNii BA55200501](https://ci.nii.ac.jp/ncid/BA55200501)实开明确何瑭撰、百陵學山、1967影印；[BB02338745](https://ci.nii.ac.jp/ncid/BB02338745)实开列學海類編第34冊中的陰陽管見，六安晁氏道光十一年跋，东京大学东洋文化研究所藏。后目责任原写何塘而作者入口何瑭，保留这个目录异字，不能引入新人物。两条目标Work的原作者、同朝代和一卷范围均一致，符合项目Work口径；新发现不支持将百陵、學海、曝書亭三种Book合为同版。曝書亭源实例尚未实开，列入执行门槛。

**平妖分立取范围证据，不以首位作者异名为理由。** 二十回侧孙楷第目录详记王慎修本、羅貫中编次及后来加题的馮猶龍增定；四十回侧總目明确馮夢龍增補。该署名不能被当成仅批点角色。[识典新平妖傳序](https://www.shidianguji.com/zh/book/CADAL02000633/chapter/1llwtnd07gjzz)可实开，但OCR有明显损坏，且引首为天許齋本，并非本案嘉會堂原刻影像；没有用残句重建回数。该案主证为固定main原始书目，不把外部搜索的现代复述替代原著录。二十回条现挂维基文库资源回数尚待核，不在本次偷偷纠正。Broad第16对另一个二十回Work未计数、未裁决。

**不空案发现的是来源汇聚污染风险。** 羂字长条第一责任为唐菩提流志，另列唐地婆訶羅、南北朝菩提留支及菩提流支；原注又有功德施与天親造的异常责任。即使两侧title_info同三十卷、author_info同唐菩提流志，也不能证明15实例全部属于同一经本。[CBETA續古今譯經圖紀](https://cbetaonline.dila.edu.tw/T2152)官方搜索摘录在 `T55n2152_p0371c16` 列该译者三十卷本，实开仅前端；[卷三十题署](https://cbetaonline.dila.edu.tw/T1092_030)也仅取得官方搜索摘录。两条均只能核标准经本，无法解释那些额外责任。本批保持open，要求17实例逐源建立作品/责任映射，不能顺势重合PR1216已经处理的人物。

## 可复核交付与边界

`cases.json` 为逐案裁决，含成员ID、原路径、SHA256、Git blob SHA1、原字段JSON指针、完整书目证据、上图instance URL及执行门槛。`original-records.json` 保存8条完整原对象与原始UTF-8；逐一重算两种散列，均与只读SQLite字段相符。固定main来源可信范围继承数据库manifest；本批没有声称独立重新抓取全树。`source-evidence.json` 区分实开馆目、转录原典、OCR损坏、搜索摘录与打开失败；`new-pair-validation.json` 留新pair排重结果；`validation.json` 明列未完成检查；`build_evidence.py` 可重建本目录证据。

执行前仍需最新main原值重验、全引用闭包、逐字段保留表、正式台账与可复现脚本、草稿/promotions同步及写后T/L/P/R、schema、check_v2、分类、官方索引和builder检查。SQLite不含Book/Collection、promotions全集，不能拿本轮散列通过冒充合并验证通过。

仅写本独占目录；未改共享汇总、原生数据、Git索引或分支，未触Feng外部数据审计。旧1876映射禁用；BOOK-0010 defer、JC-001/JC-007 hold保持。四案均为新增，无替代关系。
