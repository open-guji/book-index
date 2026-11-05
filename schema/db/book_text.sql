-- book-text 仓的规范化表：尚未并进映射的部分（手写草案，GUJI-755）。
-- 已进库（表在 schema.sql 的 bt_*、fragment*）：
--   第一批（bim #309）manifest.json、各版本 index.json（章 bt_chapter、标题层级 bt_heading、other_sources）、辑佚 fragments/*.json；
--   第二批（bim #310）整理本 NNN.json sections（bt_collated、bt_section、bt_section_work、bt_section_alt_title）、
--   original 专名 NNN.entity.json（bt_entity_layer、bt_entity_span，目标拆列，多目标在 target_multi jsonb），
--   计数视图 bt_mention（普通视图，含 target_multi）。
-- 下面这些还没进（价值低，需要时再做第三批）：pages.tsv、original 伴生层文件头、CHANGES.md、bt_file。
-- 不进库（留在 git／COS，库里只记「有没有、什么版本」）：正文 NNN.md 全文、char 每格字、cord 像素框、
--       punct 每个标点、norm 条目、fig 图片、sources/ 抓取素材。正文是否进库做全文检索另定。
-- pages.tsv：行号 → 原书页（kanripo 等）
CREATE TABLE bt_page_break (item_id text, key text, file text, line_no int, pb text NOT NULL,  -- file 存不带扩展名的章键（001），与 bt_chapter.file 可 join
  PRIMARY KEY (item_id, key, file, line_no));
-- original 各伴生层的文件头：版本、对着哪版文本、生成者
CREATE TABLE bt_layer (
  item_id text, key text, n int, layer text NOT NULL,   -- punct / entity / norm / decision / fig / char
  version text, text_version text, schema text, creator text, base_edition text, review jsonb, extra jsonb,  -- stats 已停用（第 11 组）
  -- schema 收 $schema（norm 写作 schema）；creator／base_edition 只有 punct、entity 有；review 为验收记录（date、signed_by、sample…）
  PRIMARY KEY (item_id, key, n, layer), FOREIGN KEY (item_id, key, n) REFERENCES bt_chapter ON DELETE CASCADE
);
-- CHANGES.md：每升一次版一行
CREATE TABLE bt_change (item_id text, key text, seq int, date date, target_item text, ch text, track text, old_version text, new_version text, note text, pr text,  -- 「冊」栏拆 target_item＋ch；track＝文本／标点／实体线
  PRIMARY KEY (item_id, key, seq));

-- ============ 抓取素材与其他文件：只登记，不入内容 ============
CREATE TABLE bt_file (item_id text, path text, kind text NOT NULL,  -- sources / extra / fig / proof / other
  PRIMARY KEY (item_id, path));
