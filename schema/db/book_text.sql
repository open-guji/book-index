-- book-text 仓的规范化表：尚未并进映射的部分（手写草案，GUJI-755 第 4 步第二批）。
-- 已进库（2026-11-05，bim #309，表在 schema.sql 的 bt_*、fragment*）：manifest.json、各版本 index.json
--   （章 bt_chapter、标题层级 bt_heading、other_sources；juan_groups 进 bt_version 的 jsonb 列）、辑佚 fragments/*.json。
-- 下面这些还没进：pages.tsv、original 伴生层文件头、CHANGES.md、整理本 NNN.json sections、专名 NNN.entity.json、
--   bt_file、bt_mention。并进映射时主键改用 bim 的写法（version_id＝「条目id/版本key」，章用 bt_chapter 的 seq）。
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

-- ============ 整理本结构（NNN.json sections[]）与指向 book-index 的链接 ============
CREATE TABLE bt_section (
  item_id text, key text, file text, seq int,
  level int, type text, title text, content_len int,   -- 正文不存，只存长度
  book_title text, author text, author_info text, author_type text, dynasty text, edition text, n_juan int, juan text, page text, section_kind text,
  has_work_ids boolean,                 -- 有 work_ids 键（[]＝明确未链）；链到的 Work 全在 bt_section_work（第 11 组起只写 work_ids 列表）
  book_id text, collection_id text, target_bid text,  -- target_bid 实为 Work id
  evidence jsonb,                       -- 整理证据（原下划线前缀字段，第 11 组收进 evidence）
  extra jsonb,
  PRIMARY KEY (item_id, key, file, seq)
);
CREATE TABLE bt_section_work (item_id text, key text, file text, seq int, i int, work_id text NOT NULL,  -- work_ids[]，i＝数组位置
  PRIMARY KEY (item_id, key, file, seq, i));
CREATE INDEX ON bt_section_work (work_id);

-- ============ 专名（original 的 NNN.entity.json entities[]） ============
-- 每处专名一行；对上的目标另放 bt_entity_span_target（一处可对多条：matched_multi、decomposition.parts）
CREATE TABLE bt_entity_span (
  item_id text, key text, n int, eid text,                 -- eid 为文件内编号（e01384）
  type text NOT NULL,                                      -- people／work／place…，与 book-index subtype 的对表见 README
  text text NOT NULL,
  anchor_start text, anchor_end text, start_offset int, end_offset int,
  status text,                                             -- matched / matched_multi / ambiguous / new_candidate
  canonical_name text, target_coarse text, target_level text, target_note text,  -- coarse 如 part_of_work；level 如 concept
  group_id text, group_text text, group_kind text,         -- 复合专名（如「大理寺評事」）
  source text, candidates jsonb, extra jsonb,
  PRIMARY KEY (item_id, key, n, eid)
);
-- 目标：单目标也写一行，聚合只认这张表。target_id 不一定是 Entity（type=work 时是 Work id），不加外键
CREATE TABLE bt_entity_span_target (
  item_id text, key text, n int, eid text, seq int,
  target_id text NOT NULL, canonical_name text,
  via text NOT NULL CHECK (via IN ('target','multi')),  -- target.entity_id / target.targets[]（decomposition.parts 按 spec 05 不进本格式）
  extra jsonb,
  PRIMARY KEY (item_id, key, n, eid, seq),
  FOREIGN KEY (item_id, key, n, eid) REFERENCES bt_entity_span ON DELETE CASCADE
);
CREATE INDEX ON bt_entity_span_target (target_id);

-- ============ 抓取素材与其他文件：只登记，不入内容 ============
CREATE TABLE bt_file (item_id text, path text, kind text NOT NULL,  -- sources / extra / fig / proof / other
  PRIMARY KEY (item_id, path));

-- ============ 专名计数（物化视图，建库后 REFRESH） ============
-- 实体（或作品）× 文本条目 × 章 × 次数。丛书按章聚合由本视图 join member_of 得出，不另存。
-- 出处反查一律用本视图（schema.sql 的 mention 表已删）。
CREATE MATERIALIZED VIEW bt_mention AS
  SELECT t.target_id, t.item_id, t.n AS chapter, count(*) AS n
  FROM bt_entity_span_target t GROUP BY 1,2,3;
CREATE INDEX ON bt_mention (target_id);
