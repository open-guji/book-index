#!/bin/bash
# 用法：run_batch.sh <批次目录名> <部类> <组数>   （在 book-index 根下、已切到基于最新 main 的分支）
# 从当前 main 重算候选 → 生成批次 → 应用 → 善后 → 门禁。门禁结果写 <批次>/门禁.txt
set -e
D=.claude/qa/dedup-part4; N=$1; BL=$2; K=$3
export P4WORK=${P4WORK:-/tmp/p4}; mkdir -p $P4WORK
TI=${TEXT_INDEX:-../open-guji/book-text/index/texts}
python3 $D/load.py >/dev/null
WL=(); for f in .claude/qa/dedup-judged/*.tsv; do WL+=(--whitelist "$f"); done
python3 scripts/dedup-census.py "${WL[@]}" --out $P4WORK/census >$P4WORK/census.txt 2>&1
python3 $D/cand_alpha.py | tail -1
python3 $D/mkbatch.py $P4WORK/alpha.json $D/$N --bulei $BL --n $K --base $(git rev-parse --short=10 origin/main)
python3 $D/apply_4.py $D/$N/batch.json --apply > $P4WORK/apply-$N.txt 2>&1
python3 .claude/qa/dedup-confirmed-163/postfix_common.py $D/$N --apply | tail -1
python3 .claude/qa/dedup-confirmed-163/update_index.py $D/$N
python3 $D/mkreadme.py $D/$N "4a-α $BL $N（$K 组）"
{
git -c core.quotePath=false diff --name-only | python3 .claude/qa/check_v2.py --paths - | tail -1
python3 scripts/check-classification.py | tail -1
python3 scripts/check_promo_dup.py | tail -1
python3 scripts/audit-merge-ledger.py --ledger $D/$N/merges.json --base origin/main --draft ../book-index-draft 2>&1 | grep "ERROR\|台账"
python3 scripts/check-duplicate-audit.py --text-index $TI | tail -1
python3 build/build_derived.py --check-only --text-index $TI 2>&1 | grep self_check_error
python3 .claude/qa/dedup-confirmed-163/fix_draft.py $D/$N/merges.json ../book-index-draft | tail -1
} > $D/$N/门禁.txt 2>&1
cat $D/$N/门禁.txt
