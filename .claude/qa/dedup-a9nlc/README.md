# A9／KORCIS／国图线索：同题多 Work 核并

来源：bim 报告交去重清单——A9 日本诸馆存疑升档（85 行）、C3韩越续 KORCIS（疑重复 153＋同著者多 32）、A7 国图 dup-leads-nlc（25 行）。国書／内閣／NDL、台湾国图（已有 dedup-ncltw）不在本单元。

漏斗：展开 605 对 → 已判 −374、已互链 −43、叢書子目 −100（留子目线）→ 进初判 88（A9 8、KORCIS 80、国图 0）。
初判：并 5、存疑 1（六臣註文選／六家文選，版本系统未证）、不并 82（C／D）。并档 5 组由另一子 agent 独立复核，维持 4 组并，1 组改存疑。
**并 4 组**：崔公入藥鏡註解／注解、野人閑話／閒話、鬱離子／郁離子、春秋公羊傳／嚴彭祖章句。
KORCIS 的 80 对几乎全是「同题异注本／异撰人」（左传、汉书、楚辞、淮南子、法言等），分立。D 档 6 条（金剛般若波羅密經混译本、无著者《楚辭》／《春秋公羊傳》、六臣註文選）见 `../dedup-judged/A9与国图线索.tsv`，其中金刚经两条属「混记录」Work，留拆分线。
工具：`apply_a9nlc.py`（复用 apply_batch）、`run_batch.sh b-01 <分支>`。
门禁：audit-merge-ledger T/L/P/R/D 0；check_v2 0；check-duplicate-audit PASS；build_derived self_check 0、dangling 0（「讀檔問題 3 項」在 main 上同样出现，非本批引入）。
