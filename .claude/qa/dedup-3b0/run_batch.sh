#!/bin/bash
# 3b-0 一批全流程（从最新 main 重跑）：run_batch.sh <批次名> <分支名> [mkbatch 参数...]
# 例：run_batch.sh batch-01 dedup-3b0-01 --limit 20
set -e
B=$1; BR=$2; shift 2
Q=/home/claude/book-index/.claude/qa
cd /home/claude/book-index
git fetch -q origin main
T=$(mktemp -d); cp -a .claude/qa/dedup-3b0 .claude/qa/dedup-judged/3b-0.tsv $T/
git checkout -q -- . && git clean -qfd -- Work Book Entity index promotions classification
git checkout -q -B "$BR" origin/main
rm -rf .claude/qa/dedup-3b0 && cp -a $T/dedup-3b0 .claude/qa/ && cp $T/3b-0.tsv .claude/qa/dedup-judged/
cd $Q/dedup-3b0
rm -f $B/merges.json $B/index-update.json $B/postfix_*原值.json
python3 mkbatch.py $B "$@" 2>&1 | tail -1
python3 apply_3b0.py $B/batch.json --apply > $B/apply.log 2>&1
python3 ../dedup-confirmed-163/postfix_common.py $B --apply | tail -1
python3 postfix_3b0.py $B --apply | tail -1
cd /home/claude/book-index
python3 .claude/qa/dedup-confirmed-163/update_index.py $Q/dedup-3b0/$B | cut -c1-60
cd ../book-index-draft
git fetch -q origin main && git checkout -q -- . && git checkout -q -B "$BR" origin/main
python3 ../book-index/.claude/qa/dedup-confirmed-163/fix_draft.py $Q/dedup-3b0/$B/merges.json . --apply 2>&1 | tail -1
cd /home/claude/book-index
S=$(mktemp)
git -c core.quotePath=false diff --name-only origin/main > $S
python3 scripts/audit-merge-ledger.py --ledger $Q/dedup-3b0/$B/merges.json --base origin/main --draft ../book-index-draft 2>&1 | grep ERROR | tr '\n' ' '; echo
python3 .claude/qa/check_v2.py --paths - < $S 2>&1 | tail -1
python3 scripts/check-classification.py 2>&1 | tail -1
python3 scripts/check_promo_dup.py 2>&1 | tail -1
python3 scripts/check-duplicate-audit.py --text-index ../open-guji/book-text/index/texts 2>&1 | tail -1
python3 build/build_derived.py --check-only --text-index ../open-guji/book-text/index/texts 2>&1 | grep -A2 '"dangling\|self_check_error\|"fatal' | tr -d '\n '; echo
