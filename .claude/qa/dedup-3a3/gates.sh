#!/bin/bash
# 3a-3 门禁（在已合 main 的分支上）。用法：gates.sh <批次目录>
D=$1; Q=.claude/qa
(cd ../book-index-draft && git fetch -q origin main && git checkout -q -f -B claude/dedup-3a3-$(basename $D) origin/main)
python3 $Q/dedup-confirmed-163/fix_draft.py $D/merges.json ../book-index-draft --apply | tail -1
python3 scripts/audit-merge-ledger.py --ledger $D/merges.json --base origin/main --draft ../book-index-draft 2>&1 | grep -E "ERROR|台账" | tr '\n' ' '; echo
git -c core.quotePath=false diff --name-only origin/main | grep '\.json$' | python3 $Q/check_v2.py --paths - 2>&1 | tail -1
python3 scripts/check-classification.py 2>&1 | tail -1
python3 scripts/check_promo_dup.py 2>&1 | tail -1
python3 scripts/check-duplicate-audit.py --text-index ../open-guji/book-text/index/texts 2>&1 | tail -1
python3 build/build_derived.py --check-only --text-index ../open-guji/book-text/index 2>&1 | grep -E '"self_check_error_count"'
