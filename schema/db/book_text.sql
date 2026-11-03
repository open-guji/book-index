-- book-text 仓的规范化表（D1 草案补充，GUJI-755）
-- 来源：open-guji/book-text 的 manifest.json、<版本>/index.json、pages.tsv、整理本 NNN.json、
--       original 的 NNN.{punct,entity,norm,decision}.json 文件头与专名、fragments/*.json、CHANGES.md。
-- 不进库（留在 git／COS，库里只记「有没有、什么版本」）：正文 NNN.md 全文、char 每格字、cord 像素框、
--       punct 每个标点、norm 条目、fig 图片、sources/ 抓取素材。正文是否进库做全文检索另定。
-- 表名一律 bt_ 前缀；item_id 是 book-index 的 Work 或 Book id（与 book-index 同一套 id）。

-- ============ 条目与版本 ============
CREATE TABLE bt_item (
  item_id text PRIMARY KEY, item_type char(1) NOT NULL,  -- W / B
  path text NOT NULL,                                     -- Work/c1/c2/c3/<id>
  has_manifest boolean NOT NULL, extra jsonb
);
CREATE TYPE bt_kind AS ENUM ('collated','transcription','original','fragments','other');
-- manifest.versions[] ＋ 该版本目录 index.json 的顶层字段
CREATE TABLE bt_version (
  item_id text NOT NULL REFERENCES bt_item ON DELETE CASCADE, key text NOT NULL, seq int NOT NULL,  -- seq=0 即 default
  kind text, label text, source text, source_name text, source_url text, license text, quality text,
  chapters_total int, script text, is_original boolean,
  version_label text, revision text, revised_at date, guji_markdown text, heading_levels text[],
  line_is_column boolean, catalog_type text, total_entries int, matched_entries int,  -- 目录书型整理本
  source_meta jsonb, edition_note text, references_ jsonb, extra jsonb,
  PRIMARY KEY (item_id, key)
);
CREATE TABLE bt_juan_group (item_id text, key text, seq int, label text NOT NULL, files text[] NOT NULL, extra jsonb,
  PRIMARY KEY (item_id, key, seq), FOREIGN KEY (item_id, key) REFERENCES bt_version ON DELETE CASCADE);

-- ============ 章 ============
CREATE TABLE bt_chapter (
  item_id text, key text, n int, file text NOT NULL, title text,
  has_json boolean, pages text, proofing boolean,
  layers text[],                         -- 有哪些层：char cord punct entity norm decision fig pending（由 *_file 推得）
  text_version text, punct_version text, entity_version text,
  extra jsonb,
  PRIMARY KEY (item_id, key, n), UNIQUE (item_id, key, file),
  FOREIGN KEY (item_id, key) REFERENCES bt_version ON DELETE CASCADE
);
-- 章目录缓存 headings[]（original）
CREATE TABLE bt_heading (item_id text, key text, n int, seq int, level int NOT NULL, label text, anchor text, toc boolean,
  PRIMARY KEY (item_id, key, n, seq), FOREIGN KEY (item_id, key, n) REFERENCES bt_chapter ON DELETE CASCADE);
-- pages.tsv：行号 → 原书页（kanripo 等）
CREATE TABLE bt_page_break (item_id text, key text, file text, line_no int, pb text NOT NULL,
  PRIMARY KEY (item_id, key, file, line_no));
-- original 各伴生层的文件头：版本、对着哪版文本、生成者、统计
CREATE TABLE bt_layer (
  item_id text, key text, n int, layer text NOT NULL,   -- punct / entity / norm / decision / fig / char
  version text, text_version text, schema text, creator text, base_edition text, stats jsonb, extra jsonb,
  PRIMARY KEY (item_id, key, n, layer), FOREIGN KEY (item_id, key, n) REFERENCES bt_chapter ON DELETE CASCADE
);
-- CHANGES.md：每升一次版一行
CREATE TABLE bt_change (item_id text, key text, seq int, date date, volume text, line text, old_version text, new_version text, note text, pr text,
  PRIMARY KEY (item_id, key, seq));

-- ============ 整理本结构（NNN.json sections[]）与指向 book-index 的链接 ============
CREATE TABLE bt_section (
  item_id text, key text, file text, seq int,
  level int, type text, title text, content_len int,   -- 正文不存，只存长度
  work_id text, book_id text, collection_id text, target_bid text,
  extra jsonb,
  PRIMARY KEY (item_id, key, file, seq)
);
CREATE INDEX ON bt_section (work_id) WHERE work_id IS NOT NULL;
CREATE TABLE bt_section_work (item_id text, key text, file text, seq int, i int, work_id text NOT NULL,  -- work_ids[] 多值
  PRIMARY KEY (item_id, key, file, seq, i));
CREATE INDEX ON bt_section_work (work_id);

-- ============ 专名（original 的 NNN.entity.json entities[]） ============
-- 每处专名一行；对上的目标另放 bt_entity_span_target（一处可对多条：matched_multi、decomposition.parts）
CREATE TABLE bt_entity_span (
  item_id text, key text, n int, eid text,                 -- eid 为文件内编号（e01384）
  type text NOT NULL, text text NOT NULL,
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
  via text NOT NULL CHECK (via IN ('target','multi','part')),  -- target.entity_id / target.targets[] / decomposition.parts[]
  extra jsonb,
  PRIMARY KEY (item_id, key, n, eid, seq),
  FOREIGN KEY (item_id, key, n, eid) REFERENCES bt_entity_span ON DELETE CASCADE
);
CREATE INDEX ON bt_entity_span_target (target_id);

-- ============ 辑佚（Work/<id>/fragments/<书名>.json） ============
CREATE TABLE fragment (
  work_id text NOT NULL, title text NOT NULL, path text NOT NULL UNIQUE,
  schema_version int, coverage_level text, coverage_note text,
  fragments_attested int, fragments_attested_note text, fragments_recorded int, text_available boolean,
  loss_status text, statement text, statement_note text, provenance text, provenance_note text,
  cited_in_summary jsonb, cited_in_summary_note text, ai_note text, extra jsonb,
  PRIMARY KEY (work_id, title)
);
CREATE TABLE fragment_based_on (work_id text, title text, seq int, source text, source_bid text, field text, extra jsonb,
  PRIMARY KEY (work_id, title, seq), FOREIGN KEY (work_id, title) REFERENCES fragment ON DELETE CASCADE);
CREATE TABLE fragment_collector (
  work_id text, title text, seq int, collector text, work text, collector_work_id text,
  count int, count_unit text, statement text, note text, basis text, location jsonb, extra jsonb,
  PRIMARY KEY (work_id, title, seq), FOREIGN KEY (work_id, title) REFERENCES fragment ON DELETE CASCADE);
CREATE TABLE fragment_collector_section (
  work_id text, title text, cseq int, seq int, file text, idx int, section_title text, part text, juan_no int, lei text, extra jsonb,
  PRIMARY KEY (work_id, title, cseq, seq));
-- 佚文条目
CREATE TABLE fragment_piece (
  work_id text, title text, seq int, piece_title text, text text, text_status text,
  attested_by text, confidence text, note text, extra jsonb,
  PRIMARY KEY (work_id, title, seq), FOREIGN KEY (work_id, title) REFERENCES fragment ON DELETE CASCADE);
CREATE INDEX ON fragment_piece USING gin (text gin_trgm_ops);
CREATE TABLE fragment_piece_collector (work_id text, title text, pseq int, seq int, collector text, work text, collector_work_id text,
  PRIMARY KEY (work_id, title, pseq, seq));
CREATE TABLE fragment_citation (work_id text, title text, pseq int, seq int, raw text, cited_title text, note text, extra jsonb,
  PRIMARY KEY (work_id, title, pseq, seq));

-- ============ 抓取素材与其他文件：只登记，不入内容 ============
CREATE TABLE bt_file (item_id text, path text, kind text NOT NULL,  -- sources / extra / fig / other
  PRIMARY KEY (item_id, path));

-- ============ 专名计数（物化视图，建库后 REFRESH） ============
-- 实体（或作品）× 文本条目 × 章 × 次数。丛书按章聚合由本视图 join member_of 得出，不另存。
-- schema.sql 的 mention 表留给 D5 写派生结果；章标识口径（n 与章文件键 004）D5 时统一。
CREATE MATERIALIZED VIEW bt_mention AS
  SELECT t.target_id, t.item_id, t.n AS chapter, count(*) AS n
  FROM bt_entity_span_target t GROUP BY 1,2,3;
CREATE INDEX ON bt_mention (target_id);
