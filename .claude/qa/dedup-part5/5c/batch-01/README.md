# 去重方案部分 5c 第 1 批：国图重配新建 Book 并入同版本总目 Book（2026-10-25）

基线（main 71ae495786）：国图 Book 3,394 个，全为 10-23～25 国图重配新建；fid 无重复；既有总目 Book 无国图资源。
国图↔国图（286 个 Work 下 829 个）版本项多为宽泛年代，不并只登记；见 ai-team 部分5-Book层.md「修订」节。

## 口径（B 档证据并）
同 Work＋国图版本项精确年份（非区间）＝总目 publication_info.year＋该 Work 同年总目 Book 唯一＋总目馆藏含「國家圖書館」＋国图版本项刻书者（如有）不矛盾 → 候選.tsv 77 对。
独立子 agent 逐条读两侧文件复核（逐條核.tsv）：SAME 73、DIFF 0、UNSURE 4（13 史記汪諒本/王延喆本难分、29 儒林外史为人工批注记录且版本类型不一、73 息園存稿诗文未分、76 增注啟蒙課本或为另书）→ UNSURE 不并，登记。

## 结果
57 组：keeper＝总目 Book（追加国图 resources＋resource_groups、merged_from，revision 主版本 +1），73 个国图 Book 留最小墓碑。
被并者独有的 edition／dating／ai_note（国图著录题名、责任者、版本项）原样记入 merges.json 的 loser_original_notes，且国图版本项也保留在 keeper 的 resources[].metadata.edition 与 resource_groups 标签里。
被并 Book 无任何入边（backrefs 全扫）；promotions 改动 0；草稿库无指向。

## 门禁
先 12 组（15 个被并）样本跑通 audit 全 0 ERROR，再全量。
- check_v2（130 檔）ERROR 0
- audit-merge-ledger：T/L/P/R/D ERROR 0；Q WARN：dating 73、edition 73（国图版本项写法与总目不同，预期）、title 12（异体／简称，逐条核过）
- check-classification 0 项；check_promo_dup 重复晋升 0；check-duplicate-audit PASS
- index/books 定点刷新 36 条（跳过 94 条为既有漂移）

复现：`python3 .claude/qa/dedup-part5/5c/merge_books.py .claude/qa/dedup-part5/5c/batch-01/batch.json [--apply]`
