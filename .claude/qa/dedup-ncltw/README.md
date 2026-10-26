# 台湾国图挂接线索：同题多 Work 核并

来源：C3续 台湾国图存疑档升档时「一条馆藏对上两个以上同题 Work」的交去重清单（bim `docs/馆藏资源挂接/报告/C3续-臺灣國圖存疑與越南漢喃挂接-20261026/交去重_疑重复Work.tsv` 490 行、`交去重_同著者多Work.tsv` 39 行）。基线 main `e714b68e14`。

## 漏斗

| 步骤 | 对 |
|---|---:|
| 529 行展开为 Work 对（候选先跟 merged_into） | 1,207 |
| 已判（dedup-judged 任一表） | −151 |
| 已互挂 related_works | −145 |
| 一侧或两侧是叢書子目（留部分 4，不碰） | −507 |
| 进初判 | 404 |
| 初判（5 份并行，口径 00-通用口径第一节＋部分 4 证据阶梯） 并／C／D | 24／322／58 |
| 并档独立复核（另加初判员段外发现 2 对） 维持／否 | 23／3 |
| 本串从严再否（《麟臺故事》說郛一卷節錄本对五卷本，K14） | −1 |
| **b-01 并** | **22 组** |

- 不并 384 对（C 324、D 60）全部登记 `../dedup-judged/台湾国图线索.tsv`。D 档里有几个「混记录」Work（一个 Work 混了两部以上的书），留给拆分线：d59f2pzp4bup（直齋两节解题）、d59f24mhkbnp（鄭玄注与王應麟辑本）、d59fyh6joqo0（金刚经四译本）、d59f2hq4in0g（韋述／柳芳《唐書》混新唐书）等，详见各段结果理由。
- 复核否的 3 对：《陶靖節集》湯漢箋注合刻本对陶集原本（C）、《山谷內集詩注》任渊注对黄庭坚（甲疑混《山谷集》，D）、《重刻橫浦先生文集》增辑本（D）。
- 善后：T09《後漢書》keeper 撰人「華嶤」是「華嶠」之讹（本条隋志、旧唐志原文作華嶠），`fix_author.py` 改挂華嶠 entity，index 同步。

## 文件

- `判定/`：`pairs.py`（展开、剔除）、`dossier.py`＋`mk.py`（逐对著录摘要分段）、`提示.md`／`复核提示.md`、`段1–5.md` 及 `_结果.tsv`、`复核.md`／`复核_结果.tsv`、`mkbatch.py`。
- `b-01/`：`batch.json`、`merges.json`（台账）、`apply.log`、`index-update.json`、`postfix_common-原值.json`。
- 跑法：`run_batch.sh b-01 <分支>`（从最新 main 重放：apply → postfix_common → fix_author → update_index → fix_draft（草稿库另 PR）→ 全部门禁）。

## 门禁

audit-merge-ledger T/L/P/R/D 全 0；check_v2（142 档）0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；build_derived --check-only self_check 0、dangling 0。初判并档 100% 独立复核（不止 30% 抽检）。
