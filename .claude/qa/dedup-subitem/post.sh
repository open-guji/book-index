#!/bin/bash
# 子目-甲批次善后与门禁：post.sh <批次目录> <对照基线(默认 origin/main)>
set -e
B=$1; BASE=${2:-origin/main}; TI=../book-text/index/texts
python3 .claude/qa/dedup-confirmed-163/postfix_common.py $B --apply | tail -1
python3 .claude/qa/dedup-confirmed-163/update_index.py $B | cut -c1-60
python3 .claude/qa/dedup-subitem/refresh_index_forced.py $B
python3 .claude/qa/dedup-confirmed-163/fix_draft.py $B/merges.json ../book-index-draft
(git -c core.quotePath=false diff --name-only $BASE; git -c core.quotePath=false ls-files --others --exclude-standard) | sort -u | python3 .claude/qa/check_v2.py --paths - 2>&1 | tail -1
python3 scripts/check-classification.py 2>&1 | tail -1
python3 scripts/audit-merge-ledger.py --ledger $B/merges.json --base $BASE --draft ../book-index-draft 2>&1 | grep -E "ERROR|台账|WARN"
python3 scripts/check_promo_dup.py 2>&1 | tail -1
python3 scripts/check-duplicate-audit.py --text-index $TI 2>&1 | tail -1
python3 build/build_derived.py --check-only --text-index $TI > $B/../.bd.log 2>&1 && echo "build_derived OK" || echo "build_derived FAIL"
grep -A1 '"fatal"' $B/../.bd.log; rm -f $B/../.bd.log
