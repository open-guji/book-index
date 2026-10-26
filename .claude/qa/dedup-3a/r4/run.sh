#!/bin/bash
# 3a 第四轮全流程（从最新 main 重跑）：r4/run.sh <分支名>
set -e
BR=$1
Q=/home/claude/book-index/.claude/qa
cd /home/claude/book-index
git fetch -q origin main
T=$(mktemp -d); cp -a .claude/qa/dedup-3a/r4 $T/
git checkout -q -- . && git clean -qfd -- Work Book Entity index promotions classification .claude/qa/dedup-3a/r4-01
git checkout -q -B "$BR" origin/main
rm -rf .claude/qa/dedup-3a/r4 && cp -a $T/r4 .claude/qa/dedup-3a/
cd $Q/dedup-3a
python3 r4/prefix.py
python3 r4/mkbatch.py r4/dossier.jsonl $(git rev-parse origin/main) r4-01
python3 apply_3a.py r4-01/batch.json --apply > r4-01/apply.log 2>&1
python3 ../dedup-confirmed-163/postfix_common.py r4-01 --apply | tail -1
cd /home/claude/book-index
python3 .claude/qa/dedup-confirmed-163/update_index.py $Q/dedup-3a/r4-01 | cut -c1-60
cd ../book-index-draft
git fetch -q origin main && git checkout -q -- . && git checkout -q -B "$BR" origin/main
python3 ../book-index/.claude/qa/dedup-confirmed-163/fix_draft.py $Q/dedup-3a/r4-01/merges.json . --apply 2>&1 | tail -1
cd /home/claude/book-index
S=$(mktemp)
git -c core.quotePath=false diff --name-only origin/main > $S
python3 scripts/audit-merge-ledger.py --ledger $Q/dedup-3a/r4-01/merges.json --base origin/main --draft ../book-index-draft 2>&1 | grep ERROR | tr '\n' ' '; echo
python3 .claude/qa/check_v2.py --paths - < $S 2>&1 | tail -1
python3 scripts/check-classification.py 2>&1 | tail -1
python3 scripts/check_promo_dup.py 2>&1 | tail -1
python3 scripts/check-duplicate-audit.py --text-index ../open-guji/book-text/index/texts 2>&1 | tail -1
python3 build/build_derived.py --check-only --text-index ../open-guji/book-text/index/texts 2>&1 | grep -A2 '"dangling\|self_check_error\|"fatal' | tr -d '\n '; echo
