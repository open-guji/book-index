# book-index Schema（目录页）

**格式定义已移到 [`schema/`](schema/README.md)**（2026-10-08 终版，overview#496）。本档只是目录；`book-index-draft/SCHEMA.md` 同样指向这里。

| 档 | 讲什么 |
|---|---|
| [schema/README.md](schema/README.md) | 总则、源档与产物、文件布局、ID、版本号、JSON 书写格式、校验入口、字段表体例 |
| [schema/common.md](schema/common.md) | 共用对象：authors、IndexEntry、resources、Description、Source、Location、计量、dating、并条账、共通管理字段、revision 口径、朝代与时代轴 |
| [schema/work.md](schema/work.md) | Work 字段表；关联词表 |
| [schema/book.md](schema/book.md) | Book 字段表 |
| [schema/collection.md](schema/collection.md) | Collection 字段表 |
| [schema/entity.md](schema/entity.md) | Entity：people、collective（官署）、dynasty、reign、office、place；校验码 |
| [schema/classification.md](schema/classification.md) | 分类目录 `classification/` |
| [schema/promotions.md](schema/promotions.md) | 升格对照表 `promotions/` |
| [schema/text-files.md](schema/text-files.md) | 整理本与辑佚档 |
| [schema/derived.md](schema/derived.md) | 构建产物 `_build/`、`index/` 与派生字段 |
| [schema/legacy.md](schema/legacy.md) | 旧字段与旧写法 |
| [schema/cataloging-rules.md](schema/cataloging-rules.md) | 录入判准 |
| [schema/CHANGELOG.md](schema/CHANGELOG.md) | 格式变更记录 |
| [schema/json/](schema/json/) | JSON Schema（机器可读版） |

---

## 附：D1 校验读取的朝代规范名表（过渡）

`.claude/qa/entity_subtypes.py` 的 `load_canonical_dynasties()` 目前从本档读下面两张表的首列，作为 dynasty 条目 `primary_name` 的枚举（`check_v2.py` D1）。权威版本在 [schema/common.md〈规范朝代名全表〉](schema/common.md#规范朝代名全表)，两处须逐字一致；校验脚本改读 `schema/` 之后删除本附录。

**規範朝代名完整枚舉**（按時序；2026-10-07 起與草稿庫 `schema-v2` 已入之 139 條 dynasty 條目逐字一致，overview#464）

> 本表首列即 `Entity.subtype=="dynasty"` 條 `primary_name` 之規範名來源（`check_v2.py` D1 讀此表）。條目化後改由 build 從條目生成、本表退為說明，**不得再手寫第二份**。
> 2026-10-07 起已刪 CBDB `c_dy` 列：本庫不與 CBDB 匹配、不存任何 `cbdb_*` 外部 id（用戶定，#464）。
> period 為默認值，**不反寫** `Work.period`；「null」＝無對應 period（非 12 值之一，如元末群雄、域外）。
> 北宋、南宋之上增「趙宋」（兩宋通稱，作上級條）；兩漢、十六國、十國為上級通稱條。

| 規範名 | period | 別名（庫中已有寫法；＊＝ambiguous，單獨不能定位） | 說明 |
|---|---|---|---|
| 上古傳說 | pre-qin | 上古傳說 | 三皇五帝 |
| 上古 | pre-qin |  | 上古泛稱 |
| 夏 | pre-qin |  |  |
| 商 | pre-qin |  |  |
| 西周 | pre-qin |  |  |
| 東周 | pre-qin |  |  |
| 春秋 | pre-qin |  |  |
| 戰國 | pre-qin |  |  |
| 先秦 | pre-qin | 漢前、漢以前 | 漢以前泛稱 |
| 春秋齊 | pre-qin |  | 諸侯國 |
| 春秋晉 | pre-qin |  |  |
| 春秋吳 | pre-qin |  |  |
| 春秋魯 | pre-qin |  |  |
| 戰國齊 | pre-qin |  |  |
| 戰國楚 | pre-qin |  |  |
| 戰國趙 | pre-qin |  |  |
| 秦 | qin-han | 贏秦 | 贏秦=嬴秦之訛 |
| 西漢 | qin-han |  |  |
| 新 | qin-han |  | 新莽（王莽） |
| 東漢 | qin-han | 東漢末、後漢(東漢別稱) |  |
| 兩漢 | qin-han | 前後漢 | 西漢與東漢的合稱 |
| 玄漢 | qin-han | 漢＊ | 劉玄所建，年號更始，後為赤眉所滅 |
| 赤眉 | qin-han |  | 新末赤眉軍所立政權，年號建世 |
| 三國魏 | three-kingdoms | 曹魏 |  |
| 三國蜀 | three-kingdoms | 蜀漢 |  |
| 三國吳 | three-kingdoms | 孫吳 |  |
| 三國 | three-kingdoms |  | 通稱，不拆 |
| 西晉 | jin |  |  |
| 東晉 | jin |  |  |
| 晉 | jin |  | 兩晉通稱 |
| 前涼 | jin |  | 十六國之一 |
| 前秦 | jin |  | 十六國之一 |
| 後秦 | jin | 姚秦 | 姚秦=後秦（姚萇） |
| 西燕 | jin |  | 十六國之一 |
| 北涼 | jin |  | 十六國之一，末期入南北朝 |
| 十六國 | jin |  | 五胡所建諸政權的通稱 |
| 成漢 | jin | 大成 | 氐人李氏據蜀，初號成，後改漢；屬十六國 |
| 前趙 | jin | 趙＊、漢趙 | 匈奴劉氏所建，初號漢；屬十六國 |
| 代 | jin | 拓跋代 | 鮮卑拓跋氏之代國；屬十六國 |
| 後趙 | jin | 趙＊、石趙 | 羯人石氏所建；屬十六國 |
| 前燕 | jin | 燕＊ | 鮮卑慕容氏所建；屬十六國 |
| 冉魏 | jin | 魏＊ | 冉閔所建，國號魏；屬十六國 |
| 後燕 | jin | 燕＊ | 慕容垂所建；屬十六國 |
| 西秦 | jin | 秦＊、乞伏秦 | 鮮卑乞伏氏所建；屬十六國 |
| 後涼 | jin | 涼＊ | 氐人呂氏所建；屬十六國 |
| 南涼 | jin | 涼＊ | 鮮卑禿髮氏所建；屬十六國 |
| 南燕 | jin | 燕＊ | 慕容德所建，都廣固；屬十六國 |
| 西涼 | jin | 涼＊ | 李暠所建，都敦煌酒泉；屬十六國 |
| 桓楚 | jin | 楚＊ | 桓玄篡晉所建，國號楚 |
| 胡夏 | jin | 夏＊、赫連夏、大夏＊ | 匈奴赫連氏所建，國號夏；屬十六國 |
| 北燕 | jin | 燕＊ | 高雲、馮跋所建；屬十六國 |
| 南朝宋 | nanbeichao | 劉宋、宋(劉) |  |
| 南朝齊 | nanbeichao | 南齊 |  |
| 南朝梁 | nanbeichao | 南梁 |  |
| 南朝陳 | nanbeichao | 陳 |  |
| 南朝 | nanbeichao |  | 通稱 |
| 北魏 | nanbeichao | 後魏 | 亦稱元魏 |
| 北齊 | nanbeichao |  |  |
| 北周 | nanbeichao |  |  |
| 北朝 | nanbeichao |  | 通稱 |
| 南北朝 | nanbeichao |  | 通稱，不拆 |
| 東魏 | nanbeichao | 魏＊ | 高歡所控北魏孝靜帝政權，都鄴；屬北朝 |
| 西魏 | nanbeichao | 魏＊ | 宇文泰所控北魏文帝政權，都長安；屬北朝 |
| 侯漢 | nanbeichao | 漢＊ | 侯景篡梁所建，國號漢 |
| 西梁 | nanbeichao | 梁＊、後梁＊ | 蕭詧所建的附庸政權，與南朝梁並稱 |
| 隋 | sui-tang |  |  |
| 唐 | sui-tang |  |  |
| 鄭（王世充） | sui-tang | 鄭 | 隋末王世充所建 |
| 武周 | sui-tang | 周＊、大周＊ | 武則天改唐為周的政權，夾於唐中 |
| 夏（竇建德） | sui-tang | 夏＊、竇夏 | 隋末河北義軍首領竇建德所建 |
| 魏（李密） | sui-tang | 魏＊ | 隋末李密據洛口所建，瓦崗軍所奉 |
| 涼（李軌） | sui-tang | 涼＊ | 隋末李軌據河西所建 |
| 梁（梁師都） | sui-tang | 梁＊ | 隋末梁師都據朔方所建，倚突厥 |
| 楚（林士弘） | sui-tang | 楚＊ | 隋末林士弘據江西所建 |
| 秦（薛舉） | sui-tang | 秦＊ | 隋末薛舉據隴西所建 |
| 定楊（劉武周） | sui-tang | 定楊、劉武周 | 隋末劉武周據馬邑所建政權，無正式國號 |
| 梁（蕭銑） | sui-tang | 梁＊ | 隋末蕭銑據江陵一帶所建 |
| 燕（高開道） | sui-tang | 燕＊ | 隋末高開道據北平一帶所建 |
| 梁（沈法興） | sui-tang | 梁＊ | 隋末沈法興據江南所建 |
| 楚（朱粲） | sui-tang | 楚＊ | 隋末朱粲據荊襄所建 |
| 許（宇文化及） | sui-tang | 許 | 隋末宇文化及弒煬帝後所建 |
| 吳（李子通） | sui-tang | 吳＊ | 隋末李子通據江淮所建 |
| 漢（劉黑闥） | sui-tang | 漢＊、漢東 | 唐初劉黑闥承竇建德餘部所建 |
| 宋（輔公祏） | sui-tang | 宋＊ | 唐初輔公祏於江南所建 |
| 大燕（安祿山） | sui-tang | 大燕＊、燕＊ | 安史之亂中安祿山所建，歷四帝 |
| 秦（朱泚） | sui-tang | 秦＊ | 唐德宗時朱泚所建 |
| 楚（李希烈） | sui-tang | 楚＊ | 唐德宗時淮西節度使李希烈所建 |
| 漢（朱泚） | sui-tang | 漢＊ | 朱泚由秦改稱的國號 |
| 大齊（黃巢） | sui-tang | 大齊＊、齊＊ | 唐末黃巢起義所建政權 |
| 後梁 | five-dynasties |  | 五代朱溫 |
| 後唐 | five-dynasties |  |  |
| 後晉 | five-dynasties |  |  |
| 後漢 | five-dynasties |  | 五代劉知遠（東漢亦稱後漢，個別宜核） |
| 後周 | five-dynasties |  |  |
| 五代 | five-dynasties |  | 通稱，不拆 |
| 前蜀 | five-dynasties |  | 十國之一 |
| 後蜀 | five-dynasties |  | 十國之一 |
| 楊吳 | five-dynasties | 吳(楊) | 十國之一 |
| 南唐 | five-dynasties |  | 十國之一 |
| 吳越 | five-dynasties |  | 十國之一 |
| 閩 | five-dynasties | 閩國 | 十國之一 |
| 十國 | five-dynasties |  | 五代時南方與河東諸政權的通稱 |
| 馬楚 | five-dynasties | 楚＊ | 馬氏據湖南；屬十國 |
| 南漢 | five-dynasties |  | 劉氏據嶺南；屬十國 |
| 南平 | five-dynasties | 荊南、北楚 | 高氏據荊南；屬十國 |
| 北漢 | five-dynasties |  | 劉崇據河東；屬十國 |
| 大燕（劉守光） | five-dynasties | 大燕＊、燕＊ | 五代初劉守光據幽州所建 |
| 北宋 | song |  |  |
| 南宋 | song |  |  |
| 趙宋 | song | 兩宋、南北宋、宋＊ | 宋代的通稱，以別於南朝劉宋 |
| 遼 | liao-jin-yuan |  |  |
| 西夏 | liao-jin-yuan |  |  |
| 金 | liao-jin-yuan |  |  |
| 蒙古 | liao-jin-yuan |  | 蒙古汗國至元 |
| 元 | liao-jin-yuan |  |  |
| 偽齊 | liao-jin-yuan | 齊＊、劉齊、大齊＊ | 金扶持劉豫（1130-1137） |
| 西遼 | liao-jin-yuan |  | 耶律大石西遷所建 |
| 北元 | liao-jin-yuan |  | 元亡後退據漠北的政權 |
| 北遼 | liao-jin-yuan |  | 遼末耶律淳於燕京所建，不久即亡 |
| 明 | ming |  |  |
| 清 | qing | 清末 |  |
| 後金 | qing |  | 滿洲人入關前政權，1616 年努爾哈赤建，1636 年皇太極改國號為清 |
| 中華民國 | modern | 民國、民初 |  |
| 中華人民共和國 | modern | 當代、現代、近代 |  |
| 天完 | null |  | 紅巾軍徐壽輝所建 |
| 大周 | null | 周＊、大周＊ | 張士誠據江浙所建政權 |
| 韓宋 | null |  | 紅巾軍韓山童、韓林兒所建 |
| 大漢 | null |  | 陳友諒所建政權 |
| 明夏 | null | 夏＊ | 明玉珍據四川所建政權 |
| 大順 | null |  | 李自成所建農民政權 |
| 南明 | null |  | 明亡後南方的明宗室政權 |
| 大西 | null |  | 張獻忠所建農民政權 |
| 吳周 | null |  | 吳三桂在衡州稱帝所建政權 |
| 太平天國 | null | 太平天国 | 洪秀全所建的農民政權 |

**域外朝代**（不歸入 period 枚舉，`period` 留 null；日本、江戶時代、朝鮮、新羅、高麗已建 dynasty 條，韓國、英國、美國、比利時是國名不建條，`dynasty` 保持自由文本、`_dynasty_id` 留空）：

| 規範名 | 庫中寫法 | 說明 |
|---|---|---|
| 日本 | 日本、日 | |
| 江戶時代 | 日本江戶時代、日本寶永年間 | 寶永為江戶時代年號 |
| 朝鮮 | 朝鮮、朝鮮（明） | 李氏朝鮮，1392–1897 |
| 高麗 | 高麗 | 高麗王朝，918–1392；2026-10-07 起從朝鮮拆出（CBDB c_dy=14，與朝鮮前後相繼，#464） |
| 新羅 | 新羅 | 朝鮮三國之一 |
| 韓國 | 韓國 | |
| 英國 | 英國 | |
| 美國 | 美國 | |
| 比利時 | 比利時 | |

**需拆分的歧義朝代**：见 [schema/common.md](schema/common.md#需拆分的歧义朝代逐条判定不自动归并)。
