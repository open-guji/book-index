# 黄金样例（官方副本）

`entries.json`：`[{name, type, record, expect_index_entry, negative}]`，index 条目提取的共享对拍向量（overview#606 B6）。
**官方副本在本仓**；下游各拷一份并在头注释写来源 sha，不做跨仓运行时依赖：

| 处 | 读它的测试 |
|---|---|
| book-index `build/build_derived.py` | `tests/test_golden_parity.py` |
| book-index-manager `entry_extractor.py` / `ui/src/core/storage.ts` | `tests/test_golden_parity.py`、`ui/tests/unit/golden-parity.test.ts` |
| kaiyuanguji-web `derived.mjs` | 待 B5 接入 |

加例规矩：先改本仓，再让下游同步；`negative: true` 是旧写法记录，`expect_index_entry` 里不得出现由旧字段推出的值。
首版内容取自 bim#202 的 15 例（Ella 先行落地）；来源 bim `main`。

**覆盖范围与已知盲区（2026-11-03，S5-G）**：向量是「单条记录 → index 条目」的纯函数对拍，**不带 `--text-index`**，所以 Work 的 `has_text`／`has_collated`（build 并入 Book 与 book-text，bim／TS 只看本条 `resources`）、以及 `promoted_to` 取升格对照的路径都不在对拍里；三端分歧清单见 `schema/derived.md〈八〉三端分歧`。bim 与本仓 build 在全库 80.6 万条上 11-03 逐条对拍 0 差异（不给 text-index 时）。
