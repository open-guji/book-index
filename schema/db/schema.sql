-- book-index 规范化数据库表结构（D1 草案，PostgreSQL 16）
-- 真源仍是 git 里的 JSON；本库由 bim 从 JSON 生成，随时可重建。
-- 约定：
--   * 每条主记录一行；数组对象 → 子表（owner_id + seq 保序）；跨记录引用 → 关系表（带外键）。
--   * 已知字段一律有列；未登记的键进该行 extra(jsonb)，保证还原无损（门禁见 README）。
--   * 草稿库（book-index-draft）同表结构，靠 repo 列区分；外键只在 repo 内成立（见 README §外键）。
--   * 外键不在本文件：建表 → COPY → constraints.sql（NOT VALID）→ checks.sql 出悬空清单 → 清干净后 VALIDATE。

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============ 公共：枚举 ============
CREATE TYPE edition_type AS ENUM ('刻本','抄本','稿本','活字本','石印本','油印本','曬印本','鉛印本','影印本','套印本','拓本','印刷本','其他');
CREATE TYPE loss_status  AS ENUM ('lost','partially_extant','extant','undetermined');
CREATE TYPE work_subtype AS ENUM ('book','article','poem','chapter');
CREATE TYPE coll_subtype AS ENUM ('work_collection','book_collection');
CREATE TYPE entity_subtype AS ENUM ('people','collective','dynasty','reign','office','place','seal','publisher');
CREATE TYPE attested_status AS ENUM ('extant','lost','partial','not_seen');

-- ============ 版本：每次建库一行，便于对账 ============
CREATE TABLE build_meta (
  repo text NOT NULL, git_commit text NOT NULL, built_at timestamptz NOT NULL DEFAULT now(),
  schema_version int NOT NULL, PRIMARY KEY (repo)
);

-- ============ 主表：Entity ============
CREATE TABLE entity (
  id text PRIMARY KEY,
  repo text NOT NULL,                      -- 'index' | 'draft'
  subtype entity_subtype NOT NULL,
  primary_name text NOT NULL,
  dynasty text, dynasty_basis text,
  period text, period_basis text,
  review_status text,
  description_text text,
  name_basis text, ai_note text,
  schema_version int NOT NULL, revision text, revised_at date, updated_at text,
  retired boolean, retired_reason text,
  extra jsonb                              -- 长尾字段
);
CREATE TABLE entity_alt_name (owner_id text REFERENCES entity(id) ON DELETE CASCADE, seq int, name text NOT NULL, type text, ambiguous boolean, note text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE entity_external_id (owner_id text REFERENCES entity(id) ON DELETE CASCADE, key text, seq int NOT NULL DEFAULT 0, value text, PRIMARY KEY (owner_id, key, seq)); -- cbdb_id/wikidata_id/viaf_id/cbdb_match/cbdb_source；cbdb_id_alt 为数组，一值一行
CREATE TABLE entity_dates (owner_id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, birth int, death int, floruit_start int, floruit_end int, start_year int, end_year int, basis text, extra jsonb);

-- Entity 子类表（主键即 entity.id）
CREATE TABLE person    (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, title_or_office text, native_place text, native_place_basis text, native_place_entity_id text);
CREATE TABLE collective(id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, collective_kind text, institution_level text, function text, basis text);  -- 起讫年见 entity_dates  -- parent_id 进 entity_relation(rel='parent')
CREATE TABLE publisher (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, publisher_kind text, status text);  -- 起讫年见 entity_dates
CREATE TABLE dynasty   (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE);  -- 起止年见 entity_dates；parent_id 进 entity_relation(rel='parent')
CREATE TABLE reign     (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, ruler_name text,  -- dynasty_id 进 entity_relation(rel='in_dynasty')
   ruler_entity_id text);  -- 起止年见 entity_dates
CREATE TABLE office    (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, office_level text, office_class text, function text,  -- institution_ref 进 entity_relation(rel='institution')
   basis text, rank_text text, rank_basis text, base_office_id text, qualifier_kind text, qualifier_name text, qualifier_note text, qualifier_target text);
CREATE TABLE place     (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, concept_id text, place_level text, modern_text text, modern_relation text, modern_adcode text, modern_note text);
CREATE TABLE seal      (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, seal_text text, seal_kind text, seal_style text, seal_form text, usage_scope text);
CREATE TABLE place_history (owner_id text REFERENCES entity(id) ON DELETE CASCADE, seq int, name text NOT NULL, level text, start_year int, end_year int, note text, parent_id text, extra jsonb, PRIMARY KEY (owner_id, seq));
-- 沿革段的朝代 history[].dynasty_ids[]，可按朝代反查地名
CREATE TABLE place_history_dynasty (owner_id text, hseq int, seq int, dynasty_id text NOT NULL, PRIMARY KEY (owner_id, hseq, seq),
  FOREIGN KEY (owner_id, hseq) REFERENCES place_history ON DELETE CASCADE);
CREATE INDEX ON place_history_dynasty (dynasty_id);
CREATE TABLE entity_image (owner_id text REFERENCES entity(id) ON DELETE CASCADE, seq int, file text, credit text, license text, source_url text, note text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE entity_location (owner_id text REFERENCES entity(id) ON DELETE CASCADE, seq int, name text, place_id text, note text, extra jsonb, PRIMARY KEY (owner_id, seq));

-- Entity 关系表（每种关系只存一遍）
CREATE TABLE entity_relation (
  src text NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  rel text NOT NULL CHECK (rel IN ('in_dynasty','parent','predecessor','superior','owner','in_group','institution','person')),
    -- in_dynasty←dynasty_ids | parent←parent_id | predecessor←predecessors | superior←superiors | owner←owner_ids/owners | in_group←group_ids | institution←institution_ids | person←relations[]（亲属师承，kind=type，note=basis，sources 进 extra）
    --   institution 兼收 office.institution_ref 与 seal.institution_ids；in_dynasty 兼收 reign.dynasty_id
  dst text NOT NULL, seq int NOT NULL DEFAULT 0,
  role text, year int, start_year int, end_year int, kind text, note text, extra jsonb,
  PRIMARY KEY (src, rel, dst, seq)
);
CREATE INDEX ON entity_relation (dst, rel);
CREATE TABLE entity_appears_in (owner_id text REFERENCES entity(id) ON DELETE CASCADE, seq int, ref_type text, ref_id text, position text, note text, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 主表：Work ============
CREATE TABLE work (
  id text PRIMARY KEY, repo text NOT NULL,
  title text NOT NULL, subtype work_subtype, original_title text, title_basis text,
  dynasty text, dynasty_basis text, period text, period_basis text, period_upper text, period_upper_basis text,
  description_text text,
  juan_number int, juan_unit text, juan_description text, juan_source text, measure_info text,
  loss_status loss_status, loss_status_basis text, loss_status_note text,
  authenticity text, authenticity_basis text,
  preferred_book text, review_status text,
  title_emendation jsonb, version_graph jsonb, collection_scale jsonb, publication_info jsonb, appendix jsonb,
  ai_note text, schema_version int NOT NULL, revision text, revised_at date, updated_at text,
  extra jsonb
);
CREATE TABLE work_title_alt (owner_id text REFERENCES work(id) ON DELETE CASCADE, seq int, title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE work_additional (owner_id text REFERENCES work(id) ON DELETE CASCADE, seq int, book_title text NOT NULL, n_juan int, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 主表：Book ============
CREATE TABLE book (
  id text PRIMARY KEY, repo text NOT NULL,
  work_id text NOT NULL,                  -- edition_of：Book → Work（FK 在后）
  title text NOT NULL, edition text, edition_type edition_type, section text,
  juan_number int, juan_unit text, juan_description text, juan_source text, measure_info text,
  volume_count jsonb, page_count jsonb,
  pub_year text, pub_year_iso text, pub_place text, pub_publisher text, pub_details text, pub_source text,
  dating_certainty text, dating_source text, dating_basis text, dating_era text, dating_reign text, dating_year int, dating_year_range int[] CHECK (array_length(dating_year_range,1) = 2), dating_based_on jsonb, dating_later_repair jsonb,
  physical_leaf_style text, physical_binding text, physical_dimensions text, physical_condition text, physical_source text,
  review_status text, lineage jsonb,                          -- 去掉 derived_from／related_to 之后的其余键；边进 book_relation
  current_location jsonb, description_text text, metadata jsonb, zhsy_id text,
  ai_note text, schema_version int NOT NULL, revision text, revised_at date, updated_at text,
  appendix jsonb, extra jsonb
);
CREATE TABLE book_title_alt (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
-- 馆藏（provenance）：一册多馆，另有印记
CREATE TABLE book_provenance (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, institution text NOT NULL, call_number text, notes text, source text, seals text[], extra jsonb, PRIMARY KEY (owner_id, seq));
-- 印记 provenance[].seal_marks[]：Book → Entity(seal)
CREATE TABLE book_seal_mark (owner_id text, prov_seq int, seq int, seal_id text, position text, note text, source text, extra jsonb,
  PRIMARY KEY (owner_id, prov_seq, seq), FOREIGN KEY (owner_id, prov_seq) REFERENCES book_provenance ON DELETE CASCADE);
CREATE INDEX ON book_seal_mark (seal_id);
-- 版本源流 lineage.derived_from[] / related_to[]：Book → Book 有向边
CREATE TABLE book_relation (src text NOT NULL REFERENCES book(id) ON DELETE CASCADE, kind text NOT NULL CHECK (kind IN ('derived_from','related_to')),
  seq int NOT NULL, dst text, relation text, confidence text, evidence text, extra jsonb, PRIMARY KEY (src, kind, seq));
CREATE INDEX ON book_relation (dst);
CREATE TABLE book_base_edition (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, role text, name text, source text, book_id text, note text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE book_attached_text (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, book_title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE book_location_history (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, location text, name text, item_id text, url text, note text, description text, source text, acckey text, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 主表：Collection ============
CREATE TABLE collection (
  id text PRIMARY KEY, repo text NOT NULL,
  subtype coll_subtype NOT NULL, title text NOT NULL, edition text, publisher text, publish_year text, holder text, work_id text,
  count_juan int, count_ce int, count_zhong int, count_han int, count_source text,
  juan_number int, juan_unit text, juan_description text, juan_source text, measure_info text, page_count jsonb, review_status text,
  total_works int, total_volumes int, pub_year text, pub_year_iso text, pub_place text, pub_publisher text, pub_details text,
  dating jsonb, current_location jsonb, description_text text, sections text[],
  ai_note text, schema_version int NOT NULL, revision text, revised_at date, updated_at text,
  extra jsonb
);
CREATE TABLE collection_title_alt (owner_id text REFERENCES collection(id) ON DELETE CASCADE, seq int, title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE collection_editor (owner_id text REFERENCES collection(id) ON DELETE CASCADE, seq int, name text NOT NULL, role text NOT NULL, dynasty text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE collection_content (owner_id text REFERENCES collection(id) ON DELETE CASCADE, seq int, type text, title text, scope text, note text, position text, work_id text, book_id text, collection_id text, related_work_id text, own_work_id text, categorization text, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 三类共用明细表（owner_type + owner_id；不设外键，由触发/检查保证） ============
-- description.sources[]：四类共用（含 Entity），字符串或对象原样
CREATE TABLE description_source (owner_id text, seq int, source jsonb NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
-- 责任者 authorship：Work/Book/Collection → 人物或出版者
CREATE TABLE authorship (
  owner_id text NOT NULL, owner_type char(1) NOT NULL,  -- W/B/C
  seq int NOT NULL, name text NOT NULL, role text NOT NULL,
  entity_id text,           -- 对应 Entity（FK 在后）
  dynasty text, dynasty_basis text, name_basis text, role_basis text, original_name text, note text,
  source jsonb, extra jsonb,
  PRIMARY KEY (owner_id, seq)
);
CREATE INDEX ON authorship (entity_id) WHERE entity_id IS NOT NULL;
CREATE INDEX ON authorship USING gin (name gin_trgm_ops);
-- 著录 indexed_by / emendated_by
CREATE TABLE index_entry (
  owner_id text NOT NULL, owner_type char(1) NOT NULL, kind char(1) NOT NULL DEFAULT 'I', -- I=indexed_by E=emendated_by
  seq int NOT NULL, source text NOT NULL, source_bid text, title_info text, summary text,
  section text, section_basis text, author_info text, juan_count text, juan text, volume text, page text, edition text, catalog_no text,
  note text, in_note_of text, attested_status attested_status, attested_status_raw text, attested_status_note text,
  misattached boolean, misattached_note text, extra jsonb,
  PRIMARY KEY (owner_id, kind, seq)
);
CREATE INDEX ON index_entry (source_bid);
-- 资源
CREATE TABLE resource_group (owner_id text NOT NULL, key text NOT NULL, label text, description text, extra jsonb, PRIMARY KEY (owner_id, key));
CREATE TABLE resource (
  owner_id text NOT NULL, owner_type char(1) NOT NULL, seq int NOT NULL,
  rid text, name text, short_name text, url text, types text[], details text, grp text, group_role text,
  root_type text, color_mode text, expected_volumes int, note text, source_label text,
  volumes jsonb, metadata jsonb, extra jsonb,
  PRIMARY KEY (owner_id, seq)
);
CREATE INDEX ON resource (rid);
-- 计量 measures[]（Work 约 6 万、Book 351、Collection 1）
CREATE TABLE measure (owner_id text NOT NULL, seq int NOT NULL, number int, unit text, note text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE source_ref (owner_id text NOT NULL, seq int NOT NULL, sid text, name text, type text, details text, position text, version text, processor_version text, raw jsonb, extra jsonb, PRIMARY KEY (owner_id, seq)); -- sources[]（对象；字符串旧写法进 raw）
-- 并条历史
CREATE TABLE merge_event (
  owner_id text NOT NULL, kind text NOT NULL,   -- merged_in | merged_from | merge_history
  seq int NOT NULL, other_id text, title text, primary_name text, at text, by text, rule text, why text, title_info text, author text, via text, note text, reason text, date text, extra jsonb,
  PRIMARY KEY (owner_id, kind, seq)
);
CREATE INDEX ON merge_event (other_id);
-- todo[]：四类共用（现只有 Entity 37 条）
CREATE TABLE record_todo (owner_id text, seq int, what text, by text, date text, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 关系表 ============
-- Book/Work → Collection（成员，带册次）
CREATE TABLE member_of (
  member_id text NOT NULL, member_type char(1) NOT NULL,  -- B / W / C
  collection_id text NOT NULL, seq int NOT NULL,
  volume_index jsonb, grp text, details text, sub_items jsonb,
  PRIMARY KEY (member_id, collection_id, seq)
);
CREATE INDEX ON member_of (collection_id);
CREATE TABLE work_relation (src text NOT NULL, dst text NOT NULL, relation text NOT NULL, seq int NOT NULL DEFAULT 0, note text, extra jsonb, PRIMARY KEY (src, relation, dst, seq));
CREATE INDEX ON work_relation (dst, relation);
CREATE TABLE related_book (src text NOT NULL, dst text NOT NULL, PRIMARY KEY (src, dst));
CREATE TABLE related_collection (src text NOT NULL, dst text NOT NULL, PRIMARY KEY (src, dst));
-- 墓碑：被并者 → 现行（entity/work/book/collection 共用）
CREATE TABLE merged_into (dead_id text PRIMARY KEY, live_id text NOT NULL, record_type char(1) NOT NULL);
CREATE INDEX ON merged_into (live_id);
-- book-text 专名号反查（D5 才灌）：实体 × 书 × 章 × 次数
-- item_id 可为 Book 或 Collection id；entity_id 存 book-text 里的原始 id（可能已并条），不加外键，派生时按 merged_into 解析
CREATE TABLE mention (entity_id text NOT NULL, item_id text NOT NULL, chapter text NOT NULL, n int NOT NULL, PRIMARY KEY (entity_id, item_id, chapter));
CREATE INDEX ON mention (item_id);
-- book-text 各表见 book_text.sql（bt_ 前缀与 fragment*）

-- ============ 检索索引 ============
CREATE INDEX ON work  USING gin (title gin_trgm_ops);
CREATE INDEX ON book  USING gin (title gin_trgm_ops);
CREATE INDEX ON collection USING gin (title gin_trgm_ops);
CREATE INDEX ON entity USING gin (primary_name gin_trgm_ops);
CREATE INDEX ON entity_alt_name USING gin (name gin_trgm_ops);
CREATE INDEX ON book (work_id);
CREATE INDEX ON work (period);
CREATE INDEX ON entity (subtype);
CREATE INDEX ON book_provenance (institution);
