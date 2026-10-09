# 升格对照表（`promotions/`）

草稿记录升格（promote）到正式库时，换一个正式 id。**草稿 id → 正式 id 的唯一权威是正式库的 `promotions/` 分片**。草稿记录里不写 `promoted_to`／`_promoted_to`；构建产物和索引里的 `promoted_to` 由 build 按本表回填（见 [derived.md](derived.md)）。

---

## 一、分片

| 项 | 规定 |
|---|---|
| 位置 | 正式库 `promotions/<分片键>.json` |
| 分片键 | **草稿 id 的末 2 个字符**（与网站的 PH 分片同键）；草稿 id 是 base36，故最多 36×36＝1,296 片 |
| 每片形状 | 与旧整档相同：`{"version": 1, "promotions": {<草稿 id>: <项>}}` |
| 键序 | `promotions` 内按草稿 id 字典序 |
| 旧整档 | 根目录 `promotions.json` 已于 2026-10-08 切成分片后删除，不双写（book-index#43） |

实测（10-08）：1,296 片，共 59,693 项（Book 33,583、Work 24,508、Entity 1,602）。

## 二、项

| 字段 | 类型 | 必填 | 含义 | 取值 | 例 |
|---|---|---|---|---|---|
| `production_id` | string | 必填 | 正式 id | 正式库记录 id | `"98xt9ds3d3"` |
| `type` | string | 必填 | 记录类型 | `work`｜`book`｜`collection`｜`entity` | `"book"` |
| `promoted_at` | string | 必填 | 升格时间 | ISO 8601 UTC（`YYYY-MM-DDTHH:MM:SSZ`） | `"2026-10-08T20:54:05Z"` |

```json
{"version": 1, "promotions": {
  "11sjkima7v505": {"production_id": "98xt9ds3d3", "type": "book", "promoted_at": "2026-10-08T20:54:05Z"}
}}
```

## 三、读写

- **写**：只经 bim `PromotionsStore`（只重写动过的片，读盘合流后原子替换）；`bim promote` 自动调用。不手拼路径、不手改。
- **读**：bim `promotion.load_all(root)`；build `build/v2common.py` 的 `read_promotions_raw`（纯标准库）。二者都同时认分片与旧整档，并存时分片优先。读项时，正式 id 依次取 `production_id`、`to`、`official_id`、`id`（后三者是旧写法，现存 0）。
- **网站**：打包时直接读源分片，生成带哈希的分片供客户端按需取。

## 四、相关规矩

- 升格后的草稿墓碑原样保留，不写升格印记（overview#464）。
- 草稿库根目录现存一个空的 `promotions.json`（`{"version":1,"promotions":{}}`），是旧读者的遗留；bim ui `github-storage.ts` 仍从草稿仓读它，见 [legacy.md](legacy.md)。
- 校验：bim `validate-promotions`（正式库一侧悬空必须为 0）。
