# 史部 19:00 续查：两份漂移正文已审，维持两案待核

固定基准 `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。已读 PLAN、史部 Astra 报告/cases 及该 main 的《正式库并条审查规则》。本轮替换 H-C010、H-C082 为 H-1900-001、H-1900-002，均为 open；史部仍为 **113案：9确认、3分立、101待核；实际新增合并0**。这里未将原作同一、版本相关或 related 边当作可执行合并。

## 原档读取及漂移结论

6份 Work 原文从固定 main 定点读取成功，SHA-256 与 Git blob 均重算；另外按固定主树同题路径取得24份邻域档案（20 Book、4 Work）。因partial clone的无懒取读取失败，后者使用旧归档原字节，经 Git blob 与固定 main 树逐一相等验证才当作当前证据，旧 book-index 本身不被视为main。30份原字节和双散列均落盘。范围是同题路径邻域，**不是全部引用**。

| 漂移成员 | 唯一变化字段 | 审后含义 |
|---|---|---|
| d59fym9z61hc 公門不費錢功德錄 | related_works 新增 d59fz73hih34 | 旧甘峻卿关联未变；题名、作者、总目及生成说明均未变。 |
| d59fybc8uxvk 太康地記 | 原无 related_works，新增王谟辑本及候选另一成员两边 | 原作、辑本关联被补入，不构成已经并条。 |

旧 SHA-256、旧/新 blob、完整前后值见 `upstream-drift-review.json`。两份 drift 的“正文读取 deferred”已由本目录证据解除；尚未解决的身份/执行门槛仍保留。`cases.json` 对两案四个成员每个现有顶层字段给出保留/处理理由。若将来并到其 related 对象，改指将产生自边，须明确处理并保存旧关系台账。

## H-1900-001：公門不費錢功德錄

原候选一侧 `d59fz73hih34` 只挂源 `n2htu6i0tvy33r07`。其直接Book `994q45lxxc` edition为空、无contained_in，只记中科院和上图藏；这不能凭馆藏交集推成天壤阁本。另一侧 `d59fym9z61hc` 对应明确的天壤阁本及丛书集成初编本。匿名“清□□撰”不能充当共同具名作者，故原两成员保持open。

同题邻域补见三个应优先精查的叢書子目Work：

| Work | 母丛书提示 | 直接Book |
|---|---|---|
| d59fyh7lgetd | 天壤閣叢書二十種增刊六種 | 99406xhc00；contained_in 8rldobjop9fn |
| d59fyi36ap6q | 天壤閣叢書二十種 | 99412cpcld；contained_in 8rldocexzrpf |
| d59fy3pv9gjk | 叢書集成初編四千一百七種 | 993mxxxla8；contained_in 8rldny4iwjy8 |

这三者不在原H-C010成员内，未为增加确认数而直接扩组。它们与明确版本侧构成比缺版次成员更强的下一步小组，仍须核母Collection、增刊位置及重印说明。

本轮打开[东京大学东洋文化研究所分类目录](https://shanben.ioc.u-tokyo.ac.jp/list.php?jump_data=2&order=rn_no&p=14)，该馆将一卷《公門不費錢功德錄》列为《明刑弼教錄》子目；母目明记天壤阁叢书之一、光绪六年刊本。再打开[馆藏PDF](https://shanben.ioc.u-tokyo.ac.jp/pdf/016960-公門不費錢功德錄一卷-冊一.pdf)，实际目验第3、4、5、14页（零起算2、3、4、13）：第3页有补刊序、王懿荣光绪六年署，第14页可见题名及天壤阁叢书刊牌。这次确有书影目验，初次第3/4页请求超时后重试成功；没有据序作者擅补全书作者。

旧关联 `d59fyna62n0g` 则是甘峻卿辑《不費錢功德錄》三卷附录一卷，光绪二十五年津逮楼本。其责任层次、篇幅与版本均不同，不能删掉“公門”便整条合入。本轮只排除这种未经证明的扩组，并未宣称已核两书全文而作全组separate。

## H-1900-002：太康地記

`d59fz73mi9s0` 的直接Book `994q3jg3cw` 同样是版本空、无contained_in的中科院一卷本；`d59fybc8uxvk` 的 `9952lyvjeo` 明记说郛本。新关联 `d59fymcjka9t` 明记“晉□□撰；清王謨輯”，有重订汉唐地理书钞、汉唐地理书钞、汉唐地理书钞存本三版本。不能以相同一卷或同一原书名把说郛节录与清代辑佚范围视为全等。

核读[畢沅《晉太康三年地志王隱晉書地道志總序》转录](https://www.shidianguji.com/zh/book/NLG312001056800/chapter/1lg83ljil2wwq)：乾隆四十九年序论旧书地志、地记、地理记、土地记诸称，并交代辑集和附录。该证据说明原作异名与后世辑佚，不等于现存所有辑本同一，也不能拿畢沅本直接证明王谟本内容范围。这里是读转录，未目验该序书影。

另定位两处具体解析污染，供独立修复，不作为并条理由：

| Book | 当前污染 | 原始著录可支持的边界 |
|---|---|---|
| 9945egx5vl | publication_info.year=漢；抄錄者=唐地理書；edition_type=抄本 | 《漢唐地理書鈔本》是叢书版本串；“鈔”不能自动证明抄写本，汉唐也非刊刻年份。 |
| 9945eglxc1 | publication_info.year=漢；刊刻者=唐地理書；ai_note称“存本”表示后印/补刻 | 原串为《漢唐地理書鈔存本》；目前没有刊年、刊者、后印的独立依据。 |

说郛Work还连到多种叢书子目Book，馆藏notes出现一百卷及一百二十卷本。这些是父叢书的卷数，不可改写成《太康地記》的卷数，也不可机械合Book。

## 下一步和交付边界

先查两个缺版次instance的母目、索书号及卷首；公门案优先核天壤阁三个强关联成员，太康案先拆清节录/辑本层次并独立修复出版字段污染。全引用、promotions、草稿和book-text门槛交根代理；本轮无keeper决策，无原生数据改写、提交、分支或外发。

交付：`cases.json`、`current-records.json`、`title-neighborhood-records.json`、`upstream-drift-review.json`、`references.json`、`validation.json`、`build_report.py`。脚本只重建本目录cases/validation，重算30档双散列；验证通过不等于schema、分类builder或全引用审计通过。
