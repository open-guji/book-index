#!/bin/bash
# 3a-3 一批流水：apply → postfix → index → 草稿库同步 → 门禁。用法：run_batch.sh <批次目录> <README 标题>（在 book-index 根目录、分支已从 origin/main 起）
set -e
D=$1; T=$2; Q=.claude/qa
python3 $Q/dedup-3a3/apply_3a3.py $D/batch.json --apply > $D/../apply.log 2>&1 || { tail $D/../apply.log; exit 1; }
python3 $Q/dedup-confirmed-163/postfix_common.py $D --apply | tail -1
python3 $Q/dedup-confirmed-163/update_index.py $D | tail -1 | cut -c1-60
(cd ../book-index-draft && git fetch -q origin main && git checkout -q -B claude/dedup-3a3-$(basename $D) origin/main)
python3 $Q/dedup-confirmed-163/fix_draft.py $D/merges.json ../book-index-draft --apply | tail -1
python3 $Q/dedup-3a3/mkreadme.py $D "$T"
python3 scripts/audit-merge-ledger.py --ledger $D/merges.json --base origin/main --draft ../book-index-draft 2>&1 | grep -E "ERROR|台账"
git -c core.quotePath=false diff --name-only | grep '\.json$' | python3 $Q/check_v2.py --paths - 2>&1 | tail -1
python3 scripts/check-classification.py 2>&1 | tail -1
python3 scripts/check_promo_dup.py 2>&1 | tail -1
python3 scripts/check-duplicate-audit.py --text-index ../open-guji/book-text/index/texts 2>&1 | tail -1
python3 build/build_derived.py --check-only --text-index ../open-guji/book-text/index 2>&1 | grep -E '"self_check_error_count"'
