# 部分 5 普查脚本（2026-10-25，原样入库供重跑）
在 book-index 仓根依次运行（中间结果写 /tmp/claude-0/s/，可自行改路径）：
1. `extract_books.py`：全扫 live Book，输出 books2.jsonl（核心欄哈希、sources id、contained_in、馆藏等）。
2. `group_same_edition.py`：同 Work 同版本名分组并分档（ms 抄本稿本／dated 有年份／named／generic，及 /ci-diff），输出 g5b.json。
3. `tier_dated.py`：对 dated 档逐组剔除卷数／measure_info／版本类型／题名／责任者／物理描述不同及「分立依據」，余为候选。
之后还需剔除故宫／国图一部一条藏本记录（ai_note 为空或以「國圖數字古籍重配」开头）与地望前缀不同的族谱，再交子 agent 逐条核。
