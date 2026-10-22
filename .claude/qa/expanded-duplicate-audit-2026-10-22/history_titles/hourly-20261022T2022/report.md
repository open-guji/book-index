# 史部20:22新案：4组，3确认、1待核

固定main `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本轮仅写本目录；原生合并0。全部为新案，supersedes=null；跨六路既有cases.json成员ID检索无交叠。宽扫候选不是既有人工案件，也不计作确认。

实际复核8个Work成员，另读3个related目标Work、4个作者Entity；15份原字节快照全部与固定main树Git blob及只读census SHA256一致。没有Book/Collection全扫，没有书影目验，没有全引用或执行检查。

| 案 | 状态 | 结论 |
|---|---|---|
| H-2022-001 | confirmed | 㑹/會只是题名异体；两条均为谢承七卷原作的目录身份 |
| H-2022-002 | confirmed | 三朝北盟集編是徐梦莘自序题，與會編指同一二百五十卷书 |
| H-2022-003 | confirmed | 三藩/三籓紀事本末为杨陆荣四卷原作异体题 |
| H-2022-004 | open | 题名省记可解释，但宋原书与四库重辑本的作品范围须先定 |

## H-2022-001 — 㑹稽先賢傳 / 會稽先賢傳

成员：`d59f27scdgjm`, `d59f27suh81u`。

固定main两条同署三国吴谢承、同一Entity，均以七卷为原书卷数。异体题只载国史经籍志；常体题兼载隋唐目录。
已打开隋书卷33杂传原文转录，明确七卷谢承，并与钟离岫会稽后贤传记二卷、会稽先贤像赞五卷分列，排除邻题误并。

保留要求：两种原题、国史经籍志独有著录与来源、旧唐书五卷异数必须并存；七卷为原书，后世一卷辑本不得覆盖原卷数。；d59f27suh81u已有merged_in 1evcs0f6qxj40和related_works→d59fycrzr7y8；全部历史和出边保留。

执行门槛：d59fycrzr7y8明确清黄奭辑的一卷汉学堂知足斋本，本案不纳入；不得因原作身份确认自动吞并辑本。；d59f27suh81u indexed_by[2].summary尾部夹入徐整豫章列士传；单独台账清理串条，不传播为谢承著述。；执行前重新fetch main并校验原字节；制作keeper/losers逐字段无损台账及全部源值历史。；未扫描全库引用、分类成员、promotions、草稿及book-text；须另做全引用审计后跑T/L/P/R、schema、check_v2、classification和derived基线比较。；确认只涉及Work身份，不授权机械并Book或人物；本轮无原生修改。

来源：[S1](https://zh.wikisource.org/wiki/隋書/卷33)。

## H-2022-002 — 三朝北盟集編 / 三朝北盟會編

成员：`d59f2hj7qi2r`, `d59f2hrhiwap`。

固定main两条同署徐梦莘、同Entity、250卷，集编条来自国史经籍志。
国图明抄本卷首转录题三朝北盟集编序，并题三朝北盟集编书目；序述上中下三帙、250卷。国史经籍志卷三另列集补50卷，不能把集编误当续编。

保留要求：保留集編题名及国史经籍志著录；會編条全部资源组、馆藏链接及已合并历史保留。；序文转录的绍兴三十二年/四十六年，与库内四库提要的三十一年/四十五年有差别；不替换为统一断年，保留各源原话待书影核字。

执行门槛：不纳入北盟集补50卷；本轮未逐册检验會編条资源或Book。；识典卷首转录有明显OCR断句、误字；确认依序题与250卷结构，不采用自动转录每一字作精校。；执行前重新fetch main并校验原字节；制作keeper/losers逐字段无损台账及全部源值历史。；未扫描全库引用、分类成员、promotions、草稿及book-text；须另做全引用审计后跑T/L/P/R、schema、check_v2、classification和derived基线比较。；确认只涉及Work身份，不授权机械并Book或人物；本轮无原生修改。

来源：[S2](https://www.shidianguji.com/zh/book/NGJ892412000000049154883/chapter/1lvroqroh4wtv), [S3](https://www.shidianguji.com/zh/book/CADAL02091118/chapter/1lcq2me5aorop)。

## H-2022-003 — 三藩紀事本末 / 三籓紀事本末

成员：`d59f2moxmh34`, `d59f2nc7qnls`。

两条同署清杨陆荣、同Entity，均四卷；籓字条独载清史稿艺文志。
中研院提要明确杨陆荣、康熙五十六年成书，记南明福唐桂三王，四卷共22篇；其分卷篇目与本库四库提要相接，不能误解为吴三桂三藩之乱另一书。

保留要求：保留三籓源题及清史稿著录；四库存目、书目答问、存目丛书的四卷来源分别保留。；中国古籍总目著录title_info作二十二卷且摘要共22版本，与四卷原作冲突；不能把22篇/22版本自动转成22卷。

执行门槛：逐查d59f2moxmh34 indexed_by[3]对应总目原文和全部Book范围，排除丛编父子串接；本轮仅证明四卷原作身份，未证明22卷聚合来源可直接合入。；当前四库summary写康王，而中研院和卷目为唐王；此为独立字误风险，保留原值后核原书，不顺手覆盖。；执行前重新fetch main并校验原字节；制作keeper/losers逐字段无损台账及全部源值历史。；未扫描全库引用、分类成员、promotions、草稿及book-text；须另做全引用审计后跑T/L/P/R、schema、check_v2、classification和derived基线比较。；确认只涉及Work身份，不授权机械并Book或人物；本轮无原生修改。

来源：[S4](https://taicool.ith.sinica.edu.tw/browse-ebook.html?id=EB0000000149), [S5](https://www.guoxue.com/shibu/24shi/qingshigao/qsg_146.htm)。

## H-2022-004 — 五代史纂誤 / 五代史記纂誤

成员：`d59f2hs822gx`, `d59f2huxrchs`。

固定main纂误条引宋史三卷、直斋五卷；史记纂误条主要依据永乐大典辑本，作者同署吴缜。
四库提要明确原书久佚，辑得112事，相对晁公武所记200余事仅存五六成，又加薛史异同附识；卷数相近不证明原貌、重辑和附识层完全相同。
提要同时讨论刘羲仲作者异说并判不足据；这一异说应保留来源层，不另造吴缜/刘羲仲人物合并。

保留要求：保留宋史3卷、直斋5卷、重辑3卷及112事各自作用域；保留原作者异说、四库辑佚与附识责任。；related_works→d59f20aowb9c目前是司马迁史记，不能仅因标题含史记而当作五代史底本。

执行门槛：核宋原本/四库辑本身份模型、目录及首末，明确是否原作的一种版本或需独立辑佚Work，再定keeper。；d59f2huxrchs /related_works/0 的 contains_text_of→司马迁史记须单独核实，不能机械迁移为可信关系。；纂误条related→d59fyptzppfl是无名氏五代史纂不分卷明抄本，缺誤字也不能纳入本案；须独立看原件。；执行前重新fetch main并校验原字节；制作keeper/losers逐字段无损台账及全部源值历史。；未扫描全库引用、分类成员、promotions、草稿及book-text；须另做全引用审计后跑T/L/P/R、schema、check_v2、classification和derived基线比较。；确认只涉及Work身份，不授权机械并Book或人物；本轮无原生修改。

来源：[S6](https://zh.wikisource.org/zh-hant/四庫全書總目提要/卷046)。

## 边界与后续

五代史案保持open，并非因同作者自动合并。前三案也不是可执行merge-map；keeper_proposal仅供后续台账设计。会稽黄奭一卷辑本、北盟集补50卷均明确排除。三藩22卷字段和五代史错误关系均须先核，未原生修复。

S1/S2/S3/S6为原书或古目录转录，非书影校读；S4为中研院馆目完整提要；S5仅检索片段且直开超时。全部工具返回存evidence/web-retrievals.json，不能将搜索片段说成实物目验。未使用旧1876映射，未触动BOOK-0010、#1216四人或冯氏专案。

可复核：cases.json、sources.json、current-records.json、discovery-candidates.json、validation.json、snapshots/、evidence/、build_report.py。
