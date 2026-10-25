# 回补：早先 Book 合并漏并的 sources／indexed_by／provenance（2026-10-25）

merge_books.py 早期版本只把被并者的 contained_in／resources 并入 keeper，sources／indexed_by／provenance 没并（README 写了取并集，实际没做）。
已合的 5a 第 1 批、5b 第 1 批因此有 27 个 keeper 少了被并者的馆藏、出处与著录；5c 第 1 批的国图被并者没有这三栏，不受影响。
union_lost_fields.py 从各批 merges.json 记的 base 提交读被并者原文，把 keeper 缺的条目补上（回补清單.json）。脚本本身已改正。
