#!/bin/bash
# 用法：run_batch.sh <批次目录> <gids逗号串>   在最新 origin/main 起的分支、book-index 根下运行
# 需要环境变量 NR=判定工作目录（含 pairs.tsv、groups.jsonl、judge/*.tsv）
set -e
B=$1; G=$2; R=$(git rev-parse --show-toplevel); cd "$R"; D=.claude/qa/dedup-nores
python3 $D/mkbatch_nr.py $B $NR/pairs.tsv $NR/groups.jsonl $NR/judge/*.tsv --gids $G --base $(git rev-parse --short=10 origin/main)
python3 .claude/qa/dedup-part4/apply_4.py $B/batch.json --apply > $B/.apply.log 2>&1 || { tail $B/.apply.log; exit 1; }
python3 .claude/qa/dedup-confirmed-163/postfix_common.py $B --apply | tail -1
python3 $D/fix_intra.py $B
python3 .claude/qa/dedup-confirmed-163/update_index.py $B | tail -1
python3 .claude/qa/dedup-confirmed-163/fix_draft.py $B/merges.json ../book-index-draft --apply | tail -1
rm -f $B/.apply.log
