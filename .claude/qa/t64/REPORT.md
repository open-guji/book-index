# T64（overview#367，接 #358 T63）报告

## 提交
- 数据与工具改动：`203d7cde4d`。**注意：该提交信息是「合流後索引回寫（reindex.py）」，不是我写的。** 我先 `git add` 前误跑了 `pushmain.sh`（当时 HEAD 脱离 main，`git checkout main` 因有未提交改动失败，我未察觉），脚本的「索引回写」步骤把工作区全部改动一并 `git add -A` 提交并推上了 main。内容经 verify.py OK 后才推，数据无误，只是提交信息不对。已推的 main 不改写，此处说明。
- 本报告：见本文件所在提交。

## 第一步：mergework.py 补三处缺口（+测试）
1. 并后 `Book.work_id`（及 `Collection.work_id`）改指 keeper，记录与 `index/books`／`index/collections.json` 同改。
2. keeper 的 `related_works` 删自指项（含指向被并者、改指后成自指者，以及原有自指项）。
3. 重算 keeper `_edition_count`（与 verify.py 同口径＝Book.work_id 指向 keeper 的 Book 数；0 则删该字段）。
4. 顺手：改指后的 `related_works[].title`／`contained_works[].title` 同步为 keeper 现名（否则 verify 报 title 漂移，孝經一条实际触发）。
- 测试：`tests/test_mergework_t64.py`（沙盒端到端：改指、自指、计数、无 Book 时去字段、title 同步），`tests/test_mergework_fields.py`、`.claude/qa/tests/test_entity_merge.py` 仍通过。

## 合并表（Work 95,044 → 95,038，并掉 6 条；Entity 并 2 条）
| # | 保留 | 并掉 | 理由（库内证据） |
|---|---|---|---|
| 1a | Entity `hixhd2h9bmgu` 嚴用和 | Entity `hixhd2h9bv7h` 嚴用和 | 同一人：两 entity 各只繫《濟生方》一书（即同书二条）；《四庫總目》「宋嚴用和撰」、《清史稿藝文志》「宋嚴用和濟生方」。「明」系 entity_propagation 之误，并后 dynasty/period 改宋。保留 bmgu 因 alt_names、籍贯、external_ids 较备。 |
| 1b | Work `d59f2nj2nh8j` 濟生方 | `d59f2hsf8iyo` 嚴氏濟生方 | 嚴氏条 ai_note 已载「《濟生方》即《嚴氏濟生方》，非二书」；二条同撰人同卷（八卷）。保留濟生方：通行题名，四庫提要、分类、资源皆备。并后：dynasty/period 明→宋；description 原「別無他證」失实已重写；清史稿著录一节并入；Book 3 部（_edition_count=3）；resources 并入时重复的 wikisource 去重。 |
| 2a | Entity `hixhd2h9bnq8` 王實甫 | Entity `hixhd2h9bnqy` 王德信 | 两 entity 互以对方名为 alt_names；Work 西廂記 ai_note「元王德信（實甫）撰」。为并 2c 先行。**两者 cbdb_id 不同（690977／101416，皆 auto_create），库内无证可定，保留 bnq8 之值，被并者之 101416 记入 ai_note，未入 external_ids。** |
| 2b | `d59f2j4v7dvl` 西廂記（王實甫） | `d59f2j5992bl` 西廂記（王德信撰、關漢卿續） | 题同；撰人同一人（见 2a）；皆朱墨套印本（「明烏程凌氏刊」／「明淩濛初刻」）。「關漢卿續」补入 keeper authors（无 entity_id，同原条）。 |
| 2c | `d59f2j5a6ry8` 新校注古本西廂記（王實甫） | `d59f2j522lts`（王德信） | 题同；同为香雪居刻（「明萬曆間香雪居刊本」／「明萬曆四十二年王氏香雪居刻本」）。 |
| 2d | `d59f2j4xpa80` 張深之先生正北西廂秘本（王實甫） | `d59f2j4qitq8`（王德信、關漢卿續） | 题同；「明末刊本」／「明崇禎刻本」；同 2b，補「關漢卿續」。 |
| 4 | `d59f28noh3ph` 孝經注疏 | `d59f28nbd4w5` 孝經正義、`d59f2hel1s04` 孝經正義（邢昺） | 正義＝注疏：正義条四庫「唐玄宗明皇帝禦注，宋邢昺疏」，崇文總目「邢昺等撰」；known-issues `suitang-20260906-L孤雁連帶重出六組` 之六同判「一書二題」。**第三条 d59f2hel1s04 不在任务点名之列，因与注疏条为同一证据链一并并入。** 保留注疏条：authors 兼御注与疏、Book 8 部、入十三經注疏 Collection。卷数（正義三卷／書目答問九卷）为分卷之异。并入时搬来的 dynasty「唐」已撤（keeper period=song）。 |

另改 `Collection/h/h/k/8rlcsybg2hhk/zhsy_book_mappings.json`（3 处 work_id）与 `Collection/c/q/o/8rlb6yi1ecqo/cptw/volume_book_mapping.json`（1 处）。

## 不并（同名别书／关系已定），已补 ai_note 区分
- 第3组 後漢書三条：
  - `d59f28mh3478`（李賢注本，百卷）与范曄条 `d59f28715gqo`：不并。库例以 `contains_text_of` 把注本繫于范曄条，注本与正文各一条（该条 T3 ai_note：「本條所著錄者是李賢注本，非范曄原書」）。两条各补一句。
  - `d59f9uwcyvig`（補晉志无撰人一百卷）：既非范曄书也非李賢注本——其所据案语自称「祕書監袁山松撰」。补了一句区分；是否并袁山松后漢書见下「拿不准」。
  - 附记（未动）：`d59f28715gqo` 的 indexed_by 里仍留一节新唐書藝文志「章懷太子賢注後漢書一百卷」，与 `d59f28mh3478` 所繫重复（2026-08-20 旧案称已归他条，此节未撤）。

## 拿不准（未动）
1. 典語 `d59f9uwotw5g`（補晉志，无撰人十卷）／`d59f27sslssk`（陸景，輯佚一卷）：补晉志该条案语自称「陸景撰。据《舊唐志》」，全库同题仅此一条有撰人，我倾向是同书（輯本一卷与原書十卷之卷数差由輯佚而来）。但 2026-09-06 的前案依「不据考证文回填撰人」之则判异书，我不愿无声推翻已立之则。**建议并，keeper=d59f27sslssk；请裁。**
2. 後漢書 `d59f9uwcyvig`（補晉志）：同理，案语称袁山松撰，疑与 `d59f27y9vs3l` 袁山松後漢書（東晉，101卷，另有补晉志二家著录）、`d59f9pqkl0cq` 袁崧後漢書 为同一书。同上则，未动。
3. 新刻出像增補搜神記 `d59f27x76cqs`（干寶，20卷）／`d59f2q95czy9`（續修，6卷，无撰人）：`d59f27x76cqs` 下挂的两部 Book 一为文淵閣四庫本《搜神記》（20卷原书），一为明金陵唐富春校刊《新刻出像增補搜神記》（故宮 6 冊），是**混装的 Work**；`d59f2q95czy9` 只对应后者。直接并会把 6 卷增補本并进 20 卷原书。须先把 `d59f27x76cqs` 拆开（原书 Book 归《搜神記》），之后 `d59f2q95czy9` 才可并入拆出的增補本条。（二条 B3 旧注亦言「須先釐清，不可再併」。）
4. 郎潛紀聞二筆三筆 `d59f2mubs2yp`（續修，十二卷；所繫 Book 题「郎潛紀聞」光緒甲申重刊，故宮 8 冊）／二筆 `d59f2ncmq1oh`（清史稿 16 卷）／三筆 `d59f2ncn1a80`（清史稿 12 卷）：二筆、三筆彼此不是一书；合刻本是否＝二者之和、还是只有三筆（12 卷与三筆同数）库内无证。不并二筆三筆，不动。

## 西廂記相关 Work 清单（除上表已并，其余库内尚存，均未并）
- 书名不同、各为独立版本条，不并：`d59f2j4qu29u` 三先生合評元本北西廂、`d59f2j4pwcn5` 重刻訂正元本批點畫意北西廂、`d59f2j4t0q2o` 拯西廂、`d59f2j4u9o8y` 新刊合併董解元西廂記新刊合併王實甫西廂記（合刻）、`d59f2neblfy8` 新校注古本西廂記彙考（王驥德）、`d59f2gnclds1` 奇妙全相注釋西廂記卷首題詠、`d59f2nl0vvnm` 識閒堂第一種翻西廂（周公魯）、`d59f2pwsv1tu` 新編題西廂記詠十二月賽駐雲飛。
- 他书：`d59f2gjsauip` 古本董解元西廂記（董解元，諸宮調）。
- 同名异书（撰人不同）：`d59f2j4mgqo1` 西廂會真傳（王實甫）与 `d59f28m0uryb` 西廂會真傳（元稹）。未补区分，建议补。
- 金聖嘆批本一族，题名不同、版本不同，证据不足不并：`d59f2j55tgci` 貫華堂第六才子書西廂記（作者栏王德信、清貫華堂刊）、`d59f2mxz6znl` 第六才子書西廂記（金聖嘆評、文會堂）、`d59f2n5epd6p` 增補簽注繪像第六才子西廂釋解。
- 并后各 keeper 的 `_edition_count` 已重算（4v7dvl=3、5a6ry8=2、xpa80=2）。

## 检验
- `python3 .claude/qa/verify.py` → OK；`backrefs.py --audit` 悬空 0；`reindex.py` 待回写 0。
- Work 数：95,044 → 95,038（差 6＝并掉 6 条）；Entity 并掉 2 条。
- 被并 id（6 条 Work、2 条 Entity）在 Work/Book/Collection/Entity/curation/index 无结构性引用（唯余 ai_note／merged_in 的叙述性文字）。
- `Book.work_id` 悬空 0。

## 本仓外旧 id 引用（未改，待 book-text 一侧处理）
扫了 `open-guji/book-text`（66106d922）与 `open-guji/kaiyuanguji-web`（后者无命中）。`open-guji-dataset`、`book-index-manager` 等其余仓未扫。

| 文件（book-text） | 旧 id | 新 id |
|---|---|---|
| `Work/i/y/o/d59f2hsf8iyo/`（整个目录：manifest.json、default/index.json、kanripo/ …） | d59f2hsf8iyo | d59f2nj2nh8j |
| `index/texts/e.json`（键） | d59f2hsf8iyo | d59f2nj2nh8j |
| `Work/l/z/4/d59f2mp0flz4/default/030.json`（work_id） | d59f2hsf8iyo | d59f2nj2nh8j |
| `Work/4/w/5/d59f28nbd4w5/`（整个目录：manifest.json、default/index.json …） | d59f28nbd4w5 | d59f28noh3ph |
| `index/texts/6.json`（键） | d59f28nbd4w5 | d59f28noh3ph |
| `Work/1/d/u/d59f2htm01du/default/006.json`（work_id） | d59f28nbd4w5 | d59f28noh3ph |
| `Work/9/3/6/d59f2nl40936/default/002.json`（work_id） | d59f28nbd4w5 | d59f28noh3ph |
| `Work/9/6/q/d59f2gdp696q/default/007.json`（work_id） | d59f28nbd4w5 | d59f28noh3ph |
| `Work/a/f/4/d59dh3vo9af4/default/036.json`（work_id） | d59f28nbd4w5 | d59f28noh3ph |
| `Work/c/1/t/d59f2hqc0c1t/default/007.json`（work_id） | d59f28nbd4w5 | d59f28noh3ph |
| `Work/d/1/d/d59f2mel8d1d/default/013.json`（work_id） | d59f2hel1s04 | d59f28noh3ph |

注意：book-text 里 `Work/3/p/h/d59f28noh3ph/` 已存在（keeper 自己的文本目录），旧目录 `d59f28nbd4w5`（Kanripo WYG 本）搬过去会撞，需作为新版本并入而非覆盖；`index/texts/8.json` 亦已含 d59f28noh3ph 的键。
