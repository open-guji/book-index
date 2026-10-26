# 研-方志：方志同题组判定（只读研究）

口径全文：ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/研-方志-判定口径.md`。

要点：一个修次＝一个 Work，不同修次不并；真重复主要是故宫《善本舊籍》、史志书目录入的无年号 Work 与总目 [年号] Work 重出。

## 用法

```
python3 scripts/dedup-census.py --out /tmp/census
BOOK_INDEX=. python3 .claude/qa/dedup-fangzhi/fangzhi_judge.py /tmp/census/同题组.tsv /tmp/fangzhi
```

输出：`判定-全部对.tsv`、`候选A-同修次同人.tsv`、`候选B-同年同卷待核.tsv`、`续修增修E.tsv`、`存疑D.tsv`、`非方志X-组.tsv`、`纯C组-分立对.tsv`（可直接追加进 `../dedup-judged/研-方志.tsv`）、`统计.json`。

## 20261025/（基线 main 96e96c9148）

2,079 组、7,404 条 Work、13,061 对：A 256、B 188、C 10,886、E 57、D 1,211、X 463（148 组）。
纯 C 组 1,040 组（4,545 对）已写入 `../dedup-judged/研-方志.tsv`；含 A／B／D／E 的组未登记（whitelist 按连通判已判，会盖掉组内真重复），并完 A／B 后重跑再补。

## 20261026/（基线 main 5011c2be23，已带各单元 dedup-judged 白名单）

新增三条判据：同一史志书目里分条著录、不同修纂人 → C「同目分条」；修纂人朝代（authors[].dynasty）晚于书目断代 → C「书目断代」；故宫刊年比总目修次年晚 5 年以上且修纂人对不上 → C「后刊异人」。修纂人比较前先过 scan.py 的 VARIANTS 异体表。
1,057 组 8,881 对：A 285、B 176、C 7,153、E 59、D 740（原 1,220）、X 468。新纯 C 组 118 组（703 对）追加进 `../dedup-judged/研-方志.tsv`，方志未判 1,057 → 939。
用户 10-26 定：同地异修不互链，只登记分立。
