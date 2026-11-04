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
  schema_version int NOT NULL, revision text, revised_at date,
  retired boolean, retired_reason text,
  extra jsonb                              -- 长尾字段
);
CREATE TABLE entity_alt_name (owner_id text REFERENCES entity(id) ON DELETE CASCADE, seq int, name text NOT NULL, type text, ambiguous boolean, note text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE entity_external_id (owner_id text REFERENCES entity(id) ON DELETE CASCADE, key text, value jsonb NOT NULL, PRIMARY KEY (owner_id, key)); -- cbdb_id/wikidata_id/viaf_id/cbdb_id_alt（cbdb_match/cbdb_source 已挪到顶层 external_ids_meta，列在 person）；值原样（cbdb_id 是整数、cbdb_id_alt 是数组），查时用 value = '123'::jsonb
CREATE INDEX ON entity_external_id (key, value);
CREATE TABLE entity_dates (owner_id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, birth int, death int, floruit_start int, floruit_end int, start_year int, end_year int, basis text, extra jsonb);

-- Entity 子类表（主键即 entity.id）
CREATE TABLE person    (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, title_or_office text, native_place text, native_place_basis text, native_place_entity_id text, cbdb_match text, cbdb_source text);
CREATE TABLE collective(id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, concept_id text, collective_kind text, institution_level text, function text, function_basis text);  -- 起讫年见 entity_dates  -- concept_id（官署具体条→概念条，原 parent_id）
CREATE TABLE publisher (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, publisher_kind text, status text);  -- 起讫年见 entity_dates
CREATE TABLE dynasty   (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE);  -- 起止年见 entity_dates；parent_id 进 entity_relation(rel='parent')
CREATE TABLE reign     (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, ruler_name text,  -- dynasty_id 进 entity_relation(rel='in_dynasty')
   ruler_entity_id text);  -- 起止年见 entity_dates
CREATE TABLE office    (id text PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE, concept_id text, office_level text, office_class text, function text,  -- institution_ref 进 entity_relation(rel='institution')
   function_basis text, rank_text text, rank_basis text, base_office_id text, qualifier_kind text, qualifier_name text, qualifier_note text, qualifier_target text);
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
    -- in_dynasty←dynasty_ids | parent←parent_id（仅 dynasty／publisher；office／官署的概念条指向改存 concept_id 列）| predecessor←predecessors | superior←superiors | owner←owner_ids/owners | in_group←group_ids | institution←institution_ids | person←relations[]（亲属师承，kind=type，note=basis，sources 进 extra）
    --   institution 兼收 office.institution_ref 与 seal.institution_ids；in_dynasty 兼收 reign.dynasty_id
  dst text NOT NULL, seq int NOT NULL DEFAULT 0,
  src_key text NOT NULL,   -- 来自文件里哪个键（dynasty_ids／dynasty_id／owners／owner_ids…），同一 rel 有多个来源键，还原要靠它
  role text, year int, start_year int, end_year int, kind text, note text, sources jsonb, extra jsonb,
  -- person 关系双向都存（互为逆称，与文件一致），不在库里派生反向
  PRIMARY KEY (src, src_key, seq)
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
  ai_note text, schema_version int NOT NULL, revision text, revised_at date,
  extra jsonb
);
CREATE TABLE work_title_alt (owner_id text REFERENCES work(id) ON DELETE CASCADE, seq int, title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE work_additional (owner_id text REFERENCES work(id) ON DELETE CASCADE, seq int, book_title text NOT NULL, n_juan int, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 主表：Book ============
CREATE TABLE book (
  id text PRIMARY KEY, repo text NOT NULL,
  work_id text NOT NULL,                  -- edition_of：Book → Work（FK 在后）
  title text NOT NULL, edition text, edition_type edition_type,
  measure_info text, page_count jsonb,                         -- 卷册计量全在 measure 表（11-03 第 3 组删 juan_count／volume_count）
  pub_place text, pub_publisher text, pub_details text, pub_source text,   -- publication_info 的 year／year_iso 已并入 dating（第 1 组）
  dating_certainty text, dating_source text, dating_basis text, dating_era text, dating_reign text, dating_year int, dating_year_range int[] CHECK (array_length(dating_year_range,1) = 2),
  dating_year_uncertain boolean, dating_text text, dating_later_repair jsonb,   -- dating.based_on 已并入 book_base_edition（第 6 组）
  physical_leaf_style text, physical_binding text, physical_dimensions text, physical_condition text, physical_source text,
  lineage jsonb,                          -- 只剩 status／extant_juan／alias／note（第 6 组）
  description_text text, metadata jsonb, zhsy_id text,
  ai_note text, schema_version int NOT NULL, revision text, revised_at date,
  extra jsonb
);
CREATE TABLE book_title_alt (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
-- 馆藏（provenance）：一册多馆，另有印记
CREATE TABLE book_provenance (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, institution text NOT NULL, call_number text, notes text, source text, seals text[], extra jsonb, PRIMARY KEY (owner_id, seq));
-- 印记 provenance[].seal_marks[]：Book → Entity(seal)
CREATE TABLE book_seal_mark (owner_id text, prov_seq int, seq int, seal_id text, position text, note text, source text, extra jsonb,
  PRIMARY KEY (owner_id, prov_seq, seq), FOREIGN KEY (owner_id, prov_seq) REFERENCES book_provenance ON DELETE CASCADE);
CREATE INDEX ON book_seal_mark (seal_id);
-- 所出之本 base_edition[]（第 6 组起吸收 lineage.derived_from 与 dating.based_on）：Book → Book／Work／假想节点
CREATE TABLE book_base_edition (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, role text NOT NULL, relation text, name text, source text NOT NULL,
  book_id text, work_id text, hypothetical_id text, confidence text, evidence text, note text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE INDEX ON book_base_edition (book_id);
CREATE TABLE book_attached_text (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, book_title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE book_location_history (owner_id text REFERENCES book(id) ON DELETE CASCADE, seq int, location text, name text, item_id text, url text, note text, description text, source text, acckey text, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 主表：Collection ============
CREATE TABLE collection (
  id text PRIMARY KEY, repo text NOT NULL,
  subtype coll_subtype NOT NULL, title text NOT NULL, edition text, work_id text,
  count_juan int, count_ce int, count_zhong int, count_han int, count_source text,
  juan_number int, juan_unit text, juan_description text, juan_source text, measure_info text, page_count jsonb, review_status text,
  pub_year text, pub_year_iso text, pub_place text, pub_publisher text, pub_details text,
  dating jsonb, current_location jsonb, description_text text,
  ai_note text, schema_version int NOT NULL, revision text, revised_at date,
  extra jsonb
);
CREATE TABLE collection_title_alt (owner_id text REFERENCES collection(id) ON DELETE CASCADE, seq int, title text NOT NULL, extra jsonb, PRIMARY KEY (owner_id, seq));
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
  rid text, name text, label text, short_name text, url text, types text[], details text, grp text, group_role text,
  root_type text, color_mode text, expected_volumes int, note text, source_label text,
  volumes jsonb, metadata jsonb, extra jsonb,
  PRIMARY KEY (owner_id, seq)
);
CREATE INDEX ON resource (rid);
-- 计量 measures[]（Work 约 6 万、Book 351、Collection 1）
CREATE TABLE measure (owner_id text NOT NULL, seq int NOT NULL, number int, unit text, note text, extra jsonb, PRIMARY KEY (owner_id, seq));
CREATE TABLE source_ref (owner_id text NOT NULL, seq int NOT NULL, sid text, name text, type text, details text, position text, version text, processor_version text, raw jsonb, extra jsonb, PRIMARY KEY (owner_id, seq)); -- sources[]（对象；字符串旧写法进 raw）
-- todo[]：四类共用（现只有 Entity 37 条）
CREATE TABLE record_todo (owner_id text, seq int, what text, by text, date text, extra jsonb, PRIMARY KEY (owner_id, seq));

-- ============ 关系表 ============
-- Book/Work → Collection（成员，带册次）
CREATE TABLE member_of (
  member_id text NOT NULL, member_type char(1) NOT NULL,  -- B / W / C
  collection_id text NOT NULL, seq int NOT NULL,
  volume_index jsonb, grp text, details text, section text, orig_order int,  -- section：S2-I 从 Book 顶层挪入 contained_in[] 项
  sub_items jsonb, extra jsonb,  -- orig_order 从 details「叢編原序 N」抽出
  PRIMARY KEY (member_id, collection_id, seq)
);
CREATE INDEX ON member_of (collection_id);
CREATE TABLE work_relation (src text NOT NULL, dst text NOT NULL, relation text NOT NULL, seq int NOT NULL DEFAULT 0, note text, extra jsonb, PRIMARY KEY (src, relation, dst, seq));
CREATE INDEX ON work_relation (dst, relation);
CREATE TABLE related_book (src text NOT NULL, seq int NOT NULL, dst text NOT NULL, relation text, confidence text, evidence text, extra jsonb, PRIMARY KEY (src, seq));  -- 按文件里的列表存，两侧各存各的（还原要保留顺序）；Book 项是对象 {book_id, relation?, confidence?, evidence?}（第 6 组），Collection 项仍是 id 字符串
CREATE TABLE related_collection (src text NOT NULL, seq int NOT NULL, dst text NOT NULL, PRIMARY KEY (src, seq));
-- 并条账：被并者 → 现行（entity/work/book/collection 共用）。两个来源一起装：
--   现存墓碑文件（src='tombstone'）＋已清墓碑的台账 .claude/qa/purge-tombstones/ledger/*.tsv（src=台账文件名）。
-- live_id 是链末的现行记录（装载时沿链解到底），direct_into 是墓碑上原写的 merged_into；
-- rule/at/by/why 取墓碑的 merged_basis（台账来源取同名列）。11-03 起记录里不再有 merged_in/merged_from/merge_history，
-- 删前的账在台账 history-20261103.tsv（old_id→keeper），装载时也进本表。
CREATE TABLE merged_into (dead_id text PRIMARY KEY, live_id text NOT NULL, direct_into text, record_type char(1) NOT NULL, title text, src text NOT NULL,
  rule text, at text, by text, why text, extra jsonb);
CREATE INDEX ON merged_into (live_id);
-- book-text 专名号反查（D5 才灌）：实体 × 书 × 章 × 次数
-- 专名出处见 book_text.sql 的物化视图 bt_mention
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
