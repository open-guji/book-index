# 史部20:00新候选审查：9案，4确认、1分立、4待核

固定main `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本轮只写本目录；原生合并0。读取当前正式库并条规则，Work身份确认与执行放行严格分开。未重跑H-C010/H-C082，未使用旧1876映射。

继承宽扫发现覆盖68,536个史部联合范围Work、214,720候选对（非判同数）；本轮人工审查9组、17个不同Work，新增宽扫候选8组，另从台湾同地同年号邻域补1组分立。前8组以discovery_candidate_ids记录H-BROAD发现来源；这些宽扫候选不是旧有效案件。本轮9案均为新审查案件，supersedes为null，不替代任何旧案。

快照54档（17 Work、30 Book、7 Collection），原字节存snapshots/，Git blob与固定主树逐档相等；Work另与SQLite SHA256相等。旧归档Book/Collection只有字节匹配当前树才使用。当前记录及源instance指针见current-records.json。此为题名邻域，未声称全引用扫描。

## 本轮结论

| 案 | 状态 | 判断 |
|---|---|---|
| H-2000-001 | open | 新疆全书与分篇范围不能因短题合并 |
| H-2000-002 | open | 台湾一卷杂钞不能直接等同范志二十五卷 |
| H-2000-003 | confirmed | 嘉定镇江志方括号与丛书子目同一原作 |
| H-2000-004 | confirmed | 天启东安六卷原志与残五卷为同一原作 |
| H-2000-005 | open | 丁酉北闱七狱疑大狱讹字但南京原本未核 |
| H-2000-006 | confirmed | 丙湖是香艳丛书西湖游幸记子目误字 |
| H-2000-007 | open | 二十四史日月考236卷与残存月日考须核总范围 |
| H-2000-008 | confirmed | 于阗行程记/录有原目录明确异名校语 |
| H-2000-009 | separate | 刘良璧二十卷与六十七/范咸二十五卷为前后修次，不能删福建/重修归一 |

## H-2000-001 — [乾隆]新疆外藩紀畧 / [乾隆]新疆紀畧

成员：`d59fyqws9hq9`, `d59fz6iy1c74`。

固定记录两题均署七十一；外藩题二卷有乾隆四十二年思位堂刻本，短题同时含西域闻见录本、丛钞本及一卷著录。
LOC实物目录把同一总题之下的新疆纪略与外藩纪略分装，说明总题、分题共存。当前外藩二卷到底只含外藩分篇还是全书，尚无卷首及目录证据。

证据：[S1](https://www.loc.gov/item/2014514489/)。

仍需：读9949tyvk74等思位堂本目录、卷首和末叶，核是否新疆篇或外藩篇；再核994pgaw5j4的西域闻见录位置及一卷条的节录界限。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-002 — [乾隆]臺灣府志 / [乾隆]重修臺灣府志

成员：`d59fyfdagoow`, `d59fynrbt7uq`。

993yll8zk0 contained_in→8rldo9qhnwua明确为管庭芬待清书屋杂钞，所载一卷；范志主体二十五卷首一卷。
独立提要确认范志的篇章纲目和增损前志性质，无法证明杂钞一卷是残卷、节抄还是摘要改编。

证据：[S2](https://taicool.ith.sinica.edu.tw/browse-ebook.html?id=EB0000000105)。

仍需：查天津图书馆待清书屋杂钞该子目起讫、卷首题及选抄说明；在摘编/残本范围消歧前不定keeper。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-003 — [嘉定]鎮江志 / 嘉定鎮江志

成员：`d59f2hrjebk2`, `d59fymhwgt1c`。

同属宋卢宪嘉定镇江志，22卷主体；宛委别藏残22卷首1卷独立馆目与两侧所载版本相接，括号是年号标示。附录、清人校勘记属于版本附属，不构成另一卢宪原作。
Book 994bqhru9t把宣统二年刻与宋嘉熙二年碛砂延圣院刻串接并解析year1238；9945fxcw74把抄本与奚冈篆刻串接；9950nh4740把嘉定六年修误当抄写年1213。三处是出版字段污染，不能随合并当真保存为统一出版断代。

证据：[S3](https://ci.nii.ac.jp/ncid/BN03253416), [S4](https://ci.nii.ac.jp/ncid/BA64163665)。

仍需：合并前逐字段保留22/30卷历史著录分歧、两版校勘责任；污染字段单独原目录核查/台账，不给Book机械并条。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-004 — [天啓]東安縣志 / 天啓本東安縣志殘

成员：`d59fynqru134`, `d59fz6izliww`。

9946simxa8著原六卷而馆藏注明存卷二至六；994pgde1vk残五卷挂安次县旧志合刊Collection，责任人为郑之城修、冯泰运纂。
独立东洋文库同一安次上下文明确天启五年原本、存卷2–6，并把康熙10卷和乾隆22卷列为另种，排除同名异地及不同修次误并。

证据：[S5](https://www.toyo-bunko.org/open/KansekiQueryResult10.php?ORDERBY1=&UNIT=200&andor=&iPage=56&iTotal=80868&navizonestart=6&searchtype=&sw1=)。

仍需：保留6卷原数和残存5卷分别作用域；1935/1936合刊年份与鄭之城/成字异需版本层核查，不能机械合Book。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-005 — 丁酉北闈大獄記畧 / 丁酉北闈七獄記畧

成员：`d59fxv8iodts`, `d59fxyd4ukn4`。

同一信天翁权威URI、一卷及1911商务印书馆的独立藏品目录强烈支持七→大误录。
但独立1917台大本不是南京1911本；现有目录摘要未给七狱侧卷首、正文起讫或痛史分册位置。

证据：[S6](https://www.ahm.cn/Wap/News/Details/cpzm?nid=11165), [S7](https://commons.wikimedia.org/wiki/File:NTUL-9900006341_丁酉北闈大獄記略_一卷.pdf)。

仍需：读南京图书馆38oqlna27qelkyz6对应卷首及1911出版牌记，与痛史第三种及正文首末核同；确认是源目录误录后方可改题并条。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-006 — 丙湖遊幸記 / 西湖遊幸記

成员：`d59fyel16arl`, `d59fyrs8f5z4`。

丙湖Book993xj9k2yo父8rldo8x3677k确指宣统国学扶轮社香艳丛书，西湖Book994b8q6q68亦明记香艳丛书本，作者周密、一卷一致。
独立实体馆藏编目PDF目验第26页，香艳十一集确著西湖游幸记，前后子目连续；这条母子位置证据比同题同作者摘要更强，丙/西形近误字可认定同一Work。

证据：[S8](https://www.city.machida.tokyo.jp/bunka/bunka_geijutsu/cul/cul08Literature/kensaku_mokuroku/aosiba.files/kanseki.pdf)。

仍需：未来合并保留丙湖源题及来源1wma8m8f8za6n50k作为误题台账；两Book源ID不同且edition/contained_in不同，不作机械并Book。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-007 — 二十四史日月考 / 二十四史月日考

成员：`d59f2ndjt79c`, `d59fyt7eejgh`。

当前日月考236卷来自清史稿艺文志；月日考两稿本有明确残存各史清单，并非完全没有卷数资料。
国图衍生目录A02187称存116卷，周书上卷；本库994cp88nb4馆藏notes作周书二卷。上图994cp7xerl覆盖宋辽金元，与国图残存范围不同，不能把残存卷数简单相加当作236。

证据：[S9](https://commons.wikimedia.org/wiki/File:NLC892-412000002897-66220_二十四史月日考_第19冊.pdf)。

仍需：对读清史稿原著录及汪氏稿本总目、序跋，证明日月/月日题倒置与236卷原编范围；优先校周书上卷/二卷差异。若并条，处理已有related_works改指后的自边。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-008 — 于闐國行程錄 / 于闐國行程記

成员：`d59f2gc9cv0h`, `d59f2gci3i82`。

钱绎崇文总目辑释卷二地理类，在平居诲于阗国行程记一卷条下明确说明宋志记作录；前项敦煌新录、后项晋安海物异名记范围清楚。
这直接解释两Work分别来自崇文总目/国史经籍志与宋史艺文志的题名差异；不是因复制书目段落自动判同。

证据：[S10](https://zh.wikisource.org/zh/崇文總目輯釋/卷二)。

仍需：未来保留记/录两题、各目录来源、资源和period依据；高居诲/平居诲人名版本问题另开人物审查，不在此案擅自更改作者实体。；未做全库引用/分类成员/promotions/草稿/book-text检查；确认只到Work身份，不等于可执行并条。；执行前重取main并逐档校hash，另立keeper/losers及无损字段台账，按正式规则跑T/L/P/R、schema、classification、derived检查。

## H-2000-009 — [乾隆]重修福建臺灣府志 / [乾隆]重修臺灣府志

成员：`d59fyqxfoagx`, `d59fynrbt7uq`。

当前记录分别署刘良璧与六十七/范咸、20卷首1卷与25卷首1卷。
中研院提要明确范志参酌、增损高/刘前志；同一地区和乾隆年号不取消后修新编身份。

证据：[S2](https://taicool.ith.sinica.edu.tw/browse-ebook.html?id=EB0000000105)。

仍需：不建立merge-map；可另核前后修订关系，但不以related关系替代两条身份。

## 证据边界与交接

实际目验仅为町田市民文学馆目录PDF第26页，非古书正文书影；于阗案阅读的是古目录原文转录。上图原始在线instance打开不可用，LOC 403、安徽馆405与陕西馆超时均未伪称已阅原页。sources.json逐项区分完整页面、检索片段、转录及图像。目录摘抄本身只证明来源，不独自证明作品身份。

嘉定案三个出版字段污染和二十四史稿本周书卷数冲突均已落入cases.json；未做原生修复。执行门槛必须另行完成，尤其无损台账、related自边、Book差异、全部引用与草稿同步。

旧人工cases的成员交叠检索结果：[]。

可复核产物：cases.json、sources.json、current-records.json、validation.json、snapshots/与build_report.py。
