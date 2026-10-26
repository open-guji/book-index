#!/usr/bin/env bash
# schema-landed-check：Schema落地验收一键跑（overview#606 B6，总计划 §八 V1–V7）。
# 用法（在 book-index 仓根）：
#   scripts/schema-landed-check.sh [all|schema|build|scan|readers|golden|text|online]
# 只读、不改任何文件；末尾输出结果表，任一项红则退出码 1。每项的原始输出落到 $OUT/<项>.log，验收时逐条贴 #606。
# 路径可用环境变量改：DRAFT BIM WEB TEXT（默认与本仓同级）。online 要联网，all 默认不跑，加 ONLINE=1 才跑。
set -u
cd "$(dirname "$0")/.." || exit 2
DRAFT=${DRAFT:-../book-index-draft}; BIM=${BIM:-../book-index-manager}
WEB=${WEB:-../kaiyuanguji-web};      TEXT=${TEXT:-../book-text}
OUT=${OUT:-$(mktemp -d)}
# OUT 不存在则建；建不出或写不进就直接退出 2，不能让日志写失败后原始命中为空而假绿（GUJI-13）
mkdir -p "$OUT" 2>/dev/null && : >"$OUT/.w" 2>/dev/null && rm -f "$OUT/.w" || { echo "OUT 目录不可写：$OUT" >&2; exit 2; }
WHAT=${1:-all}
RESULTS=()
FAIL=0

# run <名> <说明> <命令...>：命令退出码 0 为绿；原始输出落 $OUT/<名>.log
run() {
  local name=$1 desc=$2; shift 2
  if "$@" >"$OUT/$name.log" 2>&1; then RESULTS+=("绿|$name|$desc"); else RESULTS+=("红|$name|$desc"); FAIL=1; fi
}
# 目录不存在则跳过并记"未验"，不静默绿
need() { [ -d "$1" ] || { RESULTS+=("未验|$2|目录不存在：$1"); return 1; }; }

check_schema() {
  run V1-prod  "正式库 check_schema ERROR 0 WARN 0" python3 schema/check_schema.py --quiet-warn
  need "$DRAFT" V1-draft && run V1-draft "草稿库 check_schema ERROR 0 WARN 0" python3 schema/check_schema.py --root "$DRAFT" --draft --quiet-warn
}
check_build() {
  need "$TEXT" V2 || return
  local ti="$TEXT/index/texts"
  run V2-check_v2 "check_v2 ERROR 0" python3 .claude/qa/check_v2.py --summary
  run V2-build-prod "正式库 build --check-only（drift 空、self_check 0）" python3 build/build_derived.py --text-index "$ti" --check-only
  need "$DRAFT" V2-build-draft && run V2-build-draft "草稿库 build --check-only" python3 build/build_derived.py --root "$DRAFT" --ref-root . --text-index "$ti" --check-only
  run V2-verify "verify.py --strict 末行 OK" bash -c 'python3 .claude/qa/verify.py --strict | tail -1 | grep -q OK'
}
check_scan() {
  need "$DRAFT" V3 && run V3-legacy-scan "数据旧键两库全 0" python3 scripts/legacy-scan.py . "$DRAFT"
}
# V4 读侧旧读法：窄口径 grep（只抓“回退/旧键读取”形态，不抓 index 合法键 birth_year 的普通读写），命中须逐行落在 scripts/legacy-allow.txt
check_readers() {
  local allow=scripts/legacy-allow.txt log="$OUT/V4-readers.log" bad=0
  : >"$log"
  local pats=(
    'get\(["'"'"'](birth|death)_year["'"'"']\)'                                   # Python 读旧顶层生卒年
    '(birth|death)_year *(\?\?|\|\|) *[A-Za-z_.?]*(dates\??\.|\bd\??\.)(birth|death)'   # JS 旧键 ?? dates.*
    '(birth|death)\)? *(\?\?|\|\|) *\w*\(?[A-Za-z_.]*\b(birth|death)_year'              # dates.* ?? 旧键
    '_has_full_text'                                                                      # 已退役的 _has_full_text
    '(^|[^_A-Za-z0-9])has_(text|collated)\b.*\b_has_(text|collated)\b|\b_has_(text|collated)\b.*(^|[^_A-Za-z0-9])has_(text|collated)\b'  # has_*／_has_* 双读（现行派生键只有 _has_*，读它本身不算旧读法）
    '\b(doc|derived)\??\.has_(text|collated|full_text)\b'                               # 读派生文档上无下划线的旧键
    'adaptEntry|derived-compat|migrate_v2'
    '⟨|⟩'
  )
  for root in "$BIM" "$WEB"; do
    [ -d "$root" ] || { RESULTS+=("未验|V4|目录不存在：$root"); continue; }
    for p in "${pats[@]}"; do
      git -C "$root" grep -InE "$p" -- . ':!*.md' ':!*.json' ':!*.tsv' ':!*.csv' ':!*lock*' ':!tests/**' ':!**/tests/**' ':!**/__tests__/**' ':!**/fixtures/**' ':!**/e2e/**' ':!*.test.*' ':!*.spec.*' 2>/dev/null \
        | grep -vE '^[^:]+:[0-9]+:[[:space:]]*(#|//|\*|/\*|"""|<!--)' | sed "s|^|$(basename "$root")/|"
    done
  done | sort -u >"$log.raw"
  # 允许清单格式：<仓/路径>:<正则>  # 理由（每行一条，≤5 行）；命中行匹配任一条即视为允许
  while IFS= read -r line; do
    ok=0
    while IFS= read -r a; do
      a=${a%%#*}; a=$(echo "$a" | sed 's/[[:space:]]*$//'); [ -z "$a" ] && continue
      f=${a%%:*}; re=${a#*:}
      [[ "$line" == "$f":* ]] && echo "$line" | grep -qE "$re" && { ok=1; break; }
    done <"$allow"
    [ $ok = 0 ] && { echo "$line" >>"$log"; bad=$((bad+1)); }
  done <"$log.raw"
  echo "未被允许清单覆盖的命中：$bad（原始命中 $(wc -l <"$log.raw")，允许清单 $(grep -cvE '^\s*(#|$)' "$allow") 行）" >>"$log"
  if [ $bad = 0 ]; then RESULTS+=("绿|V4|读侧旧读法命中全在允许清单"); else RESULTS+=("红|V4|读侧旧读法 $bad 处不在允许清单（见 V4-readers.log）"); FAIL=1; fi
}
check_golden() {
  run V5-book-index "book-index 黄金样例对拍" python3 -m pytest tests/test_golden_parity.py -q
  need "$BIM" V5-bim && run V5-bim "bim 黄金样例对拍（Python）" bash -c "cd '$BIM' && python3 -m pytest tests/test_golden_parity.py -q"
  [ -d "$BIM/ui/node_modules" ] && run V5-bim-ui "bim ui 黄金样例对拍（vitest）" bash -c "cd '$BIM/ui' && npx vitest run tests/unit/golden-parity.test.ts"
}
check_text() {
  need "$TEXT" V6 || return
  run V6-format "validate_text_format --strict --baseline" bash -c "cd '$TEXT' && python3 scripts/validate_text_format.py . --strict --baseline scripts/format_baseline.json"
  run V6-collated "validate-collated 退出码 0" bash -c "cd '$TEXT' && python3 scripts/validate-collated.py --root ."
  run V6-brackets "book-text 里 ⟨⟩ 为 0" bash -c "[ \"\$(git -C '$TEXT' grep -n '⟨\|⟩' -- Work Book | wc -l)\" = 0 ]"
}
check_online() {
  run V7-version "线上 /api/version：webMatchesPointer true" bash -c "curl -fsS https://www.openguji.com/api/version | tee /dev/stderr | grep -q '\"webMatchesPointer\": *true'"
}

case "$WHAT" in
  schema) check_schema;; build) check_build;; scan) check_scan;; readers) check_readers;;
  golden) check_golden;; text) check_text;; online) check_online;;
  all) check_schema; check_build; check_scan; check_readers; check_golden; check_text; [ "${ONLINE:-0}" = 1 ] && check_online;;
  *) echo "用法：$0 [all|schema|build|scan|readers|golden|text|online]" >&2; exit 2;;
esac

echo; printf '%-4s %-18s %s\n' 结果 项 说明
for r in "${RESULTS[@]}"; do IFS='|' read -r s n d <<<"$r"; printf '%-4s %-18s %s\n' "$s" "$n" "$d"; done
echo "原始输出：$OUT/*.log"
exit $FAIL
