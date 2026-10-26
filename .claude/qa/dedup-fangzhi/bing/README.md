# 方志-并：合并同一修次重出的方志 Work

执行【研-方志】结论（口径见上级目录 README 与 ai-team `研-方志-判定口径.md`）。不碰 C 异修次、D 存疑；E 续修增修分立互链另批做；同地异修不互链（用户 10-26 定）。

## 流程

```
python3 scripts/dedup-census.py --out /tmp/census
BOOK_INDEX=. python3 .claude/qa/dedup-fangzhi/fangzhi_judge.py /tmp/census/同题组.tsv /tmp/fz
BOOK_INDEX=. python3 .claude/qa/dedup-fangzhi/bing/clusters.py /tmp/fz /tmp/bing      # clusters.json＋dossier.json（卷宗，不入库）
#   卷宗分片交子 agent 逐簇核，结论写 核对/verdict*.jsonl；人工调整写 核对/keeper调整与暂缓.json
python3 .claude/qa/dedup-fangzhi/bing/mkbatch.py .claude/qa/dedup-fangzhi/bing/核对 <批次目录> [--limit N] [--skip 已做批次目录,…]
python3 .claude/qa/dedup-fangzhi/bing/apply_fz.py <批次目录>/batch.json [--apply]
python3 .claude/qa/dedup-confirmed-163/postfix_common.py <批次目录> --apply
python3 .claude/qa/dedup-confirmed-163/update_index.py <批次目录>
python3 .claude/qa/dedup-confirmed-163/fix_draft.py <批次目录>/merges.json ../book-index-draft --apply
python3 .claude/qa/dedup-fangzhi/bing/mkreadme.py <批次目录> <标题>
```

## 核对结果（基线 main e3f2a4d7 重算，与 96e96c9148 同：A 256／B 188 对）

408 簇（836 条 Work）：SAME 370、PARTIAL 2、DIFF 20、UNSURE 16。keeper 调整 12 簇（其中 4 簇改并入簇外题名多「重修／新修」的总目条）；暂缓 11 簇：混记录待拆 3（FZ0200 永順府志、FZ0213 泰安州志、FZ0232 湖廣通志），成员为叢書部子目 8（交子目／4a-α 单元）。可并 361 簇、被并 380 条。

DIFF 多为总目自身分立的同号两修（化州、信豐、太平府、河南通志等）、增修本（桐城、南城、祁縣）与同名异地（新寧縣志 广东／湖南）；UNSURE 多为千頃堂分列两条或修纂人全不同而无旁证。均不并，留在存疑。
