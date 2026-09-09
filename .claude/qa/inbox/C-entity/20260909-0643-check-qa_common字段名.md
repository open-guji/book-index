# check：qa_common.py 的 promoted_to/promoted_at 检查字段名对不上，PRO01/PRO04 从未生效

## 一句话

`qa_common.check_promote_ready_generic` 检查记录里的 `promoted_to`/`promoted_at`
（无下划线），但实际记录文件（Work/Book/Entity 三者皆然）的字段是
`_promoted_to`/`_promoted_at`（带下划线的派生字段）——`book-index-draft/SCHEMA.md`
「ID 类型编码」一节写得很明白：

> 一條記錄升格後，草稿檔保留並記 `_promoted_to` / `_promoted_at`（派生欄，故帶底線前綴）……
> `index/` 與 `promotions.json` 之欄不加底線（`promoted_to`）——整檔皆派生，欄再加底線是重複。

也就是说只有 `index/*.json` 与 `promotions.json` 里才不带下划线；record 文件（Work/Book/
Entity 的 JSON 本体）一律带下划线。`qa_common.py` 的 `check_promote_ready_generic` 读的
是 record 文件（`ctx.entity`），却按不带下划线的字段名查，所以：

- `PRO01`（production 文件不应有 tombstone 字段）——实测 production 文件本就不会有
  `promoted_to`（它们从不带下划线），检查形同虚设，但**也从来没抓到过"production 文件
  混入了带下划线 `_promoted_to`"这种真正该报的情形**（本道用 `PRO05` 单独补了这一版）。
- `PRO04`（draft 文件已 promote，不应重复 promote）——实测所有 draft 侧已 promote 的记录
  都是 `_promoted_to`，这条检查**从建库以来对三种 entity 类型全部没有生效过**。

## 扫法

```bash
cd book-index-draft
grep -rl '"promoted_to"' Entity Work Book --include=*.json | wc -l   # → 0
grep -rl '"_promoted_to"' Entity --include=*.json | wc -l            # → 24,602
grep -rl '"_promoted_to"' Work --include=*.json | wc -l              # → 89,972
```

## 例 id

`1j967c147z333`（羅汝敬，draft Entity，`_promoted_to: "hixhd2h9bfp5"`）——用
`qa_work.py`/`qa_book.py`/`qa_entity.py` 跑同类已 promote 的 draft id，PRO04 都不会报。

## 本道怎么绕的

`qa_entity.py` 没碰 `qa_common.py`（不在本道写域），自己另写了
`check_tombstone_entity`，用对字段名，还进一步拿 `promotions.json`（权威对照表）
交叉核验（记录自称已 promote 但账本没有 / 账本有但记录没回填 / 两处 id 不一致三种情形
分别报 PRO06/07/08）。`qa_work.py`/`qa_book.py` 没有类似的绕法，PRO01/04 这两条对它们
依然是死代码。

## 建议

改 `check_promote_ready_generic` 里的字段名为 `_promoted_to`/`_promoted_at`
（`qa_common.py` 不在任何一道的写域，改后需要把 `qa_work.py`/`qa_book.py`/`qa_entity.py`
三边各自跑一遍已知已 promote 的 id 回归一下，确认没有新噪音）。
