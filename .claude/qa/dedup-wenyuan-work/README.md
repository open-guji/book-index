# 文淵閣／薈要（臺北故宮）同题 Book 挂多个 Work 清理

臺北故宮《欽定四庫全書·文淵閣本》（8rlb6yi1ecqo）与《摛藻堂四庫全書薈要》（8rlb6yk66qdc）的子目 Book 有两路来源：早先按维基／故宫善本旧籍建的 988 号 Book（带冊次、典藏号），和叢書线（GUJI-526）据《中國古籍總目》建的 993／994 号 Book。两路挂的 Work 不一致，同一子目在同一套书里分挂两三个 Work。子目-甲2 收工后从 main 普查：两套里同题 Book 挂 2 个以上 Work 的 422 组。

- 判定：6 个子 agent 按 `判定/判定说明.md` 逐组判（`判定/judged0–5.tsv`）：MERGE（同一部书）、REHANG（Book 挂到了同名异书）、KEEP（四库确收同名两书）、UNSURE。
- 复核：中置信的 MERGE／REHANG 与全部高置信 REHANG 共 134 组，另两个子 agent 不看初判独立重判（`verify0/1.tsv`）；高置信 MERGE 243 组随机抽 30 组盲检（`verify2.tsv`），29 组一致，1 组（薈要《石湖詩集》，一卷选本对三十四卷）不一致，已被下面的卷数规则拦下。
- 执行条件：初判高置信、或两次独立判定动作完全一致；MERGE 另排除两侧卷数相差一倍以上的 25 组和与 `dedup-judged/` 既有不并判定冲突的 8 组。

## b-01
- 并 Work 232 簇、被并 253 条（台账 `b-01/merges.json`），改挂 Book 50 个（`b-01/rehang.json`）；keeper 取既有 Work（挂 Book 多者、著录多者优先）。
- 留人工 70 组见 `b-01/留人工.tsv`：复核不一致 25、卷数悬殊 25、存疑 12、与旧判定冲突 8。
- 同一实物的 988 与 994 Book 在 Work 统一后仍是两条，留待 Book 层（5b-乙口径）并。

工具：`apply_wy.py <plan.json> --apply`（先改挂再调 dedup-confirmed-163/apply_batch.py 并 Work）。
