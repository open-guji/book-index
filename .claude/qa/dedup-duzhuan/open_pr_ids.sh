#!/bin/bash
# 列出 book-index 所有开着的 PR 改动到的 Work/Collection 文件对应 id（每行一个），供 --skip-ids 用
R=${1:-open-guji/book-index}
for n in $(gh api "repos/$R/pulls?state=open&per_page=100" --paginate -q '.[].number'); do
  gh api "repos/$R/pulls/$n/files?per_page=100" --paginate -q '.[].filename' 2>/dev/null
done | grep -E '^Work/' | sed -E 's#.*/([0-9a-z]+)-[^/]*$#\1#' | sort -u
