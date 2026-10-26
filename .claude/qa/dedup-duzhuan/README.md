# 獨撰子目补撰人

总目「叢書部/獨撰類」子目不另题撰人，叢書线（GUJI-526）建子目 Work 时 `authors` 留空，普查因此把同一作者的书分进「一侧有一侧无」「全无」。本单元按所属 Collection 的撰者给这些子目补 `authors`，**只改撰人，不并 Work**。判据来源：ai-team 去重方案目录「子目-乙-跨丛书同题子目判据.md」第一、五节。

## 用法

```bash
.claude/qa/dedup-duzhuan/open_pr_ids.sh > /tmp/openpr.txt              # 开着的 PR 改到的 Work id，一律跳过
python3 .claude/qa/dedup-duzhuan/plan.py /tmp/dz                        # 只读：plan.json / held.tsv / stats.json（约 1 分钟）
python3 .claude/qa/dedup-duzhuan/apply.py /tmp/dz/plan.json .claude/qa/dedup-duzhuan/batch-NN --skip-ids /tmp/openpr.txt --start S --count N [--apply]
```
依赖 `pip install opencc`。每批从最新 main 重跑 plan.py。

## 口径

补：子目 Work 未并、authors 空、indexed_by 有「獨撰類」；所属 Collection（ai_note「所屬叢書記錄」源记录号）首位撰者角色为撰／著／述／作，且撰類撰者只一人。写 `{name, role: 撰, dynasty, role_basis, [entity_id]}`，名照丛书著录不改写；revision 升 minor，ai_note 加一行【獨撰子目补撰人】。

不补（held.tsv 记理由）：
- 4a-α 候选清单（`dedup-part4/候选/4a-alpha-*.json` 的 keeper 与 losers）：即将并入同作者单行本，让给部分 4／4a-α乙。
- 丛书首位撰者角色非撰（輯、編、評、錄、撰輯等，钞录／辑本类）；丛书多撰者；丛书无撰人；撰者名异常。
- 丛书题名似钞辑（鈔、抄、祕笈、選本、彙編／彙刻、輯佚）。
- 子目自带 author_info（另有撰人）；题名为卷次泛称或版本语（首、附錄、「清嘉慶四年刻」）；题名似传记附录（年譜、行狀、墓誌、祭文、題詞……）；题名似钞辑摘录（摘、雜鈔、叢鈔、輯要、先生言行／雜錄）。
- 撰者朝代与子目时段（section 末段）不合，如「民國以來」子目配「宋」撰者（丛书 contMap 朝代错）。
- 库中同题他书都题别人：他人朝代更早者疑辑本／注本／钞本（例 通齋手稿《淮南鴻烈解》）；同代或更晚者多为泛题异书，暂不补，待逐条核。同题比较用 opencc 繁简＋异体宽归一（陸遊＝陸游、歐陽脩＝歐陽修）。

entity_id 只在有确证时挂：①同题且宽归一同名的他书已挂唯一一个人物，朝代相容；②全库 Work 作者位里该名只对应一个活人物、朝代相容、人物名／别名索引也只此一人。其余留给 2.2续／2.3 从 main 重跑覆盖。

## 抽检

`抽检-80条.tsv`／`抽检-80条-判定.tsv`（独立子 agent 盲审，首版口径）：撰人 SAME 76／DIFF 0／UNSURE 4；entity SAME 54／DIFF 1（陳淵：丛书 contMap 误作宋，实为民国人）。据此加了「朝代与子目时段不合」「题名为版本语」「题名似钞辑摘录」三条剔除，4 条 UNSURE 与 1 条 DIFF 均落入新剔除。

## 台账与回滚

`batch-NN/applied.json`：每条 id、路径、前置 sha256、revision_before、所写 author、丛书。回滚＝authors 置空、revision 退回、删去 ai_note【獨撰子目补撰人】一行。

## 第二轮：逐条复核（2026-10-26，batch-05）

规则拦下的 728 条（同题他书题别人 461、丛书首位非撰 191、多撰者 26、朝代与时段不合 50）分 6 组由子 agent 逐条判定，表见 `复核-728条-判定.tsv`：补 547、不补 103、存疑 78（审核员自评证据弱的 18 条降为存疑）。`plan.py --reviewed 复核表` 对判「补」者绕过剔除规则、照表写名／责任方式／朝代；名与丛书著录不同时记 `original_name`、`name_basis`。另把首轮已补的李實洤 5 条改正为李寶洤并挂人物。
独立抽检 60 条（`抽检3-60条*.tsv`）：撰人 60/60 SAME、朝代错 0、entity 错 0；左陶右邵 责任方式据总目改作輯。
不补的 103 条以喬勤恪公全集纬书佚文、袁爽秋祕笈、陳眉公批點閒情小品等他人原作为主；存疑 78 条留待有新证据再补。
