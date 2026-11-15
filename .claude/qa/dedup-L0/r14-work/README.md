# L0 第十四轮：以前「存疑」未并的 Work 对逐对复核（2026-11-15）

基线 main `4025496a4da`。

## 范围
dedup-judged 里各轮机械判定或只抽检过、标 D／D存疑／C 存疑类而未并的 Work 对，凡两端都还活着的，共 4,397 对（敦煌遺書、殿本专名层不在内）。另纳入 L4 交来 3 对（古今譯經圖紀／續古今譯經圖紀两对、靜泰眾經目錄一对）。

## 做法（两把钥匙）
1. 第一道：按 `任务书-一道.md` 逐对判同／异／疑（每对一行，见 `复核明细.tsv` 一道三栏）。
2. 第二道：一道判「同」的 1,384 对，另起一批会话盲审（不告诉一道结论），**逐对打开库内两条 Work 原文**核 indexed_by／authors／ai_note、查混条，按 `任务书-二道.md` 判。
3. 只有两道都判「同」、且二道理由里没有「須／要先／先拆／混」等前提语的对，才进并条池；再按连通簇并，簇内若有一对不在池内（传递冲突）整簇不并。
4. keeper 取带 book-text 文本或被殿本专名层引用的一侧；一簇两侧以上都被引用的 24 簇整簇搁置（交文本侧）。

## 结果
| 一道 | 二道 | 结果 | 对数 |
|---|---|---|---|
| 同 | 同 | 并 | 928 |
| 同 | 同 | 不并（前提语／多侧被引用／传递冲突） | 47 |
| 同 | 疑 | 不并 | 405 |
| 同 | 異 | 不并 | 4 |
| 同 | — | 不并（混条须先拆，未送二道） | 18 |
| 疑 | — | 不并 | 2,494 |
| 异／異 | — | 不并 | 501 |

并 805 簇（含 L4 两对），并入 926 条 Work。L4 的靜泰眾經目錄一对判疑不并，登 `dedup-judged/L0-第十四轮.tsv`。

## 善后
- `mergework.py --by L0`（`batch_run.py` 缓存反引扫描）；台账 `merges.json`（簇号 L0R14W001–805）。
- `postfix_common.py`：126 个 keeper 删「本書惟某志一志著錄」句，原值 `postfix_common-原值.json`。
- 被并方 catalog_bound 的 period_upper 比 keeper 紧的，keeper 改取紧者（26 条；keeper 自身 period 不晚于新界才改）。
- 被并方撰人没进 keeper 的 24 处：keeper 无撰人的搬入 2 处（宋傳道、樟童帝君，带 entity）；「佚名」20 处、杜浚（＝杜濬）、胡思敬（叢書輯刊者）只在 keeper ai_note 记一句。
- promotions 566 处 production_id 改指 keeper（373 文件）；草稿库指针（merged_into／promoted_to／production_id／work_id）另开 book-index-draft PR。
- 已判登记：含被并 id 的旧判定行映射到 keeper，`dedup-judged/L0-第十四轮.tsv`。
- 顺手修 1 处：Book 99jd7e9eqg（#2659 新挂）work_id 指着第十三轮刚并掉的 d59fyitvefb4，改指 keeper d59fyg8eg7i9。

## 门禁
check_v2 0 ERROR／0 WARN；check_schema 0 ERROR；audit-merge-ledger T/L/P/R/D 皆 0；check_promo_dup 0；check-classification 0；check-duplicate-audit PASS；普查同题组未判 0、引用墓碑 0。

## 复核中记下、未在本轮处理
- 混条须先拆（18 对未送二道，另有若干二道判疑）：如 三輔黃圖 d59f2nkh7xfk、漢隸分韻 d59f2psiclc1、家世舊聞、粵滇紀略等。
- 撰人误挂：水經注箋 d59f24m8ifwl 系桑欽（应为朱謀㙔箋）、續考古圖 d59fymb4dd6o 系呂大臨（作者无考）。
- juan_count 误值：黃宗羲若干子目＝12、經問補＝18 等。
