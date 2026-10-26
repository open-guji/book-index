# 去重方案 5b-乙 第 3 批（2026-10-26）

「合并抄本与宽泛名重复 Book(5b-乙)」串。基线 book-index main 214f7287b0（合并前再合入 7fc8e16ca3）。

## 一、有年份刻本重跑：无新候选
`scan/` 三脚本从 main 重跑：同 Work 同版本名 dated 档 911 组，剔除后余 285 组；再剔故宫／国图一部一条藏本（用户已定不并）与地望不同族谱后，
只剩 47 组，均为故宫不同索书号藏本（如「贈善…」对「故志…」）、地望前缀不同的族谱或第 1 批判过 UNSURE 的 3 组。**本档不并。**

## 二、具名版本（named 档，「某叢書本」「某堂刻本」）64 组：并 28 组
named 档此前没有筛过。按 tier_dated 同样条件剔除（分立依據 281、measure_info 234、卷数 147、题名 63、物理描述 62、故宫国图一部一条 45、责任者 3）后余 64 组 129 个 Book。
- 独立子 agent 逐条读全文（`逐條核.tsv`）：SAME 41、DIFF 9、UNSURE 14；主串把 N061（宽泛「清光緒間刻本」）改存疑。
- 另一子 agent 盲检 13 组 SAME（`盲檢13.tsv`）：10 SAME、3 UNSURE，异质率超 3%，停批复盘：分歧全落在「同道同批、id 相邻、无互著迹象」的组（國朝典故六十種本 8 组、古名家雜劇本 2 组等）。
- **收紧口径**：只并有正面证据的——题名一侧带「[康熙]」类地望／朝代前缀（总目方志类互著）、ai_note 有「追加」「互著」、E／F／G 不同道各建一次、或「GUJI-94 誤拆待併」「P11 掛靠」注记。满足的 28 组盲检 10/10 一致。其余 12 组改存疑。
- 不并登记：`不並登記.tsv`（DIFF 9 组记 C、存疑 15＋12 组记 D）。

合并用 `../../5c/merge_books.py`：keeper＝馆藏多、信息全者；sources／indexed_by／provenance／contained_in／resources 取并集；被并者留墓碑；promotions 28 个文件改指。

## 三、中華再造善本补 base_edition：106 条
5b-研判「ZHSY 影印本对原本不并、建议补 base_edition」的 115 组，从当前树重核：组内活 Book 恰一个 ZHSY（zhsy_id）＋恰一个非 ZHSY、同 Work、ZHSY 尚无带 book_id 的底本项者 106 组，
在 ZHSY Book 加 `base_edition: [{role:"底本", name:<原本版本名>, book_id:<原本>, note, source}]`（schema 只在后出者一侧写）。其余 9 组（ZHSY 两部或原本多部）跳过。脚本 `zhsy_tomb.py`，日志 `zhsy_tomb-log.tsv`。

## 四、Book 墓碑 work_id 是草稿 ID：4 条
全库扫 Book，work_id 不在 Work/ 的只有 4 个 10-19 的墓碑（佛說大乘智印經等），改指各自 keeper 的 work_id。

## 门禁
check_v2 0 错；check-classification 0；check_promo_dup 0；audit-merge-ledger T/L/P/R/D 全 0（WARN 题名 13，系互著题名带前缀）；check-duplicate-audit PASS；index/books 定点刷新 12 条（40 条为 main 既有缺条，跳过）。
