# L0 收口：Work 未判同题组＋族谱同版 Book（2026-11-12）

车道文档：ai-team `domain/目录与资源/设计/2026-11-目录领域总计划-车道/L0-收口与基线.md`。

## 做法
- 基线 main `13fea63e365` 带白名单普查（`--whitelist .claude/qa/dedup-judged/*.tsv`）：Work 未判同题组 163。
- 按已连通塊生成卷宗（大塊只列 3 个代表），4 个子 agent 逐对判 A 机械并／B 证据并／C 分立／D 存疑；盲检 60 对 A/B 全 SAME。
- **只按判定行里的两条 id 并，不整塊并**（塊内也有 C/D 边）；A/B 边做并查集得 129 组，keeper 优先取被 book-text 引用的一侧，其次取判定员多数所选。
- 被并方被 book-text 四库总目殿本（96mid1ogzk）专名层引用的 5 组＋讀書志 d59f2hl2uiv6，并条须同步改 book-text，本批不并，登 `dedup-judged/L0-收口.tsv`「D待并」。
- `mergework.py` 逐组 `--apply`（124 组 186 条，`--by L0`），`postfix_common.py` 删 3 条 keeper 的「惟某志著錄，別無他證」句；promotions 里指被并 Work 的 262 处改指 keeper。
- 郡齋讀書志：d59fyfkfo8hs（昭德先生郡齋讀書志）并入 d59f2hpm3myp，keeper 改题「郡齋讀書志」，原题入 additional_titles（L0-W125）。
- 族谱同版 Book 15 对：`dedup-part5/5c/merge_books.py`（`book/`），keeper 取题名地名较细的一侧；脚本写的 keeper `merged_from` 已删（11-03 起 keeper 不记）。
- C/D 245 对登 `dedup-judged/L0-收口.tsv`。

## 未搬、只报（mergework「须人看」）
- 撰人 entity_id 未补：多为被并方是丛书子目、撰人位记的是丛书编者（馬國翰輯、胡思敬輯、沈節甫編、高鳴鳳／鄧士龍編、茅一相），不该搬；欒肇（d59g2r44aqyq 作者错）不搬；王肇釗／王肇劍、胡繼／胡經、趙浮丘公／李浮丘待核。
- 13 组字段冲突（period_basis、dynasty 等两边不同）保留 keeper 值，见 `merges.json` 对应 cluster 的 mergework 日志（scratch，未入仓）。

## 门禁
check_v2 ERROR 0；audit-merge-ledger（Work＋Book 合并台账，除 W125 因改名改路径另核）T/R/D 0，L 1（被并方「佚名」撰人位，keeper 有实名），P 仅 W125 一处；check_promo_dup 0；check-classification 0；check-duplicate-audit PASS。
草稿库另改 2 处引用（book-index-draft 同名分支）。

## 余量
本分支普查 Work 未判同题组 237：原 163 组遗留 33（大塊里卷宗只列代表、未覆盖的成员，及暂缓的 6 组），其余 204 组是 11-12 当天 L1 续修四库新建 Work、L2/L3 等车道新带来的，留 L0 下一轮。
